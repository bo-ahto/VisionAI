"""Track 3 v4 HTML 리포트 — 최종판.

v3 → v4 변경:
- PR8 (Conditional expert, negative result) 통합
- PR9 (Quantile + reweight, negative result + B4 +7pp 발견) 통합
- 최종 결론: PR7 ALL 확정 (Cold 0.391 / Warm 0.104)
- 학습 내용 (lessons learned) 섹션 추가
- 운영 구현 준비 (다음 단계)
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parent.parent.parent
DATA = REPO / "data"
OUT = REPO / "docs" / "track3_modeling_results_v4.html"


def load(name):
    p = DATA / f"track3_{name}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


def fmt(v, n=3):
    return f"{v:.{n}f}" if isinstance(v, (int, float)) else "—"


def main():
    pr5 = load("pr5_source_bias_results")
    pr7 = load("pr7_results")
    pr8 = load("pr8_conditional_results")
    pr9 = load("pr9_quantile_results")

    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>Track 3 — 가격 예측 모델링 최종 결과 v4</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 1200px; margin: 30px auto; padding: 20px; color: #222; }}
  h1 {{ border-bottom: 3px solid #2563eb; padding-bottom: 8px; }}
  h2 {{ color: #1e40af; margin-top: 36px; border-left: 4px solid #2563eb; padding-left: 12px; }}
  h3 {{ color: #1e3a8a; }}
  table {{ border-collapse: collapse; margin: 12px 0; }}
  th, td {{ border: 1px solid #d1d5db; padding: 6px 12px; text-align: left; }}
  th {{ background: #eff6ff; }}
  td.num {{ text-align: right; font-family: ui-monospace, monospace; }}
  .best {{ background: #d1fae5; font-weight: bold; }}
  .warn {{ background: #fef3c7; }}
  .err {{ background: #fee2e2; }}
  .critical {{ background: #fecaca; font-weight: bold; }}
  .new {{ background: #dbeafe; }}
  .neg {{ background: #fde2e7; color: #7f1d1d; }}
  .meta {{ color: #6b7280; font-size: 0.9em; }}
  blockquote {{ background: #f3f4f6; border-left: 4px solid #9ca3af; padding: 10px 16px; margin: 12px 0; }}
  code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  .lessons {{ background: #ecfdf5; border: 2px solid #10b981; padding: 16px; border-radius: 6px; margin: 16px 0; }}
</style></head><body>

<h1>Track 3 — 가격 예측 모델링 최종 결과 v4</h1>
<p class="meta">생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} / 9-phase + 9-PR 완료 / Codex 4회 검수 통과</p>

<blockquote class="new" style="border-color: #2563eb;">
<b>v3 → v4 변경 (최종판)</b>:
<ul>
  <li>🆕 <b>PR8 (Conditional expert)</b> — negative result (모든 variant +0.04 ~ +0.07 악화)</li>
  <li>🆕 <b>PR9 (Quantile + reweight)</b> — overall negative, <b>B4 (&gt;10M)만 -7pp 개선</b></li>
  <li>📊 최종 결론: <b>PR7 ALL이 final</b> — Cold 0.391 / Warm 0.104</li>
  <li>🎓 학습 내용 (lessons learned) 정리</li>
  <li>🚀 다음 단계: 운영 구현 (B 단계)</li>
</ul>
</blockquote>

<h2>🏆 최종 Best 모델 (확정)</h2>
<table>
<tr><th>시나리오</th><th>모델</th><th>med_APE</th><th>W30</th><th>95% CI</th></tr>
<tr class='best'><td><b>Cold-start (unseen)</b></td><td>LAD + ALL features<br><small>(6 base + source + interaction + popularity + aspect)</small></td><td class='num'>0.391</td><td class='num'>0.373</td><td class='num'>[0.407, 0.454] (multi-seed)</td></tr>
<tr class='best'><td><b>Warm-start (≥1건)</b></td><td>Tuned LGB + ALL features</td><td class='num'>0.104±0.001</td><td class='num'>0.776</td><td class='num'>[0.103, 0.105]</td></tr>
<tr class='best'><td>거장 (&gt;100M, Warm)</td><td>Warm 2-stage</td><td class='num'>0.042</td><td>—</td><td>—</td></tr>
<tr class='critical'><td>거장 (&gt;100M, Cold)</td><td>예측 불가</td><td class='num err'>0.98</td><td>—</td><td>운영 시 비공개</td></tr>
</table>

<h2>📊 모든 PR 결과 요약 (성공/실패 표)</h2>
<table>
<tr><th>PR</th><th>실험 내용</th><th>Cold 효과</th><th>결과</th></tr>
<tr class='best'><td>PR1 Optuna</td><td>LGB hyperparameter tuning</td><td class='num'>+0.015 (LGB)</td><td>✓ Warm -0.003 / Cold = LAD 확정</td></tr>
<tr class='best'><td>PR2 Blend grid</td><td>Rare artist 가중치</td><td>—</td><td>✓ 운영 라우팅 2-way 단순화</td></tr>
<tr class='best'><td>PR3 Conformal</td><td>신뢰구간</td><td>—</td><td>✓ Warm ±44%, Cold ±115%</td></tr>
<tr class='best'><td>PR4 Multi-seed Cold</td><td>GroupShuffleSplit×10</td><td>—</td><td>✓ Phase 5 robust 입증</td></tr>
<tr class='best'><td>PR5 Source bias</td><td>Artsy vs Saatchi audit</td><td>—</td><td>🔴 Artsy +45.5% 발견</td></tr>
<tr class='best'><td><b>PR7 Feature Eng</b></td><td><b>source/interaction/popularity/aspect 묶음</b></td><td class='num'><b>-0.038 (9%)</b></td><td><b>✓ 유일한 향상! Cold 0.429→0.391, Warm 0.115→0.104</b></td></tr>
<tr class='neg'><td>PR8 Conditional expert</td><td>Source/cell/soft expert + fallback</td><td class='num'>+0.042 ~ +0.071</td><td>✗ 모든 variant 악화 (표본 부족)</td></tr>
<tr class='neg'><td>PR9 Quantile + reweight</td><td>heteroscedastic 처리</td><td class='num'>+0.029 ~ +0.049 overall</td><td>✗ Overall 악화. <b>B4만 -7pp 개선</b></td></tr>
</table>
"""

    # PR7 결과 표
    if pr7:
        cold = pr7["cold"]
        warm = pr7["warm"]
        html += """
<h2>🔬 PR7 — Feature Engineering (★ 유일한 성공)</h2>
<h3>Cold LAD</h3>
<table>
<tr><th>Variant</th><th>med_APE</th><th>W30</th><th>vs baseline</th></tr>
"""
        base_med = cold["baseline"]["median"]["median_ape"]
        for v, res in cold.items():
            m = res["median"]
            delta = m["median_ape"] - base_med
            cls = "best" if v == "all" else ("err" if v == "popularity" else "")
            html += f"<tr class='{cls}'><td>{v}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td><td class='num'>{delta:+.3f}</td></tr>\n"
        html += """</table>

<h3>Warm Tuned LGB</h3>
<table>
<tr><th>Variant</th><th>med_APE</th><th>W30</th><th>vs baseline</th></tr>
"""
        base_w = warm["baseline"]["mean"]["median_ape"]
        for v, res in warm.items():
            m = res["mean"]
            delta = m["median_ape"] - base_w
            cls = "best" if v in ["all", "popularity"] else ""
            html += f"<tr class='{cls}'><td>{v}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td><td class='num'>{delta:+.3f}</td></tr>\n"
        html += """</table>
"""

    # PR8 negative
    if pr8:
        html += """
<h2>🚫 PR8 — Conditional Expert (negative result)</h2>
<table>
<tr><th>Variant</th><th>med_APE</th><th>W30</th><th>vs PR7 ALL</th></tr>
"""
        base = pr8["baseline_pr7_all"]["median"]["median_ape"]
        for name, res in pr8.items():
            m = res["median"]
            delta = m["median_ape"] - base
            cls = "best" if name == "baseline_pr7_all" else "neg"
            html += f"<tr class='{cls}'><td>{name}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td><td class='num'>{delta:+.3f}</td></tr>\n"
        html += """</table>
<blockquote>
<b>원인 (Codex 사전 경고 정확)</b>: 표본 부족 (40K rows × 12 cells = 평균 3K/cell, Artue 2,709). LAD 학습 불안정 → variance 큼.
</blockquote>
"""

    # PR9 partial
    if pr9:
        html += """
<h2>🌀 PR9 — Quantile + Reweighting (overall negative, B4 +7pp)</h2>
<table>
<tr><th>Variant</th><th>med_APE</th><th>W30</th><th>B4 (&gt;10M)</th><th>vs base</th></tr>
"""
        base_med = pr9["A_baseline_lad"]["median"]["median_ape"]
        for name, res in pr9.items():
            m = res["median"]
            b4 = res["price_band_median"].get("B4", {}).get("median_ape", 0)
            delta = m["median_ape"] - base_med
            cls = "best" if name == "A_baseline_lad" else ("warn" if delta < 0.05 else "neg")
            html += f"<tr class='{cls}'><td>{name}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td><td class='num'>{fmt(b4)}</td><td class='num'>{delta:+.3f}</td></tr>\n"
        html += """</table>
<blockquote>
<b>흥미로운 발견</b>: Overall 악화하지만 B4 (&gt;10M)만 LGB combined로 -7pp 개선 (0.602 → 0.533).
운영 시 soft routing 가능성 있으나 1차 예측 noise 위험으로 단순 LAD 유지 권장.
</blockquote>
"""

    # 학습 내용
    html += """
<h2>🎓 학습 내용 (Lessons Learned)</h2>
<div class="lessons">
<h3>1. 단일 강모델 > 조건부 분리</h3>
<ul>
  <li><b>Cold:</b> LAD (linear, outlier robust)가 LightGBM (default + Optuna 둘 다) 능가</li>
  <li>6 features만 쓰는 cold-start에서 선형 모델이 충분</li>
  <li>Tree model은 squared loss로 long-tail에 sensitive</li>
</ul>

<h3>2. Feature Engineering이 가장 안전한 향상 수단</h3>
<ul>
  <li>PR7 ALL: Cold -3.8pp / Warm -1.2pp <b>유일한 성공</b></li>
  <li>Source feature 추가가 가장 큰 효과 (Cold -0.016)</li>
  <li>Popularity는 cold-start에 악화 (unseen 작가에 정보 없음)</li>
</ul>

<h3>3. Conditional/Segmentation은 데이터 부족 시 위험</h3>
<ul>
  <li>PR8 모든 variant negative result (표본 부족)</li>
  <li>40K rows / 12 cells = 평균 3K/cell — LAD 학습에 불충분</li>
  <li>Codex 사전 경고 정확</li>
</ul>

<h3>4. Heteroscedastic 처리는 trade-off</h3>
<ul>
  <li>PR9 Quantile + reweight: B4 -7pp, 일반 +3-5pp</li>
  <li>거장 작품 정확도 ↑ vs 일반 작품 정확도 ↓</li>
  <li>Soft routing 가능성 있으나 추가 noise 위험</li>
</ul>

<h3>5. Source bias 정량화의 가치</h3>
<ul>
  <li>PR5에서 Artsy +45.5% 발견 → PR7에서 -0.016 흡수</li>
  <li>Source 정보 입력 운영 필수</li>
  <li>가격 데이터 정책 차이 (갤러리 마크업) 명시 필요</li>
</ul>
</div>

<h2>🎯 운영 권장 (최종)</h2>
<table>
<tr><th>조건</th><th>모델</th><th>med_APE</th><th>W30</th><th>주의사항</th></tr>
<tr class='best'><td>학습 ≥1건 작가</td><td>Warm Tuned LGB + ALL</td><td class='num'>0.104</td><td class='num'>0.78</td><td>artist signal 활용</td></tr>
<tr><td>학습 0건 (신규)</td><td>Cold LAD + ALL</td><td class='num'>0.391</td><td class='num'>0.37</td><td>source 정보 필수</td></tr>
<tr class='warn'><td>고가 (&gt;10M, Warm)</td><td>Warm 2-stage</td><td class='num'>0.15</td><td>—</td><td>학습된 작가 한정</td></tr>
<tr class='critical'><td>고가 (&gt;100M, Cold)</td><td>예측 불가</td><td class='num err'>0.98</td><td>—</td><td>🔴 가격 가이드 비공개</td></tr>
</table>

<h2>⚠️ 외부 보고 시 한계 명시</h2>
<ul>
  <li>🔴 본 모델은 <b>"listing-price prediction"</b>이지 "시장가치 예측" 아님</li>
  <li>🔴 <b>Source bias +45.5%</b> (Artsy 갤러리 마크업) — PR7에서 흡수, 운영 시 source 입력 필수</li>
  <li>🔴 <b>Warm 0.104는 "학습된 작가 신규 작품" 기준</b>. 신규 작가 섞이면 0.15-0.40</li>
  <li>🔴 <b>&gt;100M Cold</b>는 사실상 예측 불가 (0.98)</li>
  <li>⚠️ 시간 split 없음 — temporal validation 불가</li>
  <li>⚠️ 데이터 40K로 conditional expert/segmentation 위험 (PR8 입증)</li>
</ul>

<h2>🚀 다음 단계 (B: 운영 구현)</h2>
<ol>
  <li><b>Production model artifact</b> — PR7 ALL 학습 + joblib/pickle 저장</li>
  <li><b>운영 라우팅 함수</b> — train_count 기반 Warm/Cold 분기</li>
  <li><b>Source 입력 검증</b> — 없을 때 fallback 또는 reject</li>
  <li><b>예측 API</b> — single record / batch inference</li>
  <li><b>Monitoring</b> — 운영 데이터 분포 drift / 정확도 추적</li>
  <li><b>A/B testing 인프라</b> — Track 1 vs Track 3 비교 시 활용</li>
</ol>

<h2>📂 산출물 (최종)</h2>
<ul>
  <li><b>Plan</b>: <code>docs/track3_modeling_plan_v2_1.md</code> (Codex R3 통과)</li>
  <li><b>Phase 코드 (9 scripts)</b>: <code>split_data.py</code> ~ <code>train_phase5_final.py</code></li>
  <li><b>PR 코드 (7 scripts)</b>: PR1~9 (PR6 skipped, PR10 데이터 의존)</li>
  <li><b>리포트</b>: v1 → v2 → v3 → <b>v4 (최종)</b></li>
  <li><b>데이터</b>: <code>data/track3_unified_v1_train.csv</code> (40,137 rows, is_outlier=0)</li>
</ul>

<p class="meta" style="margin-top: 36px;">Track 3 모델링 — 9-phase + 9-PR (PR1~5, 7, 8, 9) 완료. Codex 4회 검수 통과.<br>
v4: 최종판. PR8/9 negative result 포함. 운영 구현 준비.</p>

</body></html>
"""

    OUT.write_text(html)
    print(f"✅ HTML report v4 (FINAL): {OUT}")
    print(f"   Size: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
