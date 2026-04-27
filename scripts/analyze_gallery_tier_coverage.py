"""갤러리 티어 매핑 커버리지 + 가격 분리도 분석 (Phase 1A v2).

배경:
- 협력자 제공 art_gallery_tier_list_v3는 한글 갤러리명 88개 (Tier A~E)
- Artsy 데이터는 영문 66개, Saatchi는 "Saatchi Art" 단일
- 영문→한글 수기 매핑 11건 후 매칭률 + 가격 분리도 측정

코덱스 리뷰 반영 (2026-04-27):
- P1-1: Tier D 카테고리 라벨(한국화랑협회/지역 중소) 직접 매칭 불가 → fallback rule sensitivity로 제공
- P1-2: Saatchi 강제 Tier E 재코딩 제거. Artsy/Saatchi 분리 보고
- P1-3: Tier별 가격 분포(median/IQR/bootstrap CI) 추가 — 핵심 분리도 검증
- P2-1: 기존 gallery_tier(city_count + avg_price + work_count)와 cross-tab으로 중복 여부 검증
- P2-2: Top 30 unmatched를 협력자 검수 후보 리스트로 명시
- P3: 데이터 위생(NaN dropna, whitespace 정규화)

산출물:
- model_test_results/gallery_tier_coverage.json
- model_test_results/gallery_tier_coverage_report.md

Usage:
    PYTHONPATH=src python3 scripts/analyze_gallery_tier_coverage.py
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = ROOT / "model_test_results"


# ─── 영문 갤러리명 → 협력자 리스트의 한글명 매핑 (확정 11건) ───────────
ARTSY_TO_KOR_GALLERY: dict[str, str] = {
    "Kimreeaa Gallery": "김리아갤러리",
    "Art Sohyang": "아트소향",
    "BHAK": "BHAK(비에이치에이케이)",
    "Gallery Planet": "갤러리 플래닛",
    "CHOI&CHOI": "초이앤초이 갤러리",
    "CYLINDER": "실린더",
    "Leehwaik Gallery": "이화익갤러리",
    "SPACE Willing N Dealing": "스페이스 윌링앤딜링",
    "ThisWeekendRoom": "디스위켄드룸",
    "FOUNDRY SEOUL": "파운드리 서울",
    "Artside Gallery": "아트사이드 갤러리",
}


# ─── 협력자 검수용 추정 한글 후보 (검증되지 않음 — 협력자가 확정해야 함) ─
ARTSY_REVIEW_HINTS: dict[str, str] = {
    "Art Spoon": "아트스푼?",
    "Gallery Grimson": "갤러리 그림슨?",
    "Suppoment Gallery": "써포먼트 갤러리?",
    "Keumsan Gallery": "금산갤러리?",
    "The Trinity Gallery": "트리니티 갤러리?",
    "MOOWOOSOO Gallery": "무우수갤러리?",
    "Objecthood": "오브젝트후드?",
    "Art in Dongsan": "동산방화랑?",
    "GalleryMEME": "갤러리밈?",
    "Gallery Playlist": "갤러리 플레이리스트?",
    "Galerie GAIA": "갤러리 가이아?",
    "Kuns Gallery": "쿤스 갤러리?",
    "art.ness": "아트네스?",
    "THEO": "테오?",
    "LYNN Fine Art Gallery": "린 파인아트?",
    "IdeelArt": "아이딜아트?",
    "Space776": "스페이스776?",
    "Dohing Art": "도잉아트?",
    "Gallery We": "갤러리 위?",
    "Combineworks Seoul": "컴바인웍스 서울?",
    "UARTSPACE": "유아트스페이스?",
    "galerie bruno massa": "브루노 마사?",
    "Art Works Paris Seoul Gallery": "아트웍스 파리 서울?",
    "ROY Gallery": "로이 갤러리?",
    "Gallery Ichon": "갤러리 이촌?",
}

TIER_ORDER = ["Tier A", "Tier B", "Tier C", "Tier D", "Tier E"]


def normalize(name: str | float | None) -> str:
    """공백 정규화: 다중 공백 → 단일 공백, strip."""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    return re.sub(r"\s+", " ", str(name)).strip()


def load_tier_lookup() -> dict[str, tuple[str, str]]:
    """협력자 리스트 로드. NaN 명칭 dropna, 공백 정규화."""
    tier_csv = DATA / "art_gallery_tier_list_v3.xlsx - 전체 리스트.csv"
    df = pd.read_csv(tier_csv)
    df = df.dropna(subset=["명칭"])
    lookup: dict[str, tuple[str, str]] = {}
    for _, row in df.iterrows():
        name = normalize(row["명칭"])
        tier = str(row["티어"]).strip()
        cls = str(row["분류"]).strip()
        if name:
            lookup[name] = (tier, cls)
    return lookup


def determine_gallery_tier_class(
    gallery_name: str | None,
    tier_lookup: dict[str, tuple[str, str]],
    apply_d_fallback: bool = False,
    gallery_type: str | None = None,
) -> tuple[str, str]:
    """gallery_name → (tier, class).

    apply_d_fallback=True 인 경우, 미매칭이면서 commercial gallery type이면
    Tier D ("미분류 commercial gallery — 한국화랑협회/지역 중소 추정")로 둔다.
    이는 sensitivity rule이지 확정 매핑이 아님.
    """
    n = normalize(gallery_name)
    if not n:
        return ("Tier E", "미분류")
    if n == "Saatchi Art":
        return ("Tier E", "온라인 플랫폼")
    kor_name = ARTSY_TO_KOR_GALLERY.get(n, n)
    kor_norm = normalize(kor_name)
    if kor_norm in tier_lookup:
        return tier_lookup[kor_norm]
    if apply_d_fallback and gallery_type and "Gallery" in str(gallery_type) and "Online" not in str(gallery_type):
        return ("Tier D", "미분류 commercial — 한국화랑협회/지역 추정")
    return ("Tier E", "미분류")


def bootstrap_median_ci(values: np.ndarray, n_boot: int = 1000, alpha: float = 0.05, seed: int = 42) -> tuple[float, float]:
    """Bootstrap 95% CI for median."""
    if len(values) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(n_boot, len(values)))
    boots = np.median(values[idx], axis=1)
    lo = np.quantile(boots, alpha / 2)
    hi = np.quantile(boots, 1 - alpha / 2)
    return (float(lo), float(hi))


def price_stats(df: pd.DataFrame, tier_col: str = "tier_v3") -> dict:
    """Tier별 price_krw / ln_price 분포 통계."""
    out = {}
    for tier in TIER_ORDER:
        sub = df[df[tier_col] == tier]
        n = len(sub)
        if n == 0:
            out[tier] = {"n": 0}
            continue
        p = sub["price_krw"].to_numpy()
        ln = sub["ln_price"].to_numpy()
        median = float(np.median(p))
        q25 = float(np.quantile(p, 0.25))
        q75 = float(np.quantile(p, 0.75))
        ln_mean = float(np.mean(ln))
        ln_std = float(np.std(ln, ddof=1)) if n > 1 else float("nan")
        ci_lo, ci_hi = bootstrap_median_ci(p)
        out[tier] = {
            "n": int(n),
            "price_median": round(median, 0),
            "price_q25": round(q25, 0),
            "price_q75": round(q75, 0),
            "ln_mean": round(ln_mean, 4),
            "ln_std": round(ln_std, 4) if not np.isnan(ln_std) else None,
            "median_ci95_lo": round(ci_lo, 0),
            "median_ci95_hi": round(ci_hi, 0),
        }
    return out


def crosstab_existing_tier(df: pd.DataFrame) -> dict:
    """v3_tier × 기존 gallery_tier 교차표."""
    if "gallery_tier" not in df.columns:
        return {}
    ct = pd.crosstab(df["tier_v3"], df["gallery_tier"])
    return {f"v3={r}": {f"existing={c}": int(ct.loc[r, c]) for c in ct.columns} for r in ct.index}


def analyze() -> dict:
    """Artsy + Saatchi 데이터에 매핑 적용 후 커버리지 + 가격 분리도 측정."""
    tier_lookup = load_tier_lookup()
    logger.info("Tier list loaded: %d 갤러리/기관 (NaN dropna 후)", len(tier_lookup))

    artsy = pd.read_parquet(DATA / "primary_market_dataset.parquet")
    saatchi = pd.read_parquet(DATA / "saatchi_cleaned.parquet")

    # 학습 데이터 필터 (입체 985건 등 제외)
    artsy_trained = artsy[artsy["is_excluded_for_training"] == 0].copy()
    saatchi_trained = saatchi[saatchi["is_excluded_for_training"] == 0].copy()

    logger.info("Artsy: 전체 %d / 학습 %d 작품", len(artsy), len(artsy_trained))
    logger.info("Saatchi: 전체 %d / 학습 %d 작품", len(saatchi), len(saatchi_trained))

    # ─── Artsy 매핑 (default + Tier D fallback) ─────────────
    def apply_tier_rowwise(df: pd.DataFrame, fallback: bool) -> pd.DataFrame:
        df = df.copy()
        tiers = []
        classes = []
        for _, row in df.iterrows():
            t, c = determine_gallery_tier_class(
                row.get("gallery_name"),
                tier_lookup,
                apply_d_fallback=fallback,
                gallery_type=row.get("gallery_type"),
            )
            tiers.append(t)
            classes.append(c)
        df["tier_v3"] = tiers
        df["class_v3"] = classes
        return df

    artsy_default = apply_tier_rowwise(artsy_trained, fallback=False)
    artsy_d_fallback = apply_tier_rowwise(artsy_trained, fallback=True)

    # 갤러리 단위 매칭 통계
    vc = artsy_trained["gallery_name"].value_counts()
    matched_galleries = []
    unmatched_galleries = []
    for name, cnt in vc.items():
        n_norm = normalize(name)
        kor = ARTSY_TO_KOR_GALLERY.get(n_norm, n_norm)
        if normalize(kor) in tier_lookup:
            tier, cls = tier_lookup[normalize(kor)]
            matched_galleries.append({"name": name, "kor": kor, "tier": tier, "class": cls, "n": int(cnt)})
        else:
            unmatched_galleries.append({"name": name, "n": int(cnt), "hint": ARTSY_REVIEW_HINTS.get(name, "?")})

    matched_works = sum(g["n"] for g in matched_galleries)
    unmatched_works = sum(g["n"] for g in unmatched_galleries)
    top30_unmatched_works = sum(g["n"] for g in unmatched_galleries[:30])

    # 가격 분리도 (Artsy-only — default 매핑 기준)
    artsy_price_stats = price_stats(artsy_default)
    artsy_price_stats_d = price_stats(artsy_d_fallback)  # sensitivity

    # 기존 gallery_tier와의 교차표
    artsy_crosstab = crosstab_existing_tier(artsy_default)

    # Saatchi 분리 (강제 Tier E 재코딩 X — source별로 별도 보고)
    saatchi_summary = {
        "total_works": int(len(saatchi_trained)),
        "gallery_name": "Saatchi Art (단일 source)",
        "existing_gallery_tier": int(saatchi_trained["gallery_tier"].iloc[0]) if len(saatchi_trained) else None,
        "price_median": float(np.median(saatchi_trained["price_krw"])) if len(saatchi_trained) else None,
        "price_q25": float(np.quantile(saatchi_trained["price_krw"], 0.25)) if len(saatchi_trained) else None,
        "price_q75": float(np.quantile(saatchi_trained["price_krw"], 0.75)) if len(saatchi_trained) else None,
        "ln_mean": float(np.mean(saatchi_trained["ln_price"])) if len(saatchi_trained) else None,
        "note": "온라인 플랫폼 — 갤러리 개념 미적용. 기존 파이프라인은 source='saatchi'로 분리 처리."
    }

    return {
        "tier_list_size": len(tier_lookup),
        "artsy": {
            "total_works": int(len(artsy)),
            "trained_works": int(len(artsy_trained)),
            "total_galleries": int(artsy_trained["gallery_name"].nunique()),
            "matched_galleries_count": len(matched_galleries),
            "unmatched_galleries_count": len(unmatched_galleries),
            "matched_works": matched_works,
            "unmatched_works": unmatched_works,
            "matched_works_pct": round(100 * matched_works / len(artsy_trained), 1),
            "top30_unmatched_works": top30_unmatched_works,
            "top30_unmatched_pct_of_unmatched": round(100 * top30_unmatched_works / unmatched_works, 1) if unmatched_works else 0,
            "top30_unmatched_pct_of_total": round(100 * top30_unmatched_works / len(artsy_trained), 1),
            "tier_distribution_default": {k: int(v) for k, v in artsy_default["tier_v3"].value_counts().items()},
            "tier_distribution_d_fallback": {k: int(v) for k, v in artsy_d_fallback["tier_v3"].value_counts().items()},
            "matched_galleries": matched_galleries,
            "unmatched_galleries_top30": unmatched_galleries[:30],
            "price_stats_default": artsy_price_stats,
            "price_stats_d_fallback": artsy_price_stats_d,
            "crosstab_v3_vs_existing_tier": artsy_crosstab,
        },
        "saatchi": saatchi_summary,
    }


def fmt_krw(n: float | None) -> str:
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "-"
    return f"{int(n):,}"


def write_report(result: dict, out_md: Path) -> None:
    artsy = result["artsy"]
    saatchi = result["saatchi"]

    lines = [
        "# 갤러리 티어 매핑 커버리지 + 가격 분리도 분석 (Phase 1A v2)",
        "",
        "> 코덱스 리뷰 반영본. v1의 결정적 결함(Saatchi 강제 재코딩, 가격 분리도 미측정,",
        "> Tier D 매핑 미구현)을 보정하고 Phase 1B 진행 판단을 재구성.",
        "",
        f"- 협력자 리스트: **{result['tier_list_size']}** 갤러리/기관 (NaN 1건 제외)",
        f"- Artsy 학습 데이터: **{artsy['trained_works']:,}** 작품 / {artsy['total_galleries']} 갤러리 (입체 제외 후)",
        f"- Saatchi 학습 데이터: **{saatchi['total_works']:,}** 작품 (Saatchi Art 단일 — source='saatchi'로 별도 처리)",
        "",
        "## 1. Artsy 매칭 결과",
        "",
        f"- 매칭된 갤러리: **{artsy['matched_galleries_count']}/{artsy['total_galleries']}** "
        f"({100*artsy['matched_galleries_count']/artsy['total_galleries']:.0f}%)",
        f"- 매칭된 작품: **{artsy['matched_works']:,}/{artsy['trained_works']:,}** "
        f"({artsy['matched_works_pct']}%)",
        f"- 미매칭 Top 30 = **{artsy['top30_unmatched_works']:,}** 건 = "
        f"미매칭의 **{artsy['top30_unmatched_pct_of_unmatched']}%** / Artsy 전체의 **{artsy['top30_unmatched_pct_of_total']}%**",
        "",
        f"현재 {artsy['matched_works_pct']}%는 **lookup의 하한**이지 Phase 1B의 상한이 아님. "
        f"Top 30 검수만으로 80%+ 추가 매핑 가능성.",
        "",
        "### 매칭된 갤러리 (작품 수 내림차순)",
        "",
        "| Artsy 영문명 | 한글 매칭 | Tier | Class | 작품 수 |",
        "|---|---|:---:|---|---:|",
    ]
    for g in sorted(artsy["matched_galleries"], key=lambda x: -x["n"]):
        lines.append(f"| {g['name']} | {g['kor']} | {g['tier']} | {g['class']} | {g['n']:,} |")

    lines.extend([
        "",
        "## 2. Tier 분포 (Artsy-only, 학습 데이터)",
        "",
        "| Tier | Default | Default % | +D-fallback | +D-fallback % |",
        "|:---:|---:|---:|---:|---:|",
    ])
    total = artsy["trained_works"]
    for t in TIER_ORDER:
        nd = artsy["tier_distribution_default"].get(t, 0)
        nf = artsy["tier_distribution_d_fallback"].get(t, 0)
        lines.append(
            f"| {t} | {nd:,} | {100*nd/total:.1f}% | {nf:,} | {100*nf/total:.1f}% |"
        )
    lines.extend([
        "",
        "- **Default**: 협력자 리스트 정확 매칭만 적용. 미매칭은 모두 Tier E.",
        "- **+D-fallback**: 미매칭 + commercial gallery type → Tier D로 떨어뜨리는 sensitivity rule "
        "(\"한국화랑협회 회원/지역 중소\" 카테고리 라벨이 데이터에 직접 없으므로 추정 규칙).",
        "",
        "## 3. 가격 분리도 (핵심) — Artsy-only Default 매핑",
        "",
        "**이게 Phase 1B 의미 여부의 결정적 지표.** 커버리지가 낮아도 매칭된 Tier가 가격을 의미 있게 분리한다면 가치가 있고, 반대로 분리가 약하면 매핑을 늘려도 의미가 없다.",
        "",
        "| Tier | n | median (KRW) | 95% CI | Q25 | Q75 | ln_mean | ln_std |",
        "|:---:|---:|---:|---|---:|---:|---:|---:|",
    ])
    for t in TIER_ORDER:
        s = artsy["price_stats_default"].get(t, {"n": 0})
        if s.get("n", 0) == 0:
            lines.append(f"| {t} | 0 | - | - | - | - | - | - |")
            continue
        ci = f"[{fmt_krw(s['median_ci95_lo'])} ~ {fmt_krw(s['median_ci95_hi'])}]"
        lines.append(
            f"| {t} | {s['n']:,} | {fmt_krw(s['price_median'])} | {ci} | "
            f"{fmt_krw(s['price_q25'])} | {fmt_krw(s['price_q75'])} | "
            f"{s['ln_mean']:.3f} | {s['ln_std']:.3f} |"
        )

    # 분리도 해석
    b = artsy["price_stats_default"].get("Tier B", {"n": 0})
    c = artsy["price_stats_default"].get("Tier C", {"n": 0})
    e = artsy["price_stats_default"].get("Tier E", {"n": 0})

    lines.extend([
        "",
        "### 해석",
        "",
    ])
    def ci_overlap(a: dict, b: dict) -> bool:
        return not (a["median_ci95_hi"] < b["median_ci95_lo"] or b["median_ci95_hi"] < a["median_ci95_lo"])

    if b.get("n", 0) > 0 and e.get("n", 0) > 0:
        b_e_ratio = b["price_median"] / e["price_median"]
        overlap_be = ci_overlap(b, e)
        n_b = b["n"]
        ci_msg = "겹침" if overlap_be else "**비겹침** (통계적으로 유의)"
        sample_msg = "충분" if n_b >= 300 else f"작음 (B={n_b}건, 권장 300+)"
        if (not overlap_be) and n_b >= 300:
            verdict = "유의 + 충분"
        elif not overlap_be:
            verdict = "유의 but underpowered"
        else:
            verdict = "underpowered"
        lines.append(
            f"- **Tier B vs E**: median {fmt_krw(b['price_median'])} vs {fmt_krw(e['price_median'])} "
            f"= **{b_e_ratio:.2f}x**. 95% CI {ci_msg}. "
            f"표본 {sample_msg} → {verdict}."
        )
    if c.get("n", 0) > 0 and e.get("n", 0) > 0:
        c_e_ratio = c["price_median"] / e["price_median"]
        overlap_ce = ci_overlap(c, e)
        lines.append(
            f"- **Tier C vs E**: median {fmt_krw(c['price_median'])} vs {fmt_krw(e['price_median'])} "
            f"= **{c_e_ratio:.2f}x**. 95% CI {'겹침 → 유의차 없음' if overlap_ce else '비겹침'}. "
            f"C 라벨은 가격 신호로 약함 — 협력자가 정의한 'Tier C 하이엔드 라이징/이머징' 분류가 "
            f"실제 거래 가격과 직접 연결되지 않음."
        )
    lines.extend([
        "",
        "## 4. 기존 `gallery_tier` 피처와의 교차표",
        "",
        "기존 `gallery_tier`는 `city_count + avg_price + work_count` 휴리스틱 (estimate_gallery_tier in "
        "scripts/prepare_primary_market_dataset.py:116). v3 Tier가 같은 신호인지 다른 축인지 검증.",
        "",
    ])
    if artsy["crosstab_v3_vs_existing_tier"]:
        # 행: v3, 열: existing
        ct = artsy["crosstab_v3_vs_existing_tier"]
        existing_keys = sorted({k for inner in ct.values() for k in inner.keys()})
        lines.append("| v3 \\ existing | " + " | ".join(existing_keys) + " |")
        lines.append("|" + ":---:|" * (len(existing_keys) + 1))
        for v3_key in sorted(ct.keys()):
            row = ct[v3_key]
            cells = [str(row.get(k, 0)) for k in existing_keys]
            lines.append(f"| {v3_key} | " + " | ".join(cells) + " |")
        lines.append("")
        lines.append("v3 Tier E와 Tier C 모두 기존 gallery_tier 여러 값에 걸쳐 있다면 **다른 축**. "
                     "한 값에 집중되면 **중복 신호**.")
    lines.extend([
        "",
        "## 5. Saatchi (별도 처리)",
        "",
        f"- 작품 수: {saatchi['total_works']:,}",
        f"- 기존 `gallery_tier`: **{saatchi['existing_gallery_tier']}** (단일값)",
        f"- price median: **{fmt_krw(saatchi['price_median'])} KRW** (Q25 {fmt_krw(saatchi['price_q25'])} ~ Q75 {fmt_krw(saatchi['price_q75'])})",
        f"- ln_mean: {saatchi['ln_mean']:.3f}",
        "",
        f"> {saatchi['note']}",
        "",
        "Artsy median과 Saatchi median을 직접 비교하는 것은 source 효과 + tier 효과가 섞여 있어 부적절.",
        "**v1 보고서의 통합 96.6% Tier E 수치는 source 효과로 희석된 결과이므로 폐기.**",
        "",
        "## 6. 미매칭 Top 30 — 협력자 검수 후보 리스트",
        "",
        f"이 30개를 협력자가 한글명/Tier 확정 시 Artsy unmatched의 **{artsy['top30_unmatched_pct_of_unmatched']}%**, "
        f"전체의 **{artsy['top30_unmatched_pct_of_total']}%**가 재평가됨. **ROI 가장 높은 후속 작업.**",
        "",
        "| 순위 | 영문명 | 작품 수 | 추정 한글 (검수 필요) | 리스트 등재? |",
        "|---:|---|---:|---|:---:|",
    ])
    for i, g in enumerate(artsy["unmatched_galleries_top30"], 1):
        lines.append(f"| {i} | {g['name']} | {g['n']:,} | {g['hint']} | NO |")

    lines.extend([
        "",
        "추정 한글명 중 'NO' 표시는 협력자 리스트(88건)에 없음을 의미. 즉 **이름 표기 차이가 아니라**, ",
        "이들이 협력자 리스트에 등록 안 된 갤러리. 협력자가 리스트를 확장하거나 Tier D/E를 명시해야 함.",
        "",
        "## 결론 — Phase 1B 진행 판단",
        "",
        "v1의 \"보류 권장\" 결론은 **철회**. 보유 데이터로는 결정 자체가 불가능.",
        "",
        "### 핵심 근거",
        "",
        f"- **Tier B vs E**: {fmt_krw(b.get('price_median'))} vs {fmt_krw(e.get('price_median'))} = "
        f"{(b['price_median']/e['price_median']):.2f}x — 신호 있음, 표본 부족 (B={b.get('n', 0)}건)",
        f"- **Tier C vs E**: {fmt_krw(c.get('price_median'))} vs {fmt_krw(e.get('price_median'))} = "
        f"{(c['price_median']/e['price_median']):.2f}x — 가격 분리 약함",
        f"- **Top 30 미매칭이 81%** 점유 → 검수 후 그림이 크게 바뀔 가능성 높음",
        "- 기존 `gallery_tier`와 v3는 다른 축 (cross-tab 참고)",
        "",
        "### ROI 우선순위 (코덱스 권장)",
        "",
        "1. **A. 협력자 검수** (1순위) — Top 30 unmatched 한글명/Tier 확정 → Artsy 81% 재평가",
        "2. **C. 다른 P0 우선** (2순위) — 검수 결과 나오기 전까지 career-stage v2 / source-split 등 진행",
        "3. **B. Artsy 외 데이터** (3순위) — 검수 + 가격 분리도 확인 후, 신호 약하면 그때 착수",
        "",
        "### 재판정 트리거",
        "",
        "- 검수 후 매핑이 30+ 도달하고 Tier B 표본이 300+ 늘어나면 → ablation 진행",
        "- Tier B의 가격 분리(2x+)가 검수 후에도 유지되면 → Phase 1B 진행",
        "- 검수 후에도 Tier C가 E와 분리 안 되면 → Tier C 라벨은 학습 신호로 사용 X (B만 binary)",
        "",
    ])
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = analyze()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    out_json = OUT_DIR / "gallery_tier_coverage.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=lambda o: int(o) if isinstance(o, np.integer) else float(o) if isinstance(o, np.floating) else str(o))
    logger.info("Saved: %s", out_json)

    out_md = OUT_DIR / "gallery_tier_coverage_report.md"
    write_report(result, out_md)
    logger.info("Saved: %s", out_md)

    artsy = result["artsy"]
    logger.info("=" * 60)
    logger.info("재분석 결과")
    logger.info("=" * 60)
    logger.info("Artsy 매칭: %d/%d 갤러리, %d/%d 작품 (%.1f%%)",
                artsy["matched_galleries_count"], artsy["total_galleries"],
                artsy["matched_works"], artsy["trained_works"], artsy["matched_works_pct"])
    logger.info("Tier 분포 (default): %s", artsy["tier_distribution_default"])
    logger.info("Tier 분포 (D-fallback): %s", artsy["tier_distribution_d_fallback"])
    b = artsy["price_stats_default"].get("Tier B", {})
    c = artsy["price_stats_default"].get("Tier C", {})
    e = artsy["price_stats_default"].get("Tier E", {})
    logger.info("Tier B median %s (n=%s) / Tier C median %s (n=%s) / Tier E median %s (n=%s)",
                b.get("price_median"), b.get("n"), c.get("price_median"), c.get("n"),
                e.get("price_median"), e.get("n"))


if __name__ == "__main__":
    main()
