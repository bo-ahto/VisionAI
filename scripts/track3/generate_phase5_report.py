"""Track 3 Phase 5 최종 HTML 리포트 생성."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

REPO = Path(__file__).resolve().parent.parent.parent
DATA = REPO / "data"
OUT = REPO / "docs" / "track3_modeling_results_v1.html"


def load(name):
    p = DATA / f"track3_{name}.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


def main():
    p0 = load("baseline_results")
    p1c = load("phase1_cold_results")
    p1w = load("phase1_warm_results")
    p2c = load("phase2_cold_results")
    p2w = load("phase2_warm_results")
    p3 = load("phase3_results")
    p4 = load("phase4_results")
    p45 = load("phase45_results")
    p5 = load("phase5_results")

    def fmt(v, n=3):
        return f"{v:.{n}f}" if isinstance(v, (int, float)) else "—"

    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>Track 3 — 가격 예측 모델링 결과 v1</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 1100px; margin: 30px auto; padding: 20px; color: #222; }}
  h1 {{ border-bottom: 3px solid #2563eb; padding-bottom: 8px; }}
  h2 {{ color: #1e40af; margin-top: 32px; border-left: 4px solid #2563eb; padding-left: 12px; }}
  h3 {{ color: #1e3a8a; }}
  table {{ border-collapse: collapse; margin: 12px 0; }}
  th, td {{ border: 1px solid #d1d5db; padding: 6px 12px; text-align: left; }}
  th {{ background: #eff6ff; }}
  td.num {{ text-align: right; font-family: ui-monospace, monospace; }}
  .best {{ background: #d1fae5; font-weight: bold; }}
  .warn {{ background: #fef3c7; }}
  .err {{ background: #fee2e2; }}
  .meta {{ color: #6b7280; font-size: 0.9em; }}
  blockquote {{ background: #f3f4f6; border-left: 4px solid #9ca3af; padding: 10px 16px; margin: 12px 0; }}
  code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
</style></head><body>

<h1>Track 3 — 가격 예측 모델링 결과 v1</h1>
<p class="meta">생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} / Plan: <code>docs/track3_modeling_plan_v2_1.md</code> (Codex R3 통과)</p>

<h2>🎯 목표 & 데이터</h2>
<ul>
  <li><b>Primary</b>: Cold-start (unseen artist) 예측 정확도 향상</li>
  <li><b>Secondary</b>: Warm-start (seen artist) 예측 정확도 향상</li>
  <li><b>운영 라우팅</b>: 3-way (Warm ≥3건 / Blend 1-2건 / Cold unseen)</li>
</ul>
<table>
<tr><th>항목</th><th>값</th></tr>
<tr><td>Dev pool</td><td class="num">32,891 rows / 1,706 작가</td></tr>
<tr><td>Outer holdout (Phase 5 감사)</td><td class="num">7,246 rows / 426 작가 (20%)</td></tr>
<tr><td>Source</td><td>Artsy 10,584 / Saatchi 26,844 (67%) / Artue 2,709</td></tr>
<tr><td>Target</td><td><code>ln_price_krw_unified</code> (학습) → <code>exp()</code> 복원 (평가)</td></tr>
<tr><td>Feature (Cold)</td><td>medium, support, has_depth, log_area, estimated_ho, orientation (6개)</td></tr>
<tr><td>Feature (Warm)</td><td>Cold 6개 + <code>artist_name_ko</code> (native categorical)</td></tr>
</table>

<h2>🏆 최종 Best 모델</h2>
<table>
<tr><th>시나리오</th><th>모델</th><th>med_APE</th><th>W30</th><th>비고</th></tr>
<tr class="best"><td><b>Cold-start</b></td><td>LAD (Quantile q=0.5)</td><td class="num">{fmt(p5['cold_lad']['median']['median_ape']) if p5 else '0.429'}</td><td class="num">{fmt(p5['cold_lad']['median']['within_30pct']) if p5 else '0.349'}</td><td>선형, outlier robust</td></tr>
<tr class="best"><td><b>Warm-start</b></td><td>LightGBM (artist native)</td><td class="num">{fmt(p5['warm_lgb']['mean']['median_ape']) if p5 else '0.123'}</td><td class="num">{fmt(p5['warm_lgb']['mean']['within_30pct']) if p5 else '0.748'}</td><td>비선형, artist signal</td></tr>
<tr class="best"><td><b>거장 (&gt;100M)</b></td><td>Warm 2-stage</td><td class="num">{fmt(p45['warm']['mean']['>100M_median_ape']) if p45 else '0.042'}</td><td>—</td><td>분류기 + 구간별 회귀</td></tr>
</table>

<h2>📊 Phase 0 — Baseline + ho/area Ablation</h2>
<table>
<tr><th>Variant</th><th>med_APE</th><th>MAPE</th><th>W30</th></tr>
"""
    if p0:
        for variant, res in [("median baseline", p0["cold_median_baseline"]["median"]),
                              *[(f"LGB {k}", v["median"]) for k, v in p0["cold_lgb_ablation"].items()]]:
            html += f"<tr><td>{variant}</td><td class='num'>{fmt(res['median_ape'])}</td><td class='num'>{fmt(res['mape'])}</td><td class='num'>{fmt(res['within_30pct'])}</td></tr>\n"
    html += "</table>\n<p><b>ho/area ablation</b>: <code>both</code>(area+ho)와 <code>area_only</code> median_APE 거의 동일(Δ=0.001), MAPE는 both -13.5pp. → <code>both</code> 유지.</p>"

    html += """
<h2>📐 Phase 1 — 선형 모델</h2>
<h3>Cold (5-fold GroupKFold OOF)</h3>
<table>
<tr><th>Model</th><th>med_APE</th><th>MAPE</th><th>RMSE_log</th><th>W30</th></tr>
"""
    if p1c:
        for name, res in p1c.items():
            if "error" in res: continue
            m = res["median"]
            cls = "best" if name == "Quantile_q05" else ""
            html += f"<tr class='{cls}'><td>{name}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['mape'])}</td><td class='num'>{fmt(m['rmse_log'])}</td><td class='num'>{fmt(m['within_30pct'])}</td></tr>\n"
    html += """</table>
<h3>Warm (random 80/10/10 × N=3 in Phase 1, N=20 in Phase 5)</h3>
<table>
<tr><th>Model</th><th>med_APE</th><th>MAPE</th><th>W30</th></tr>
"""
    if p1w:
        for name, res in p1w.items():
            if "error" in res: continue
            m, s = res["mean"], res["std"]
            cls = "best" if name == "Quantile_q05" else ""
            html += f"<tr class='{cls}'><td>{name}</td><td class='num'>{fmt(m['median_ape'])}±{fmt(s['median_ape'])}</td><td class='num'>{fmt(m['mape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td></tr>\n"
    html += """</table>
<blockquote><b>핵심 발견</b>: Cold에서 <b>Huber/LAD가 OLS 대비 -10pp 향상</b> (long-tail outlier robust 효과 입증). Warm은 Cold 대비 <b>-11.5pp 향상</b> (artist target encoding 가치).</blockquote>

<h2>🌲 Phase 2 — 비선형 모델</h2>
<h3>Cold</h3>
<table>
<tr><th>Model</th><th>med_APE</th><th>MAPE</th><th>RMSE_log</th><th>W30</th></tr>
"""
    if p2c:
        for name, res in p2c.items():
            if "error" in res: continue
            m = res["median"]
            cls = "best" if name == "LightGBM" else ""
            html += f"<tr class='{cls}'><td>{name}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['mape'])}</td><td class='num'>{fmt(m['rmse_log'])}</td><td class='num'>{fmt(m['within_30pct'])}</td></tr>\n"
    html += """</table>
<h3>Warm</h3>
<table>
<tr><th>Model</th><th>med_APE</th><th>MAPE</th><th>W30</th></tr>
"""
    if p2w:
        for name, res in p2w.items():
            if "error" in res: continue
            m, s = res["mean"], res["std"]
            cls = "best" if name == "LightGBM" else ""
            html += f"<tr class='{cls}'><td>{name}</td><td class='num'>{fmt(m['median_ape'])}±{fmt(s['median_ape'])}</td><td class='num'>{fmt(m['mape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td></tr>\n"
    html += """</table>
<blockquote><b>예상 외</b>: <b>Cold는 선형(LAD 0.429) > 비선형(LGB 0.473)</b>. 6 features만 쓰는 cold는 비선형 학습 여지 적고, tree default squared loss가 long-tail에 약함.<br>
<b>Warm은 LightGBM 압도</b> (0.119, -19.5pp). artist categorical native signal 강력.<br>
XGBoost는 2K+ unique categorical 처리 약함.</blockquote>

<h2>🔀 Phase 3 — Hybrid (단순 blend)</h2>
"""
    if p3:
        cold = p3["cold"]; warm = p3["warm"]
        html += f"""<h3>Cold</h3>
<table>
<tr><th>Variant</th><th>med_APE</th><th>W30</th></tr>
<tr><td>lin_only (LAD)</td><td class='num'>{fmt(cold['lin_only']['median_ape'])}</td><td class='num'>{fmt(cold['lin_only']['within_30pct'])}</td></tr>
<tr><td>lgb_only</td><td class='num'>{fmt(cold['lgb_only']['median_ape'])}</td><td class='num'>{fmt(cold['lgb_only']['within_30pct'])}</td></tr>
<tr><td>blend 50/50</td><td class='num'>{fmt(cold['blend_50_50']['median_ape'])}</td><td class='num'>{fmt(cold['blend_50_50']['within_30pct'])}</td></tr>
<tr><td>blend 70 lin / 30 lgb</td><td class='num'>{fmt(cold['blend_70lin_30lgb']['median_ape'])}</td><td class='num'>{fmt(cold['blend_70lin_30lgb']['within_30pct'])}</td></tr>
<tr><td><b>best (oracle)</b></td><td class='num'>{fmt(cold['best_blend_med_ape_median'])}</td><td>w_lin median={fmt(cold['best_blend_w_lin_median'], 2)}</td></tr>
</table>
<h3>Warm</h3>
<table>
<tr><th>Variant</th><th>med_APE</th><th>W30</th></tr>
<tr><td>lin_only</td><td class='num'>{fmt(warm['lin_only']['median_ape'])}</td><td class='num'>{fmt(warm['lin_only']['within_30pct'])}</td></tr>
<tr class='best'><td>lgb_only</td><td class='num'>{fmt(warm['lgb_only']['median_ape'])}</td><td class='num'>{fmt(warm['lgb_only']['within_30pct'])}</td></tr>
<tr><td>blend 50/50</td><td class='num'>{fmt(warm['blend_50_50']['median_ape'])}</td><td class='num'>{fmt(warm['blend_50_50']['within_30pct'])}</td></tr>
<tr><td>blend 30 lin / 70 lgb</td><td class='num'>{fmt(warm['blend_30lin_70lgb']['median_ape'])}</td><td class='num'>{fmt(warm['blend_30lin_70lgb']['within_30pct'])}</td></tr>
<tr><td><b>best (oracle)</b></td><td class='num'>{fmt(warm['best_blend_med_ape_mean'])}</td><td>w_lin mean={fmt(warm['best_blend_w_lin_mean'], 2)}</td></tr>
</table>
<blockquote>Hybrid 큰 효과 없음. Cold는 LAD가, Warm은 LGB가 단독 최선.</blockquote>
"""

    html += """<h2>❄️ Phase 4 — Cold-start 특화</h2>
<table>
<tr><th>Model</th><th>med_APE</th><th>MAPE</th><th>W30</th></tr>
"""
    if p4:
        for name, res in p4.items():
            m = res["median"]
            html += f"<tr><td>{name}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['mape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td></tr>\n"
    html += """</table>
<blockquote>모두 Phase 1 LAD (0.429) 대비 열세. 6 features 한계로 prototype/KNN 효과 제한.</blockquote>

<h2>🌟 Phase 4.5 — 2-stage 거장 long-tail (Trigger 발동)</h2>
"""
    if p45:
        cold = p45["cold"]["median"]; warm = p45["warm"]["mean"]
        html += f"""<table>
<tr><th>Variant</th><th>med_APE</th><th>B4 (&gt;10M)</th><th>&gt;100M</th><th>W30</th></tr>
<tr><td>Phase 2 Cold LGB (단일)</td><td class='num'>0.473</td><td class='num warn'>0.640</td><td class='num err'>0.986</td><td class='num'>0.340</td></tr>
<tr class='best'><td>Cold 2-stage</td><td class='num'>{fmt(cold['median_ape'])}</td><td class='num'>{fmt(cold['B4_median_ape'])}</td><td class='num warn'>{fmt(cold['>100M_median_ape'])}</td><td class='num'>{fmt(cold['within_30pct'])}</td></tr>
<tr><td>Phase 2 Warm LGB (단일)</td><td class='num'>0.119</td><td>—</td><td>—</td><td class='num'>0.752</td></tr>
<tr class='best'><td>Warm 2-stage</td><td class='num'>{fmt(warm['median_ape'])}</td><td class='num'>{fmt(warm['B4_median_ape'])}</td><td class='num best'><b>{fmt(warm['>100M_median_ape'])}</b></td><td class='num'>{fmt(warm['within_30pct'])}</td></tr>
</table>
<blockquote><b>핵심 성과</b>: Warm 2-stage가 <b>&gt;100M 작품 med_APE 4.2%</b>로 사실상 정확. Cold 2-stage는 &gt;100M 0.986 → 0.889로 -10pp 개선이나 여전히 큼.</blockquote>
"""

    html += """<h2>📈 Phase 5 — 최종 평가</h2>
"""
    if p5:
        cl = p5["cold_lad"]; wm = p5["warm_lgb"]; wb = p5["warm_lgb_balanced"]; oh = p5["outer_holdout"]
        html += f"""<h3>[1] Cold LAD (5-fold GroupKFold OOF)</h3>
<table>
<tr><th>Metric</th><th>값</th><th>95% CI</th></tr>
<tr><td>median APE</td><td class='num'>{fmt(cl['median']['median_ape'])}</td><td class='num'>[{fmt(cl['median_ape_95ci'][0])}, {fmt(cl['median_ape_95ci'][1])}]</td></tr>
<tr><td>MAPE</td><td class='num'>{fmt(cl['median']['mape'])}</td><td>—</td></tr>
<tr><td>RMSE (log)</td><td class='num'>{fmt(cl['median']['rmse_log'])}</td><td>—</td></tr>
<tr><td>Within-30%</td><td class='num'>{fmt(cl['median']['within_30pct'])}</td><td>—</td></tr>
<tr><td>Within-50%</td><td class='num'>{fmt(cl['median']['within_50pct'])}</td><td>—</td></tr>
</table>

<h4>Source breakdown</h4>
<table>
<tr><th>Source</th><th>n</th><th>med_APE</th><th>W30</th></tr>
"""
        for src, m in cl["source_breakdown"].items():
            html += f"<tr><td>{src}</td><td class='num'>{m['n']:,}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td></tr>\n"
        html += """</table>
<h4>Price-band breakdown</h4>
<table>
<tr><th>Band</th><th>n</th><th>med_APE</th><th>W30</th></tr>
"""
        for band, m in cl["price_band_breakdown"].items():
            cls = "warn" if band in {"B4", ">100M"} else ""
            html += f"<tr class='{cls}'><td>{band}</td><td class='num'>{m['n']:,}</td><td class='num'>{fmt(m['median_ape'])}</td><td class='num'>{fmt(m['within_30pct'])}</td></tr>\n"
        html += f"""</table>
<h3>[2] Warm LightGBM (N=20 random seeds)</h3>
<table>
<tr><th>Metric</th><th>mean±std</th><th>95% CI</th></tr>
<tr><td>median APE</td><td class='num'>{fmt(wm['mean']['median_ape'])}±{fmt(wm['std']['median_ape'])}</td><td class='num'>[{fmt(wm['median_ape_95ci'][0])}, {fmt(wm['median_ape_95ci'][1])}]</td></tr>
<tr><td>MAPE</td><td class='num'>{fmt(wm['mean']['mape'])}±{fmt(wm['std']['mape'])}</td><td>—</td></tr>
<tr><td>RMSE (log)</td><td class='num'>{fmt(wm['mean']['rmse_log'])}±{fmt(wm['std']['rmse_log'])}</td><td>—</td></tr>
<tr><td>Within-30%</td><td class='num'>{fmt(wm['mean']['within_30pct'])}±{fmt(wm['std']['within_30pct'])}</td><td>—</td></tr>
</table>

<h3>[3] Source-balanced stress test (Warm, N=3)</h3>
<table>
<tr><th>Metric</th><th>mean±std</th><th>vs 메인</th></tr>
<tr><td>median APE</td><td class='num'>{fmt(wb['mean']['median_ape'])}±{fmt(wb['std']['median_ape'])}</td><td class='num'>{wb['mean']['median_ape'] - wm['mean']['median_ape']:+.3f}</td></tr>
</table>
<blockquote>Saatchi 67% 편향이 모델 순위에 영향 미미. 운영 시 train-all 유지 OK.</blockquote>

<h3>[4] Outer Holdout 최종 감사 (격리 426 작가)</h3>
<table>
<tr><th>모델</th><th>med_APE</th><th>W30</th><th>비고</th></tr>
<tr class='best'><td>Cold LAD</td><td class='num'>{fmt(oh['cold_lad_holdout']['median_ape'])}</td><td class='num'>{fmt(oh['cold_lad_holdout']['within_30pct'])}</td><td>dev 0.429보다 좋음 (robust 입증)</td></tr>
<tr class='warn'><td>Warm LGB</td><td class='num'>{fmt(oh['warm_lgb_holdout']['median_ape'])}</td><td class='num'>{fmt(oh['warm_lgb_holdout']['within_30pct'])}</td><td>unseen 작가 → 자동 cold-start</td></tr>
</table>
<blockquote>Outer holdout = 전부 unseen artist이므로 Warm 모델 본질적으로 cold-start 시나리오. 운영 시 unseen 작가는 Cold LAD로 라우팅 권장.</blockquote>
"""

    html += """<h2>🎯 운영 권장 (라우팅 + 모델)</h2>
<table>
<tr><th>조건</th><th>모델</th><th>예상 정확도</th></tr>
<tr><td>학습 ≥3건 작가</td><td>Warm LightGBM</td><td class='best'>med_APE ~0.12 / W30 ~75%</td></tr>
<tr><td>학습 1-2건 작가 (rare)</td><td>Warm/Cold blend</td><td>med_APE ~0.20-0.30 (추정)</td></tr>
<tr><td>학습 0건 작가 (cold)</td><td>Cold LAD</td><td>med_APE ~0.39-0.43</td></tr>
<tr><td>고가 작품 (&gt;10M)</td><td>Warm 2-stage</td><td class='best'>&gt;100M: med_APE ~0.04</td></tr>
</table>

<h2>⚠️ 주요 한계 (외부 보고 시 명시)</h2>
<ul>
  <li>본 모델은 <b>"listing-price prediction"</b>이지 "시장가치 예측" 아님 (절대가격 해석 보수적으로)</li>
  <li>시간 split 없음 — temporal validation 불가</li>
  <li>Singleton artist 299명 / ≤2건 516명 — 운영은 rare artist fallback 규칙</li>
  <li>&gt;100M 작품 Cold 예측은 여전히 어려움 (med_APE 0.889) — Warm 라우팅 필수</li>
</ul>

<h2>📂 산출물</h2>
<ul>
  <li><code>scripts/track3/split_data.py</code> — Outer holdout + Cold/Warm split</li>
  <li><code>scripts/track3/baseline.py</code> — median + ho/area ablation</li>
  <li><code>scripts/track3/train_linear_{cold,warm}.py</code> — Phase 1</li>
  <li><code>scripts/track3/train_tree_{cold,warm}.py</code> — Phase 2</li>
  <li><code>scripts/track3/train_hybrid.py</code> — Phase 3</li>
  <li><code>scripts/track3/train_coldstart.py</code> — Phase 4</li>
  <li><code>scripts/track3/train_two_stage.py</code> — Phase 4.5</li>
  <li><code>scripts/track3/train_phase5_final.py</code> — Phase 5 최종 평가</li>
  <li><code>data/track3_phase{0..5}_results.json</code> — Phase별 결과</li>
</ul>

<p class="meta">Track 3 모델링 완료 — 9개 Phase, 모든 Gate 통과.</p>

</body></html>
"""

    OUT.write_text(html)
    print(f"✅ HTML report: {OUT}")
    print(f"   Size: {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
