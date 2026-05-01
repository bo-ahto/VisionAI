"""v3.4-2 step 3 pilot sampling: 650 target + 350 stratified random.

코덱스 권장 hybrid sampling:
- target cohort 650: cold artists + low work_count + price=0 + 매체 편중 방지
- stratified random 350: medium × price band × artist activity bucket

산출물: model_test_results/v3_diagnostics/saatchi_pilot_sample_urls.json
"""

from __future__ import annotations

import json
import logging
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from train_primary_market_v3_filtered import _warm_mask, load_data, prepare_features

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = ROOT / "model_test_results" / "v3_diagnostics"
SAMPLE_OUT_PATH = OUT_DIR / "saatchi_pilot_sample_urls.json"

TARGET_N = 650
STRATIFIED_N = 350
TOTAL_N = TARGET_N + STRATIFIED_N
RNG_SEED = 42


def price_band(p: float) -> str:
    if p < 1_000_000:
        return "low"
    if p < 5_000_000:
        return "mid"
    if p < 15_000_000:
        return "high"
    return "ultra"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(RNG_SEED)

    df = load_data()
    df = df[df.get("is_excluded_for_training", 0) != 1].reset_index(drop=True)
    _, _, groups = prepare_features(df)
    wmask = _warm_mask(groups)

    saatchi = df[df["source"] == "saatchi"].copy().reset_index(drop=True)
    saatchi_idx_in_full = df.index[df["source"] == "saatchi"].to_numpy()
    saatchi["warm"] = wmask[saatchi_idx_in_full]
    saatchi["medium_cat"] = saatchi["medium_category"].astype(str)
    saatchi["price_band"] = saatchi["price_krw"].apply(price_band)

    artist_counts = saatchi.groupby("artist_slug").size().to_dict()
    saatchi["work_count_bucket"] = saatchi["artist_slug"].map(
        lambda a: (
            "1-2"
            if artist_counts[a] <= 2
            else "3-4"
            if artist_counts[a] <= 4
            else "5-9"
            if artist_counts[a] <= 9
            else "10+"
        )
    )

    cold_mask = ~saatchi["warm"]
    n_total = len(saatchi)
    logger.info(
        "saatchi training rows: %d / cold %d / warm %d",
        n_total,
        int(cold_mask.sum()),
        int((~cold_mask).sum()),
    )

    used_urls: set[str] = set()

    # ============================================================
    # Target cohort 650
    # ============================================================
    target_records: list[dict] = []

    # (1) cold artist 작품 전체 (n=628 추정, 모두 포함)
    cold_rows = saatchi[cold_mask]
    cold_n = min(len(cold_rows), 500)  # 너무 많아도 500 제한
    cold_picked = cold_rows.sample(n=cold_n, random_state=RNG_SEED).reset_index(drop=True)
    for _, r in cold_picked.iterrows():
        if r["artwork_url"] in used_urls:
            continue
        used_urls.add(r["artwork_url"])
        target_records.append(
            {
                "artwork_url": r["artwork_url"],
                "artist_slug": str(r["artist_slug"]),
                "price_krw": float(r["price_krw"]),
                "medium_cat": r["medium_cat"],
                "price_band": r["price_band"],
                "work_count_bucket": r["work_count_bucket"],
                "warm": False,
                "target_reason": "cold_artist",
            }
        )

    # (2) price=0 작품 추가 (학습 데이터 안)
    price_zero = saatchi[saatchi["price_krw"] == 0]
    for _, r in price_zero.iterrows():
        if r["artwork_url"] in used_urls:
            continue
        used_urls.add(r["artwork_url"])
        target_records.append(
            {
                "artwork_url": r["artwork_url"],
                "artist_slug": str(r["artist_slug"]),
                "price_krw": float(r["price_krw"]),
                "medium_cat": r["medium_cat"],
                "price_band": r["price_band"],
                "work_count_bucket": r["work_count_bucket"],
                "warm": bool(r["warm"]),
                "target_reason": "price_zero",
            }
        )
        if len(target_records) >= TARGET_N - 100:  # 100 여분
            break

    # (3) low work_count 작가 작품 (3-4 bucket) — cold 외 추가
    low_wc = saatchi[(saatchi["work_count_bucket"].isin(["1-2", "3-4"])) & (~cold_mask)]
    for _, r in low_wc.sample(frac=1.0, random_state=RNG_SEED).iterrows():
        if len(target_records) >= TARGET_N:
            break
        if r["artwork_url"] in used_urls:
            continue
        used_urls.add(r["artwork_url"])
        target_records.append(
            {
                "artwork_url": r["artwork_url"],
                "artist_slug": str(r["artist_slug"]),
                "price_krw": float(r["price_krw"]),
                "medium_cat": r["medium_cat"],
                "price_band": r["price_band"],
                "work_count_bucket": r["work_count_bucket"],
                "warm": True,
                "target_reason": "low_work_count_warm",
            }
        )

    # 매체 편중 방지 (target 안에서 single medium 이 50% 넘으면 다양화)
    medium_dist = Counter(t["medium_cat"] for t in target_records)
    logger.info("target cohort 매체 분포: %s", dict(medium_dist.most_common(8)))

    # 부족분 채우기 (target_n 미달이면 random saatchi 로 채움 — 매체 편중 방지)
    while len(target_records) < TARGET_N:
        candidates = saatchi[~saatchi["artwork_url"].isin(used_urls)]
        # 가장 적은 매체 우선
        med_count = Counter(t["medium_cat"] for t in target_records)
        rare_meds = [m for m, _ in med_count.most_common()[::-1]][:3]
        cand = candidates[candidates["medium_cat"].isin(rare_meds)]
        if len(cand) == 0:
            cand = candidates
        if len(cand) == 0:
            break
        r = cand.sample(n=1, random_state=rng.randint(0, 1_000_000)).iloc[0]
        if r["artwork_url"] in used_urls:
            continue
        used_urls.add(r["artwork_url"])
        target_records.append(
            {
                "artwork_url": r["artwork_url"],
                "artist_slug": str(r["artist_slug"]),
                "price_krw": float(r["price_krw"]),
                "medium_cat": r["medium_cat"],
                "price_band": r["price_band"],
                "work_count_bucket": r["work_count_bucket"],
                "warm": bool(r["warm"]),
                "target_reason": "fill_diversity",
            }
        )

    target_records = target_records[:TARGET_N]
    logger.info("target cohort 최종: n=%d", len(target_records))

    # ============================================================
    # Stratified random 350 (warm 위주, medium × price_band 균형)
    # ============================================================
    warm = saatchi[~cold_mask & ~saatchi["artwork_url"].isin(used_urls)]
    # strata 정의: medium_cat × price_band
    strata: dict[tuple[str, str], list] = defaultdict(list)
    for _, r in warm.iterrows():
        strata[(r["medium_cat"], r["price_band"])].append(r)

    # 균등 quota: STRATIFIED_N / len(strata)
    n_strata = len(strata)
    base_quota = STRATIFIED_N // n_strata
    remainder = STRATIFIED_N - base_quota * n_strata
    quota_per_stratum = {k: base_quota for k in strata}
    # remainder 큰 strata 에 분배
    sorted_strata = sorted(strata.items(), key=lambda x: -len(x[1]))
    for i, (k, _) in enumerate(sorted_strata):
        if i < remainder:
            quota_per_stratum[k] += 1

    stratified_records: list[dict] = []
    for k, rows in strata.items():
        q = quota_per_stratum[k]
        picked = rng.sample(rows, min(q, len(rows)))
        for r in picked:
            if r["artwork_url"] in used_urls:
                continue
            used_urls.add(r["artwork_url"])
            stratified_records.append(
                {
                    "artwork_url": r["artwork_url"],
                    "artist_slug": str(r["artist_slug"]),
                    "price_krw": float(r["price_krw"]),
                    "medium_cat": r["medium_cat"],
                    "price_band": r["price_band"],
                    "work_count_bucket": r["work_count_bucket"],
                    "warm": bool(r["warm"]),
                    "target_reason": "stratified_random",
                }
            )
    # 부족분 채우기
    while len(stratified_records) < STRATIFIED_N:
        cand = warm[~warm["artwork_url"].isin(used_urls)]
        if len(cand) == 0:
            break
        r = cand.sample(n=1, random_state=rng.randint(0, 1_000_000)).iloc[0]
        used_urls.add(r["artwork_url"])
        stratified_records.append(
            {
                "artwork_url": r["artwork_url"],
                "artist_slug": str(r["artist_slug"]),
                "price_krw": float(r["price_krw"]),
                "medium_cat": r["medium_cat"],
                "price_band": r["price_band"],
                "work_count_bucket": r["work_count_bucket"],
                "warm": bool(r["warm"]),
                "target_reason": "stratified_fill",
            }
        )

    stratified_records = stratified_records[:STRATIFIED_N]
    logger.info("stratified random 최종: n=%d", len(stratified_records))

    all_samples = target_records + stratified_records
    rng.shuffle(all_samples)  # fetch order 무작위

    # diagnostics
    target_reason_dist = Counter(r["target_reason"] for r in all_samples)
    medium_dist = Counter(r["medium_cat"] for r in all_samples)
    price_band_dist = Counter(r["price_band"] for r in all_samples)
    wc_bucket_dist = Counter(r["work_count_bucket"] for r in all_samples)
    warm_count = sum(1 for r in all_samples if r["warm"])

    summary = {
        "config": {
            "target_n": TARGET_N,
            "stratified_n": STRATIFIED_N,
            "total_n": len(all_samples),
            "rng_seed": RNG_SEED,
            "scope": "v3.4-2 step 3 pilot hybrid sampling: 650 target + 350 stratified random",
        },
        "diagnostics": {
            "target_reason": dict(target_reason_dist),
            "medium_category": dict(medium_dist.most_common(15)),
            "price_band": dict(price_band_dist),
            "work_count_bucket": dict(wc_bucket_dist),
            "warm_count": warm_count,
            "cold_count": len(all_samples) - warm_count,
            "n_unique_artists": len({r["artist_slug"] for r in all_samples}),
        },
        "samples": all_samples,
    }
    SAMPLE_OUT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    logger.info("sample 저장: %s (n=%d)", SAMPLE_OUT_PATH, len(all_samples))

    print(f"\nTarget reason: {dict(target_reason_dist)}")
    print(f"Medium: {dict(medium_dist.most_common(8))}")
    print(f"Price band: {dict(price_band_dist)}")
    print(f"Work count bucket: {dict(wc_bucket_dist)}")
    print(f"Warm/Cold: {warm_count}/{len(all_samples) - warm_count}")
    print(f"Unique artists: {len({r['artist_slug'] for r in all_samples})}")
    print(f"\n저장: {SAMPLE_OUT_PATH}")


if __name__ == "__main__":
    main()
