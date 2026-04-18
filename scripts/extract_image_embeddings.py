"""이미지 임베딩 추출 — S3 이미지 → ResNet50 임베딩.

S3 URL에서 이미지를 다운로드하고 pre-trained ResNet50의 avgpool 출력(2048-dim)을
추출한 뒤 PCA로 32-dim으로 축소.

배치 처리 + 이어하기 지원 + MPS(Apple Silicon GPU) 활용.

Usage:
    PYTHONPATH=src python3 scripts/extract_image_embeddings.py
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
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from sklearn.decomposition import PCA

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "k-artmarket-cleansed-known.csv"
RAW_PATH = ROOT / "data" / "k-artmarket 1차 데이터 정제 - k_artmarket_works_updated_s3.csv"
EMBED_RAW_PATH = ROOT / "data" / "image_embeddings_raw.npy"
EMBED_PCA_PATH = ROOT / "data" / "image_embeddings_pca32.npy"
INDEX_PATH = ROOT / "data" / "image_embeddings_index.csv"
CHECKPOINT_PATH = ROOT / "data" / "image_embed_checkpoint.npz"

BATCH_SIZE = 32
PCA_DIM = 32
DELAY = 0.05  # S3 요청 간격 (초)
CHECKPOINT_INTERVAL = 500  # 중간 저장 간격


def build_model(device: str) -> tuple[torch.nn.Module, transforms.Compose]:
    """Pre-trained ResNet50 피처 추출기 + 전처리 변환."""
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    # avgpool 이후 fc 이전의 2048-dim 벡터 추출
    model.fc = torch.nn.Identity()
    model = model.to(device)
    model.eval()

    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return model, transform


def download_image(url: str, timeout: int = 10) -> Image.Image | None:
    """URL에서 이미지 다운로드."""
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        return img
    except Exception:
        return None


def main() -> None:
    """이미지 임베딩 추출 메인."""
    # 디바이스 선택
    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    logger.info("Device: %s", device)

    # 모델 로드
    model, transform = build_model(device)
    logger.info("ResNet50 loaded (2048-dim feature extractor)")

    # 학습 데이터의 이미지 URL 매핑
    data = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    raw = pd.read_csv(RAW_PATH, encoding="utf-8-sig", header=1)

    # idx로 매핑
    data["idx"] = data["idx"].astype(str)
    raw["idx"] = raw["idx"].astype(str)
    url_map = raw.set_index("idx")["img_file_name"].to_dict()

    # 학습 데이터에 URL 매핑
    data["img_url"] = data["idx"].map(url_map)
    has_url = data["img_url"].notna()
    logger.info("학습 데이터: %d건, URL 매핑: %d건 (%.1f%%)",
                len(data), has_url.sum(), has_url.sum() / len(data) * 100)

    targets = data[has_url].reset_index(drop=True)

    # 이어하기: 체크포인트 로드
    start_idx = 0
    embeddings_list = []
    valid_indices = []

    if CHECKPOINT_PATH.exists():
        ckpt = np.load(CHECKPOINT_PATH, allow_pickle=True)
        embeddings_list = list(ckpt["embeddings"])
        valid_indices = list(ckpt["indices"])
        start_idx = int(ckpt["next_idx"])
        logger.info("체크포인트 로드: %d건 완료, %d부터 재개", len(valid_indices), start_idx)

    # 배치 처리
    total = len(targets)
    failed = 0

    for i in range(start_idx, total, BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, total)
        batch_imgs = []
        batch_idxs = []

        for j in range(i, batch_end):
            url = targets.loc[j, "img_url"]
            img = download_image(url)
            if img is not None:
                try:
                    tensor = transform(img)
                    batch_imgs.append(tensor)
                    batch_idxs.append(j)
                except Exception:
                    failed += 1
            else:
                failed += 1
            time.sleep(DELAY)

        if batch_imgs:
            batch_tensor = torch.stack(batch_imgs).to(device)
            with torch.no_grad():
                features = model(batch_tensor).cpu().numpy()  # (batch, 2048)
            embeddings_list.extend(features)
            valid_indices.extend(batch_idxs)

        # 진행 로그 + 체크포인트
        if (i // BATCH_SIZE) % (CHECKPOINT_INTERVAL // BATCH_SIZE) == 0 or batch_end == total:
            logger.info(
                "  [%d/%d] extracted=%d, failed=%d (%.1f%%)",
                batch_end, total, len(valid_indices), failed,
                len(valid_indices) / max(1, batch_end) * 100,
            )
            # 체크포인트 저장
            np.savez(
                CHECKPOINT_PATH,
                embeddings=np.array(embeddings_list),
                indices=np.array(valid_indices),
                next_idx=batch_end,
            )

    # 최종 저장
    embeddings = np.array(embeddings_list)
    logger.info("Raw embeddings: %s", embeddings.shape)

    # PCA 축소 (2048 → 32)
    pca = PCA(n_components=PCA_DIM, random_state=42)
    embeddings_pca = pca.fit_transform(embeddings)
    explained = pca.explained_variance_ratio_.sum()
    logger.info("PCA %d-dim: explained variance=%.3f", PCA_DIM, explained)

    # 저장
    np.save(EMBED_RAW_PATH, embeddings)
    np.save(EMBED_PCA_PATH, embeddings_pca)

    # 인덱스 매핑 저장
    index_df = targets.loc[valid_indices, ["idx"]].reset_index(drop=True)
    index_df.to_csv(INDEX_PATH, index=False, encoding="utf-8-sig")

    logger.info("=== 완료: %d/%d 이미지 임베딩 (PCA %d-dim) ===",
                len(valid_indices), total, PCA_DIM)
    logger.info("  Raw: %s", EMBED_RAW_PATH)
    logger.info("  PCA: %s", EMBED_PCA_PATH)
    logger.info("  Index: %s", INDEX_PATH)

    # 체크포인트 정리
    CHECKPOINT_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
