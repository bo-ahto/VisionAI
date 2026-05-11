"""Track 3 v2 HTML 리포트 — Phase 0~5 + 후속 PR 1~5 통합.

새 내용 (v1 → v2):
- 후속 PR 5건 결과 섹션
- Source bias 발견 (Artsy +45.5%) — caveat 강화
- 운영 라우팅 2-way 단순화 (PR2)
- Conformal 신뢰구간 표 (PR3)
- Multi-seed Cold CI 갱신 (PR4)
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parent.parent.parent
DATA = REPO / "data"
OUT = REPO / "docs" / "track3_modeling_results_v2.html"


def load(name):
    p = DATA / f"track3_{name}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


def fmt(v, n=3):
    return f"{v:.{n}f}" if isinstance(v, (int, float)) else "—"


def main():
    p5 = load("phase5_results")
    pr1 = load("pr1_optuna_results")
    pr2 = load("pr2_blend_results")
    pr3 = load("pr3_conformal_results")
    pr4 = load("pr4_multiseed_results")
    pr5 = load("pr5_source_bias_results")

    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>Track 3 — 가격 예측 모델링 결과 v2</title>
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
  .meta {{ color: #6b7280; font-size: 0.9em; }}
  blockquote {{ background: #f3f4f6; border-left: 4px solid #9ca3af; padding: 10px 16px; margin: 12px 0; }}
  code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  .pr-summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 16px 0; }}
  .pr-card {{ border: 2px solid #2563eb; border-radius: 6px; padding: 10px; }}
  .pr-card h4 {{ margin: 0 0 6px 0; color: #1e3a8a; }}
  .pr-card .meta {{ font-size: 0.85em; }}
</style></head><body>

<h1>Track 3 — 가격 예측 모델링 결과 v2</h1>
<p class="meta">생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} / Plan: <code>docs/track3_modeling_plan_v2_1.md</code> (Codex R3 통과)</p>

<blockquote style="background: #dbeafe; border-color: #2563eb;">
<b>v1 → v2 변경</b>:
<ul>
  <li>후속 PR 1~5 결과 통합 (Optuna tuning / Blend grid / Conformal / Multi-seed / Source bias)</li>
  <li>🔴 <b>Source bias 중대 발견</b>: Artsy +45.5% (갤러리 마크업) — caveat 강화</li>
  <li>운영 라우팅 2-way 단순화 (PR2 — train_count ≥1 → Warm 100%)</li>
  <li>Conformal 신뢰구간 표 추가 (PR3)</li>
  <li>Multi-seed Cold LAD CI 정밀화 (PR4 — [0.407, 0.454])</li>
</ul>
</blockquote>

<h2>🎯 최종 운영 권장 (v2)</h2>
<table>
<tr><th>조건</th><th>모델</th><th>med_APE</th><th>W30</th><th>80% 신뢰구간</th><th>주의사항</th></tr>
<tr class='best'><td><b>학습 ≥1건 작가</b></td><td>Warm LightGBM (tuned)</td><td class='num'>0.116</td><td class='num'>0.75</td><td>±44%</td><td>artist signal 활용</td></tr>
<tr><td>학습 0건 (신규)</td><td>Cold LAD</td><td class='num'>0.431±0.028</td><td class='num'>0.37</td><td>±115%</td><td>outer holdout 0.389</td></tr>
<tr class='warn'><td>거장 (&gt;10M, Warm)</td><td>Warm 2-stage</td><td class='num'>0.15</td><td>—</td><td>—</td><td>&gt;100M med_APE 0.04</td></tr>
<tr class='critical'><td>거장 (&gt;100M, Cold)</td><td>예측 불가</td><td class='num err'>0.984</td><td>—</td><td class='err'>비신뢰</td><td>🔴 가격 가이드 비공개 권장</td></tr>
</table>

<h2>🔴 가장 중요한 운영 caveat</h2>
<blockquote style="background: #fee2e2; border-color: #dc2626;">
<b>본 모델은 "listing-price prediction"이지 "시장가치 예측" 아님</b>:
<ul>
  <li>🔴 <b>Source bias +45.5%</b> (PR5): Artsy listing이 동일 작품 특성 대비 Saatchi 대비 45.5% 비쌈 (갤러리 마크업 입증).
    <ul>
      <li>운영 시 source 정보 없이 예측하면 ±20-45% 오차</li>
      <li>Artsy 작품을 Saatchi 모델로 예측 → underestimate ~30%</li>
      <li><b>권장</b>: 운영에서 source 정보 입력 또는 source별 calibration factor 적용</li>
    </ul>
  </li>
  <li>🔴 <b>Warm 0.123은 "학습된 작가 신규 작품" 기준</b>. 실 운영에서 신규 작가 섞이면 평균 정확도는 더 낮음 (0.15-0.40 사이).</li>
  <li>🔴 <b>&gt;100M Cold 작품은 사실상 예측 불가</b> (med_APE 0.889). Warm 라우팅 필수.</li>
  <li>⚠️ 시간 split 없음 — temporal validation 불가 (가격 트렌드 변화 X)</li>
  <li>⚠️ 실제 거래가 ≠ 게시가 (미판매 / 협상 / 갤러리 마진)</li>
</ul>
</blockquote>

<h2>📊 후속 PR 1~5 요약</h2>
<div class="pr-summary">
  <div class="pr-card">
    <h4>PR1 — Optuna Tuning</h4>
    <p class="meta">LGB hyperparameter 튜닝</p>
    <p><b>Cold</b>: 0.488 (vs LAD 0.429 ✗)</p>
    <p><b>Warm</b>: 0.116 (-0.003 ✓)</p>
    <p class="meta">→ Cold = LAD 확정</p>
  </div>
  <div class="pr-card">
    <h4>PR2 — Blend Grid</h4>
    <p class="meta">Rare artist blend 비율</p>
    <p>1건: w_cold=0.20</p>
    <p>2건: w_cold=0.00</p>
    <p>≥3건: w_cold=0.00</p>
    <p class="meta">→ 실질 2-way 라우팅</p>
  </div>
  <div class="pr-card">
    <h4>PR3 — Conformal</h4>
    <p class="meta">80/90% 신뢰구간</p>
    <p>Warm 80%: ±44%</p>
    <p>Cold 80%: ±115%</p>
    <p class="meta">B4 Cold 0.47 ⚠️</p>
  </div>
  <div class="pr-card">
    <h4>PR4 — Multi-seed Cold</h4>
    <p class="meta">GroupShuffleSplit×10</p>
    <p>med_APE: 0.431±0.028</p>
    <p>95% CI: [0.407, 0.454]</p>
    <p class="meta">→ Phase 5 robust 입증</p>
  </div>
  <div class="pr-card" style="border-color: #dc2626;">
    <h4>PR5 — Source Bias 🔴</h4>
    <p class="meta">listing price 차이</p>
    <p><b>Artsy: +45.5%</b></p>
    <p>Artue: +1.0%</p>
    <p class="meta">→ 갤러리 마크업 입증</p>
  </div>
</div>

<h2>🏆 최종 Best 모델 + 95% CI</h2>
<table>
<tr><th>시나리오</th><th>모델</th><th>med_APE</th><th>95% CI</th><th>비고</th></tr>
<tr class='best'><td>Cold-start (unseen)</td><td>LAD (Quantile q=0.5)</td><td class='num'>0.431</td><td class='num'>[0.407, 0.454] (PR4)</td><td>Phase 1 best, Optuna로도 추월 X</td></tr>
<tr class='best'><td>Warm-start (≥1건)</td><td>Tuned LightGBM</td><td class='num'>0.116</td><td class='num'>[0.113, 0.119] (PR1)</td><td>PR1 tuning -0.003</td></tr>
<tr class='best'><td>거장 (&gt;100M, Warm)</td><td>Warm 2-stage</td><td class='num'>0.042</td><td>—</td><td>분류기 + 구간별 회귀</td></tr>
</table>
"""

    # PR5 source bias 섹션 (최우선)
    if pr5:
        reg = pr5["regression"]
        html += f"""
<h2>🔴 PR5 — Source Bias 분석 (가장 중요)</h2>

<h3>Source 가격 분포</h3>
<table>
<tr><th>Source</th><th>n</th><th>median (KRW)</th><th>mean (KRW)</th><th>q25</th><th>q75</th></tr>"""
        for src, stats in pr5["source_stats"]["count"].items():
            n = pr5["source_stats"]["count"][src]
            med = int(pr5["source_stats"]["median"][src])
            mean = int(pr5["source_stats"]["mean"][src])
            q25 = int(pr5["source_stats"]["q25"][src])
            q75 = int(pr5["source_stats"]["q75"][src])
            html += f"\n<tr><td><b>{src}</b></td><td class='num'>{n:,}</td><td class='num'>{med:,}</td><td class='num'>{mean:,}</td><td class='num'>{q25:,}</td><td class='num'>{q75:,}</td></tr>"
        html += f"""
</table>

<h3>Same-artist Cross-source 가격 비율 (median)</h3>
<table>
<tr><th>비교</th><th>n</th><th>median ratio</th></tr>"""
        for pair in pr5["pair_summary"]:
            cls = "critical" if pair["median_ratio"] > 1.3 else ""
            html += f"\n<tr class='{cls}'><td>{pair['src1']} / {pair['src2']}</td><td class='num'>{int(pair['n'])}</td><td class='num'>{pair['median_ratio']:.2f}×</td></tr>"
        html += f"""
</table>

<h3>Linear Regression — Source Effect (controls: medium/area/ho/orientation)</h3>
<table>
<tr><th>Source</th><th>log coefficient</th><th>vs Saatchi (%)</th></tr>
<tr><td>Saatchi (baseline)</td><td class='num'>0</td><td class='num'>—</td></tr>
<tr class='critical'><td><b>Artsy</b></td><td class='num'>{reg['artsy_log_coef']:+.3f}</td><td class='num'><b>{reg['artsy_pct_vs_saatchi']:+.1f}%</b></td></tr>
<tr><td>Artue</td><td class='num'>{reg['artue_log_coef']:+.3f}</td><td class='num'>{reg['artue_pct_vs_saatchi']:+.1f}%</td></tr>
</table>

<blockquote style="background: #fee2e2;">
<b>🔴 결론</b>: 동일 작품 특성 (medium/크기/호수/orientation) 대비 <b>Artsy listing이 Saatchi 대비 45.5% 비쌈</b>.
갤러리 마크업 가설 정량 입증.<br>
<b>운영 영향</b>: source 정보 없이 예측 시 ±20-45% 오차 가능 → source 입력 또는 calibration 필요.
</blockquote>
"""

    # PR1 Optuna
    if pr1:
        cold = pr1["cold"]
        warm = pr1["warm"]
        html += f"""
<h2>📐 PR1 — LightGBM Optuna Tuning</h2>
<h3>Cold</h3>
<table>
<tr><th>Variant</th><th>med_APE</th><th>vs reference</th></tr>
<tr><td>Default LGB (Phase 2)</td><td class='num'>0.473</td><td>—</td></tr>
<tr class='warn'><td>Tuned LGB (PR1)</td><td class='num'>{fmt(cold['final_5fold_median']['median_ape'])}</td><td class='num'>vs default {cold['vs_default_0473']:+.3f}</td></tr>
<tr class='best'><td>LAD (Phase 1)</td><td class='num'>0.429</td><td class='num'>vs Tuned LGB {-cold['vs_lad_0429']:+.3f}</td></tr>
</table>
<blockquote>Optuna 튜닝 후에도 LGB가 LAD 추월 실패. <b>Cold model = LAD 확정</b>.</blockquote>

<h3>Warm</h3>
<table>
<tr><th>Variant</th><th>med_APE (mean±std)</th><th>vs default</th></tr>
<tr><td>Default LGB (Phase 2)</td><td class='num'>0.119±0.002</td><td>—</td></tr>
<tr class='best'><td>Tuned LGB (PR1)</td><td class='num'>{fmt(warm['final_n3_mean']['median_ape'])}±{fmt(warm['final_n3_std']['median_ape'])}</td><td class='num'>{warm['vs_default_0119']:+.3f}</td></tr>
</table>
<blockquote><b>Warm model = Tuned LightGBM 확정</b>. 미세 개선 (-0.003).</blockquote>
"""

    # PR2 Blend grid
    if pr2:
        html += """
<h2>🔀 PR2 — Rare Artist Blend Grid</h2>
<table>
<tr><th>Category</th><th>n</th><th>Best w_cold</th><th>Best med_APE</th></tr>
"""
        for cat, res in pr2.items():
            html += f"<tr><td>{cat}</td><td class='num'>{res['n']:,}</td><td class='num'>{res['best_w_cold']:.2f}</td><td class='num'>{res['best_med_ape']:.3f}</td></tr>\n"
        html += """</table>
<blockquote><b>운영 라우팅 단순화</b>: <code>train_count ≥ 1</code> → Warm 100% (rare도 Warm 우세), <code>train_count == 0</code> → Cold LAD. Plan v2.1의 3-way → 실질 2-way.</blockquote>
"""

    # PR3 Conformal
    if pr3:
        html += """
<h2>📏 PR3 — Conformal Prediction</h2>
<h3>Coverage + 폭 (예측가 대비)</h3>
<table>
<tr><th>모델</th><th>Target</th><th>Overall coverage</th><th>폭 (±%)</th><th>B4 coverage</th></tr>
"""
        for key in ["warm_lgb_80pct", "warm_lgb_90pct", "cold_lad_80pct", "cold_lad_90pct"]:
            if key not in pr3: continue
            cov = pr3[key]
            o = cov["overall"]
            b4 = cov["by_price_band"].get("B4", {}).get("coverage", 0)
            cls = "warn" if b4 < 0.7 else ""
            target = key.split("_")[-1]
            model = "Warm LGB" if "warm" in key else "Cold LAD"
            half_width = o["median_width_pct"] / 2
            html += f"<tr class='{cls}'><td>{model}</td><td>{target}</td><td class='num'>{o['coverage']:.3f}</td><td class='num'>±{half_width:.1f}%</td><td class='num'>{b4:.3f}</td></tr>\n"
        html += """</table>
<blockquote>Warm 80% interval (±44%)은 운영 가용. Cold 80% (±115%)는 넓지만 calibrated. B4 (>10M) Cold 0.47 → 거장 작품 신뢰구간 신뢰 불가.</blockquote>
"""

    # PR4 Multi-seed Cold LAD
    if pr4:
        html += f"""
<h2>🎲 PR4 — Multi-seed Cold LAD (GroupShuffleSplit × 10)</h2>
<table>
<tr><th>Estimate</th><th>med_APE</th><th>95% CI</th><th>비고</th></tr>
<tr><td>Phase 5 (5-fold OOF)</td><td class='num'>0.429</td><td class='num'>[0.393, 0.540]</td><td>N=5 bootstrap (wide)</td></tr>
<tr class='best'><td><b>PR4 GSSplit × 10</b></td><td class='num'><b>{fmt(pr4['median_ape_mean'])}±{fmt(pr4['median_ape_std'])}</b></td><td class='num'><b>[{fmt(pr4['median_ape_95ci'][0])}, {fmt(pr4['median_ape_95ci'][1])}]</b></td><td>N=10 (정밀)</td></tr>
</table>
<blockquote>Phase 5 single estimate (0.429)는 multi-seed mean (0.431)과 일치 → <b>Cold LAD 추정치 robust 입증</b>. 진짜 CI는 [0.407, 0.454].</blockquote>
"""

    html += """
<h2>📋 Phase별 진행 요약</h2>
<table>
<tr><th>Phase</th><th>목표 / Gate</th><th>최선 결과</th><th>핵심 발견</th></tr>
<tr><td>0</td><td>baseline + ho/area ablation</td><td>median 0.754 / LGB both 0.472</td><td>both 유지 (MAPE 안정)</td></tr>
<tr><td>1 (선형)</td><td>cold &lt; 75%</td><td>LAD 0.429 / Quantile 0.314</td><td>Cold LAD가 outlier robust</td></tr>
<tr><td>2 (비선형)</td><td>cold &lt; 60%</td><td>LGB 0.473 / Warm LGB 0.119</td><td>Cold는 선형이 우세</td></tr>
<tr><td>3 (Hybrid)</td><td>cold &lt; 55%</td><td>best blend 0.421</td><td>Hybrid 가치 작음</td></tr>
<tr><td>4 (Cold 특화)</td><td>cold &lt; 50%</td><td>KNN_k10 0.494</td><td>6 features 한계</td></tr>
<tr><td>4.5 (거장 2-stage)</td><td>B4/&gt;100M 해결</td><td>Warm &gt;100M 0.042</td><td>Cold는 부분 해결</td></tr>
<tr><td>5 (최종)</td><td>95% CI + 감사</td><td>Cold 0.429, Warm 0.123</td><td>Outer holdout Cold 0.389</td></tr>
</table>

<h2>📂 산출물</h2>
<ul>
  <li><b>Plan</b>: <code>docs/track3_modeling_plan_v2_1.md</code> (Codex R3 통과)</li>
  <li><b>최종 모델 코드</b>:
    <ul>
      <li><code>scripts/track3/split_data.py</code></li>
      <li><code>scripts/track3/baseline.py</code> / <code>train_linear_{cold,warm}.py</code> / <code>train_tree_{cold,warm}.py</code></li>
      <li><code>scripts/track3/train_hybrid.py</code> / <code>train_coldstart.py</code> / <code>train_two_stage.py</code></li>
      <li><code>scripts/track3/train_phase5_final.py</code></li>
    </ul>
  </li>
  <li><b>후속 PR (이번 v2 새로)</b>:
    <ul>
      <li><code>scripts/track3/pr1_optuna_tuning.py</code> — LGB Optuna</li>
      <li><code>scripts/track3/pr2_rare_artist_blend.py</code> — Blend grid</li>
      <li><code>scripts/track3/pr3_conformal_prediction.py</code> — Conformal</li>
      <li><code>scripts/track3/pr4_multiseed_cold_lad.py</code> — Multi-seed</li>
      <li><code>scripts/track3/pr5_source_bias_audit.py</code> — Source bias</li>
    </ul>
  </li>
  <li><b>데이터</b>: <code>data/track3_unified_v1.parquet</code> (학습 셋 40,137 rows)</li>
</ul>

<h2>🔄 미실행 (향후 작업)</h2>
<ol>
  <li><b>Source feature 학습 input 추가</b> (PR5 결과 반영) — Artsy +45.5% calibration</li>
  <li><b>Time-aware validation</b> — listing year 수집 후 temporal split</li>
  <li><b>Multi-seed Warm + Outer holdout balanced</b></li>
  <li><b>Cold 호수별 separate model</b> — B4 거장만 별도 학습</li>
  <li><b>운영 라우팅 production 구현</b> + monitoring</li>
</ol>

<p class="meta" style="margin-top: 36px;">Track 3 모델링 — 9-phase + 5-PR 완료. Codex 3회 검수 통과.<br>
v2: 후속 PR 5건 통합 + source bias 발견 + 운영 가이드 단순화.</p>

</body></html>
"""

    OUT.write_text(html)
    print(f"✅ HTML report v2: {OUT}")
    print(f"   Size: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
