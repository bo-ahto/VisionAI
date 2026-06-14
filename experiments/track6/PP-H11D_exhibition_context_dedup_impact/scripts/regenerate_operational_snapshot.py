#!/usr/bin/env python3
"""PP-H11D ①: 패치된 build_snapshot을 실제로 실행해 operational 스냅샷 재생성·검증.

run_pp_h11은 수집용 네트워크 라이브러리(requests/bs4/ddgs)를 모듈 상단에서
import하지만 build_snapshot 자체는 이를 쓰지 않는다. 서빙 스냅샷 재생성에는
검색 API가 필요 없으므로, 네트워크 모듈을 스텁 처리해 실제 패치된
build_snapshot/merge_artist_selection_with_latest를 그대로 import하고
캐시 standardized 데이터로 스냅샷을 재계산한다.

- 실제 패치 함수 == 측정용 replica 일치 검증
- 현행 서빙 스냅샷과 diff
- --write 지정 시에만 프로덕션 스냅샷 교체(기본은 dry-run, 산출물은 실험 폴더)
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[4]
SCRIPTS = REPO / "scripts" / "track6"
ART_DIR = Path(__file__).resolve().parents[1] / "artifacts"
STD_PATH = (
    REPO
    / "data"
    / "track6"
    / "external_search"
    / "operational"
    / "track6_artist_search_operational_standardized_latest.csv"
)
SERVING_SNAPSHOT = (
    REPO
    / "data"
    / "track6"
    / "external_search"
    / "operational"
    / "track6_artist_search_operational_snapshot_latest.csv"
)


def _stub(name: str, attrs: dict[str, object] | None = None) -> None:
    """네트워크 전용 모듈을 가짜로 등록(build_snapshot은 미사용)."""
    if name in sys.modules:
        return
    mod = types.ModuleType(name)
    for k, v in (attrs or {}).items():
        setattr(mod, k, v)
    sys.modules[name] = mod


def import_h11():
    _stub("requests")
    _stub("bs4", {"BeautifulSoup": object})
    _stub("ddgs", {"DDGS": object})
    _stub("duckduckgo_search", {"DDGS": object})
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import run_pp_h11_operational_search_experiments as h11

    return h11


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="프로덕션 서빙 스냅샷 덮어쓰기")
    args = ap.parse_args()

    h11 = import_h11()
    std = pd.read_csv(STD_PATH, low_memory=False)
    cur = (
        pd.read_csv(SERVING_SNAPSHOT, low_memory=False)
        if SERVING_SNAPSHOT.exists()
        else pd.DataFrame()
    )
    # build_snapshot은 line 747에서 artist_df를 left-merge하며, artist_df가 split
    # row-count 메타(train/validation/test/total_row_count)를 운반한다. 이 값들은
    # URL dedup과 무관(작품수 메타)하므로 현행 스냅샷에서 그대로 보존해 artist_df로
    # 넘긴다. 그러면 출력 스키마/컬럼순서가 현행과 동일하게 유지된다.
    count_cols = h11.ARTIST_COUNT_COLUMNS
    if not cur.empty and all(c in cur.columns for c in count_cols):
        artist_df = (
            cur[["artist_search_name", *count_cols]].drop_duplicates("artist_search_name").copy()
        )
    else:
        artist_df = pd.DataFrame(
            {"artist_search_name": sorted(std["artist_search_name"].dropna().unique())}
        )
    snap = h11.build_snapshot(std, artist_df)

    ART_DIR.mkdir(parents=True, exist_ok=True)
    regen_path = ART_DIR / "regenerated_operational_snapshot_latest.csv"
    snap.to_csv(regen_path, index=False)

    # 검증: 실제 패치 함수가 만든 카운트를 현행 서빙 스냅샷과 비교
    key = "artist_search_name"
    report_lines = [f"regenerated artists: {len(snap)}"]
    if not cur.empty and key in cur.columns:
        common = sorted(set(snap[key]) & set(cur[key]))
        a = snap.set_index(key).loc[common]
        b = cur.set_index(key).loc[common]
        for col in [
            "search_exhibition_context_count",
            "search_art_context_count",
            "search_quality_score",
            "search_result_count",
        ]:
            if col in a.columns and col in b.columns:
                d = (
                    pd.to_numeric(a[col], errors="coerce") - pd.to_numeric(b[col], errors="coerce")
                ).astype(float)
                report_lines.append(
                    f"{col:34s} mean_signed_delta={d.mean():+.4f} "
                    f"max_abs={d.abs().max():.4f} changed={(d.abs() > 1e-9).sum()}/{len(d)}"
                )
        report_lines.append(f"common artists compared: {len(common)}")
    print("\n".join(report_lines))
    (ART_DIR / "regenerate_report.txt").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    if args.write:
        snap.to_csv(SERVING_SNAPSHOT, index=False)
        print(f"\nWROTE production snapshot: {SERVING_SNAPSHOT.relative_to(REPO)}")
    else:
        rel = regen_path.relative_to(REPO)
        print(f"\n[dry-run] regenerated -> {rel} (use --write to replace production)")


if __name__ == "__main__":
    main()
