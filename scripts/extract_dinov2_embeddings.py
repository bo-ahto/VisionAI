"""V5 Track B — DINOv2 embedding 추출 (Artsy 7,640건).

코덱스 권고:
- DINOv2-base (M2 Mac MPS 적합, retrieval 직접적, 텍스트 의존 X)
- Cache key: artwork_id + URL hash (재사용 검증 가능)
- LAO split 분리는 다음 단계에서 (본 스크립트는 raw embedding 만)

Output: model_test_results/dinov2_embeddings.parquet
- columns: artwork_id, image_url, url_hash, embedding (768-dim list)

Usage: python3 scripts/extract_dinov2_embeddings.py [--limit N]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"
CACHE_DIR = ROOT / ".cache" / "dinov2_images"
EMBED_PATH = OUT_DIR / "dinov2_embeddings.parquet"

MODEL_NAME = "facebook/dinov2-base"  # 768-dim


def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def download_image(url: str, timeout: int = 10) -> Image.Image | None:
    """Download image with simple disk cache (URL hash key)."""
    h = url_hash(url)
    cache_path = CACHE_DIR / f"{h}.bin"
    if cache_path.exists():
        try:
            with cache_path.open("rb") as f:
                return Image.open(io.BytesIO(f.read())).convert("RGB")
        except Exception:
            pass  # corrupt, redownload
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with cache_path.open("wb") as f:
            f.write(r.content)
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception as e:
        logger.warning(f"Download fail {h}: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="작품 수 제한 (테스트용)")
    parser.add_argument("--batch", type=int, default=8, help="GPU batch size")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("V5 Track B — DINOv2 embedding 추출")
    logger.info("=" * 60)

    # 1. Load metadata
    df = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    df = df[df["image_url"].notna()].copy().reset_index(drop=True)
    if args.limit:
        df = df.head(args.limit)
    logger.info(f"Total artworks: {len(df)}")

    df["url_hash"] = df["image_url"].apply(url_hash)

    # 2. Resume check
    if EMBED_PATH.exists():
        existing = pd.read_parquet(EMBED_PATH)
        existing_ids = set(existing["artwork_id"].astype(str))
        logger.info(f"Resume: {len(existing_ids)} 기존 embedding")
        df_todo = df[~df["artwork_id"].astype(str).isin(existing_ids)].copy()
    else:
        existing = pd.DataFrame()
        df_todo = df.copy()
    logger.info(f"Embed 대상: {len(df_todo)}")

    if len(df_todo) == 0:
        logger.info("✓ All embeddings already cached.")
        return

    # 3. Load model
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    logger.info(f"Loading {MODEL_NAME} on {device}...")
    processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME).to(device).eval()
    logger.info(f"  Model loaded ({sum(p.numel() for p in model.parameters()) / 1e6:.0f}M params)")

    # 4. Extract embeddings (batch)
    results = []
    fail_count = 0
    t0 = time.time()
    batch_size = args.batch

    for i in range(0, len(df_todo), batch_size):
        batch = df_todo.iloc[i:i + batch_size]
        images = []
        meta = []
        for _, row in batch.iterrows():
            img = download_image(row["image_url"])
            if img is None:
                fail_count += 1
                continue
            images.append(img)
            meta.append({"artwork_id": str(row["artwork_id"]), "image_url": row["image_url"], "url_hash": row["url_hash"]})

        if not images:
            continue

        try:
            inputs = processor(images=images, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = model(**inputs)
            # CLS token (first token) — 768-dim for dinov2-base
            embeds = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            for m, e in zip(meta, embeds):
                results.append({**m, "embedding": e.tolist()})
        except Exception as e:
            logger.warning(f"Batch {i} embed fail: {e}")
            fail_count += len(images)

        # Progress + intermediate save (every ~100 items, batch-aligned)
        if len(results) > 0 and len(results) >= getattr(main, "_next_save", 100):
            elapsed = time.time() - t0
            eta = elapsed / len(results) * (len(df_todo) - len(results))
            logger.info(f"  [{len(results)}/{len(df_todo)}] {elapsed:.0f}s elapsed, ETA {eta:.0f}s, fails {fail_count}")
            # Intermediate save
            interim = pd.DataFrame(results)
            if not existing.empty:
                interim = pd.concat([existing, interim], ignore_index=True)
            interim.to_parquet(EMBED_PATH, index=False)
            main._next_save = len(results) + 100

    # 5. Final save
    new_df = pd.DataFrame(results)
    if not existing.empty:
        new_df = pd.concat([existing, new_df], ignore_index=True)
    new_df.to_parquet(EMBED_PATH, index=False)

    elapsed = time.time() - t0
    logger.info(f"\n✓ Saved {len(new_df)} embeddings → {EMBED_PATH}")
    logger.info(f"  Total time: {elapsed:.0f}s, fails: {fail_count}")
    logger.info(f"  Embedding dim: {len(new_df['embedding'].iloc[0])}")


if __name__ == "__main__":
    main()
