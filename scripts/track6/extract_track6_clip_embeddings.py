#!/usr/bin/env python3
"""Extract CLIP embeddings for Track6 rows keyed by _track6_row_id."""
from __future__ import annotations

import argparse
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
import torch
from PIL import Image


REPO = Path(__file__).resolve().parents[2]
BASE_DIR = REPO / "data" / "track6" / "image_multimodal"
MANIFEST_PATH = BASE_DIR / "track6_image_manifest.csv"
DEFAULT_EMBED_PATH = BASE_DIR / "track6_clip_pilot_embeddings.npy"
DEFAULT_INDEX_PATH = BASE_DIR / "track6_clip_pilot_index.csv"
DEFAULT_FAILURE_PATH = BASE_DIR / "track6_clip_pilot_failures.csv"
DEFAULT_REPORT_PATH = REPO / "docs" / "track6" / "experiments" / "track6_clip_pilot_embedding_report.md"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; VisionAITrack6CLIP/1.0)",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--splits", nargs="+", default=["train", "val_cold", "test_cold"])
    parser.add_argument("--sources", nargs="+", default=["saatchi", "artsy"])
    parser.add_argument("--per-split-source", type=int, default=5)
    parser.add_argument("--train-per-source", type=int)
    parser.add_argument("--val-cold-per-source", type=int)
    parser.add_argument("--test-cold-per-source", type=int)
    parser.add_argument("--val-warm-per-source", type=int)
    parser.add_argument("--test-warm-per-source", type=int)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--sleep-seconds", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model-name", default="ViT-B-32")
    parser.add_argument("--pretrained", default="openai")
    parser.add_argument("--embedding-output", type=Path, default=DEFAULT_EMBED_PATH)
    parser.add_argument("--index-output", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--failure-output", type=Path, default=DEFAULT_FAILURE_PATH)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--checkpoint-every", type=int, default=250)
    parser.add_argument("--progress-every", type=int, default=1)
    parser.add_argument("--fetch-workers", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--fetch-window", type=int, default=128)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--retry-backoff", type=float, default=2.0)
    return parser.parse_args()


def sample_size_for_split(args: argparse.Namespace, split: str) -> int:
    overrides = {
        "train": args.train_per_source,
        "val_cold": args.val_cold_per_source,
        "test_cold": args.test_cold_per_source,
        "val_warm": args.val_warm_per_source,
        "test_warm": args.test_warm_per_source,
    }
    value = overrides.get(split)
    return args.per_split_source if value is None else value


def select_targets(args: argparse.Namespace) -> pd.DataFrame:
    manifest = pd.read_csv(MANIFEST_PATH, low_memory=False)
    frame = manifest[
        manifest["has_image_url"]
        & manifest["split"].isin(args.splits)
        & manifest["resolved_source_bucket"].isin(args.sources)
    ].copy()
    samples: list[pd.DataFrame] = []
    for (split, _source), group in frame.groupby(["split", "resolved_source_bucket"], sort=False):
        sample_size = min(sample_size_for_split(args, split), len(group))
        if sample_size <= 0:
            continue
        samples.append(group.sample(n=sample_size, random_state=args.seed))
    if not samples:
        return frame.iloc[0:0].copy()
    out = pd.concat(samples, ignore_index=True)
    return out.sort_values(["split", "resolved_source_bucket", "_track6_row_id"]).reset_index(drop=True)


def fetch_image(url: str, timeout: float, max_retries: int, retry_backoff: float) -> Image.Image:
    retry_statuses = {429, 500, 502, 503, 504}
    last_response: requests.Response | None = None
    last_exception: Exception | None = None
    for attempt in range(max(0, max_retries) + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
        except requests.RequestException as exc:
            last_exception = exc
            if attempt >= max_retries:
                raise
            time.sleep(retry_backoff * (2 ** attempt))
            continue
        last_response = response
        if response.status_code not in retry_statuses or attempt >= max_retries:
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content)).convert("RGB")
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            sleep_seconds = float(retry_after)
        else:
            sleep_seconds = retry_backoff * (2 ** attempt)
        time.sleep(sleep_seconds)
    if last_exception is not None:
        raise last_exception
    assert last_response is not None
    last_response.raise_for_status()
    return Image.open(io.BytesIO(last_response.content)).convert("RGB")


def fetch_target(
    record: dict[str, Any],
    timeout: float,
    max_retries: int,
    retry_backoff: float,
) -> tuple[dict[str, Any], Image.Image | None, int, str | None]:
    started = time.time()
    try:
        image = fetch_image(str(record["image_url"]), timeout, max_retries, retry_backoff)
        return record, image, int((time.time() - started) * 1000), None
    except Exception as exc:  # noqa: BLE001
        return record, None, int((time.time() - started) * 1000), f"{type(exc).__name__}: {exc}"


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def repo_relative(path: Path) -> str:
    resolved = path if path.is_absolute() else REPO / path
    try:
        return str(resolved.resolve().relative_to(REPO))
    except ValueError:
        return str(resolved.resolve())


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO / path


def load_existing_outputs(args: argparse.Namespace) -> tuple[list[np.ndarray], list[dict[str, Any]], list[dict[str, Any]], set[int]]:
    embedding_path = repo_path(args.embedding_output)
    index_path = repo_path(args.index_output)
    failure_path = repo_path(args.failure_output)
    if not args.resume or not embedding_path.exists() or not index_path.exists():
        return [], [], [], set()

    existing_embeddings = np.load(embedding_path)
    existing_index = pd.read_csv(index_path, low_memory=False)
    if len(existing_embeddings) != len(existing_index):
        raise ValueError(
            f"resume mismatch: embeddings rows {len(existing_embeddings)} != index rows {len(existing_index)}"
        )
    embeddings = [row.astype(np.float32) for row in existing_embeddings]
    index_rows = existing_index.to_dict("records")
    done_ids = set(pd.to_numeric(existing_index["_track6_row_id"], errors="coerce").dropna().astype(int).tolist())
    failures: list[dict[str, Any]] = []
    existing_failure_count = 0
    if failure_path.exists() and failure_path.stat().st_size > 1:
        existing_failure_count = len(pd.read_csv(failure_path, low_memory=False))
    print(
        f"resume loaded successes={len(index_rows)} previous_failures_to_retry={existing_failure_count}",
        flush=True,
    )
    return embeddings, index_rows, failures, done_ids


def save_outputs(
    args: argparse.Namespace,
    embeddings: list[np.ndarray],
    index_rows: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    *,
    target_count: int,
    device: str,
    write_final_report: bool,
) -> None:
    embedding_path = repo_path(args.embedding_output)
    index_path = repo_path(args.index_output)
    failure_path = repo_path(args.failure_output)
    report_path = repo_path(args.report_output)
    embedding_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    failure_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    embedding_array = np.vstack(embeddings).astype(np.float32) if embeddings else np.empty((0, 512), dtype=np.float32)
    np.save(embedding_path, embedding_array)
    pd.DataFrame(index_rows).to_csv(index_path, index=False)
    failure_columns = ["_track6_row_id", "split", "resolved_source_bucket", "image_url", "error"]
    pd.DataFrame(failures, columns=failure_columns).to_csv(failure_path, index=False)
    if write_final_report:
        write_report(
            args,
            target_count=target_count,
            success_count=len(index_rows),
            failure_count=len(failures),
            embedding_shape=embedding_array.shape,
            device=device,
        )


def load_model(args: argparse.Namespace, device: str) -> tuple[Any, Any]:
    import open_clip

    model, _, preprocess = open_clip.create_model_and_transforms(
        args.model_name,
        pretrained=args.pretrained,
    )
    model = model.to(device)
    model.eval()
    return model, preprocess


def append_success(
    embeddings: list[np.ndarray],
    index_rows: list[dict[str, Any]],
    record: dict[str, Any],
    vector: np.ndarray,
    elapsed_ms: int,
) -> None:
    embeddings.append(vector.astype(np.float32))
    index_rows.append({
        "_track6_row_id": record["_track6_row_id"],
        "split": record["split"],
        "resolved_source_bucket": record["resolved_source_bucket"],
        "track4_source": record["track4_source"],
        "artist_key": record["artist_key"],
        "artist_name_ko": record["artist_name_ko"],
        "title_raw": record["title_raw"],
        "image_url": record["image_url"],
        "elapsed_ms": elapsed_ms,
    })


def append_failure(
    failures: list[dict[str, Any]],
    record: dict[str, Any],
    error: str,
) -> None:
    failures.append({
        "_track6_row_id": record["_track6_row_id"],
        "split": record["split"],
        "resolved_source_bucket": record["resolved_source_bucket"],
        "image_url": record["image_url"],
        "error": error,
    })


def encode_pending(
    pending: list[tuple[dict[str, Any], Image.Image, int]],
    *,
    model: Any,
    preprocess: Any,
    device: str,
    embeddings: list[np.ndarray],
    index_rows: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    if not pending:
        return

    tensors: list[torch.Tensor] = []
    valid: list[tuple[dict[str, Any], int]] = []
    for record, image, elapsed_ms in pending:
        try:
            tensors.append(preprocess(image))
            valid.append((record, elapsed_ms))
        except Exception as exc:  # noqa: BLE001
            append_failure(failures, record, f"{type(exc).__name__}: {exc}")

    pending.clear()
    if not tensors:
        return

    try:
        batch = torch.stack(tensors).to(device)
        with torch.no_grad():
            features = model.encode_image(batch)
            features = features / features.norm(dim=-1, keepdim=True)
        vectors = features.cpu().numpy().astype(np.float32)
        for vector, (record, elapsed_ms) in zip(vectors, valid, strict=True):
            append_success(embeddings, index_rows, record, vector, elapsed_ms)
    except Exception as exc:  # noqa: BLE001
        for record, _elapsed_ms in valid:
            append_failure(failures, record, f"{type(exc).__name__}: {exc}")


def write_report(
    args: argparse.Namespace,
    target_count: int,
    success_count: int,
    failure_count: int,
    embedding_shape: tuple[int, ...],
    device: str,
) -> None:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success_rate = success_count / target_count if target_count else 0.0
    split_sample_config = {
        "default_per_split_source": args.per_split_source,
        "train": sample_size_for_split(args, "train"),
        "val_cold": sample_size_for_split(args, "val_cold"),
        "test_cold": sample_size_for_split(args, "test_cold"),
        "val_warm": sample_size_for_split(args, "val_warm"),
        "test_warm": sample_size_for_split(args, "test_warm"),
    }
    text = f"""# Track6 CLIP 임베딩 파일럿 결과

- 생성 시각: {generated_at}
- 목적: Track6 `_track6_row_id` 기준으로 이미지 임베딩을 생성할 수 있는지 확인한다.
- 대상 split: `{', '.join(args.splits)}`
- 대상 출처: `{', '.join(args.sources)}`
- split/출처별 샘플 수 설정: `{split_sample_config}`
- 모델: `{args.model_name}` / pretrained `{args.pretrained}`
- 실행 장치: `{device}`

## 결과

- 대상 이미지 수: {target_count}
- 성공 이미지 수: {success_count}
- 실패 이미지 수: {failure_count}
- 성공률: {success_rate:.4f}
- 임베딩 shape: `{embedding_shape}`
- 임베딩 파일: `{repo_relative(args.embedding_output)}`
- 인덱스 파일: `{repo_relative(args.index_output)}`
- 실패 파일: `{repo_relative(args.failure_output)}`

## 해석

- 이 파일럿이 성공하면 전체 Track6 이미지 임베딩 추출로 확장할 수 있다.
- 인덱스 파일에 `_track6_row_id`가 남기 때문에 기존 `idx` 기반 임베딩보다 안전하게 split 데이터와 결합할 수 있다.
- 다음 단계는 Cold 기준 이미지 단독 모델과 정형 피처 + 이미지 결합 모델을 비교하는 것이다.
"""
    repo_path(args.report_output).write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    targets = select_targets(args)
    device = device_name()
    model, preprocess = load_model(args, device)

    embeddings, index_rows, failures, done_ids = load_existing_outputs(args)
    total_targets = len(targets)
    if done_ids:
        targets = targets[~targets["_track6_row_id"].astype(int).isin(done_ids)].reset_index(drop=True)
        print(f"resume remaining targets={len(targets)} of total={total_targets}", flush=True)

    pending: list[tuple[dict[str, Any], Image.Image, int]] = []
    records = targets.to_dict("records")
    processed = 0
    fetch_workers = max(1, args.fetch_workers)
    batch_size = max(1, args.batch_size)
    fetch_window = max(batch_size, args.fetch_window)

    with ThreadPoolExecutor(max_workers=fetch_workers) as executor:
        for start in range(0, len(records), fetch_window):
            window = records[start:start + fetch_window]
            futures = [
                executor.submit(fetch_target, record, args.timeout, args.max_retries, args.retry_backoff)
                for record in window
            ]
            for future in as_completed(futures):
                record, image, elapsed_ms, error = future.result()
                processed += 1
                if error is not None or image is None:
                    append_failure(failures, record, error or "Unknown image fetch error")
                else:
                    pending.append((record, image, elapsed_ms))
                    if len(pending) >= batch_size:
                        encode_pending(
                            pending,
                            model=model,
                            preprocess=preprocess,
                            device=device,
                            embeddings=embeddings,
                            index_rows=index_rows,
                            failures=failures,
                        )

                should_log_progress = (
                    args.progress_every <= 1
                    or processed % args.progress_every == 0
                    or processed == len(records)
                )
                if should_log_progress:
                    done_count = len(index_rows) + len(failures) + len(pending)
                    print(
                        f"[{processed}/{len(records)} remaining, {done_count}/{total_targets} total] "
                        f"success={len(embeddings)} pending={len(pending)} failures={len(failures)}",
                        flush=True,
                    )

                if args.checkpoint_every > 0 and processed % args.checkpoint_every == 0:
                    encode_pending(
                        pending,
                        model=model,
                        preprocess=preprocess,
                        device=device,
                        embeddings=embeddings,
                        index_rows=index_rows,
                        failures=failures,
                    )
                    save_outputs(
                        args,
                        embeddings,
                        index_rows,
                        failures,
                        target_count=total_targets,
                        device=device,
                        write_final_report=False,
                    )
                    print(f"checkpoint wrote {repo_relative(args.embedding_output)} rows={len(index_rows)}", flush=True)
                time.sleep(args.sleep_seconds)

    encode_pending(
        pending,
        model=model,
        preprocess=preprocess,
        device=device,
        embeddings=embeddings,
        index_rows=index_rows,
        failures=failures,
    )

    save_outputs(
        args,
        embeddings,
        index_rows,
        failures,
        target_count=total_targets,
        device=device,
        write_final_report=True,
    )
    embedding_shape = (len(embeddings), 512) if embeddings else (0, 512)
    print(f"wrote {repo_relative(args.embedding_output)} shape={embedding_shape}", flush=True)
    print(f"wrote {repo_relative(args.index_output)} rows={len(index_rows)}", flush=True)
    print(f"wrote {repo_relative(args.failure_output)} rows={len(failures)}", flush=True)
    print(f"wrote {repo_relative(args.report_output)}", flush=True)


if __name__ == "__main__":
    main()
