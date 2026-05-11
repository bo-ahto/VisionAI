"""Track 3 v3 HTML 리포트 — PR7 (Feature Engineering 묶음) 통합.

v2 → v3 변경:
- PR7 ablation 결과 + Cold/Warm ALL features 적용
- 업데이트된 최종 Best: Cold 0.391 / Warm 0.104
- Source feature 효과 입증 (Cold -0.016)
- Cold popularity 위험 입증 (Codex 경고 정확)
- 다음 작업: PR8 (Conditional expert) 권장 (Codex 검수 통과)
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parent.parent.parent
DATA = REPO / "data"
OUT = REPO / "docs" / "track3_modeling_results_v3.html"


def load(name):
    p = DATA / f"track3_{name}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


def fmt(v, n=3):
    return f"{v:.{n}f}" if isinstance(v, (int, float)) else "—"


def main():
    p5 = load("phase5_results")
    pr5 = load("pr5_source_bias_results")
    pr7 = load("pr7_results")

    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>Track 3 — 가격 예측 모델링 결과 v3</title>
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
  .meta {{ color: #6b7280; font-size: 0.9em; }}
  blockquote {{ background: #f3f4f6; border-left: 4px solid #9ca3af; padding: 10px 16px; margin: 12px 0; }}
  code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
</style></head><body>

<h1>Track 3 — 가격 예측 모델링 결과 v3</h1>
<p class="meta">생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} / Plan: <code>docs/track3_modeling_plan_v2_1.md</code> (Codex R3 통과)</p>

<blockquote class="new" style="border-color: #2563eb;">
<b>v2 → v3 변경</b>:
<ul>
  <li>🆕 <b>PR7 (Feature Engineering 묶음) 결과 통합</b>
    <ul>
      <li>Cold ALL features: <b>0.429 → 0.391 (-0.038, 9% 향상)</b></li>
      <li>Warm ALL features: <b>0.115 → 0.104 (-0.012, 10% 향상)</b></li>
    </ul>
  </li>
  <li>🔬 <b>Codex 권장 정확</b>: Source feature 효과 (Cold -0.016) + popularity Cold 위험 (+0.016 악화)</li>
  <li>📋 다음 단계: <b>PR8 (Conditional expert + fallback)</b> — Codex 검수 통과</li>
</ul>
</blockquote>

<h2>🏆 최종 Best 모델 (v3)</h2>
<table>
<tr><th>시나리오</th><th>모델</th><th>med_APE</th><th>W30</th><th>vs v2</th></tr>
<tr class='best'><td><b>Cold-start</b></td><td>LAD + ALL features<br><small>(base 6 + source + interaction + popularity + aspect)</small></td><td class='num'>0.391</td><td class='num'>0.373</td><td class='num'>-0.038 ★</td></tr>
<tr class='best'><td><b>Warm-start (≥1건)</b></td><td>Tuned LGB + ALL features<br><small>(base 7 + interaction + popularity + aspect)</small></td><td class='num'>0.104±0.001</td><td class='num'>0.776</td><td class='num'>-0.012 ★</td></tr>
<tr class='best'><td>거장 (&gt;100M, Warm)</td><td>Warm 2-stage</td><td class='num'>0.042</td><td>—</td><td>(미적용)</td></tr>
<tr class='critical'><td>거장 (&gt;100M, Cold)</td><td>예측 불가</td><td class='num err'>0.984</td><td>—</td><td>(PR8에서 처리 예정)</td></tr>
</table>

<h2>🔬 PR7 — Feature Engineering Ablation (v3 핵심)</h2>
"""

    if pr7:
        cold = pr7["cold"]
        warm = pr7["warm"]
        html += """
<h3>Cold LAD (5-fold GroupKFold OOF, fold-median)</h3>
<table>
<tr><th>Variant</th><th>med_APE</th><th>MAPE</th><th>RMSE_log</th><th>W30</th><th>vs baseline</th></tr>
"""
        base_med = cold["baseline"]["median"]["median_ape"]
        for v, res in cold.items():
            m = res["median"]
            delta = m["median_ape"] - base_med
            if v == "all":
                cls = "best"
            elif v == "popularity":
                cls = "err"  # 악화
            elif v == "source":
                cls = "new"  # 가장 좋은 single
            else:
                cls = ""
            html += f"<tr class='{cls}'><td>{v}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['mape'])}</td><td class='num'>{fmt(m['rmse_log'])}</td><td class='num'>{fmt(m['within_30pct'])}</td><td class='num'>{delta:+.3f}</td></tr>\n"
        html += """</table>

<h3>Warm Tuned LGB (random 80/10/10 × N=3)</h3>
<table>
<tr><th>Variant</th><th>med_APE (mean±std)</th><th>MAPE</th><th>W30</th><th>vs baseline</th></tr>
"""
        base_w = warm["baseline"]["mean"]["median_ape"]
        for v, res in warm.items():
            m = res["mean"]; s = res["std"]
            delta = m["median_ape"] - base_w
            if v == "all" or v == "popularity":
                cls = "best"
            else:
                cls = ""
            html += f"<tr class='{cls}'><td>{v}</td><td class='num'>{fmt(m['median_ape'])}±{fmt(s['median_ape'])}</td><td class='num'>{fmt(m['mape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td><td class='num'>{delta:+.3f}</td></tr>\n"
        html += """</table>

<blockquote>
<b>핵심 발견 (Codex 예측 정확)</b>:
<ul>
  <li>✅ <b>Cold source -0.016</b>: PR5에서 입증된 +45.5% bias 정량 흡수 확인</li>
  <li>⚠️ <b>Cold popularity +0.016 악화</b>: cold-start unseen 작가에 popularity 의미 없음 (Codex 경고 적중)</li>
  <li>★ <b>Cold ALL -0.038 (9% 향상)</b>: 단일 feature 합보다 더 큰 효과 (상호보완)</li>
  <li>✅ <b>Warm popularity -0.012</b>: artist signal과 결합 효과 최대</li>
  <li>· Warm source 효과 미미: artist categorical이 이미 source 정보 포함</li>
  <li>· N=3이라 0.103/0.104는 사실상 동률 (Codex 경고)</li>
</ul>
</blockquote>
"""

    # PR5 source bias (요약)
    if pr5:
        reg = pr5["regression"]
        html += f"""
<h2>🔴 Source Bias (PR5 — v2에서 발견, PR7 흡수)</h2>
<table>
<tr><th>Source</th><th>log coef</th><th>vs Saatchi (%)</th></tr>
<tr><td>Saatchi (baseline)</td><td class='num'>0</td><td>—</td></tr>
<tr class='critical'><td><b>Artsy</b></td><td class='num'>{reg['artsy_log_coef']:+.3f}</td><td class='num'><b>{reg['artsy_pct_vs_saatchi']:+.1f}%</b></td></tr>
<tr><td>Artue</td><td class='num'>{reg['artue_log_coef']:+.3f}</td><td class='num'>{reg['artue_pct_vs_saatchi']:+.1f}%</td></tr>
</table>
<blockquote>
PR7에서 Cold source feature 추가 → med_APE -0.016 (직접 흡수 확인).
운영 시 source 정보 입력 필수.
</blockquote>
"""

    html += """
<h2>📋 후속 PR 진행 상황</h2>
<table>
<tr><th>PR</th><th>Status</th><th>핵심 결과</th></tr>
<tr><td>PR1 Optuna Tuning</td><td>✓ 완료</td><td>Cold = LAD 확정, Warm tuned -0.003</td></tr>
<tr><td>PR2 Blend grid</td><td>✓ 완료</td><td>운영 라우팅 2-way 단순화</td></tr>
<tr><td>PR3 Conformal</td><td>✓ 완료</td><td>Warm 80% ±44%, Cold 80% ±115%</td></tr>
<tr><td>PR4 Multi-seed Cold</td><td>✓ 완료</td><td>CI [0.407, 0.454]</td></tr>
<tr><td>PR5 Source bias</td><td>✓ 완료</td><td>🔴 Artsy +45.5% 입증</td></tr>
<tr class='best'><td><b>PR7 Feature Eng 묶음</b></td><td><b>✓ 완료 (v3)</b></td><td><b>Cold -3.8pp, Warm -1.2pp</b></td></tr>
<tr class='new'><td><b>PR8 Conditional expert</b></td><td><b>🔄 진행 중</b></td><td>price-band/source soft expert, Codex 권장</td></tr>
<tr><td>PR9 Quantile + reweight</td><td>대기</td><td>PR8 다음 (분리 평가)</td></tr>
<tr><td>PR10 Time-aware</td><td>데이터 의존</td><td>listing year 수집 후</td></tr>
</table>

<h2>🎯 운영 권장 (v3 갱신)</h2>
<table>
<tr><th>조건</th><th>모델</th><th>med_APE</th><th>W30</th><th>주의</th></tr>
<tr class='best'><td>학습 ≥1건 작가</td><td>Warm Tuned LGB + ALL features</td><td class='num'>0.104</td><td class='num'>0.78</td><td>artist signal 활용</td></tr>
<tr><td>학습 0건 (신규)</td><td>Cold LAD + ALL features</td><td class='num'>0.391</td><td class='num'>0.37</td><td>source 정보 필수</td></tr>
<tr class='warn'><td>거장 (&gt;10M, Warm)</td><td>Warm 2-stage</td><td class='num'>0.15</td><td>—</td><td>학습된 작가 한정</td></tr>
<tr class='critical'><td>거장 (&gt;100M, Cold)</td><td>예측 불가</td><td class='num err'>0.98</td><td>—</td><td>🔴 비공개, PR8 처리 예정</td></tr>
</table>

<h2>⚠️ 주요 한계 (외부 보고 시)</h2>
<ul>
  <li>🔴 <b>"listing-price prediction"</b>이지 "시장가치 예측" 아님</li>
  <li>🔴 <b>Source bias +45.5%</b> (Artsy 갤러리 마크업) — PR7에서 부분 흡수, 운영 시 source 입력 필수</li>
  <li>🔴 <b>Warm 0.104는 "학습된 작가 신규 작품" 기준</b>. 실 운영 신규 작가 섞이면 0.15-0.40</li>
  <li>🔴 <b>&gt;100M Cold 0.98</b>: 사실상 예측 불가, PR8에서 conditional expert로 시도 중</li>
  <li>⚠️ 시간 split 없음 — temporal validation 불가</li>
  <li>⚠️ Cold popularity feature는 cold-start에 악화 (운영 시 사용 X 권장)</li>
</ul>

<h2>📂 산출물</h2>
<ul>
  <li><b>Plan</b>: <code>docs/track3_modeling_plan_v2_1.md</code> (Codex R3 통과)</li>
  <li><b>최종 모델 코드 (8 phase)</b>: <code>scripts/track3/split_data.py</code> ~ <code>train_phase5_final.py</code></li>
  <li><b>후속 PR 코드 (6건)</b>:
    <ul>
      <li>PR1: <code>pr1_optuna_tuning.py</code></li>
      <li>PR2: <code>pr2_rare_artist_blend.py</code></li>
      <li>PR3: <code>pr3_conformal_prediction.py</code></li>
      <li>PR4: <code>pr4_multiseed_cold_lad.py</code></li>
      <li>PR5: <code>pr5_source_bias_audit.py</code></li>
      <li>PR7: <code>pr7_feature_engineering.py</code> ← v3 핵심</li>
      <li>PR8: <code>pr8_conditional_expert.py</code> ← 🔄 진행 중</li>
    </ul>
  </li>
</ul>

<p class="meta" style="margin-top: 36px;">Track 3 모델링 — 9-phase + 7-PR 완료, PR8 진행 중. Codex 4회 검수 통과.<br>
v3: PR7 통합 + Cold/Warm 모두 의미 있는 향상 (9-10%).</p>

</body></html>
"""

    OUT.write_text(html)
    print(f"✅ HTML report v3: {OUT}")
    print(f"   Size: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
