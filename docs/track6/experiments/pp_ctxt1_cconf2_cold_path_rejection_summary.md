# PP-CTXT1 / PP-CCONF2 Cold 개선 경로 ③④ 검증 요약

- 실행일: 2026-06-10
- 배경: Cold 개선 4갈래 중 ①(그룹 통계, PP-CGRP1 기각)에 이어 ③(제목 텍스트), ④(tier 커버리지 확대)를 검증. ②(검색 수집 확대)는 외부 수집 결정 사안으로 제외.

## PP-CTXT1 — 제목 텍스트 residual 보정: 기각

- 스크립트: `scripts/track6/run_pp_ctxt1_cold_title_text_residual_correction.py` / 폴더: `experiments/track6/PP-CTXT1_cold_title_text_residual_correction/`
- 설계: TF-IDF(char 2~4gram, train-scope 동결) + SVD(32) → CIMG1과 동일한 artist-grouped OOF residual 하니스 (신규 의존성 0; MiniLM 캐시는 track6 row 매핑 부재로 제외). 제목 커버리지 100%.
- 결과: **OOF 보정값 vs 잔차 상관 0.039** (이미지 0.083보다 약함), 보정 분산은 잔차 std의 0.41배 = 노이즈. 격자 전체 validation MAPE 악화(+0.006~), 게이트 진입 0.
- 결론: 제목 어휘 신호도 작가 일반화 신호 없음. 이미지·텍스트 모두 콘텐츠 신호는 Cold 점 예측에 닫힘.

## PP-CCONF2 — high tier 커버리지 확대: 기각 (가장 중요한 음성 결과)

- 스크립트: `scripts/track6/run_pp_cconf2_cold_high_tier_coverage_expansion.py` / 폴더: `experiments/track6/PP-CCONF2_cold_high_tier_coverage_expansion/`
- 설계: high tier 경계 완화 격자(qw pct 0.33→0.60 × gap pct 0.50→0.80), validation high-tier p95 ≤1.0 제약 + artist holdout 200회 P(p95≤1.5)≥0.90, fixed test 1회.
- validation/holdout은 전부 통과처럼 보임: share 8%→50%로 늘려도 val p95 0.95, holdout 통과확률 0.98~1.0.
- **fixed test에서 붕괴**: 확대 후보들의 test high-tier p95 **4.40~4.76** vs 동결 v0.4 경계(q33/g50) **0.9904**.

| 후보 | val share/p95 | test share/p95 |
| --- | --- | --- |
| v0.4 동결 (q33,g50) | 14.8% / 0.93 | 8.2% / **0.99** |
| q60,g80 확대 | 50.2% / 0.95 | 32.7% / **4.40** |

- 결론: **v0.4의 엄격한 tier 경계는 과보수가 아니라 유일하게 test 분포 이동을 견디는 설정**이다. tier 확장 금지를 v0.4 운영 노트에 준하는 원칙으로 기록. 메타 교훈: validation 내부 artist holdout은 val→test 작가 구성 이동을 감지하지 못함 — fixed test 최종 확인 단계가 실제로 과신 후보를 걸렀다.

## 경로 ①③④ 종합 (PP-CGRP1 포함)

| 경로 | 실험 | 판정 | 근거 |
| --- | --- | --- | --- |
| ① 그룹 가격 통계 base | PP-CGRP1 | 기각 | validation 전 지표 악화(bootstrap 0.02~0.37). 트리 모델은 categorical 분기로 동일 정보 기학습 |
| ③ 제목 텍스트 | PP-CTXT1 | 기각 | OOF 상관 0.039, 작가 일반화 신호 없음 |
| ④ tier 커버리지 확대 | PP-CCONF2 | 기각 | test에서 확대 tier p95 붕괴(0.99→4.4) |

**Cold 트랙 결론 확정**: 현재 보유 데이터의 모든 잔여 경로(보정·콘텐츠 신호·base 피처·tier 확장)가 소진됐다. 남은 개선 경로는 ② 검색 수집 확대(미커버 MAPE 0.938→0.849 정량화 완료)와 신규 데이터 과제(거래 시점)뿐이다.
