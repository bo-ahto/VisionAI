"""CLIP 이미지 임베딩 추출 — S3 이미지 → ViT-B/32 CLIP 512-dim.

CLIP은 이미지-텍스트 쌍으로 학습되어 시각적 의미/스타일을 더 잘 캡처.
ResNet50(ImageNet) 대비 미술품 가격 예측에 더 적합.

Usage:
    python3 scripts/extract_clip_embeddings.py
"""
from __future__ import annotations

import io
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import torch
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "k-artmarket-cleansed-known.csv"
RAW_PATH = ROOT / "data" / "k-artmarket 1차 데이터 정제 - k_artmarket_works_updated_s3.csv"
EMBED_PATH = ROOT / "data" / "clip_embeddings.npy"
INDEX_PATH = ROOT / "data" / "clip_embeddings_index.csv"
CHECKPOINT_PATH = ROOT / "data" / "clip_embed_checkpoint.npz"

BATCH_SIZE = 32
DELAY = 0.05
CHECKPOINT_INTERVAL = 500


def main() -> None:
    """CLIP 임베딩 추출."""
    import open_clip

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    logger.info("Device: %s", device)

    # CLIP 모델 로드
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai"
    )
    model = model.to(device)
    model.eval()
    logger.info("CLIP ViT-B/32 loaded (512-dim)")

    # URL 매핑
    data = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    raw = pd.read_csv(RAW_PATH, encoding="utf-8-sig", header=1)

    data["idx"] = data["idx"].astype(str)
    raw["idx"] = raw["idx"].astype(str)
    url_map = raw.set_index("idx")["img_file_name"].to_dict()

    data["img_url"] = data["idx"].map(url_map)
    has_url = data["img_url"].notna()
    targets = data[has_url].reset_index(drop=True)
    logger.info("대상: %d건 (URL 매핑: %.1f%%)", len(targets), has_url.sum() / len(data) * 100)

    # 이어하기
    start_idx = 0
    embeddings_list = []
    valid_indices = []

    if CHECKPOINT_PATH.exists():
        ckpt = np.load(CHECKPOINT_PATH, allow_pickle=True)
        embeddings_list = list(ckpt["embeddings"])
        valid_indices = list(ckpt["indices"])
        start_idx = int(ckpt["next_idx"])
        logger.info("체크포인트: %d건 완료, %d부터 재개", len(valid_indices), start_idx)

    total = len(targets)
    failed = 0

    for i in range(start_idx, total, BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, total)
        batch_imgs = []
        batch_idxs = []

        for j in range(i, batch_end):
            url = targets.loc[j, "img_url"]
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    tensor = preprocess(img)
                    batch_imgs.append(tensor)
                    batch_idxs.append(j)
                else:
                    failed += 1
            except Exception:
                failed += 1
            time.sleep(DELAY)

        if batch_imgs:
            batch_tensor = torch.stack(batch_imgs).to(device)
            with torch.no_grad():
                features = model.encode_image(batch_tensor)
                features = features / features.norm(dim=-1, keepdim=True)  # L2 정규화
                features = features.cpu().numpy()
            embeddings_list.extend(features)
            valid_indices.extend(batch_idxs)

        if (i // BATCH_SIZE) % (CHECKPOINT_INTERVAL // BATCH_SIZE) == 0 or batch_end == total:
            logger.info("  [%d/%d] extracted=%d, failed=%d (%.1f%%)",
                        batch_end, total, len(valid_indices), failed,
                        len(valid_indices) / max(1, batch_end) * 100)
            np.savez(CHECKPOINT_PATH,
                     embeddings=np.array(embeddings_list) if embeddings_list else np.empty((0, 512)),
                     indices=np.array(valid_indices),
                     next_idx=batch_end)

    # 최종 저장
    embeddings = np.array(embeddings_list)
    logger.info("CLIP embeddings: %s", embeddings.shape)

    np.save(EMBED_PATH, embeddings)

    index_df = targets.loc[valid_indices, ["idx"]].reset_index(drop=True)
    index_df.to_csv(INDEX_PATH, index=False, encoding="utf-8-sig")

    logger.info("=== 완료: %d/%d CLIP 512-dim 임베딩 ===", len(valid_indices), total)

    CHECKPOINT_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
