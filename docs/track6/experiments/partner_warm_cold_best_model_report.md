# Warm/Warm-lite/Cold 가격 예측 모델 종합 리포트

- 작성일: 2026-06-10
- 최종 수정일: 2026-06-15
- 보고 목적: 협력 업체 공유용 기술 설명 및 성능 요약
- 대상 범위: Warm 5건 이상 최종 후보 + Warm-lite 0.1v 적용 경로 + Cold 성능 기준 모델
- 문서 상태: 현재 0.1v API 구현값과 문서 성능 기준을 분리 표기

## 1. 결론 요약

- 가격 예측 모델 적용 기준: 작가 매칭 신뢰도와 학습 데이터 내 사용 가능한 작가 가격 이력 수에 따라 Warm, Warm-lite, Cold 경로로 구분
- 현재 `official_v0_1_service.py` 구현 기준: 매칭점수 `0.80 이상`이고 같은 작가 가격 이력이 `5건 이상`이면 Warm, `1~4건`이면 Warm-lite, 그 외 예측 가능 입력은 Cold 또는 검수대기
- 이 보고서 기준: WMIN8 Warm, Warm-lite, Cold 검색 피처 모델은 현재 0.1v API 구현 상태와 각 성능 기준을 분리해 설명한다. 내부 모델 artifact 버전명(`warm_lite_quantile_residual_v0.1`, `cold_prediction_v0.2_operational` 등)을 API 버전으로 해석하지 않음

- Warm 경로 적용 대상: 작가가 신뢰도 높게 매칭되고, 학습 데이터 안에 같은 작가의 사용 가능한 가격 이력이 5건 이상인 작품
- Warm-lite 경로 적용 대상: 작가가 신뢰도 높게 매칭되고, 같은 작가의 사용 가능한 가격 이력이 1~4건인 작품
- Cold 경로 적용 대상: 같은 작가의 학습 이력이 0건이거나, 작가 매칭이 불확실한 작품
- 성능 관리 방식: Warm, Warm-lite, Cold의 입력 조건과 난이도가 다르므로 별도 지표로 관리

- 보고서 기준 성능:

| 구분 | 채택 모델 | 상태 | 평가 기준 | 평가 행 수(n) | MdAPE | MAPE | p95 APE | 해석 |
|---|---|---|---|---:|---:|---:|---:|---|
| Warm 성능 기준 | 이력 기반 조건부 유사작품 보정 모델 | WMIN8 후보/동결 번들 | fixed test | 607 | 0.104326 | 0.235814 | 0.739416 | 정밀 유사작품 매칭(최소 표본 1)으로 기준가격을 만들고, 위험도가 높은 작품만 보수적 대안 가중으로 조건부 교체 |
| Warm-lite 성능 기준 | 작가 이력 1~4건 전용 Quantile residual 모델 | 0.1v 포함 경로/동결 번들 | 실존 저이력 작가 leave-one-out | 1,947 | 0.107246 | 0.275773 | 0.852026 | 매칭된 작가의 1~4건 이력으로 기준가격을 계산하고 Quantile residual로 보정 — 같은 작품을 Cold로 보낼 때(MdAPE 0.5429) 대비 약 5.06배 정확 |
| Cold 성능 기준 | 검색 피처 포함 Quantile 예측 + 과대예측 방어 + 작가 검색 보정 | v0.3 guard+search 재현 검증 기준 | fixed test | 3,099 | 0.409820 | 0.849260 | 2.346465 | 신규/저이력 작가 상황에서 검색 피처와 불확실성 방어를 함께 사용 |

- 위 표의 `n`은 학습에 사용된 작품 수가 아니라 성능 지표를 계산한 평가 행 수다. Warm 607과 Cold 3,099는 fixed test 평가 행 수이고, Warm-lite 1,947은 실존 저이력 작가 649명 leave-one-out 평가를 3회 반복한 행 수다.

- RMSE log는 Cold 비교값이 없어 위 모델 간 성능표에서는 제외한다. Warm `0.377190`, Warm-lite Quantile residual `0.423003`은 각 경로의 로그가격 기준 보조 검증값으로만 사용한다.

- 현재 0.1v API 구현과 이 보고서 기준의 관계:

| 항목 | 현재 0.1v API 구현 기준 | 이 보고서 성능 기준 |
|---|---|---|
| Warm 라우팅 | `작가매칭신뢰도점수 >= 0.80` AND `같은작가_사용가능가격이력수 >= 5` | WMIN8 fixed test 성능과 산식 설명 |
| 1~4건 이력 | `작가매칭신뢰도점수 >= 0.80` AND `같은작가_사용가능가격이력수 1~4`이면 Warm-lite | Warm-lite 동결/검증 성능 설명 |
| Cold 모델 | 매칭 실패, 이력 0건, 입력 부족 또는 검수 필요 구간 | 검색 피처 포함 v0.3 성능 기준을 비교 기준으로 설명 |
| 문서 해석 | 현재 0.1v API 동작 설명 | fixed test/검증 지표와 내부 artifact 근거를 함께 표기 |

- 핵심 판단:

- Warm 모델 구조: `정밀 유사작품 기준가격(최소 표본 1) + Huber 잔차 보정 + 위험도 조건부 가중 라우터` (2026-06-13 후보 갱신, 이전 후보 대비 MdAPE -26%/MAPE -13%/p95 -8%)
- Warm 보정 방식: 기본은 유사작품 가중 0.70 기준가격 + Huber 잔차 보정, 예측 위험도가 상위 50%이고 보수 대안(가중 0.85)이 0.005 로그 이상 낮을 때만 대안으로 교체
- 적용 범위(현재 0.1v API): 고신뢰 매칭 + 이력 5건 이상 → Warm / 고신뢰 매칭 + 이력 1~4건 → Warm-lite / 그 외 → Cold 또는 검수대기
- Warm-lite의 의미: 이력이 1건이라도 있으면 그 작가의 실제 가격이 가장 강한 신호 — 재검증(PP-WCUT4)에서 실존 저이력 작가 기준 Cold MdAPE `0.5429` 대비 Warm-lite `0.1092`, `4.97배` 차이 확인
- Warm/Warm-lite 분리 근거: 1~4건 전체를 Warm 계열 proxy로 통일하면 Warm-lite보다 나빠졌고(PP-WMIN9E), 누수 없이 재학습 가능한 WMIN8 축만 다시 만든 부분 재학습 실험도 MdAPE/MAPE 기준 Warm-lite보다 나빴다(PP-WMIN11). 5건 이상을 Warm-lite로 통일해도 WMIN8보다 나빠졌기 때문에(PP-WMIN9D), 현재 근거는 `1~4건 Warm-lite / 5건 이상 Warm` 분리를 지지한다
- 5건 기준의 의미: 5건은 성능이 자연스럽게 급변하는 절대 임계값이 아니라, 현재 WMIN8 Warm 본체가 검증된 적용 범위다. 이 경계를 양쪽으로 바꾸는 반례 실험에서 전체 성능이 악화되어 현행 경계를 유지한다
- Warm-lite 내부 로직 근거: PP-WLITE-Q1~Q4에서 Quantile residual 후보가 저이력 구간의 중앙오차와 tail 안정성을 개선했고, PP-WLITE-Q5에서 번들 replay/API parity를 통과했다. 현재 0.1v API Warm-lite 채택값은 `Quantile 평균 + clip(0.50 * LightGBM Huber 잔차, -0.10, +0.10)` 동결 번들이다
- Warm 보조 정보: 유사작품 정보는 Warm 내부 기준가격과 신뢰도 계산을 돕는 보조 피처이며, 유사작가나 유사작품만으로 Warm 적용 범위를 넓히지 않음
- Cold 성능 기준 모델 구조: `검색 피처 포함 대표 예측가격 + 과대예측 방어 + 작가 검색 보정값`
- Cold 보정 방식: 검색 피처로 작가 문맥을 보강하고, 예측 불확실성이 큰 경우 낮은쪽 40% 지점 가격 기준으로 하향
- 최종 가격 변환: 각 경로는 로그가격에서 계산 후 `exp()`를 적용해 원화 예측가격으로 변환
- MAPE 계산 기준: `최종예측가격_KRW = exp(최종_로그가격)`으로 원화 예측가격을 만든 뒤 실제 원화 가격과 비교해 계산
- RMSE log 계산 기준: `최종_로그가격`과 `실제_로그가격`의 차이로 계산

### 1.1 문서 읽는 법 및 약어

- 이 문서에서 `현재 0.1v API`는 `price_prediction_v0.1` 공식 서비스 코드가 실제로 선택하는 경로를 뜻한다. 현재 기준은 `0.80 + 이력 5건 이상 → Warm`, `0.80 + 이력 1~4건 → Warm-lite`, 그 외는 Cold 또는 검수대기다
- 이 문서에서 `후보`는 검증·동결은 끝났지만 현재 0.1v API 동작과 동일하다고 단정하지 않는 비교 기준을 뜻한다
- 이 문서에서 `성능 기준`은 해당 경로의 실험·재현 파일에서 성능 지표를 확인한 기준 모델을 뜻한다. 운영 API에 이미 그대로 붙었다는 뜻은 아니며, 현재 0.1v API 구현 상태와 구분해서 읽어야 한다
- 이 문서에서 `학습 단계`는 실제 가격이 있는 과거 데이터로 피처, 회귀계수, tree 모델, 보정표, 임계값을 만드는 단계다
- 이 문서에서 `사용 단계`는 새 작품이 들어왔을 때 동결된 모델/계수/보정표를 적용해 가격을 계산하는 단계다. 사용 단계에서는 실제 판매가격을 알 수 없으므로 실제 가격은 입력으로 쓰지 않는다

| 용어 또는 약어 | 의미 | 처음 보는 독자를 위한 해석 |
|---|---|---|
| Warm | 같은 작가의 사용 가능한 학습 가격 이력이 5건 이상일 때 쓰는 경로 | 작가 본인의 과거 가격 신호를 강하게 활용하는 경로 |
| Warm-lite | 같은 작가 이력이 1~4건뿐일 때 쓰는 저이력 경로 | 현재 0.1v API에 포함된 저이력 작가용 경량 모델 |
| Cold | 같은 작가 이력이 없거나 라우팅 조건을 못 맞출 때 쓰는 경로 | 작가 개인 이력보다 작품 크기, 매체, 작가 메타, 검색 문맥 등으로 추정 |
| 학습 단계 | 실제 가격이 있는 과거 데이터로 모델과 보정값을 만드는 단계 | 회귀계수, tree 모델, 잔차 보정값, lookup, 라우팅 임계값을 만든 뒤 동결 |
| 사용 단계 | 새 작품에 동결 모델을 적용해 가격을 계산하는 단계 | 실제 가격 없이 입력 피처만으로 로그가격을 계산하고 `exp()`로 원화 변환 |
| WMIN8 | Warm 5건 이상 경로의 내부 실험 ID | 대외 설명에서는 `이력 기반 조건부 유사작품 보정 모델`로 부름 |
| WMIN 계열 | Warm 후보를 순차 검증한 내부 실험 묶음 | `WMIN2`, `WMIN8`, `WMIN10`처럼 단계별 점검·성능·parity를 확인한 기록 |
| WMIN8 svc-core proxy | WMIN8의 유사작품통계 Huber 축만 저이력 행에 적용한 비교 기준 | full WMIN8이 아니라 1~4건에서 Warm 계열을 쓰는 경우를 누수 없이 비교하기 위한 proxy |
| full WMIN8 | 5건 이상 Warm 경로의 전체 계산 구조 | svc-core, PPV8 방어값, Huber 잔차 보정, 위험도 라우터를 모두 포함 |
| PP 계열 ID | 가격 예측 실험 추적 ID | `PP-WCUT4`, `PP-WMIN10`처럼 내부 재현·감사용 이름이며 모델명이 아님 |
| PP258 | 이전 Warm 기준선 | WMIN8 성능 비교용 이전 후보이며 WMIN8 직접 재현 근거가 아님 |
| WCUT/WLITE | Warm-lite 저이력 작가 검증 계열 | 1~4건 이력 경로의 성능과 artifact를 검증한 실험 묶음 |
| WMIN9C | Warm-lite와 WMIN8 svc-core proxy의 저이력 동일 행 비교 | 1~4건을 Warm 계열로 보낼 수 있는지 확인한 직접 비교 |
| WMIN9D | 5건 이상 fixed test에 Warm-lite를 강제 적용한 counterfactual 비교 | 5건 이상은 Warm을 유지해야 하는지 확인한 실험 |
| WMIN9E | 1~4건을 Warm 계열로 통일할 수 있는지 k별로 정리한 의사결정표 | k=1/2/3/4 각각에서 Warm-lite와 Warm proxy 승패를 요약 |
| WMIN11 | 1~4건 hold-out에서 재학습 가능한 WMIN8 축을 누수 없이 다시 만든 부분 재학습 실험 | full WMIN8 완료 실험이 아니라, frozen PPV8를 쓰지 않고 svc-core와 L10 보조축을 재학습한 추가 검증 |
| E2E/RHO/WMATCH/RMAP/MCAL | 라우팅·매칭 임계값 검증 계열 | 0.90과 0.80 정책 비교, 오매칭 위험, 매칭 점수 캘리브레이션을 검증한 실험 묶음 (`PP-RMAP1`, `PP-MCAL1` 포함) |
| seed / seed 평균 | 같은 모델을 다른 난수 시드로 여러 번 학습해 평균낸 값 | 우연한 학습 변동을 줄이기 위한 안정화 방식 |
| 문자열 유사도 | 작가명 두 개의 글자 유사도를 0~100점으로 환산한 값 | 오탈자·표기 차이가 있어도 비슷한 작가명을 찾기 위한 매칭 점수. 내부 matcher 명칭은 `fuzzy ratio` |
| CatBoost | gradient boosting 계열 모델 | Warm의 버킷순차보정 보조축에서는 Quantile/잔차 보정에 사용된다. Cold 성능 기준의 주 모델은 LightGBM Quantile이며, CatBoost는 Cold 기준 경로의 주 채택 모델이 아님 |
| fixed test | 실험 비교를 위해 고정해 둔 테스트 데이터 | 모델끼리 공정하게 비교하기 위한 고정 평가셋 |
| validation OOF | 학습에 직접 쓰지 않은 fold 예측 검증 | 과적합 여부를 보기 위한 out-of-fold 검증 |
| leave-one-out | 하나를 빼고 나머지로 예측하는 검증 | 저이력 작가에서 자기 가격 누수를 막기 위한 평가 방식 |
| artifact / 동결 번들 | 모델과 설정을 재현 가능하게 저장한 파일 묶음 | 후보 모델을 같은 방식으로 다시 실행하기 위한 패키지 |
| adapter | 실험 산출물을 API 입력·출력 구조에 맞추는 연결층 | 실험 계산과 서비스 계산이 같은지 확인할 때 사용 |
| parity | 두 계산 경로가 같은 결과를 내는지 보는 검증 | 예측 로그가격 차이가 거의 0이면 통과로 해석 |
| search-free | 검색 피처 없이 동작하는 내부 Cold 번들 상태 | API 버전이 아니라 Cold artifact/adapter 상태를 가리키는 표현 |
| guard | 큰 과대예측을 줄이는 방어 로직 | 불확실성이 큰 작품을 더 보수적으로 예측 |
| lookup | 미리 계산해 저장한 표에서 값을 찾는 방식 | 실시간 학습이 아니라 저장된 보정값 조회 |
| 0604 stress | 2026-06-04 신규 라벨 스트레스 평가 | 새 라벨 조건에서도 성능이 악화되지 않는지 보는 추가 검증 |
| w700 / w850 | 유사작품 신호 가중치 설정 | 각각 유사작품 기준가격을 70%, 85% 반영하는 Warm 후보 |
| q50 | 중앙값 기준 임계 | validation에서 위험도 상위 절반을 나누는 기준 |
| min1 | Warm 안에서 비슷한 과거 작품을 1건부터 참고하는 설정 | Warm 라우팅 기준을 1건으로 낮춘다는 뜻이 아니라, 전체 이력 5건 이상 작가 안에서 대상 작품과 비슷한 과거 작품이 1건만 있어도 기준가격 계산에 쓴다는 뜻 |
| 보조안정 Warm 예측값 | Warm 기준가격에 일부 섞는 보조 예측 축 | 큰오차방어 Warm 예측값 75%와 버킷순차보정 Warm 예측값 25%를 로그가격에서 섞은 값 |
| 큰오차방어 Warm 예측값 | 여러 Warm 후보를 다시 입력으로 쓰는 Huber meta-stacking 예측값 | 하위 후보들의 평균·표준편차·범위·기준후보와의 차이·불확실성 폭을 사용하고, 결과를 하위 후보 범위 근처로 clip해 큰 외삽을 막는 방어형 보조축 |
| 버킷순차보정 Warm 예측값 | 생성 bucket과 Quantile/Huber/CatBoost 순차 모델로 만든 보조 Warm 예측값 | 정해진 산식 하나가 아니라, 학습된 모델 파이프라인이 만든 로그가격. Warm 최종 경로에서는 보조안정 값의 25% 축으로만 사용 |
| Huber | 큰 오차의 영향을 완만하게 처리하는 강건 회귀 손실/방식 | Huber 자체가 모델명은 아니며, Huber loss 기준으로 회귀계수와 절편을 데이터에 맞춰 산출한 예측기를 뜻함 |
| LightGBM Huber residual | LightGBM이 Huber 목적함수로 남은 오차를 예측하는 보정층 | Warm-lite에서 Quantile 평균 로그가격 위에 clip된 잔차 보정을 더함 |
| counterfactual / 강제 적용 | 실제 운영 라우팅과 다르게 모델을 일부러 태워보는 실험 | 정책을 바꾸기 위한 근거가 아니라 경계값의 타당성을 확인하는 반례 검증 |
| label leakage / 누수 | 평가 대상의 정답 정보가 학습 또는 피처에 섞이는 문제 | 성능이 실제보다 좋게 보일 수 있어 hold-out 검증에서 반드시 차단 |
| SVC / svc 컬럼 | 유사작품 비교군 통계 계열 내부명 | 문서에서는 유사작품 비교군 기준가격 또는 fallback 값으로 해석 |
| fold | 검증을 위해 데이터를 나눈 조각 | 자기 가격이 자기 피처에 들어가는 누수를 막는 데 사용 |
| holdout / bootstrap | 안정성 검증 방법 | 특정 split에만 우연히 맞은 것이 아닌지 반복 확인하는 절차 |
| R1~R5 | 라우팅 모니터링 점검 항목 | 규칙 위반, 트래픽 비중, 보조정보 통과, Warm-lite 실측 성능, 동명이인율 점검 |

### 1.2 수치 근거 감사 결과

- 이 문서의 숫자는 `실험 결과값`, `동결 policy/config 값`, `코드 정책 상수`, `재계산값`으로 구분해 관리한다
- 직접 근거 파일을 확인하지 못한 숫자는 본문 지표에서 제거하거나 보류 사유를 적는다

| 수치 영역 | 확인 근거 | 판정 |
|---|---|---|
| Warm WMIN8 fixed test/validation 성능, 이전 후보 대비 delta, route gate | `models/track6/warm_wmin8_operational_candidate/config/warm_model_policy_wmin8.json` | 확인됨 |
| Warm WMIN8 API parity | `experiments/track6/PP-WMIN10_warm_wmin8_api_fixed_test_parity/reports/result_report.md` | 607/607건 성공, max diff `5.33e-15` 확인 |
| Warm 최소 표본 1 적용 후 정밀 비교군 매칭률 `81.9%` | `experiments/track6/PP-WMIN2_warm_artist_min1_svc_numeric/reports/result_report.md` | 확인됨 |
| `정밀 매칭률 40.7%` 후보 수치 | 직접 커버리지 artifact 미확인. `PP-K3`(별도 Warm 실험)의 MAPE `0.4073`과 혼동 가능성이 있어 본문 비교 수치에서 제외 | 보류/제거 |
| 2026-06-04 신규 라벨 stress | `experiments/track6/PP-WMIN5_warm_min1_0604_stress/reports/result_report.md` | WMIN4 min1 계열의 선행 안전성 점검으로 확인. WMIN8 선택 근거로 직접 사용하지 않음 |
| Warm-lite PP-WCUT4 성능 `0.1092/0.2866/0.8765`, Cold 기준 `0.5429/0.9946/2.5358` | `experiments/track6/PP-WCUT4_real_low_history_validation/reports/result_report.md` | 확인됨 |
| Warm-lite Quantile residual RMSE log `0.423003` | `experiments/track6/PP-WLITE-Q3_quantile_residual_correction_validation/outputs/q1_predictions_all_seeds.csv`에서 `qavg_lgbres_s05_cap010_pred_log`와 실제 로그가격으로 재계산 | 현재 채택 모델 보조 검증값 |
| Warm-lite 이전 저이력 경로 RMSE log `0.447586` | `experiments/track6/PP-WCUT4_real_low_history_validation/outputs/preds_seed*.csv`에서 `wlite_pred_log`와 실제 로그가격으로 재계산 | 경로 분리 근거용 이전 기준값. 현재 채택 모델 성능표에는 사용하지 않음 |
| Warm-lite vs WMIN8 svc-core proxy 1~4건 직접 비교 | `experiments/track6/PP-WMIN9C_warm_lite_vs_wmin8_lowhistory/reports/result_report.md` | 1~4건 전체 Warm-lite `0.1092/0.2866/0.8765`, WMIN8 svc-core proxy `0.1291/0.2932/0.9163` 확인 |
| 1~4건 Warm 통일 가능 여부 k별 판단 | `experiments/track6/PP-WMIN9E_lowhistory_warm_only_decision/reports/result_report.md` | k=2/3 Warm-lite 전 지표 우세, k=1/4 혼합, 1~4 전체 Warm-lite 전 지표 우세 |
| 1~4건 WMIN8 부분 재학습 검증 | `experiments/track6/PP-WMIN11_lowhistory_full_wmin8_clean_pilot/reports/result_report.md` | 1,947행 기준 Warm-lite `0.1092/0.2866/0.8765`, 부분 재학습 라우팅 후보 `0.1480/0.2931/0.8716`. frozen full WMIN8/PPV8는 사용하지 않음 |
| 5건 이상에 Warm-lite 강제 적용 비교 | `experiments/track6/PP-WMIN9D_forced_warm_warmlite_boundary/reports/result_report.md` | WMIN8 `0.104326/0.235814/0.739416`, 강제 Warm-lite `0.108722/0.248054/0.837824` 확인 |
| Warm-lite Quantile 직접 적용 1차 검증 | `experiments/track6/PP-WLITE-Q1_warm_lite_quantile_candidate_validation/reports/result_report.md` | PP-WCUT5-equivalent 실존 저이력 leave-one-out에서 Quantile q50 계열 후보의 개선 신호 확인 |
| Warm-lite Quantile 후속 절단 검증 | `experiments/track6/PP-WLITE-Q2_quantile_followup_truncation_validation/reports/result_report.md` | PP-WCUT6-equivalent k절단 검증에서 `lgbq_full_lean_avg`가 `0.1575/0.3076/1.0279`로 개선. 이 결과는 Q3/Q4/Q5 승격 전의 단순 Quantile 후보 근거 |
| Warm-lite Quantile 잔차 보정 검증 | `experiments/track6/PP-WLITE-Q3_quantile_residual_correction_validation/reports/result_report.md` | OOF Quantile 잔차로 CatBoost/LightGBM 보정층을 검증. Q1-like에서는 `qavg_lgbres_s05_cap010`이 `0.1072/0.2758/0.8520`, Q2-like에서는 `0.1545/0.3034/1.0005`. CatBoost보다 LightGBM Huber residual 보정이 우세 |
| Warm-lite Quantile 최종 후보 비교 | `experiments/track6/PP-WLITE-Q4_quantile_final_comparison/reports/result_report.md` | Q1/Q2/Q3 산출물을 같은 행 기준으로 병합. Q2-like 운영 절단 검증에서 `residual_lgb_s05_cap010`이 `0.1545/0.3034/1.0005`로 단순 Quantile 평균 `0.1575/0.3076/1.0279`보다 전 지표 개선. Q1-like에서는 단순 50:50 blend가 MdAPE/MAPE 우세이나 residual 후보가 p95 우세 |
| Warm-lite Quantile residual API 번들 동결/parity | `models/track6/warm_lite_quantile_residual_v0.1/manifest.json`, `experiments/track6/PP-WLITE-Q5_quantile_residual_bundle_api_parity/reports/bundle_replay_parity_report.md`, `experiments/track6/PP-WLITE-Q5_quantile_residual_bundle_api_parity/reports/official_v0_1_api_parity_report.md` | 새 번들 `official_v0_1_warm_lite_quantile_residual` 동결. Q3 Q2-like 7,284행 replay max log diff `3.55e-15`, v0.1 HTTP API 24건 parity max log diff `0.0` 통과 |
| Warm-lite guard 개선 후보 | `experiments/track6/PP-WLITE-GUARD3_refined_trigger_search/reports/result_report.md` | k=1~2 고위험 일부 행만 낮은 2개 평균으로 교체하는 후보는 오프라인 개선 확인. 현재 0.1v 채택값은 아니므로 본문 성능 기준에는 반영하지 않음 |
| Cold v0.3 guard+search 성능과 재현 | `models/track6/cold_prediction_v0.3/reports/cold_best_research_model_detailed_report.md`, `models/track6/cold_prediction_v0.3/reproduction/best_research_reproducibility_check.json` | 확인됨 |
| 현재 0.1v 라우팅 상수 `0.80 + 1~4건/5건 분기` | `src/visionai/price_engine/api/official_v0_1_service.py` | 코드 확인됨 |
| `0.80` 임계 및 라우팅 누수율 | `experiments/track6/PP-E2E1_routing_pipeline_replay/reports/result_report.md`, `experiments/track6/PP-RMAP1_routing_map_optimization/reports/result_report.md`, `experiments/track6/PP-RHO1_out_of_dict_homonym_rate/reports/result_report.md` | v2 수치로 갱신 |
| `MAPE 기준 0.83, p95 기준 0.85` 후보 수치 | 세부 분리 근거 미확인. `PP-MCAL1/WMATCH1`의 required accuracy floor `0.85`만 남김 | 보류/제거 |

## 2. 적용 구조

- 현재 0.1v API 구현 관점의 계산 흐름:

```text
[작품 입력]
  - 작가 정보
  - 작품 크기
  - 매체/지지체
  - 작품 메타
        |
        v
[작품 라우팅]
  - 작가가 신뢰도 높게 매칭되는가? (매칭점수 0.80 이상)
  - 같은 작가의 사용 가능한 가격 이력이 몇 건인가?
        |
        +---------------+----------------------+----------------+
        |               |                      |
        v               v                      v
 [Warm 경로]      [Warm-lite 경로]        [Cold/검수대기 경로]
  이력 5건 이상     이력 1~4건              매칭 실패, 이력 0건, 입력 부족,
  - WMIN8 adapter   - warm_lite_quantile_residual_v0.1  또는 동명이인 검수 필요
  - 기준가격/보정    - Quantile residual    - Cold adapter 또는 보류
        |               |                      |
        +---------------+----------------------+
                        |
                        v
              [최종 예측가격 및 지표 출력]
```

- 문서 성능 기준 관점의 계산 흐름:

```text
[작품 입력]
      |
      v
[작품 라우팅]
  - 작가매칭신뢰도점수 0.80 이상?
  - 같은 작가의 사용 가능한 가격 이력이 몇 건인가?
      |
      +---------------+----------------------+----------------+
      |               |                      |
      v               v                      v
[Warm]           [Warm-lite]             [Cold 성능 기준]
 이력 5건 이상     이력 1~4건              매칭 실패 또는 이력 0건
 - WMIN8           - warm_lite_quantile_residual_v0.1  - 검색 피처 포함 v0.3
 - 위험도 라우터    - Quantile residual    - 과대예측 방어
      |               |                      |
      +---------------+----------------------+
                      |
                      v
            [최종 예측가격 및 지표 출력]
```

### 2.1 Warm/Warm-lite/Cold 라우팅 기준

- 핵심 답변: 작가 이력이 1건이라도 있으면 무조건 Warm으로 보내는 구조가 아님
- 실험 split 기준: Warm validation/test 작가는 학습 데이터에 같은 작가가 존재하고, 최소 학습 이력 5건을 만족하도록 구성
- 실험 split 기준: Cold validation/test 작가는 학습 데이터의 `artist_key`, 정규화 작가명과 겹치지 않도록 구성
- 현재 0.1v API 구현 기준: `작가매칭신뢰도점수 >= 0.80` 통과 시 이력 `5건 이상 → Warm`, `1~4건 → Warm-lite`, 그 외(매칭 실패/이력 0건/검수 필요) `→ Cold 또는 검수대기`
- 이력 1~4건 처리는 Warm 5건 이상 본체가 아니라 전용 경량 경로(Warm-lite)로 처리 — 1~4건을 Warm 본체로 직접 보내지 않는 구조 제약은 유지
- Warm-lite 경로 동결 완료: 이력 1~4건 고신뢰 매칭 작가 전용 Warm-lite 경로가 Quantile residual 번들로 동결됨 (`warm_lite_quantile_residual_v0.1`, PP-WLITE-Q5)
- 운영 전제: 매칭 점수 캘리브레이션과 신규 트래픽 모니터링은 계속 필요하며, 동명이인 위험이 높으면 0.1v API에서도 검수대기로 보냄
- 유사작품 정보의 역할: Warm/Warm-lite/Cold 라우팅을 단독으로 결정하는 기준이 아니라, Warm 내부 기준가격과 신뢰도 계산을 안정화하는 보조 근거

#### 2.1.1 라우팅 수치 기준

| 구분 | 현재 0.1v API 구현 기준 | 문서 성능 기준 | 비고 |
|---|---|---|---|
| `작가매칭신뢰도점수` | Warm/Warm-lite `0.80 이상`, Cold/검수대기 `0.80 미만` 또는 동명이인 위험 | 동일 | 0.80은 PP-E2E1/RHO1 재검증 이후 공식 0.1v 코드에 반영됨 |
| `같은작가_사용가능가격이력수` | Warm `5건 이상`, Warm-lite `1~4건`, Cold `0건` | 동일 | Warm-lite는 0.1v API에 포함 |
| Cold 모델 | 0.1v API 내부 Cold adapter/artifact | v0.3 guard+search 재현 검증 기준 | 성능표의 Cold 수치는 Cold 성능 기준 fixed test |

```text
현재 0.1v API 라우팅 공식

매칭 통과 = (작가매칭신뢰도점수 >= 0.80)

매칭 통과 AND 이력 >= 5       → Warm
매칭 통과 AND 이력 1~4건      → Warm-lite
그 외                         → Cold 또는 검수대기
```

```text
문서 성능 기준 라우팅 공식

매칭 통과 = (작가매칭신뢰도점수 >= 0.80)
            # 구현 주의: 부동소수점 경계 — tolerance(1e-6) 적용 필수

매칭 통과 AND 이력 >= 5       → Warm
매칭 통과 AND 이력 1~4건      → Warm-lite (이력 1건은 `confidence_grade=warm_lite_low`, `display_policy=wide_range_with_review_flag`)
그 외 (매칭 실패/이력 0건)    → Cold

점수 0.80~0.90 구간(이름 일치·보조정보 무)은 0.1v API에서도 상위 경로 가능하되, 보조정보/동명이인 위험에 따라 검수 플래그 또는 검수대기가 붙을 수 있음
```

#### 2.1.1.1 이력 5건 기준의 성격과 실험 근거

- 기준의 성격: 현재 0.1v API는 `5건 이상 → Warm / 1~4건 → Warm-lite / 0건 또는 매칭 실패 → Cold 또는 검수대기`로 동작한다
- 먼저 결론: 이 분기는 "1~4건은 항상 약하고 5건부터 갑자기 강하다"는 단순 가정이 아니다. 현재 보유한 비누수 검증에서 `1~4건 전체는 Warm-lite가 더 안정적`이고, `5건 이상 전체는 WMIN8 Warm이 더 안정적`이었기 때문에 유지하는 운영 경계다
- WMIN8의 최소 표본 1 완화 의미: Warm 진입 조건을 5건에서 1건으로 낮췄다는 뜻이 아니다. 0.1v 라우팅은 그대로 `5건 이상 → Warm`, `1~4건 → Warm-lite`다. 여기서 `최소 표본 1`은 Warm으로 들어온 5건 이상 작가 안에서, 대상 작품과 비슷한 과거 작품이 1건만 있어도 기준가격 계산에 참고한다는 뜻이다
- 실측 근거 1 (PP-WCUT1 이력 절단 실험, warm test 607행): 작가 이력을 k건으로 인위 절단하면 현행 유사작품 찾기 단계(min5)는 k=5에서 MdAPE `0.49 → 0.18`로 단절 개선한다. 반면 min1 변형은 k=1부터 Cold를 이기고(`0.2038` vs `0.4983`), k=4에서는 MdAPE `0.1462`까지 낮아진다
- 실측 근거 2: 이 결과 때문에 `5건`은 성능이 갑자기 좋아지는 통계 임계값이라기보다 현재 Warm 본체의 구조 제약으로 해석한다. `이력 5~7건 0.2256 vs 50건 이상 0.1072` 구간 후보 수치는 이번 감사에서 직접 산출 artifact를 찾지 못해 본문 근거 지표에서 제외함
- Warm-lite 동결 완료: 저표본 매칭(최소 1건)을 허용한 Warm-lite 경로가 Quantile residual 후보 검증과 Q5 parity를 통과해 `warm_lite_quantile_residual_v0.1`로 동결됨
- Warm-lite 현재 채택 모델 성능(PP-WLITE-Q3/Q5, 실존 저이력 LOO 1,947행): `0.107246 / 0.275773 / 0.852026`
- 저이력 Warm 통일 검증(PP-WMIN9E): 1~4건 전체에서 Warm-lite `0.1092 / 0.2866 / 0.8765`, WMIN8 svc-core proxy `0.1291 / 0.2932 / 0.9163`으로 Warm-lite가 전 지표 우세. k=2와 k=3은 Warm-lite 전 지표 우세, k=1은 MAPE만 proxy가 `0.0009p` 낮고, k=4는 p95만 proxy가 낮다
- 1~4건에 full WMIN8을 그대로 적용하지 않는 이유: PP-WCUT4/WMIN9C의 저이력 검증 행은 train 안의 작품을 hold-out해서 만든다. frozen full WMIN8의 PPV8/상류 Warm 모델을 그대로 호출하면 해당 hold-out 작품을 이미 학습한 모델이 될 수 있어 label leakage가 생긴다. 누수 없는 full WMIN8 1~4 직접 비교는 PPV8와 상류 Warm stack을 hold-out별로 재학습해야 한다
- 추가 시도(PP-WMIN11 부분 재학습 실험): frozen full WMIN8/PPV8를 쓰지 않고, hold-out을 뺀 학습 데이터로 WMIN8 svc-core와 L10 버킷순차보정 축을 다시 학습해 1,947행에서 비교했다. 전체 결과는 Warm-lite `0.1092 / 0.2866 / 0.8765`, 부분 재학습 라우팅 후보 `0.1480 / 0.2931 / 0.8716`이다. p95는 부분 재학습 후보가 `0.0048` 낮지만, MdAPE는 `+0.0388`, MAPE는 `+0.0066` 나빠 전체 가격 정확도 기준으로 Warm-lite 유지 판단을 바꾸지 않는다
- PP-WMIN11 한계: 이 결과도 full WMIN8 완료 실험은 아니다. PPV8의 큰오차방어 축은 기본 Huber, L8/L9 순차보정, D4 blend, R5 잔차 안정화, E1 작가이력 라우팅, K3 유사작품 fallback, U1 생성 bucket 후보 같은 상류 Warm 예측값을 같은 hold-out 조건으로 다시 만들어야 한다. 아직 `PPV8 = 0.75 * 큰오차방어 + 0.25 * 버킷순차보정` 전체를 hold-out별로 완전 재학습한 값은 아니므로, 문서에서는 `WMIN8 부분 재학습 추가 근거`로만 사용한다
- 5건 이상 반례 검증(PP-WMIN9D): 같은 607개 Warm fixed test 행에 Warm-lite를 강제 적용하면 `0.108722 / 0.248054 / 0.837824`이고, WMIN8은 `0.104326 / 0.235814 / 0.739416`이다. 5건 이상 전체 기준에서는 WMIN8이 MdAPE/MAPE/p95를 모두 낮춘다
- 운영 연동 전제: 매칭 점수 캘리브레이션 + 신규 트래픽 모니터링(절단 시뮬레이션 한계 보완). 현재 0.1v API에는 0.80 기준 Warm/Warm-lite 분기가 반영되어 있으며, 동명이인 위험이 높으면 검수대기로 보냄

경계 판단을 위해 실제로 물은 질문은 다음 네 가지다.

| 질문 | 사용한 검증 | 결과 | 현재 판단 |
|---|---|---|---|
| 이력 1~4건을 Cold로 보내도 되는가? | PP-WCUT4 실존 저이력 작가 leave-one-out | Warm-lite `0.1092 / 0.2866 / 0.8765`, Cold `0.5429 / 0.9946 / 2.5358` | 같은 작가 이력이 1건이라도 있으면 Cold보다 Warm-lite가 훨씬 강함 |
| 이력 1~4건을 Warm 계열 하나로 통일해도 되는가? | PP-WMIN9E, WMIN8 svc-core proxy 동일 행 비교 | 1~4건 전체 Warm-lite `0.1092 / 0.2866 / 0.8765`, proxy `0.1291 / 0.2932 / 0.9163` | 현재 비누수 근거로는 1~4건 Warm 통일을 지지하지 않음 |
| full WMIN8을 누수 없이 1~4건에 직접 적용해 볼 수 있는가? | PP-WMIN11 부분 재학습 실험 | frozen full WMIN8/PPV8는 배제. 재학습 가능한 svc-core+L10 축으로 만든 후보는 `0.1480 / 0.2931 / 0.8716` | 완전 full은 아직 아니지만, 재현 가능한 축만으로는 Warm-lite를 대체할 근거가 부족 |
| 이력 5건 이상을 Warm-lite로 보내도 되는가? | PP-WMIN9D, 607개 Warm fixed test 행에 Warm-lite 강제 적용 | WMIN8 `0.104326 / 0.235814 / 0.739416`, 강제 Warm-lite `0.108722 / 0.248054 / 0.837824` | 5건 이상 전체는 WMIN8 Warm 유지 |
| Warm-lite Quantile residual이 현재 채택값인가? | PP-WLITE-Q1~Q5 | Q4에서 `residual_lgb_s05_cap010`이 Q2-like 기준 `0.1545 / 0.3034 / 1.0005`로 단순 평균 후보보다 추가 개선. Q5에서 bundle replay/API parity 통과 | 현재 0.1v Warm-lite 채택값은 `Quantile 평균 + clip(0.50 * LightGBM Huber 잔차, -0.10, +0.10)` |

1~4건 k별 판단은 다음처럼 읽는다. 세 값은 `MdAPE / MAPE / p95 APE` 순서다.

| 이력 수 | Warm-lite | WMIN8 svc-core proxy | 해석 |
|---:|---:|---:|---|
| 1건 | `0.1207 / 0.3415 / 0.9559` | `0.1271 / 0.3406 / 0.9573` | Warm-lite가 MdAPE와 p95 우세, proxy는 MAPE만 `0.0009p` 우세 |
| 2건 | `0.1184 / 0.2707 / 0.8779` | `0.1448 / 0.2821 / 0.9478` | Warm-lite 전 지표 우세 |
| 3건 | `0.1060 / 0.2541 / 0.7142` | `0.1195 / 0.2661 / 0.7489` | Warm-lite 전 지표 우세 |
| 4건 | `0.0923 / 0.2557 / 0.7884` | `0.1190 / 0.2634 / 0.7682` | Warm-lite가 MdAPE와 MAPE 우세, proxy는 p95만 우세 |
| 1~4건 전체 | `0.1092 / 0.2866 / 0.8765` | `0.1291 / 0.2932 / 0.9163` | Warm-lite 전 지표 우세 |

PP-WMIN11 부분 재학습 실험은 proxy보다 한 단계 더 Warm 본체에 가깝게 시도한 검증이다. 다만 정확한 full WMIN8이 아니라, 누수 없이 다시 만들 수 있는 `svc-core`와 `L10 버킷순차보정` 축만 사용했다.

| 후보 | 1~4건 전체 MdAPE / MAPE / p95 APE | Warm-lite 대비 해석 |
|---|---:|---|
| Warm-lite | `0.1092 / 0.2866 / 0.8765` | 기준 |
| WMIN8 svc-core 재학습축 | `0.1291 / 0.2932 / 0.9163` | MdAPE/MAPE/p95 모두 Warm-lite보다 나쁨 |
| WMIN8 부분 재학습 라우팅 후보(PPV8 대신 L10 보조축 사용) | `0.1480 / 0.2931 / 0.8716` | p95만 `0.0048` 낮고 MdAPE/MAPE는 나쁨 |

5건 이상에서 Warm을 유지하는 판단도 "모든 세부 구간의 모든 지표에서 Warm이 항상 1위"라는 뜻은 아니다. PP-WMIN9D의 전체 607행 기준에서 WMIN8이 MdAPE/MAPE/p95를 모두 낮췄고, 특히 큰 오차를 보는 p95에서 `0.837824 → 0.739416`으로 차이가 컸기 때문에 운영 경계는 5건 이상 Warm으로 둔다. 세부 history bin에서는 MdAPE가 Warm-lite에 유리한 구간도 있으므로, 향후 운영 라벨이 쌓이면 5~9건 구간만 따로 재검증할 수 있다.

정리하면 현재 경계의 근거는 다음과 같다.

```text
작가 매칭 신뢰도 >= 0.80
AND 사용 가능한 같은 작가 가격 이력 = 0건
  -> 작가 가격 기준을 만들 수 없으므로 Cold 또는 검수대기

작가 매칭 신뢰도 >= 0.80
AND 사용 가능한 같은 작가 가격 이력 = 1~4건
  -> Cold보다 훨씬 낫고, Warm proxy 통일보다 전체 지표가 나은 Warm-lite

작가 매칭 신뢰도 >= 0.80
AND 사용 가능한 같은 작가 가격 이력 >= 5건
  -> Warm-lite 강제 적용보다 전체 지표가 나은 WMIN8 Warm
```

현재 직접 검증의 한계도 명시한다. 1~4건에 대해 frozen full WMIN8 전체 파이프라인을 그대로 호출하는 비교는 label leakage 위험 때문에 유효한 근거로 쓰지 않는다. PP-WMIN11에서 frozen full WMIN8/PPV8를 배제하고 재학습 가능한 축까지는 시도했지만, 정확한 full WMIN8 저이력 직접 비교를 끝내려면 PPV8 큰오차방어 축과 그 입력이 되는 상류 Warm 후보들까지 hold-out별로 재학습해야 한다. 따라서 현재 문서의 운영 판단은 Warm-lite/Cold 직접 비교, WMIN8 svc-core proxy, PP-WMIN11 부분 재학습 실험, 5건 이상 강제 Warm-lite 반례를 함께 본 판단이다.

#### 2.1.2 작가매칭신뢰도점수 계산 방식

- 목적: 입력 작가가 학습 데이터의 특정 작가와 같은 사람인지 0~1 사이 점수로 환산
- 점수 해석: `1.00`에 가까울수록 같은 작가일 가능성이 높고, `0.00`에 가까울수록 같은 작가로 볼 근거가 약함
- 현재 0.1v Warm/Warm-lite 라우팅 기준: `작가매칭신뢰도점수 >= 0.80` AND 가격 이력 `1건 이상`
- 이력 분기: 가격 이력 `5건 이상`이면 Warm, `1~4건`이면 Warm-lite, `0건`이면 Cold 또는 검수대기
- 보수 원칙: 작가명이 같아도 동명이인 위험이 높거나 핵심 정보가 충돌하면 Warm/Warm-lite로 바로 보내지 않음
- 현재 구현: 공식 0.1v API는 `direct_key`, `alias`, `fuzzy` 상태와 생년 보정, 동명이인 위험도를 직접 계산한다. 별도의 하위점수 5개를 따로 만들거나 반환하지 않는다.

작가명 정규화 방식:

```text
정규화작가명 =
  소문자 변환
  + 앞뒤 공백 제거
  + 모든 공백 제거
  + 괄호/문장부호/기호 제거
  + 한글명/영문명 alias는 사전에 저장된 정규화 alias와 비교
```

한글 이름 입력을 artist_key로 연결하는 방식:

```text
[입력 작가명: 한글명 중심]
        |
        v
[작가명 정규화]
  - 소문자 변환
  - 모든 공백 제거
  - 괄호/문장부호/기호 제거
        |
        v
[학습 작가 사전에서 후보 검색]
  - artist_key 직접 지정이면 artist_registry에서 바로 조회
  - artist_aliases.alias_normalized 완전 일치 후보 확인
  - 완전 일치가 없으면 alias_normalized LIKE 부분 이름 후보 확인
        |
        v
[후보 검증]
  - 후보가 1명인가?
  - 현재 구현상 생년이 충돌하지 않는가?
  - 국적/외부 작가 식별자는 후속 확장 보조정보로 관리
  - 동명이인 후보가 섞이지 않는가?
        |
        v
[확정된 후보의 artist_key 사용]
```

| 단계 | 처리 | Warm 라우팅 영향 |
|---|---|---|
| `artist_key` 직접 지정 | 입력 key가 `artist_registry.artist_key`와 일치 | `작가매칭신뢰도점수=1.00`, 동명이인 위험 0으로 보고 이력 수만 확인 |
| 정규화 alias 완전 일치 | 입력 한글명/영문명이 `artist_aliases.alias_normalized`와 일치 | 현재 0.1v 구현상 기본 점수 `1.00`에서 시작 |
| 부분 이름 후보 | 완전 일치가 없고 정규화 이름이 alias 일부와 일치 | 현재 0.1v 구현상 `match_status=fuzzy`, 기본 점수 `0.78`에서 시작 |
| 생년 일치 | 입력 생년과 사전 생년이 모두 있고 같음 | 현재 0.1v 구현상 `+0.05` 보정 |
| 생년 불일치 | 입력 생년과 사전 생년이 모두 있고 다름 | 현재 0.1v 구현상 `-0.15` 보정. 더 보수적인 차단은 후속 정책 개선 대상 |
| 동명이인 후보 | 후보가 여러 명이거나 사전의 `is_homonym`이 참 | `homonym_risk_score` 상승. `0.60` 이상이면 검수대기 |

운영 또는 후보 정책 적용에 필요한 작가 사전 필드:

| 필드 | 용도 |
|---|---|
| `artist_key` | 모델 내부에서 사용하는 작가 고유 식별자 |
| `artist_name_ko` | 한글명 직접 매칭 |
| `artist_name_ko_normalized` | 공백/대소문자/기호 차이를 줄인 한글명 |
| `artist_name_ko_no_space` | 한글명 공백 제거 매칭 |
| `artist_name_en` | 영문명 보조 매칭 |
| `artist_name_en_reversed` | 영문 성/이름 순서가 바뀐 경우 보조 매칭 |
| `birth_year` | 현재 0.1v 구현에서 생년 일치/불일치 보정에 사용 |
| `nationality` | 작가 메타/후속 검증 보조정보. 현재 0.1v 매칭 점수 직접 보정에는 사용하지 않음 |
| `external_artist_id` | Artsy, Saatchi 등 외부 작가 식별자 검증 후보. 현재 0.1v 매칭 점수 직접 보정에는 사용하지 않음 |
| `usable_training_price_count` | Warm 라우팅의 가격 이력 수 기준 |

주의할 점:

- 한글 이름 문자열 자체가 `artist_key`가 되는 것은 아님
- 한글 이름은 학습 작가 사전에서 기존 `artist_key` 후보를 찾기 위한 입력값
- 같은 한글명이 여러 작가에게 연결되면 보조 정보 확인 전까지 Warm으로 보내지 않음
- 학습 작가 사전에 alias가 없으면 자동 번역/로마자 변환만으로는 고신뢰 매칭으로 보지 않음
- 검색 결과만으로 같은 작가라고 추정되는 경우는 `작가매칭신뢰도점수`를 낮게 보고 Cold로 처리

현재 0.1v API 실제 구현:

```text
if 입력_artist_key 또는 selected_artist_key가 학습 artist_key와 일치:
    match_status = direct_key
    artist_match_score = 1.00
    homonym_risk_score = 0.00
else:
    입력 이름을 정규화한다
    정규화 alias 완전 일치 후보가 있으면:
        match_status = alias
        base_score = 1.00
    완전 일치 후보가 없고 부분 이름 후보가 있으면:
        match_status = fuzzy
        base_score = 0.78

    입력 생년과 후보 생년이 모두 있으면:
        같을 때 +0.05
        다를 때 -0.15

    artist_match_score =
        alias는 0.00~1.00 범위로 제한
        fuzzy는 0.00~0.95 범위로 제한

    homonym_risk_score =
        clip((후보 artist_key 수 - 1) * 0.35 + is_homonym * 0.25, 0.00, 1.00)

    homonym_risk_score >= 0.60이면 review_required
```

구현 단계별 해석:

| 단계 | 계산되는 값 | 설명 |
|---|---|---|
| 직접 key 조회 | `match_status=direct_key`, `artist_match_score=1.00`, `homonym_risk_score=0.00` | 사용자가 특정 학습 작가 key를 지정한 경우 |
| alias 완전 일치 | `match_status=alias`, 기본 `artist_match_score=1.00` | 정규화된 입력 이름이 학습 작가 alias와 완전히 같은 경우 |
| 부분 이름 후보 | `match_status=fuzzy`, 기본 `artist_match_score=0.78` | 완전 일치가 없고, 입력 이름이 alias 일부와 맞는 경우 |
| 생년 보정 | 생년 일치 `+0.05`, 생년 불일치 `-0.15` | 입력 생년과 사전 생년이 모두 있을 때만 적용 |
| 점수 제한 | alias 최대 `1.00`, fuzzy 최대 `0.95` | 부분 이름 후보가 과도하게 확정되지 않도록 제한 |
| 동명이인 위험 | `clip((후보 수 - 1)*0.35 + is_homonym*0.25, 0, 1)` | 후보가 여러 명이거나 동명이인 플래그가 있으면 위험도 상승 |
| 검수대기 | `homonym_risk_score >= 0.60` | 직접 key 지정이 아니면 Warm/Warm-lite 대신 검수대기 |

임계값 `0.80` 채택의 정량 근거:

- 오매칭 비용: 잘못된 작가의 이력으로 Warm 가격을 만들면 MdAPE `0.66~0.70`, p95 APE `9.3~9.7`로 Cold(`0.41 / 2.17`)보다 훨씬 나쁨. 장르가 비슷한 작가로 잘못 매칭되어도 영향은 거의 동일하게 파괴적임.
- 기대손실 계산(PP-WMATCH1/PP-MCAL1): 매칭 실제 정확도가 약 `85%` 이상일 때만 Warm 라우팅이 Cold 대비 기대 우위. `MAPE 기준 0.83, p95 기준 0.85`처럼 지표별로 나눈 세부 임계는 직접 근거가 확인되지 않아 본문 기준으로 사용하지 않음
- 동명이인 실태(학습 데이터 실측): 작가 1,773명 중 정규화 한글명 충돌 117 `artist_key`(6.6%), 충돌 작가의 생년 보유율 41% — "보조 정보 확인 전 Warm 금지" 원칙의 근거
- 운영 과제: 매칭 점수와 실제 정확도의 대응(캘리브레이션)은 운영 매칭 로그·검수 데이터로 보정 필요 — 위 가중치 산식은 이 보정 전까지의 보수 설계안
- 재검증 결과(PP-E2E1 v2, 2026-06-12): 임계 `0.90`은 자격 작가의 `61.5%`(clean)~`71.6%`(dirty)를 보조정보 부재만으로 Cold로 보내 기대 MAPE가 `0.9202~0.9399`까지 올라간다. 임계 `0.80`은 자격 작가 Cold 누수 `3.7%~24.4%`, Cold 오유입 `0~0.5%`, 기대 MAPE `0.8008~0.8499`로 개선된다. RMAP1 허용 오매칭률은 1~4건 구간 `27.8~30.4%`, 5건 이상 구간 `16.7%`라 PP-RHO1 proxy `5.0%` 대비 마진이 있다. 이 재검증 결과가 현재 0.1v API의 `0.80` 기준 근거다

현재 0.1v 구현 기준 예시:

| 상황 | 계산 | 작가매칭신뢰도점수 | 라우팅 해석 |
|---|---|---:|---|
| `artist_key`가 학습 데이터와 동일 | 직접 일치 | `1.00` | 가격 이력 5건 이상이면 Warm |
| 정규화 alias 완전 일치, 생년 정보 없음, 동명이인 위험 없음 | alias 기본 점수 | `1.00` | 이력 수에 따라 Warm/Warm-lite 가능 |
| 정규화 alias 완전 일치, 생년 일치 | `1.00 + 0.05`, alias 최대값 제한 | `1.00` | 이력 수에 따라 Warm/Warm-lite 가능 |
| 부분 이름 후보, 생년 일치 | `0.78 + 0.05` | `0.83` | 동명이인 위험이 낮고 이력 수가 있으면 Warm/Warm-lite 가능 |
| 부분 이름 후보, 생년 정보 없음 | fuzzy 기본 점수 | `0.78` | `0.80` 미만이므로 Cold/검수대기 |
| 후보가 여러 명이어서 동명이인 위험 높음 | `homonym_risk_score >= 0.60` | 점수와 별개로 검수대기 | Warm/Warm-lite 차단 |

운영 개선 과제:

- 현재 0.1v는 `artist_match_score`, `homonym_risk_score`, `match_status`, `match_basis`, `matched_alias`, `review_required`를 반환한다.
- 발표/검수 설명력을 높이려면 향후 API에서 `name_match_basis`, `birth_year_adjustment`, `candidate_count`, `is_homonym`, `review_required_reason` 같은 분해 근거를 함께 반환하는 것이 좋다.
- 다만 점수 산식 자체를 바꾸는 것은 라우팅 결과가 달라지므로, parity와 PP-E2E/RMAP 재검증 후 별도 적용해야 한다.

| 작가 매칭 상태 | `작가매칭신뢰도점수` | 라우팅 판단 |
|---|---:|---|
| `artist_key`가 동일하게 매칭됨 | `1.00` | 가격 이력 수 조건을 추가 확인 |
| 정규화 alias가 완전 일치하고 동명이인 위험이 낮음 | `1.00` | 가격 이력 수 조건을 추가 확인 |
| 부분 이름 후보이고 생년이 일치함 | `0.83` | 가격 이력 수와 동명이인 위험을 추가 확인 |
| 부분 이름 후보이고 생년 정보가 없음 | `0.78` | `0.80` 미만이므로 Cold 또는 검수대기 |
| 후보가 여러 명이어서 `homonym_risk_score >= 0.60` | 점수와 별개 | 검수대기 |
| 같은 작가로 볼 근거가 없음 | `0.00` | Cold |

`같은작가_사용가능가격이력수`에 포함하는 데이터 기준:

- 같은 작가로 확정된 학습 데이터 작품
- 실제 가격값이 존재하고 `가격 > 0`인 작품
- 로그가격 계산이 가능한 작품
- 현재 예측 대상 작품과 중복되지 않는 작품
- 동일 거래/동일 작품 중복 입력이 제거된 작품
- 테스트 데이터 또는 운영 평가 대상의 정답 가격을 포함하지 않은 작품

| 현재 0.1v API 조건 | 경로 | 판단 이유 |
|---|---|---|
| 작가매칭신뢰도점수 `0.80 이상`이고 같은 작가의 사용 가능한 학습 가격 이력이 `5건 이상` | Warm | 작가별 과거 가격대를 기준가격에 반영할 수 있음 |
| 작가매칭신뢰도점수 `0.80 이상`이고 같은 작가의 사용 가능한 학습 가격 이력이 `1~4건` | Warm-lite | 저이력 작가 전용 경량 기준가격 모델로 처리 |
| 작가 매칭이 불확실하거나 동명이인 위험이 높음 | Cold 또는 검수대기 | 잘못된 작가 이력을 Warm/Warm-lite 기준가격에 쓰는 위험이 큼 |
| 학습 데이터에 같은 작가 이력이 없음 | Cold | 작품/작가 메타/검색 피처와 비작가 비교군으로 추정해야 함 |
| 같은 작가는 아니지만 매체/크기/지지체가 비슷한 유사작품만 있음 | Cold 보조 근거 또는 낮은 신뢰도 참고 | 작가별 가격 기준은 없으므로 Warm으로 보지 않음 |

```text
현재 0.1v API Warm/Warm-lite/Cold 라우팅 판단

작가매칭신뢰도점수 >= 0.80?
        |
        +-- 아니오 --> Cold 또는 검수대기
        |
        v
같은작가_사용가능가격이력수 >= 5건?
        |
        +-- 예 ----> Warm
        |
        +-- 아니오 --> 같은작가_사용가능가격이력수 1~4건?
                       |
                       +-- 예 ----> Warm-lite
                       |
                       +-- 아니오 --> Cold
```

- 현재 0.1v API에서는 `작가매칭신뢰도점수 >= 0.80`이고 이력 `1~4건`이면 Warm-lite로 분기한다. 이 정책은 모델 artifact 버전명과 별개로 공식 0.1v API 라우팅 기준이다

- 문서에서 `작가 이력이 충분하다`의 의미: 단순히 작가명이 한 번 등장했다는 뜻이 아니라, 가격 예측 기준으로 사용할 수 있는 같은 작가의 학습 가격 이력이 충분하다는 뜻
- 문서에서 `신규/저이력 작가`의 의미: 학습 데이터에 같은 작가 이력이 없거나, 있더라도 Warm 기준가격을 만들기에는 표본 수와 매칭 신뢰도가 부족한 작가

## 3. 평가 기준

- 성능 수치 기준: Warm 성능 기준과 Cold 성능 기준의 fixed test 기준

| 구분 | 평가 데이터 | 목적 |
|---|---|---|
| Warm fixed test | 607건 | Warm 후보 실험들과 동일한 고정 평가셋에서 WMIN8 후보 성능 확인 |
| Warm validation out-of-fold | 519건 | 미세 보정 학습 및 과적합 방지 검증 |
| Cold fixed test | 3,099건 | Cold 성능 기준 모델 성능 확인 |
| Cold validation | 2,753건 | guard 임계값과 검색 보정 재현 확인 |

- 주요 지표 해석:

| 지표 | 의미 | 낮을수록 좋은가 |
|---|---|---|
| MdAPE | 작품별 절대 퍼센트 오차의 중앙값 | 예 |
| MAPE | 작품별 절대 퍼센트 오차의 평균 | 예 |
| p95 APE | 큰 오차 상위 5% 구간을 보는 95퍼센타일 오차 | 예 |
| RMSE log | 로그가격 기준 평균제곱근 오차 | 예 |

MAPE 계산식:

```text
최종예측가격_KRW = exp(최종_로그가격)

작품별_APE =
  abs(최종예측가격_KRW - 실제가격_KRW)
  / 실제가격_KRW

MAPE = mean(작품별_APE)
MdAPE = median(작품별_APE)
p95 APE = quantile(작품별_APE, 0.95)
```

RMSE log 계산식:

```text
RMSE log =
  sqrt(mean((최종_로그가격 - 실제_로그가격)^2))
```

- MAPE, MdAPE, p95 APE: 원화 가격으로 변환한 뒤 실제 원화 가격과 비교한 비율 오차
- RMSE log: 로그가격 공간에서 계산한 오차
- RMSE log 사용 범위: 모델이 학습/보정하는 로그가격 공간의 오차를 확인하기 좋은 보조 지표다. 다만 Cold 비교값이 없어 세 경로 간 성능 비교표에는 사용하지 않는다.

### 3.1 모델/학습법/통계 방식 표기 점검

- 점검 목적: 모델명, 학습법, 통계 처리, 후처리 로직이 서로 섞여 보이지 않도록 문서용 표기와 실제 역할을 구분
- 표기 원칙: 최종 계산 경로에 영향을 주는 항목은 본문에서 기능 중심 이름과 계산 역할을 함께 표기
- 제외 원칙: 최종 계산 경로에 포함되지 않는 실험 후보명이나 내부 추적 ID는 본문 설명이 아니라 내부 추적 표에서만 관리

| 구분 | 문서용 표기 | 실제 의미 | 이 보고서에서의 사용 위치 |
|---|---|---|---|
| 모델 학습법 | `Huber loss 기반 잔차 회귀` | Huber loss를 기준으로 회귀계수와 절편을 산출해, 기준 로그가격에 남은 잔차를 예측하는 강건 회귀 | Warm 미세 보정값의 원천 후보 계산 |
| 모델 학습법 | `방향 분류 모델` | 기준가격보다 실제 가격이 높을지 낮을지를 확률로 판단하는 분류 모델 | 이전 Warm 후보와 비교/진단 맥락에서 사용. WMIN8 후보의 핵심 결정은 위험도 조건부 라우터 |
| 모델 학습법 | `LightGBM Quantile 회귀` | LightGBM 트리 모델을 평균 예측이 아니라 특정 Quantile 위치의 가격을 예측하도록 학습한 방식 | Cold 성능 기준 모델, 낮은쪽 방어가격, 불확실성 폭 생성 |
| 통계 방식 | `Quantile예측구간폭` | 높은 Quantile 예측값과 낮은 Quantile 예측값의 차이 | Warm 보정 상한 축소, Cold 불확실성 판단 |
| 통계 방식 | `잔차` | `실제_로그가격 - 예측_로그가격` | Warm Huber 회귀계수 산출, Cold 구간별 보정값 계산 |
| 통계 방식 | `중앙값` 또는 `median()` | 값을 순서대로 정렬했을 때 가운데에 있는 값 | MdAPE 지표, Cold 구간별 잔차 안정화 |
| 통계 방식 | `rank01()` | 값의 상대적 순위를 0~1 범위로 변환하는 처리 | Warm 작품단위위험도 계산 |
| 후처리 방식 | `clip()` | 값이 정해진 하한/상한을 넘지 않도록 제한하는 처리 | Warm 보정 상한, Cold 구간별 보정값 제한 |
| 후처리 방식 | `bucket()` 또는 구간화 | 연속값을 의미 있는 구간으로 나누는 처리 | 가격대, 신뢰도, Quantile예측구간폭 구간 생성 |
| 후처리 방식 | `lookup` | 학습 중 실시간으로 계산하는 모델이 아니라 미리 검증해 저장한 표에서 값을 조회하는 방식 | Cold 작가 검색 보정값 적용 |
| 계산 표현 | `로그가격` | 가격에 자연로그를 적용한 값 | 각 경로에서 로그가격으로 계산 후 원화 가격으로 변환 |
| 계산 표현 | `exp()` | 로그가격을 다시 원화 가격으로 되돌리는 지수 함수 | 각 경로의 최종 원화 예측가격 산출 |
| 평가 표현 | `fixed test` | 실험 간 비교를 위해 고정한 테스트 데이터 | Warm 성능 기준과 Cold 성능 기준의 비교 기준 |
| 평가 표현 | `validation out-of-fold` | 학습에 직접 쓰지 않은 fold 예측으로 검증하는 방식 | Warm 미세 보정의 과적합 여부 확인 |

- 표기 보완 결과:

- `Quantile`은 Warm과 Cold에서 모두 사용되지만 역할이 다르므로 별도 표기
- Warm의 `Quantile` 역할: 기준가격 생성이 아니라 보정 위험도와 보정 상한 계산에 사용
- Cold의 `LightGBM Quantile 회귀` 역할: 기준 후보, 보수 후보, 예측 불확실성 폭을 직접 생성
- `Huber`는 약어가 아니라 손실 함수/강건 회귀 방식 이름이다. 본문에서 `Huber 모델`이라고 줄여 쓰는 경우는 `Huber loss 기준으로 계수와 절편을 데이터에 맞춰 산출한 회귀 예측기`를 뜻한다
- `lookup`, `rank01`, `clip`, `bucket`, `median`은 모델명이 아니라 통계/후처리 방식으로 표기

Quantile 역할 차이:

| 구분 | Warm에서의 Quantile | Cold에서의 Quantile |
|---|---|---|
| 핵심 역할 | 최종 예측가격을 직접 만들지 않음 | Cold 성능 기준 예측가격의 출발점이 되는 기준 후보를 직접 만듦 |
| 사용 위치 | 기준가격 생성 이후의 위험도 판단 단계 | 기준가격 후보 생성 단계와 과대예측 방어 단계 |
| 주요 산출값 | `Quantile예측구간폭` | `검색피처포함_기초Quantile후보_로그가격`, `낮은쪽40퍼센트기준_로그가격`, `Quantile예측구간폭` |
| 가격 이동 방식 | 예측 폭이 넓으면 보정 상한을 줄여 가격을 덜 움직임 | 예측 폭이 넓고 과대예측 위험이 있으면 낮은쪽 40% 지점 가격 쪽으로 낮춤 |
| 해석 | “이 작품은 불확실하니 Warm 보정을 약하게 하자” | “이 작품의 기준가격과 낮은쪽 방어가격을 Quantile 모델로 만들자” |

Warm에서의 Quantile 사용 흐름:

```text
[미세보정전 기준로그가격]
        |
        v
[Quantile예측구간폭 확인]
        |
        v
[불확실성순위 = rank01(Quantile예측구간폭)]
        |
        v
[적용상한 축소]
        |
        v
[최종보정값을 작게 제한]
        |
        v
[최종 Warm 로그가격]
```

Cold에서의 Quantile 사용 흐름:

```text
[작품 피처 + 작가 메타 피처 + 검색 피처]
        |
        v
[LightGBM Quantile 회귀]
        |
        +--> 검색피처포함_기초Quantile후보_로그가격
        +--> 낮은쪽40퍼센트기준_로그가격
        +--> Quantile예측구간폭
        |
        v
[Quantile예측구간폭 구간별 잔차 보정]
        |
        v
[과대예측 위험이면 낮은쪽 40% 지점 가격 쪽으로 하향]
        |
        v
[최종 Cold 로그가격]
```

## 4. Warm 모델 상세

> 2026-06-13 후보 갱신 반영: Warm 5건 이상 경로의 보고서상 후보를 `이력 기반 조건부 유사작품 보정 모델`(내부 추적 WMIN8)로 정리함. 이 문서에서는 현재 0.1v API의 Warm 5건 이상 경로를 이 후보 adapter 기준으로 설명하고, 1~4건은 Warm-lite 경로로 분리한다.

| 구분 | 내용 |
|---|---|
| 핵심 변경 | Warm 안에서 비슷한 과거 작품 비교군을 1건부터 참고하도록 완화(적용 후 정밀 비교군 매칭률 81.9%) + Huber 잔차 보정 계수 재산출 + 위험도 조건부 가중 라우터(기본 0.70 / 위험 구간 보수 대안 0.85) |
| 성능 | fixed test `0.104326 / 0.235814 / 0.739416` (이전 후보 대비 MdAPE -26% / MAPE -13% / p95 -8%). 2026-06-04 신규 라벨 stress는 WMIN4 min1 계열의 선행 안전성 점검이며 WMIN8 선택에는 직접 사용하지 않음 |
| 재현 | 동결 번들 `models/track6/warm_wmin8_exact_runtime_candidate` — 실험↔후보 adapter 예측 일치 검증(parity max diff 5.3e-15) |

### 4.1 모델 목적

- 적용 대상: 작가가 신뢰도 높게 매칭되고, 학습 데이터 안에 같은 작가의 사용 가능한 가격 이력이 5건 이상인 작품
- 모델 구조: 가격을 처음부터 새로 예측하는 단일 모델이 아니라, 선행 Warm 예측가격으로 만든 기준 로그가격 위에 매우 작은 보정값을 더하는 구조
- 계산 관점: `기준가격 + 미세 보정값`

- 핵심 처리:

- 1차 기준가격: 최소 표본 1 유사작품 찾기 단계로 기본 후보(w700)와 보수 대안 후보(w850)를 생성
- 보정 조건: Huber 잔차 보정 후 작품 단위 위험도와 기본/대안 후보 차이를 보고 위험 구간에서만 보수 대안으로 교체

#### 4.1.1 Warm 적용 범위가 5건 이상인 이유

Warm의 5건 기준은 "5건부터 성능이 반드시 급변한다"는 의미가 아니라, 현재 WMIN8 Warm 본체가 검증된 적용 범위다. WMIN8은 같은 작가의 하위 유사작품 비교군, 보조 안정 Warm 예측값, Huber 잔차 보정, 위험도 라우터를 함께 쓰는 구조이므로 1~4건처럼 작가 이력 자체가 매우 적은 구간에는 별도 검증이 필요하다.

현재 근거는 다음처럼 정리한다.

| 검증 | 비교 | 결과 | 해석 |
|---|---|---|---|
| 1~4건을 Warm 계열으로 보낼 수 있는가 | Warm-lite vs WMIN8 svc-core proxy | Warm-lite `0.1092 / 0.2866 / 0.8765`, proxy `0.1291 / 0.2932 / 0.9163` | 1~4건 전체는 Warm-lite 유지가 더 안정적 |
| 1~4건에 full WMIN8 직접 비교를 시도했는가 | PP-WMIN11 부분 재학습 실험 | frozen full WMIN8/PPV8 배제, 부분 재학습 라우팅 후보 `0.1480 / 0.2931 / 0.8716` | 재학습 가능한 WMIN8 축만으로는 Warm-lite 대체 근거 부족. 정확한 full WMIN8은 PPV8 상류 재학습 필요 |
| 5건 이상도 Warm-lite로 처리할 수 있는가 | WMIN8 vs 강제 Warm-lite | WMIN8 `0.104326 / 0.235814 / 0.739416`, 강제 Warm-lite `0.108722 / 0.248054 / 0.837824` | 5건 이상 전체는 WMIN8 Warm 유지가 더 안정적 |
| WMIN8의 최소 표본 1은 무엇인가 | Warm 안에서 기준가격을 만들 때 쓰는 비교군 기준 | 대상 작품과 비슷한 같은 작가 과거 작품을 1건부터 참고 | Warm 진입 기준을 1건으로 낮춘 것이 아님 |

따라서 4.2의 `최소 표본 1`은 Warm 내부의 비교군 매칭 규칙이고, 0.1v API 라우팅은 계속 `1~4건 Warm-lite / 5건 이상 Warm`이다.

### 4.2 Warm 계산 순서도

Warm은 학습 단계에서 여러 기준가격 후보, 보조 예측축, 잔차 보정 모델, 라우팅 조건을 만든 뒤 동결한다. 사용 단계에서는 새 작품에 대해 이 동결된 구성요소를 적용만 하며, 새 작품의 실제 가격은 사용하지 않는다.

#### 4.2.1 Warm 학습 단계 순서도

```text
[Warm 학습 데이터]
  - 실제 로그가격이 있는 과거 작품
  - 작가키, 작품 크기, 매체/지지체, 작가 이력
        |
        v
[비교군 통계 생성 규칙 학습/검증]
  - 같은 작가 유사작품 찾기 단계 정의
  - 작가+재료/지지체+크기 -> 작가+크기 -> 작가 전체 -> 일반 fallback
  - fold/OOF 기준으로 자기 가격 누수 차단
        |
        v
[하위 Warm 후보 예측값 생성]
  - 기본 Huber 후보
  - L8/L9 순차보정 후보
  - D4 blend 후보
  - R5 p95/MAPE 방어 후보
  - E1 작가이력 라우팅, K3 유사작품 fallback, U1 확장 후보
        |
        v
[보조안정 Warm 축 학습]
  - 큰오차방어 축: 하위 Warm 후보 예측값을 입력으로 Huber meta-model 학습
  - 버킷순차보정 축: Quantile -> Huber 중심선 -> CatBoost 잔차 보정 학습
  - PPV8 보조안정값 = 0.75 * 큰오차방어 + 0.25 * 버킷순차보정
        |
        v
[WMIN8 기준 후보 생성]
  - 기본 후보 w700 = 0.70 * 유사작품기준 + 0.30 * 보조안정값
  - 대안 후보 w850 = 0.85 * 유사작품기준 + 0.15 * 보조안정값
        |
        v
[Huber 잔차 보정 학습]
  - 실제 로그가격 - 기준 후보 로그가격을 잔차 target으로 사용
  - 비교군 표본 수, 가격 IQR, 구간폭, 보조안정값 차이 등 10개 피처로 보정계수 산출
        |
        v
[위험도 라우터 선택]
  - validation에서 위험도임계값과 대안교체최소차이 선택
  - 위험도임계값 = 0.2534165869
  - 대안교체최소차이 = 0.005 log
  - 근거: PP-WMIN8 후보 비교에서 `min1_route_w850_risk_q50_altlower_gap005` 선택. `risk_q50`은 validation risk_score 중앙값, `altlower_gap005`는 대안 후보가 기본 후보보다 최소 0.005 log 낮아야 한다는 조건
        |
        v
[동결 산출물]
  - 비교군 통계 규칙
  - 보조안정 Warm 예측축
  - Huber 잔차 보정 모델
  - 위험도 라우터 조건
```

#### 4.2.2 Warm 사용 단계 순서도

```text
[Warm 입력 작품]
  - 작가키 (이력 5건 이상으로 확정)
  - 작품 크기/매체/지지체
  - 유사작품 비교군 통계
        |
        v
[같은 작가 안에서 가장 비슷한 과거 작품으로 기준가격 생성]
  - 먼저 확인: 같은 작가 + 비슷한 재료/지지체 + 비슷한 크기
  - 없으면 확인: 같은 작가 + 비슷한 크기
  - 그래도 없으면 확인: 같은 작가 전체 과거 작품
  - 여기서 "1건부터 사용"은 Warm 대상 작가(전체 이력 5건 이상) 안에서 비슷한 과거 작품이 1건만 있어도 참고한다는 뜻
  - 1~4건 이력 작가를 Warm으로 보내는 뜻은 아님. 1~4건 작가는 계속 Warm-lite 대상
  - 검증할 때는 예측 대상 작품 자기 자신을 비교군에서 빼고 계산. 빼고 나서 비교군이 0건이면 다음 후보로 내려감
        |
        v
[보조안정_Warm예측로그가격 생성]
  - 목적: 같은 작가 유사작품 기준가격이 소표본 때문에 과하게 흔들리지 않도록 보조 기준을 만든다
  - 예측 시점에는 새로 학습하지 않고, 이미 동결된 두 예측 축을 적용한다

  [축 A: 큰오차방어_Warm예측로그가격]
    - 내부명: V2_방어형후보_로그가격
    - 입력: 기본 Huber, L8/L9 순차보정, D4 블렌드, R5 p95/MAPE 방어, 작가이력 라우팅, 유사작품 fallback, U1 확장 후보 등 여러 Warm 후보 예측값
    - 파생 입력: 후보 평균, 후보 표준편차, 후보 범위, 기준후보와의 차이, 불확실성 폭
    - 처리: Huber meta-model이 방어형 중심 로그가격을 예측하고, 하위 후보 범위에서 과도하게 벗어나지 않도록 clip
    - 출력: clip까지 적용된 방어형 중심 로그가격. 다음 단계에서 보조안정_Warm예측로그가격의 75% 축으로 사용

  [축 B: 버킷순차보정_Warm예측로그가격]
    - 입력: 작품 크기/형태/매체/지지체/작가 식별 피처
    - bucket 생성: 크기/형태/재료 조합을 size_bucket, shape_bucket, support_size_bucket, medium_shape_bucket으로 구간화
    - 의미 구분: bucket은 4개 피처 묶음이고, 아래 1/2/3은 그 bucket 피처가 들어가는 처리 순서
    - 처리 단계 1: 원본 작품 피처 + bucket 피처를 CatBoost Quantile에 넣어 q10_log, q50_log, q90_log, Quantile예측구간폭 생성
    - 처리 단계 2: 원본 작품 피처 + bucket 피처 + Quantile 피처를 Huber 중심선에 넣어 중심 로그가격 계산
    - 처리 단계 3: 원본 작품 피처 + bucket 피처 + Quantile 피처 + Huber 중심선을 CatBoost 잔차 모델에 넣어 남은 오차 예측
    - 출력: Huber 중심선 로그가격 + CatBoost 잔차보정. 다음 단계에서 보조안정_Warm예측로그가격의 25% 축으로 사용

  보조안정_Warm예측로그가격
    = PPV8_안정블렌드_로그가격
    = 0.75 * 큰오차방어_Warm예측로그가격
      + 0.25 * 버킷순차보정_Warm예측로그가격
        |
        v
[기준 로그가격 = 두 가격 신호를 가중 평균]
  - 기본 후보(w700): 0.70 * 같은작가_유사작품기준로그가격 + 0.30 * 보조안정_Warm예측로그가격
  - 대안 후보(w850): 0.85 * 같은작가_유사작품기준로그가격 + 0.15 * 보조안정_Warm예측로그가격
        |
        v
[Huber 잔차 보정]
  - 비교군/보조 안정 Warm 예측값/수축값/구간폭 10개 피처로 남은 잔차를 작게 보정
  - 기본 후보와 대안 후보 각각 적용
        |
        v
[작품 단위 위험도 계산]
  - Quantile예측구간폭, 후보예측분산, 기준-안정기준차이, 신뢰도, 가격대를 가중합
        |
        v
[위험도 조건부 라우터]
  - 작품단위위험도 >= 위험도임계값(0.2534165869)
  - 기본후보_보정로그가격 - 대안후보_보정로그가격 >= 대안교체최소차이(0.005 log)
  - 두 조건이 모두 통과하면 대안 후보로 교체
  - 그 외에는 기본 후보 유지
        |
        v
[최종 Warm 로그가격]
        |
        v
[최종 Warm 가격 = exp(최종 Warm 로그가격)]
```

- 학습 단계와 사용 단계의 차이: 학습 단계에서는 실제 가격으로 잔차 target을 만들고 validation으로 위험도임계값과 대안교체최소차이를 고른다. 사용 단계에서는 실제 가격을 모르므로, 동결된 비교군 통계 규칙과 보조 예측축, 잔차 보정 모델, 라우터 조건만 적용한다
- 핵심 변경 (2026-06-13, WMIN8 후보): 이전 Warm 기준선(방향 분류 + 미세 보정)과 달리, Warm 안에서 대상 작품과 비슷한 같은 작가 과거 작품을 1건부터 참고하도록 바꿔 기준가격 근거를 더 많이 활용한다. 위험한 작품에만 보수적 대안 가중으로 조건부 교체하며, 이 변화는 라우팅 기준 변경이 아니므로 1~4건 작가는 계속 Warm-lite로 간다
- 정밀 비교군 매칭률: 최소 표본 1 기준 `81.9%` (WMIN2 fixed test 작품 기준). `40.7%` 후보 수치는 직접 커버리지 artifact가 확인되지 않았고 `PP-K3`(별도 Warm 실험)의 MAPE `0.4073`과 혼동 가능성이 있어 본문 비교 지표에서 제외함

### 4.3 Warm 사용 피처

- Warm 기준가격 생성층: Warm 대상(작가 전체 이력 5건 이상) 안에서 대상 작품과 가장 비슷한 같은 작가 과거 작품을 찾고, 그 비교군이 1건만 있어도 기준 로그가격 계산에 사용
- Warm 잔차 보정층: 비교군/보조 안정 Warm 예측값/수축 prior/구간폭 차이를 입력으로 받아 남은 잔차를 작게 보정
- Warm 라우터층: 작품 단위 위험도와 기본/대안 후보 차이를 보고 어느 후보를 쓸지 결정
- 작가 정보 반영 방식: 작가키는 유사작품 비교군 매칭에 사용되며, 이력 5건 이상 작가만 이 경로로 들어옴

#### 4.3.1 Warm 유사작품 찾기 단계 (최소 표본 1)

| 우선순위 | 비교군 그룹 | 최소 표본 | 의미 |
|---|---|---:|---|
| 1 | 작가 + 재료/지지체 + 크기 구간 | 1 | 같은 작가, 비슷한 재료/지지체, 비슷한 크기 |
| 2 | 작가 + 크기 구간 | 1 | 같은 작가, 비슷한 크기 |
| 3 | 작가 전체 이력 | 1 | 같은 작가 전체 거래 이력 |
| 4 | 재료/지지체 + 크기 (작가 무관) | 30 | 작가 비교군이 비면 사용하는 일반 비교군 |
| 5~7 | 재료/크기 일반 그룹, 전체 학습 데이터 | 30~50 / 제한 없음 | 최종 fallback |

- 이전 Warm 기준선과의 차이: 예전에는 `같은 작가 + 비슷한 조건` 비교군도 5건 이상 있어야 그 그룹을 썼지만, 현재는 1건만 있어도 쓴다. 단, Warm에 들어오는 조건은 여전히 작가 전체 가격 이력 5건 이상이다. 작가 전체 이력이 1~4건이면 Warm이 아니라 Warm-lite로 간다
- 자기 가격 사용 방지: 검증에서는 예측하려는 작품 자기 자신을 비교군에서 제외한다. 제외 후 1순위 비교군이 0건이면 2순위로, 2순위도 0건이면 3순위로 내려간다. 내부 점검 실험(WMIN2)에서 이 동작을 행별로 확인했다

#### 4.3.2 Warm 잔차 보정 입력 피처

| 문서용 이름 | 내부 컬럼명 | 의미 |
|---|---|---|
| `보조안정_Warm예측로그가격` | `pp_v8_compact_blend_mape_guarded_pred_log` (fallback: `ppv8_defensive`) | 작품 크기, 매체/지지체, 작가 이력, 유사작품 통계로 만든 보조 Warm 예측 로그가격. 큰오차방어 Warm 예측값 75%와 버킷순차보정 Warm 예측값 25%를 섞은 값이며, 같은 작가 유사작품 비교군이 좁을 때 기준가격이 과하게 흔들리지 않도록 일부 섞는 안정화 기준 |
| `유사작품fallback값` | `svc_fallback` | 최소 표본 1 유사작품 비교군 통계 기반 예측값 |
| `수축Huber보정값` | `shrunk_huber_refit` | 소표본 비교군 중앙값을 상위 그룹으로 수축한 뒤 만든 Huber 예측값 |
| `수축유사작품prior` | `shrunk_svc_prior` | 수축 처리한 유사작품 비교군 prior |
| `로그면적` | `log_area` | 작품 면적의 로그값 |
| `비교군표본수로그` | `svc_group_n_log` | 유사작품 비교군 표본 수의 로그값 |
| `비교군가격IQR` | `svc_prior_iqr` | 유사작품 비교군 가격 사분위 범위 |
| `현재-보조안정예측차이` | `current_ppv8_gap` | 현재 기준가격과 보조 안정 Warm 예측 로그가격의 차이 |
| `현재-수축Huber차이` | `current_shrunk_huber_gap` | 기준가격과 수축 Huber 값의 차이 |
| `원본-수축prior차이` | `raw_shrunk_prior_gap` | 원본 prior와 수축 prior의 차이 |

#### 4.3.3 보조안정 Warm 예측값 생성 흐름

`보조안정_Warm예측로그가격`은 Warm 계산 중간에 갑자기 생기는 단순 산식값이 아니다. 문서 변수 기준으로는 `PPV8_안정블렌드_로그가격`이며, 이미 학습·동결된 두 예측 축을 로그가격 단위에서 섞어 만든 보조 기준이다.

```text
보조안정_Warm예측로그가격
  = PPV8_안정블렌드_로그가격
  = 0.75 * 큰오차방어_Warm예측로그가격
    + 0.25 * 버킷순차보정_Warm예측로그가격
```

- 큰오차방어 Warm 예측값: `V2_방어형후보_로그가격`이다. 기본 Huber, L8/L9 순차보정, D4 블렌드, R5 p95/MAPE 방어, 작가이력 라우팅, 유사작품 fallback, U1 확장 후보처럼 이미 만들어진 Warm 후보 예측값을 다시 입력으로 쓰는 Huber meta-stacking 결과다
- 버킷순차보정 Warm 예측값: `L10_생성버킷_순차보정_로그가격`이다. 작품 크기·형태·매체/지지체를 bucket으로 나누고, Quantile 모델과 Huber 중심선, CatBoost 잔차 보정을 순서대로 적용해 만든 예측값이다
- 예측 시점에는 새로 학습하지 않는다. 학습된 Quantile/Huber/CatBoost 모델과 동결된 bucket 규칙을 적용해 값을 계산한다
- 같은 작가 이력 5건 이상은 Warm 최종 경로의 라우팅 조건이다. 버킷순차보정 값 자체가 5건을 요구한다는 뜻은 아니지만, 현재 최종 Warm 모델에서는 5건 이상 Warm 경로 안에서만 보조 축으로 사용된다

큰오차방어 Warm 예측값은 다음 흐름으로 만들어진다.

```text
[하위 Warm 후보 예측값]
  - 기본_Huber_로그가격
  - L8_순차보정_로그가격, L9_순차보정_로그가격
  - D4_블렌드_로그가격
  - R5_p95방어_로그가격, R5_MAPE방어_로그가격
  - 작가이력_라우팅_로그가격
  - 유사작품_fallback_로그가격
  - U1_생성버킷확장_로그가격, U1_작가크기작품수_로그가격
        |
        v
[meta feature 생성]
  - 예측값_평균 = mean(하위후보_예측로그가격들)
  - 예측값_표준편차 = std(하위후보_예측로그가격들)
  - 예측값_범위 = max(하위후보) - min(하위후보)
  - 기준후보와의_차이_j = 하위후보_j - 기준후보
  - 불확실성_폭 = routing_width
        |
        v
[Huber meta-model]
  - 하위 후보 예측값과 meta feature를 입력으로 방어형 로그가격을 예측
        |
        v
[component range clipping]
  - clip(V2_raw_로그가격, 하위후보_최소값 - 0.03, 하위후보_최대값 + 0.03)
        |
        v
[큰오차방어_Warm예측로그가격]
  - 이 값이 보조안정_Warm예측로그가격의 75% 축으로 들어감
```

여기서 `clip`은 임의로 낮추거나 올리는 장치가 아니라, meta-model 출력이 입력으로 사용한 하위 Warm 후보들의 범위에서 과도하게 벗어나는 것을 막는 외삽 방어다. 따라서 큰오차방어 축은 "새 원본 피처 하나로 가격을 맞히는 블랙박스"가 아니라, 여러 Warm 후보가 서로 얼마나 동의하거나 벌어지는지를 보고 안정적인 중심값을 고르는 2단계 예측 축이다.

버킷순차보정 Warm 예측값은 내부적으로 다음 순서로 만들어진다.

```text
[작품 기본 피처]
  - width_cm, height_cm, area_cm2, log_area
  - medium_category, support_category, artist_key
        |
        v
[생성 bucket 피처]
  - size_bucket, shape_bucket
  - support_size_bucket, medium_shape_bucket
  - is_large_2d, is_large_3d
  - 이후 Quantile, Huber 중심선, CatBoost 잔차 보정에 계속 입력으로 사용
        |
        v
[CatBoost Quantile 예측]
  - 입력: 작품 기본 피처 + 생성 bucket 피처 + 작가 식별/학습량 피처
  - q10_log, q50_log, q90_log
  - quantile_width = q90_log - q10_log
        |
        v
[Huber 중심선]
  - 입력: 작품 기본 피처 + 생성 bucket 피처 + Quantile 피처
  - 출력: 안정적인 중심 로그가격
        |
        v
[CatBoost 잔차 보정]
  - 입력: 작품 기본 피처 + 생성 bucket 피처 + Quantile 피처 + Huber 중심선
  - 출력: Huber 중심선에서 남은 오차 보정값
        |
        v
[버킷순차보정_Warm예측로그가격]
  = Huber 중심선 로그가격 + CatBoost 잔차보정
  - 이 값이 보조안정_Warm예측로그가격의 25% 축으로 들어감
```

버킷순차보정 안에서 피처는 단계별로 다음처럼 사용된다.

| 피처 묶음 | 예시 피처 | 사용 단계 | 역할 |
|---|---|---|---|
| 작품 크기 피처 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio` | bucket 생성, Quantile, Huber 중심선, CatBoost 잔차 보정 | 크기와 형태에 따른 기본 가격 차이를 반영 |
| 입체/형태 피처 | `has_depth`, `is_3d_candidate`, `is_extreme_aspect_ratio` | bucket 생성, Quantile, Huber 중심선, CatBoost 잔차 보정 | 평면/입체 여부와 극단 비율 작품의 가격 차이를 반영 |
| 매체/지지체 피처 | `medium_category`, `support_category`, `medium_support_bucket` | bucket 생성, Quantile, Huber 중심선, CatBoost 잔차 보정 | oil/canvas, acrylic/paper처럼 재료 조합별 가격 패턴 반영 |
| 작가 식별/학습량 피처 | `artist_key`, `artist_works_log`, `artist_works_count_train` | Quantile, Huber 중심선, CatBoost 잔차 보정 | 작가별 가격 수준과 학습 데이터 내 작가 표본량 차이를 반영 |
| 생성 bucket 피처 | `size_bucket`, `shape_bucket`, `support_size_bucket`, `medium_shape_bucket`, `is_large_2d`, `is_large_3d` | Quantile, Huber 중심선, CatBoost 잔차 보정 | 연속값인 크기·형태를 모델이 쓰기 쉬운 구간 신호로 변환 |
| Quantile 예측값 | `q10_log`, `q50_log`, `q90_log` | Huber 중심선, CatBoost 잔차 보정 | 낮은쪽/중앙/높은쪽 가격 후보를 제공 |
| Quantile 파생값 | `quantile_width`, `price_range_ratio` | Huber 중심선, CatBoost 잔차 보정 | 가격 예측의 불확실성 폭을 반영 |
| Huber OOF 중심선 | `L10_Huber_OOF_중심선_로그가격` | 학습 단계의 잔차 target 생성 | 실제 로그가격에서 중심선을 뺀 잔차를 만들어 CatBoost가 남은 오차만 학습하게 함 |
| 실제 로그가격 | `actual_log` | 학습 단계에서만 사용 | 잔차 target 계산과 성능 평가에만 사용. 운영 예측 입력으로는 사용하지 않음 |

단계별로 다시 풀면 다음과 같다.

```text
1. 작품 크기/형태/매체/지지체 피처
   -> 생성 bucket 피처를 만든다.

2. 작품 피처 + 생성 bucket + 작가 식별/학습량 피처
   -> CatBoost Quantile이 q10/q50/q90을 예측한다.

3. 작품 피처 + 생성 bucket + q10/q50/q90 + quantile_width
   -> Huber 중심선이 안정적인 중심 로그가격을 계산한다.

4. 학습 때:
   실제_로그가격 - Huber_OOF_중심선_로그가격
   -> CatBoost 잔차 모델의 target으로 사용한다.

5. 사용 단계에서:
   작품 피처 + 생성 bucket + Quantile 피처 + Huber 중심선
   -> 동결된 CatBoost 잔차 모델이 잔차보정값을 예측한다.

6. Huber 중심선 로그가격 + CatBoost 잔차보정값
   -> 버킷순차보정_Warm예측로그가격

7. 버킷순차보정_Warm예측로그가격
   -> 보조안정_Warm예측로그가격을 만들 때 25% 축으로 들어간다.
```

학습 단계와 사용 단계(예측 단계)는 반드시 구분해서 봐야 한다.

```text
[학습 단계]
1. 학습 작품의 기본 피처와 생성 bucket 피처를 만든다.
2. CatBoost Quantile 모델 3개가 q10/q50/q90 로그가격을 학습한다.
3. q90_log - q10_log로 Quantile예측구간폭을 만든다.
4. 기본 피처 + bucket 피처 + Quantile 피처를 넣고 Huber 중심선을 학습한다.
5. 학습 데이터에서 Huber OOF 예측을 만든다.
6. 실제 로그가격 - Huber OOF 중심선 로그가격을 잔차 target으로 둔다.
7. CatBoost 잔차 모델이 이 잔차 target을 학습한다.
8. bucket 규칙, Quantile 모델, Huber 중심선, CatBoost 잔차 모델을 동결한다.

[사용 단계 / 예측 단계]
1. 새 작품의 기본 피처와 생성 bucket 피처를 만든다.
2. 동결된 CatBoost Quantile 모델로 q10/q50/q90을 예측한다.
3. 동결된 Huber 중심선 모델로 중심 로그가격을 계산한다.
4. 동결된 CatBoost 잔차 모델로 보정해야 할 잔차를 예측한다.
5. 버킷순차보정_Warm예측로그가격 = Huber 중심선 로그가격 + 예측 잔차보정값
```

여기서 `Huber 중심선`은 최종 가격을 단독으로 결정하는 값이 아니라, 먼저 안정적인 중심 가격을 잡는 기준선이다. Huber loss는 큰 오차 작품의 영향을 완만하게 처리하므로, 일부 비정상 고가/저가 작품이 있어도 중심선이 과도하게 끌려가지 않도록 한다.

`CatBoost 잔차 보정`은 이 중심선에서 반복적으로 남는 오차를 학습한 보정 모델이다. 학습 때는 `실제_로그가격 - Huber_OOF_중심선_로그가격`을 target으로 사용하지만, 예측 때는 실제 가격을 알 수 없으므로 저장된 CatBoost 모델이 피처만 보고 잔차 보정값을 예측한다. `OOF` 예측을 쓰는 이유는 Huber 중심선이 학습 행을 직접 본 상태에서 잔차를 계산하면 보정 모델이 과하게 좋은 잔차를 학습할 수 있기 때문이다.

의문이 생기기 쉬운 부분은 다음처럼 해석한다.

| 질문 | 해석 |
|---|---|
| 버킷순차보정은 고정 산식인가? | 아니다. bucket을 만드는 규칙은 고정되어 있지만, q10/q50/q90, Huber 중심선, CatBoost 잔차 보정은 학습된 모델 출력이다 |
| 예측할 때도 CatBoost를 새로 학습하는가? | 아니다. 학습은 과거 데이터에서 끝났고, 예측 시점에는 동결된 CatBoost 모델을 적용만 한다 |
| 잔차 보정은 실제 가격을 알아야 가능한가? | 실제 가격은 학습 때 residual target을 만들 때만 사용한다. 운영 예측에서는 실제 가격 없이 피처만으로 잔차를 예측한다 |
| Huber 중심선은 왜 필요한가? | 먼저 안정적인 중심 가격을 잡아 CatBoost가 전체 가격을 처음부터 맞히는 부담을 줄이고, CatBoost는 남은 오차 패턴만 보정하게 하기 위해서다 |
| Quantile q10/q90은 최종 가격인가? | 아니다. 가격 분포의 낮은쪽/높은쪽 후보로 불확실성 폭을 만들고, Huber와 CatBoost 잔차 보정의 입력으로 사용한다 |
| 5건 이상 이력이 버킷순차보정의 필수 조건인가? | 아니다. 5건 이상은 최종 Warm 경로의 라우팅 조건이고, 버킷순차보정 값 자체는 피처와 동결 모델로 계산된다 |
| 버킷순차보정이 최종 Warm 가격을 직접 정하는가? | 아니다. 보조안정 Warm 예측값의 25% 축이고, 그 보조안정 값도 다시 기본/대안 기준가격에 일부만 섞인다 |

따라서 Warm 전체 구조는 단일 예측 모델 하나가 바로 가격을 내는 방식이 아니라, `같은작가 유사작품 기준가격`을 중심으로 두고 `큰오차방어`, `버킷순차보정`, `Huber 잔차 보정`, `위험도 라우터`를 단계적으로 결합하는 조건부 앙상블 구조로 해석하는 것이 정확하다.

#### 4.3.4 Warm 위험도 입력 피처

| 문서용 이름 | 내부 컬럼명 | 위험도 반영 방식 |
|---|---|---|
| `Quantile예측구간폭` | `quantile_width` | 폭이 1.20을 넘는 정도를 0~1로 환산 (가중 0.38) |
| `후보예측분산` | `component_prediction_spread` | 0.18 기준 정규화 (가중 0.22) |
| `현재-안정기준차이` | `current_vs_stable_gap_abs` | 0.06 기준 정규화 (가중 0.14) |
| `신뢰도구간` | `confidence_tier` | 저신뢰면 가산 (가중 0.16) |
| `안정기준가격대` | `stable_price_band` | 초고가 구간이면 가산 (가중 0.10) |

### 4.4 Warm 모델과 산식

- Warm WMIN8 후보 모델의 순차 구성:

| 단계 | 역할 | 모델/방법 |
|---|---|---|
| 비교군 기준가격 | 같은 작가의 비슷한 과거 작품을 1건부터 참고해 기준 로그가격 생성 | 같은작가 유사작품 기준 로그가격 (내부명: svc_numeric/min1 계열) |
| 가중 혼합 | 같은 작가 유사작품 가격 신호와 보조 안정 Warm 예측값을 가중 평균 | 기본 후보 w700(유사작품 70%) / 대안 후보 w850(유사작품 85%) |
| 잔차 보정 | 남은 잔차를 작게 보정 | Huber 잔차 모델 (10개 피처) |
| 위험도 라우터 | 위험한 작품만 보수적 대안으로 교체 | 위험도임계값 + 대안교체최소차이 |

- 1단계 — 비교군 가중 기준가격:

```text
같은작가_유사작품기준로그가격
  = Warm 대상 작가 안에서 대상 작품과 비슷한 과거 작품을 찾아 만든 기준 로그가격
  # 비슷한 과거 작품은 1건만 있어도 참고하지만,
  # Warm 대상 자체는 여전히 작가 전체 이력 5건 이상이어야 함

보조안정_Warm예측로그가격
  = PPV8_안정블렌드_로그가격
  = 0.75 * 큰오차방어_Warm예측로그가격
    + 0.25 * 버킷순차보정_Warm예측로그가격

큰오차방어_Warm예측로그가격
  = 여러 Warm 후보 예측값과 후보 간 평균/표준편차/범위/불확실성 폭을 입력으로 한 Huber meta-stacking 예측값

버킷순차보정_Warm예측로그가격
  = 생성 bucket 피처와 Quantile/Huber/CatBoost 순차 모델로 만든 Warm 예측값

기본후보_기준가 = 0.70 * 같은작가_유사작품기준로그가격 + 0.30 * 보조안정_Warm예측로그가격
대안후보_기준가 = 0.85 * 같은작가_유사작품기준로그가격 + 0.15 * 보조안정_Warm예측로그가격
```

- `같은작가_유사작품기준로그가격`은 내부 실험/컬럼명으로는 `min1` 또는 `svc_numeric` 계열에 해당한다. 문서 산식에서는 라우팅 기준과 혼동을 줄이기 위해 의미 중심 이름을 사용한다
- 기본 후보의 `0.70`은 WMIN2의 `min1_70_30_basis` 구조를 WMIN3 Huber 재적합과 WMIN4 운영 결정 검증으로 통과시킨 값이다. 즉 현재 Warm의 기본 출발점은 "같은 작가 유사작품 기준가격 70% + 보조 안정 Warm 예측값 30%"이다
- 대안 후보의 `0.85`는 WMIN7에서 `0.50~0.90` 범위의 유사작품 기준가격 가중 후보를 비교한 뒤, WMIN8 라우터 검증에서 `min1_w850_huber_refit_partial`이 위험 구간의 대안 후보로 선택된 값이다
- `큰오차방어_Warm예측로그가격`은 원본 피처만 넣은 단일 모델이 아니라, 여러 Warm 후보 예측값을 다시 입력으로 쓰는 방어형 2단계 예측값이다. 세부 흐름은 4.3.3절의 `V2_방어형후보_로그가격` 설명을 따른다
- `버킷순차보정_Warm예측로그가격`은 단순한 규칙값이 아니라 학습된 모델 파이프라인의 출력이다. `size_bucket`, `shape_bucket`, `support_size_bucket`, `medium_shape_bucket` 같은 생성 bucket을 만든 뒤 CatBoost Quantile로 가격 분포를 보고, Huber로 중심 가격을 잡고, CatBoost 잔차 모델로 남은 오차를 보정해 만든다
- 위 식의 뜻은 "같은 작가의 비슷한 작품 가격 신호를 주로 보되, 별도로 만든 보조 Warm 예측값을 일부 섞어 기준가격이 과하게 흔들리지 않게 한다"이다

말로 풀면:

```text
기본 기준가격 =
  같은 작가의 비슷한 작품 가격 신호 70%
  + 보조 안정 Warm 예측값 30%

대안 기준가격 =
  같은 작가의 비슷한 작품 가격 신호 85%
  + 보조 안정 Warm 예측값 15%
```

- 2단계 — Huber 잔차 보정 (각 후보별):

```text
잔차예측 = Huber잔차모델(10개 피처)
보정후보_로그가격 = 후보_기준가 + 0.50 * clip(잔차예측, -0.05, +0.05)
```

- `clip`은 계산값이 하한보다 작으면 하한으로, 상한보다 크면 상한으로 제한하는 함수다. 여기서는 Warm의 주 신호인 같은 작가 이력 기반 기준가격을 보호하기 위해 사용한다. 잔차 모델의 예측값을 그대로 더하면 일부 표본이 적거나 유사작품 구성이 흔들리는 작품에서 기준가격을 과도하게 뒤집을 수 있으므로, 잔차 예측값을 먼저 -0.05~+0.05 log로 제한한 뒤 그 절반만 반영한다. 최종 적용 보정폭은 최대 -0.025~+0.025 log다.

- 보정 강도와 상한은 PP-HCOEF3 반복 검증에서 통과한 안정 설정 `hcoef2_size_reliability_cap005_s050`을 사용한다. 여기서 `alpha=0.01`은 잔차 모델의 규제 강도, `cap=0.05`는 잔차예측 제한폭, `strength=0.50`은 제한된 잔차예측값의 반영 비율을 뜻함

- 3단계 — 작품 단위 위험도:

```text
작품단위위험도
  = clip(
      0.38 * clip((Quantile예측구간폭 - 1.20) / 0.95, 0, 1)
      + 0.22 * clip(후보예측분산 / 0.18, 0, 1)
      + 0.14 * clip(현재-안정기준차이 / 0.06, 0, 1)
      + 0.16 * (신뢰도구간 == 저신뢰)
      + 0.10 * (안정기준가격대 == 초고가),
      0,
      1
    )
```

- 4단계 — 위험도 조건부 라우터:

```text
위험도임계값 = validation risk_score 중앙값(q50) = 0.2534165869
대안교체최소차이 = 0.005 log

대안교체조건 =
  작품단위위험도 >= 위험도임계값
  and (기본후보_보정로그가격 - 대안후보_보정로그가격) >= 대안교체최소차이

근거:
  - PP-WMIN8 `min1_route_w850_risk_q50_altlower_gap005` 선택
  - risk_q50: validation risk_score 중앙값
  - altlower_gap005: 대안교체최소차이 0.005 log 조건

최종_Warm_로그가격
  = 대안후보_보정로그가격  if 대안교체조건
  = 기본후보_보정로그가격  otherwise

최종_Warm_가격_KRW = exp(최종_Warm_로그가격)
```

- 라우터의 의미: 기본은 유사작품 가중 0.70 기준가격을 쓰되, 예측 위험도가 높고 더 보수적인 가중 0.85 후보가 기본 후보보다 `0.005` 로그 이상 낮게 예측할 때만 대안으로 교체해 큰 오차를 방어
- 대안 후보가 0.85 가중인 이유: 위험한 작품에서는 보조 안정 Warm 예측값의 비중을 줄이고, 같은 작가 유사작품 비교군 신호를 더 신뢰하는 편이 큰 오차를 줄임

#### 4.4.1 Warm 피처-계산 연결 순서도

```text
[입력 피처]
  - artist_key
  - medium/support/size_bucket
  - width_cm, height_cm, area_cm2, log_area
        |
        v
[같은 작가 유사작품 비교군 매칭]
  - 작가+재료/지지체+크기
  - 작가+크기
  - 작가 전체
        |
        v
[비교군 통계 피처]
  - 같은작가_유사작품기준로그가격
  - 비교군표본수로그
  - 비교군가격IQR
        |
        v
[보조 안정 Warm 예측값 생성]
  - 큰오차방어_Warm예측로그가격
  - 버킷순차보정_Warm예측로그가격
    = 생성 bucket -> Quantile -> Huber 중심선 -> CatBoost 잔차보정
  - 보조안정 = 0.75 * 큰오차방어 + 0.25 * 버킷순차보정
        |
        v
[기본/대안 기준가격 생성]
  - 기본후보_기준가 = 0.70 * 같은작가_유사작품기준로그가격 + 0.30 * 보조안정_Warm예측로그가격
  - 대안후보_기준가 = 0.85 * 같은작가_유사작품기준로그가격 + 0.15 * 보조안정_Warm예측로그가격
        |
        v
[Huber 잔차 보정 피처]
  - 기준가격과 보조 안정 Warm 예측값/수축값의 차이
  - log_area
  - 비교군표본수로그, 비교군가격IQR
        |
        v
[후보별 보정 로그가격]
  - 기본후보_보정로그가격
  - 대안후보_보정로그가격
        |
        v
[위험도 피처]
  - Quantile예측구간폭
  - 후보예측분산
  - 현재-안정기준차이
  - 신뢰도구간
  - 안정기준가격대
        |
        v
[위험도 조건부 라우터]
  - 작품단위위험도가 위험도임계값(0.2534165869) 이상인지 확인
  - 기본후보_보정로그가격 - 대안후보_보정로그가격이 대안교체최소차이(0.005 log) 이상인지 확인
  - 두 조건이 모두 통과하면 대안 후보, 아니면 기본 후보 선택
        |
        v
[최종 Warm 로그가격 -> exp() -> 원화 예측가격]
```

#### 4.4.2 Warm 계산 예시

> 아래 숫자는 계산 흐름을 설명하기 위한 예시이며, 실험 성능 지표나 특정 운영 작품의 실제 예측값이 아니다.

```text
입력 상황:
  작가 매칭 신뢰도 = 0.92
  같은 작가 사용 가능 이력 = 12건
  작품 = oil/canvas, 100cm x 80cm
  log_area = log(8000) = 8.987

1) 라우팅:
  작가 매칭 신뢰도 0.92 >= 0.80
  같은 작가 사용 가능 이력 12건 >= 5건
  따라서 Warm 경로 진입

2) 유사작품 비교군 선택:
  전체 같은 작가 이력 = 12건

  1순위 조건 확인:
    같은 작가 + oil/canvas + 비슷한 크기 구간
    자기 fold 제외 후 남은 비교 작품 = 3건

  1순위에서 1건 이상 발견됐으므로 이 비교군을 사용
  2순위(같은 작가+크기), 3순위(작가 전체), 일반 fallback은 사용하지 않음

3) 비교군 통계 계산:
  선택된 3건의 로그가격 예시 = [18.100, 18.300, 18.500]

  같은작가_유사작품기준로그가격 = median([18.100, 18.300, 18.500]) = 18.300
  비교군표본수로그 = log1p(3) = 1.386
  비교군가격IQR = 18.400 - 18.200 = 0.200

4) 보조 안정 Warm 예측값 계산:
  큰오차방어 내부 계산:
    하위 Warm 후보 예측 로그가격 예시 =
      기본_Huber 18.420
      L8_순차보정 18.550
      L9_순차보정 18.490
      R5_p95방어 18.610
      유사작품_fallback 18.360

    meta feature:
      후보평균 = 18.486
      후보범위 = 18.610 - 18.360 = 0.250
      기준후보와의 차이들 = 각 후보 - 기본_Huber
      불확실성폭 = 동결 파이프라인에서 계산된 routing_width

    Huber meta-model raw 예측 = 18.500
    하위후보 clip 범위 = [18.360 - 0.030, 18.610 + 0.030] = [18.330, 18.640]
    큰오차방어_Warm예측로그가격 = clip(18.500, 18.330, 18.640) = 18.500

  버킷순차보정 내부 계산:
    입력 피처:
      width_cm 100, height_cm 80, area_cm2 8,000, log_area 8.987
      medium_category oil, support_category canvas, artist_key 존재
      artist_works_count_train 12, artist_works_log = log1p(12) = 2.565

    생성 bucket 피처:
      size_bucket 중형
      shape_bucket 균형형
      support_size_bucket canvas_중형
      medium_shape_bucket oil_균형형

    CatBoost Quantile 예측 = q10_log 17.700, q50_log 18.250, q90_log 18.900
    Quantile예측구간폭 = 18.900 - 17.700 = 1.200

    Huber 중심선 입력:
      입력 피처 + 생성 bucket 피처 + q10/q50/q90 + Quantile예측구간폭
    Huber 중심선 로그가격 = 18.260

    CatBoost 잔차 모델 입력:
      입력 피처 + 생성 bucket 피처 + q10/q50/q90 + Quantile예측구간폭
    CatBoost 잔차보정 = +0.040
      - 이 값은 학습 때 실제_로그가격 - Huber_OOF_중심선_로그가격을 target으로 학습한 잔차 모델의 예측값
      - 예측 시점에는 실제 가격을 쓰지 않고, 작품 피처와 Quantile 피처만으로 +0.040을 예측
    버킷순차보정_Warm예측로그가격 = 18.260 + 0.040 = 18.300

  보조안정_Warm예측로그가격
    = 0.75 * 18.500 + 0.25 * 18.300
    = 18.450

5) 기준가격 후보 2개 생성:
  기본후보_기준가 = 0.70 * 18.300 + 0.30 * 18.450 = 18.345
  대안후보_기준가 = 0.85 * 18.300 + 0.15 * 18.450 = 18.323

6) Huber 잔차 보정:
  기본후보 잔차예측 = +0.020
  기본후보 보정값 = 0.50 * clip(+0.020, -0.05, +0.05) = +0.010
  기본후보_보정로그가격 = 18.355

  대안후보 잔차예측 = +0.016
  대안후보 보정값 = 0.50 * clip(+0.016, -0.05, +0.05) = +0.008
  대안후보_보정로그가격 = 18.331

7) 작품 단위 위험도 계산:
  Quantile예측구간폭 = 1.65
  후보예측분산 = 0.08
  현재-안정기준차이 = 0.03
  신뢰도구간 = 표준 또는 고신뢰
  안정기준가격대 = 초고가 아님

  Quantile 폭 기여 = 0.38 * clip((1.65 - 1.20) / 0.95, 0, 1) = 0.180
  후보 분산 기여 = 0.22 * clip(0.08 / 0.18, 0, 1) = 0.098
  기준 차이 기여 = 0.14 * clip(0.03 / 0.06, 0, 1) = 0.070
  신뢰도 기여 = 0.000
  가격대 기여 = 0.000

  작품단위위험도 = 0.180 + 0.098 + 0.070 = 0.348
  위험도임계값 = 0.2534165869
  대안교체최소차이 = 0.005 log

8) 라우터 조건 검사:
  조건 A: 작품단위위험도 >= 위험도임계값
    0.348 >= 0.2534165869 이므로 통과

  조건 B: 기본 후보와 대안 후보의 차이가 대안교체최소차이 이상인가?
    기본후보_보정로그가격 - 대안후보_보정로그가격
      = 18.355 - 18.331
      = 0.024
    0.024 >= 대안교체최소차이(0.005 log) 이므로 통과

  조건 A와 조건 B가 모두 통과했으므로 대안후보 선택
  만약 둘 중 하나라도 실패했다면 기본후보_보정로그가격 18.355를 유지

최종:
  최종_Warm_로그가격 = 18.331
  최종_Warm_가격_KRW = exp(18.331) ~= 91,000,000원
```

### 4.5 Warm 성능 해석

- Warm fixed test 607건 기준 WMIN8 후보 성능:

| 지표 | 값 | 이전 Warm 기준선 대비 |
|---|---:|---:|
| MdAPE | 0.104326 | -0.036650 (-26%) |
| MAPE | 0.235814 | -0.034074 (-13%) |
| p95 APE | 0.739416 | -0.067909 (-8%) |
| RMSE log | 0.377190 | -0.020264 |

- validation OOF 519건 기준: MdAPE 0.094033 / MAPE 0.175114 / p95 APE 0.571291
- 반복 안정성: artist 그룹 holdout에서 이전 Warm 기준선 대비 MAPE 승률 1.000, p95 승률 0.988
- 2026-06-04 신규 라벨 스트레스 평가: WMIN4 min1 계열 선행 후보에서 이전 Warm 기준선 대비 명확한 악화 없음 (MAPE delta `-0.057663`, p95 delta `-0.084486`). 단, 이 평가는 WMIN8 선택용 직접 지표가 아니라 min1 비교군 확대의 선행 안전성 근거로만 해석
- 후보 adapter 통합 검증: 동결 번들과 실험 산출물의 예측 일치 (재현 max 로그 차이 5.3e-15)
- Warm 모델 해석: 유사작품 비교군 매칭을 최소 표본 1로 넓혀 정밀도를 크게 올리고, 위험한 작품만 보수적으로 방어하는 구조
- 대외 설명 권장 표현: `정밀 유사작품 비교군 기반 위험도 조건부 Warm 모델`

## 5. Warm-lite 모델 상세

> 이 절은 작가 매칭은 확실하지만 같은 작가 가격 이력이 1~4건뿐인 0.1v 적용 경로를 설명한다. Warm-lite는 Warm의 부속 설명이 아니라 현재 라우팅에서 Warm 5건 이상 경로와 분리된 별도 예측 경로다.

### 5.1 모델 목적

- 적용 대상: `작가매칭신뢰도점수 >= 0.80`이고 사용 가능한 같은 작가 가격 이력이 `1~4건`인 작품
- 분리 이유: 1~4건은 같은 작가 가격 신호가 존재하지만, 5건 이상 Warm처럼 정밀 비교군·위험도 라우터를 안정적으로 운영하기에는 표본이 작다
- 모델 구조: 서빙 시점에 매칭 작가의 1~4건 이력 통계를 만들고, LightGBM Quantile full/lean q50 평균을 기준 로그가격으로 만든 뒤 LightGBM Huber residual 보정을 clip 범위 안에서 더함
- 계산 관점: `저이력 작가 가격 통계 + 작품 크기/매체 피처 → Quantile 기준 로그가격 → clipped 잔차 보정`

핵심 처리는 다음과 같다.

- 작가 가격 이력 1~4건을 Cold보다 우선 사용
- 이력 수가 1건이면 예측 산식은 그대로 두고 `confidence_grade=warm_lite_low`, `display_policy=wide_range_with_review_flag`를 함께 반환
- 학습·검증에서는 자기 가격이 자기 피처에 들어가지 않도록 fold/leave-one-out 방식으로 작가 통계를 계산

### 5.2 Warm-lite 계산 순서도

Warm-lite는 학습 단계와 사용 단계를 분리해서 이해해야 한다. 학습 단계에서는 1~4건 작가 이력만 볼 수 있는 상황을 재현해 Quantile 기준가격 모델과 residual 보정 모델을 만든다. 사용 단계에서는 새 작품의 실제 가격을 알 수 없으므로, 동결된 모델에 작가 이력 통계와 작품 피처만 넣어 로그가격을 계산한다.

#### 5.2.1 Warm-lite 학습 단계 순서도

```text
[Warm-lite 학습/검증 데이터 구성]
  - 실제 로그가격이 있는 과거 작품
  - 같은 작가 이력을 1~4건만 볼 수 있는 저이력 상황을 재현
  - fold/leave-one-out으로 자기 가격이 자기 통계에 들어가지 않게 차단
        |
        v
[작가 이력 찾기 단계 정의]
  - 같은 작가 + 같은 매체/지지체 + 같은 크기 구간
  - 없으면 같은 작가 + 같은 크기 구간
  - 없으면 같은 작가 전체 1~4건
  - 예외적으로 통계 생성 실패 시 동결 fallback 통계 사용
        |
        v
[학습용 Warm-lite 피처 생성]
  - 작품 크기/면적/비율/입체 여부
  - 매체/지지체/크기 구간
  - 작가 로그가격 중앙값, q25/q75, IQR
  - 작가 면적단가 중앙값, 표본 수, 이력 매칭 단계
        |
        v
[LightGBM Quantile 모델 학습]
  - 전체 피처 기반 모델(full): q10/q50/q90을 학습해 가격 중심과 예측구간을 생성
  - 저표본 안정화 모델(lean): 저표본에서 흔들릴 수 있는 일부 q25/q75/IQR·분산 피처를 줄인 q50 모델
  - target: 실제 로그가격
  - 의미: 작가 이력 통계와 작품 피처로 저이력 작가의 기준 로그가격을 예측
        |
        v
[OOF Quantile 기준값과 잔차 생성]
  - fold/leave-one-out 예측으로 자기 가격 누수를 차단한 기준값 생성
  - Quantile평균로그가격 = 0.50 * full_q50 + 0.50 * lean_q50
  - 잔차 target = 실제 로그가격 - Quantile평균로그가격
        |
        v
[LightGBM Huber residual 보정 모델 학습]
  - 입력: Warm-lite 기본 피처 + q10/q50/q90 + Quantile예측구간폭 + Quantile평균로그가격
  - target: Quantile 기준값에서 남은 잔차
  - Huber objective: 큰 오차 한두 건에 과하게 끌려가지 않도록 잔차 보정층을 강건하게 학습
        |
        v
[검증 및 산식 동결]
  - PP-WLITE-Q1~Q5에서 Quantile 평균, residual 보정, bundle replay/API parity 검증
  - 채택 후보: qavg_lgbres_s05_cap010
        |
        v
[동결 산출물]
  - 작가 이력 통계 생성 규칙
  - LightGBM Quantile 전체 피처 기반(full) / 저표본 안정화(lean) 모델
  - LightGBM Huber residual 보정 모델
  - 최종 산식: Quantile평균로그가격 + clip(0.50 * residual, -0.10, +0.10)
  - 이력 1건/2~4건 신뢰도 표시 정책
```

#### 5.2.2 Warm-lite 사용 단계 순서도

```text
[Warm-lite 입력 작품]
  - 작가키 또는 고신뢰 작가 매칭 결과
  - 같은 작가 사용 가능 가격 이력 1~4건
  - 작품 크기/매체/지지체
        |
        v
[작가 이력 통계 생성]
  - 같은 매체·지지체 + 크기 구간 이력 우선 확인
  - 없으면 같은 크기 구간 이력
  - 없으면 작가 전체 1~4건 이력
  - 운영 사용 시 동결된 이력 store에서 확정된 같은 작가 가격 이력만 사용
        |
        v
[Warm-lite 피처 구성]
  - 작품 크기 피처: 가로/세로/깊이/면적/로그면적/비율/입체 여부
  - 작품 범주 피처: 매체, 지지체, 크기 구간
  - 작가 이력 피처: 로그가격 중앙값, 사분위, 면적단가 중앙값, 표본 수
        |
        v
[LightGBM Quantile 기준 로그가격]
  - 전체 피처 기반 full_q50: 작가 가격 q25/q75/IQR과 면적단가 분산까지 포함한 기준 로그가격
  - 저표본 안정화 lean_q50: 저표본 흔들림을 줄인 축약 입력 기준 로그가격
  - q10/q90/width: residual 보정과 불확실성 판단에 사용할 예측구간 피처
  - Quantile평균로그가격 = 0.50 * full_q50 + 0.50 * lean_q50
        |
        v
[LightGBM Huber residual 보정]
  - Quantile평균로그가격에서 남은 오차를 예측
  - 적용보정값 = clip(0.50 * residual, -0.10, +0.10)
  - 최종 Warm-lite 로그가격 = Quantile평균로그가격 + 적용보정값
        |
        v
[신뢰도 표시 정책]
  - 이력 1건: confidence_grade=warm_lite_low, display_policy=wide_range_with_review_flag
  - 이력 2~4건: confidence_grade=warm_lite_standard, display_policy=point_estimate_with_standard_range
        |
        v
[최종 Warm-lite 가격 = exp(최종 Warm-lite 로그가격)]
```

- 학습 단계와 사용 단계의 차이: 학습/검증 단계에서는 실제 로그가격을 target으로 Quantile 모델과 residual 보정 모델을 만들고, 자기 가격 누수를 막기 위해 fold/leave-one-out 통계를 쓴다. 사용 단계에서는 실제 가격 없이 작가 이력 통계와 작품 피처만 만들어 동결된 모델에 적용한다

### 5.3 Warm-lite 사용 피처

| 피처 구분 | 원천 또는 직접 입력 | 파생 피처 | 예측에서의 역할 |
|---|---|---|---|
| 작품 크기 | `width_cm`, `height_cm`, `depth_cm` 또는 크기 문자열 | `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate` | 작품 크기와 형태에 따른 가격 차이를 반영 |
| 작품 매체/지지체 | `medium`, `category` | `medium_category`, `support_category`, `size_bucket` | 매체·지지체·크기 구간별 가격 패턴 반영 |
| 작가 이력 수 | 매칭 작가의 사용 가능 가격 이력 수 | 모델 입력: `grp_n_log` / 출력: `artist_history_n`, `confidence_grade` | 예측에는 표본 수 로그를 쓰고, 예측 후 1건과 2~4건의 신뢰도 표시를 구분 |
| 작가 로그가격 통계 | 매칭 작가의 1~4건 가격 이력 | `artist_log_price_median`, `artist_log_price_q25`, `artist_log_price_q75`, `artist_log_price_iqr` | 저이력 작가의 직접 가격 수준을 반영 |
| 작가 면적단가 통계 | 이력 작품의 가격과 면적 | `artist_log_price_per_area_median`, `artist_area_adjusted_log_price` | 대상 작품 크기에 맞춰 작가 가격 수준을 보정 |
| 이력 매칭 단계 | 작가 이력과 대상 작품의 조건 비교 | `history_match_level`, `same_medium_support_size_flag`, `same_size_flag` | 같은 작가 이력이 대상 작품과 얼마나 가까운지 반영 |
| fallback 통계 | 작가 이력 조건이 너무 약한 경우의 동결 비교군 통계 | 비작가 비교군 기준가격 대용치 | 작가 이력만으로 불안정한 경우 가격 수준을 안정화 |

#### 5.3.1 Warm-lite 단계별 피처 사용처

Warm-lite는 1~4건 이력만 보고 단순 평균을 내는 모델이 아니다. 먼저 같은 작가 이력에서 통계를 만들고, 그 통계와 작품 피처로 Quantile 기준 로그가격을 계산한 뒤 residual 보정을 더한다.

| 단계 | 사용 피처 | 계산 또는 사용 방식 | 해석 |
|---|---|---|---|
| 라우팅 | `작가매칭신뢰도점수`, `같은작가_사용가능가격이력수` | 현재 0.1v 기준 `0.80 이상` AND `1~4건`이면 Warm-lite | 작가 매칭은 믿을 수 있지만 Warm 5건 기준에는 못 미치는 작품을 분리 |
| 작품 기본 피처 | `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate` | Quantile full/lean과 residual 보정에 공통 입력 | 크기, 면적, 형태, 입체 여부의 가격 차이를 반영 |
| 작품 범주 피처 | `medium_category`, `support_category`, `size_bucket`, `medium_support_bucket` | 이력 찾기 단계와 LightGBM 범주 입력에 사용 | acrylic/paper, oil/canvas 같은 재료·지지체·크기 조합 반영 |
| 작가 이력 매칭 | `medium_support_bucket`, `size_bucket` | 같은 작가 이력 안에서 `재료/지지체+크기 → 크기 → 작가 전체` 순서로 최소 1건 매칭 | 이력이 적어도 대상 작품과 가장 가까운 같은 작가 이력을 우선 사용 |
| 작가 가격 통계 | `grp_log_price_median`, `grp_log_price_q25`, `grp_log_price_q75`, `grp_log_price_iqr` | 매칭된 같은 작가 이력의 로그가격 분위 통계를 Quantile/residual 입력으로 사용 | 작가의 직접 가격 수준과 가격 분산을 반영 |
| 작가 면적단가 통계 | `grp_unit_area_median`, `grp_unit_area_iqr`, `grp_price_proxy` | `grp_price_proxy = grp_unit_area_median + 대상작품_log_area`를 Quantile/residual 입력으로 사용 | 이력 작품과 대상 작품의 크기 차이를 보정 |
| 표본/매칭 신뢰도 | `grp_n_log`, `grp_match_level` | 이력 표본 수와 매칭 단계 번호를 Quantile/residual 입력으로 사용 | 같은 2건이라도 가까운 비교군인지, 작가 전체 이력인지 구분 |
| 대체 통계(fallback) | 동결된 비작가 fallback 단계, global fallback | 정상적인 1~4건 Warm-lite에서는 3순위 작가 전체 이력에서 보통 매칭됨. fallback은 결측 방어용 | 작가 이력 통계를 만들 수 없는 예외 상황에서만 가격 수준을 비워두지 않음 |

- 작가 이력 매칭 순서:

```text
1순위: 같은 작가 + 같은 매체/지지체 + 같은 크기 구간
2순위: 같은 작가 + 같은 크기 구간
3순위: 같은 작가 전체 1~4건 이력
4순위: 동결된 비작가 비교군 통계
```

- 4순위 fallback 주의: Warm-lite 라우팅 자체는 같은 작가 이력 1~4건이 있는 경우만 들어온다. 따라서 정상 입력에서는 3순위 `작가 전체 1~4건 이력`에서 통계가 만들어진다. 4순위 fallback은 입력 결측이나 통계 생성 실패에 대비한 방어 장치이지, 작가 이력 없이 Warm-lite를 쓰겠다는 뜻이 아니다.

#### 5.3.2 Warm-lite Quantile residual 입력과 산식

현재 0.1v API에서 Warm-lite는 `models/track6/warm_lite_quantile_residual_v0.1` 번들의 동결 산식만 사용한다. 계산은 "기준 로그가격을 먼저 만들고, 남은 오차만 제한적으로 보정"하는 두 단계 구조다.

| 구성 | 주요 입력 | 출력 | 역할 |
|---|---|---|---|
| 전체 피처 기반 LightGBM Quantile | 작품 크기/형태 피처 + 매체/지지체/크기 범주 + 작가 로그가격 median/q25/q75/IQR + 면적단가 median/IQR + 면적보정 기준가격 + 표본 수/매칭 단계 | `full_q10`, `full_q50`, `full_q90`, `Quantile예측구간폭` | 작가 이력의 가격 중심과 예측 불확실성 폭을 계산 |
| 저표본 안정화 LightGBM Quantile | 작품 크기/형태 피처 + 매체/지지체/크기 범주 + 작가 로그가격 median/IQR + 면적보정 기준가격 + 표본 수/매칭 단계 | `lean_q50` | q25/q75, 면적단가 IQR처럼 1~4건에서 흔들릴 수 있는 피처 의존도를 줄인 기준 로그가격 |
| LightGBM Huber residual | Warm-lite 기본 피처 + `full_q10/full_q50/full_q90` + `Quantile예측구간폭` + `Quantile평균로그가격` | `LightGBM_Huber_잔차` | Quantile 평균이 남긴 반복 오차를 보정. 보정폭은 clip으로 제한 |

```text
LightGBM_full_q50 =
  LightGBM Quantile alpha=0.50(
    작품 피처 + 전체 피처 기반 작가 이력 통계 + 범주 피처
  )

LightGBM_lean_q50 =
  LightGBM Quantile alpha=0.50(
    작품 피처 + 저표본 안정화 피처 + 범주 피처
  )

Quantile평균로그가격 =
  0.50 * LightGBM_full_q50
  + 0.50 * LightGBM_lean_q50

LightGBM_Huber_잔차 =
  LightGBM objective=huber(
    작품 피처 + 작가 이력 통계 + Quantile q10/q50/q90/width 피처
  )

최종_Warm-lite_로그가격 =
  Quantile평균로그가격
  + clip(0.50 * LightGBM_Huber_잔차, -0.10, +0.10)
```

- 학습 단계: 과거 저이력 상황을 fold/leave-one-out으로 재현해 Quantile 기준값을 만들고, `실제 로그가격 - Quantile평균로그가격`을 residual target으로 학습한다
- 사용 단계(예측 단계): 새 작품에는 실제 가격을 쓰지 않고, 작가 이력 통계와 작품 피처만 넣어 `full_q50`, `lean_q50`, residual 보정값을 순서대로 계산한다
- 이력 1건인 경우: q25/q75/IQR 정보가 제한적이므로 `confidence_grade=warm_lite_low`, `display_policy=wide_range_with_review_flag`를 붙인다. 이는 최종 로그가격을 바꾸는 산식이 아니라, 같은 점 예측값을 더 낮은 신뢰도로 표시하고 운영 검수 대상으로 분리하기 위한 출력 정책이다
- 동결/parity 상태: Q3 Q2-like 7,284행 replay max log diff `3.55e-15`, v0.1 HTTP API 24건 parity max log diff `0.0`

- Warm과의 차이: Warm-lite는 같은 작가 이력 1~4건을 직접 통계화하지만, Warm처럼 5건 이상 비교군에서 위험도 라우터를 돌리지는 않는다
- Cold와의 차이: Cold는 같은 작가 가격 이력이 없거나 매칭이 불확실할 때 작품·작가 메타·검색 문맥으로 추정하지만, Warm-lite는 고신뢰 매칭 작가의 실제 가격 이력을 핵심 신호로 사용한다

### 5.4 Warm-lite 모델과 산식

- 1단계 — 사용 가능한 작가 이력 정의:

```text
사용가능작가이력 =
  학습 데이터에서 매칭 작가가 같고
  가격 라벨이 있으며
  학습/검증 시 자기 fold를 제외한 작품

k = count(사용가능작가이력)

Warm-lite 적용 조건:
  작가매칭신뢰도점수 >= 0.80
  AND 1 <= k <= 4
```

- 2단계 — 작가 이력 통계:

```text
작가로그가격중앙값 = median(이력_로그가격)
작가로그가격IQR = q75(이력_로그가격) - q25(이력_로그가격)

작가면적단가로그중앙값 =
  median(이력_로그가격 - 이력_log_area)

면적보정작가기준로그가격 =
  작가면적단가로그중앙값 + 대상작품_log_area
```

- 3단계 — Quantile residual 예측:

```text
Warm-lite_기본피처 =
  작품크기피처
  + 매체/지지체/크기구간피처
  + 작가이력통계피처
  + 이력매칭단계피처
  + fallback통계피처

LightGBM_full_q50 =
  Quantile모델_full(Warm-lite_기본피처)

LightGBM_lean_q50 =
  Quantile모델_lean(Warm-lite_기본피처에서 저표본 흔들림 피처 일부 제외)

Quantile평균로그가격 =
  0.50 * LightGBM_full_q50
  + 0.50 * LightGBM_lean_q50

LightGBM_Huber_잔차 =
  Huber잔차모델(Warm-lite_기본피처 + Quantile q10/q50/q90/width)

최종_Warm-lite_로그가격 =
  Quantile평균로그가격
  + clip(0.50 * LightGBM_Huber_잔차, -0.10, +0.10)

최종_Warm-lite_가격_KRW =
  exp(최종_Warm-lite_로그가격)
```

- Huber 의미: 여기서 Huber는 큰 오차의 영향을 완만하게 처리하는 손실/강건 목적함수다. 현재 Warm-lite에서는 LightGBM residual 모델의 objective가 Huber이며, residual 보정값은 `clip`으로 로그 기준 ±0.10 안에서만 반영한다
- 동결 번들: `models/track6/warm_lite_quantile_residual_v0.1`

#### 5.4.1 Warm-lite 피처-계산 연결 순서도

```text
[입력 피처]
  - artist_key 또는 고신뢰 작가 매칭 결과
  - width_cm, height_cm, depth_cm, area_cm2, log_area
  - medium_category, support_category, size_bucket
        |
        v
[사용 가능한 작가 이력 1~4건 조회]
  - 학습/검증 시 자기 fold 제외
  - 서빙 시점에는 확정된 같은 작가 가격 이력만 사용
        |
        v
[작가 이력 통계 피처]
  - artist_history_count
  - artist_log_price_median
  - artist_log_price_iqr
  - artist_log_price_per_area_median
  - history_match_level
        |
        v
[대상 작품 크기와 결합]
  - 면적보정작가기준로그가격 =
    작가면적단가로그중앙값 + 대상작품_log_area
        |
        v
[Warm-lite Quantile 입력]
  - 작품 크기/매체/지지체 피처
  - 작가 이력 통계 피처
  - 이력 매칭 단계 피처
  - fallback 통계 피처
        |
        v
[LightGBM Quantile q50 예측]
  - 전체 피처 기반 full q50: 작가 가격 q25/q75, 면적단가 IQR까지 포함
  - 저표본 안정화 lean q50: 저표본 흔들림을 줄인 축약 피처 구성
        |
        v
[Quantile 평균 로그가격]
  - 0.50 * full_q50 + 0.50 * lean_q50
        |
        v
[LightGBM Huber 잔차 보정]
  - Quantile q10/q50/q90/width와 기본 피처로 남은 오차 예측
  - clip(0.50 * 잔차, -0.10, +0.10)만 더함
        |
        v
[신뢰도 표시 정책]
  - 이력 1건이면 `confidence_grade=warm_lite_low`, `display_policy=wide_range_with_review_flag`
  - 이력 2~4건이면 `confidence_grade=warm_lite_standard`, `display_policy=point_estimate_with_standard_range`
        |
        v
[최종 Warm-lite 로그가격 -> exp() -> 원화 예측가격]
```

#### 5.4.2 Warm-lite 계산 예시

> 아래 숫자는 계산 흐름을 설명하기 위한 예시이며, 실험 성능 지표나 특정 운영 작품의 실제 예측값이 아니다.

```text
1) 라우팅 판단:
  작가 매칭 신뢰도 = 0.87
  같은 작가 사용 가능 가격 이력 k = 2건
  0.87 >= 0.80 이므로 작가 매칭 통과
  1 <= k <= 4 이므로 Warm-lite 대상
  k < 5 이므로 Warm 대상은 아님

2) 입력 작품 피처:
  작품 = acrylic/paper, 72cm x 60cm
  area_cm2 = 72 * 60 = 4,320
  log_area = log(4,320) = 8.371
  aspect_ratio = 72 / 60 = 1.200
  medium_category = acrylic
  support_category = paper
  size_bucket = 중형 예시

3) 사용 가능한 같은 작가 이력 조회:
  학습/검증 시 자기 fold 제외 후 남은 같은 작가 가격 이력 = 2건
  이력 매칭 단계 = 같은 작가 + 같은 크기 구간
  1순위(같은 작가 + 같은 매체/지지체 + 같은 크기 구간)는 충분하지 않음
  2순위(같은 작가 + 같은 크기 구간)에서 2건을 사용
  이 단계는 Warm-lite 대상 1~4건 작가를 Warm으로 보내는 정책 변경이 아님

4) 작가 로그가격 통계:
  이력 1 로그가격 = 17.450
  이력 2 로그가격 = 17.600
  작가로그가격중앙값 = median(17.450, 17.600) = 17.525
  작가로그가격q25(Quantile 보간 기준) = 17.488
  작가로그가격q75(Quantile 보간 기준) = 17.563
  작가로그가격IQR = 17.563 - 17.488 = 0.075

5) 작가 면적단가 통계:
  이력 1: 로그가격 17.450, 이력_log_area 8.200
    -> 이력별 면적단가 로그 = 17.450 - 8.200 = 9.250
  이력 2: 로그가격 17.600, 이력_log_area 8.550
    -> 이력별 면적단가 로그 = 17.600 - 8.550 = 9.050
  작가면적단가로그중앙값 = median(9.250, 9.050) = 9.150
  면적보정작가기준로그가격 = 9.150 + 대상작품_log_area 8.371 = 17.521

6) Warm-lite Quantile residual 입력:
  작품 크기 피처:
    area_cm2 4,320, log_area 8.371, aspect_ratio 1.200
  작품 범주 피처:
    medium_category acrylic, support_category paper, size_bucket 중형 예시
  작가 이력 통계 피처:
    artist_history_count 2
    artist_log_price_median 17.525
    artist_log_price_q25 17.488
    artist_log_price_q75 17.563
    artist_log_price_iqr 0.075
    artist_log_price_per_area_median 9.150
    artist_area_adjusted_log_price 17.521
  이력 매칭 단계 피처:
    history_match_level = 같은 작가 + 같은 크기 구간
  대체 통계(fallback) 피처:
    정상 Warm-lite 경로에서는 사용하지 않음
    같은 작가 통계 생성 실패나 입력 결측에 대비한 방어용

7) LightGBM Quantile 예측:
  full_q50 입력:
    작품 크기/범주 피처
    + 작가 로그가격 median/q25/q75/IQR
    + 작가 면적단가 median/IQR
    + 면적보정작가기준로그가격
    + 이력 수와 매칭 단계

  lean_q50 입력:
    작품 크기/범주 피처
    + 작가 로그가격 median/IQR
    + 면적보정작가기준로그가격
    + 이력 수와 매칭 단계
    # q25/q75와 면적단가 IQR은 저표본 흔들림을 줄이기 위해 제외

  LightGBM_full_q50 = 17.540
  LightGBM_lean_q50 = 17.500
  Quantile평균로그가격 = 0.50 * 17.540 + 0.50 * 17.500 = 17.520

8) LightGBM Huber 잔차 보정:
  residual 입력:
    작품/작가 이력 통계 피처
    + q10/q50/q90 예측값
    + Quantile예측구간폭

  LightGBM_Huber_잔차 = 0.060
  원시보정값 = 0.50 * 0.060 = 0.030
  적용보정값 = clip(0.030, -0.10, +0.10) = 0.030
  최종_Warm-lite_로그가격 = 17.520 + 0.030 = 17.550

9) 등급 판단과 원화 변환:
  k = 2이므로 confidence_grade=warm_lite_standard
  최종_Warm-lite_가격_KRW = exp(17.550) ~= 41,900,000원
```

### 5.5 Warm-lite 성능 해석

- 현재 채택 모델 성능 (PP-WLITE-Q3/Q5, 실존 저이력 작가 649명 leave-one-out × 3회, 1,947행): Warm-lite Quantile residual `0.107246 / 0.275773 / 0.852026`
- 경로 분리 기준 성능 (PP-WCUT4, 실존 저이력 작가 동일 행 비교): Warm-lite 저이력 경로 `0.1092 / 0.2866 / 0.8765`, 동일 행 Cold `0.5429 / 0.9946 / 2.5358`
- RMSE log `0.423003`은 Q3 Q1-like 산출물에서 재계산한 Warm-lite Quantile residual 보조 검증값이며, 동일 행 Cold RMSE log가 없어 비교 지표로는 사용하지 않음

| 이력 수 | Warm-lite MdAPE | 같은 작품을 Cold로 보낼 때 | 해석 |
|---|---:|---:|---|
| 1건 | 0.1107 | 0.5639 | 1건이어도 작가 실제 가격 이력이 Cold보다 강한 신호 |
| 2건 | 0.1300 | 0.5606 | 중앙오차는 k=1/3/4보다 높지만 Cold 대비 큰 우위 유지 |
| 3건 | 0.0901 | 0.5071 | Warm 5건 이상 경로에 가까운 중앙오차 |
| 4건 | 0.0913 | 0.5105 | 저이력 구간 중 안정적인 중앙오차 |

Warm-lite 경로와 내부 로직을 유지하는 근거:

| 검증 질문 | 실험 | 결과 | 판단 |
|---|---|---|---|
| 1~4건 이력을 Cold로 보내도 되는가? | PP-WCUT4 | Warm-lite MdAPE `0.1092`, Cold MdAPE `0.5429` | Cold로 보내면 같은 작가 가격 신호를 버리는 손실이 큼 |
| 1~4건을 Warm 계열으로 통일해도 되는가? | PP-WMIN9E / PP-WMIN9C | 전체 1~4건 Warm-lite `0.1092 / 0.2866 / 0.8765`, WMIN8 svc-core proxy `0.1291 / 0.2932 / 0.9163` | 현재 비누수 근거로는 Warm-lite 유지가 우세 |
| 1~4건에 full WMIN8 직접 비교를 시도했는가? | PP-WMIN11 부분 재학습 실험 | frozen full WMIN8/PPV8 없이 재학습 가능한 축만 비교: 부분 재학습 라우팅 후보 `0.1480 / 0.2931 / 0.8716` | p95는 근소 개선이나 MdAPE/MAPE가 악화되어 Warm-lite 유지. 정확한 full WMIN8은 PPV8 상류 재학습 필요 |
| 5건 이상에도 Warm-lite를 쓰면 되는가? | PP-WMIN9D | 5건 이상 WMIN8 `0.104326 / 0.235814 / 0.739416`, 강제 Warm-lite `0.108722 / 0.248054 / 0.837824` | 5건 이상은 Warm 유지 |
| Quantile residual 방식이 현재 채택값인가? | PP-WLITE-Q1 / PP-WLITE-Q2 / PP-WLITE-Q3 / PP-WLITE-Q4 / PP-WLITE-Q5 | Q3에서 `qavg_lgbres_s05_cap010`이 1,947행 기준 `0.107246 / 0.275773 / 0.852026`. Q4에서 같은 후보가 최종 비교 1위. Q5에서 bundle replay/API parity 통과 | 현재 0.1v Warm-lite 계산식은 `lgbq_full_lean_avg + clip(0.50 * LightGBM Huber 잔차, -0.10, +0.10)` |

1~4건을 Warm으로 통일할 수 있는지에 대한 직접 근거(PP-WMIN9E, PP-WMIN9C 동일 행 비교):

| 이력 수 | Warm-lite | WMIN8 svc-core proxy | 판정 |
|---:|---:|---:|---|
| 1건 | `0.1207 / 0.3415 / 0.9559` | `0.1271 / 0.3406 / 0.9573` | 혼합. Warm-lite는 MdAPE/p95 우세, proxy는 MAPE 0.0009p 우세 |
| 2건 | `0.1184 / 0.2707 / 0.8779` | `0.1448 / 0.2821 / 0.9478` | Warm-lite 전 지표 우세 |
| 3건 | `0.1060 / 0.2541 / 0.7142` | `0.1195 / 0.2661 / 0.7489` | Warm-lite 전 지표 우세 |
| 4건 | `0.0923 / 0.2557 / 0.7884` | `0.1190 / 0.2634 / 0.7682` | 혼합. Warm-lite는 MdAPE/MAPE 우세, proxy는 p95 우세 |
| 1~4건 전체 | `0.1092 / 0.2866 / 0.8765` | `0.1291 / 0.2932 / 0.9163` | Warm-lite 전 지표 우세 |

- 위 표의 WMIN8 svc-core proxy는 full WMIN8이 아니다. full WMIN8은 PPV8 방어값, Huber 잔차 보정, 위험도 라우터까지 포함하는 5건 이상 경로다
- PP-WMIN11은 이 한계를 줄이기 위해 frozen full WMIN8/PPV8를 쓰지 않고 svc-core와 L10 보조축을 재학습한 부분 재학습 실험이다. 그러나 PPV8 큰오차방어 축에 들어가는 기본 Huber, L8/L9, D4, R5, E1, K3, U1 상류 후보 전체를 같은 hold-out 조건으로 재생성하지 못했으므로 정확한 full WMIN8 완료 실험은 아니다
- Warm-lite 유지 판단: 현재 유효 근거에서는 1~4건 전체를 Warm으로 통일하는 것보다 Warm-lite 전용 경로를 유지하는 편이 MdAPE/MAPE/p95 기준으로 낫다
- Warm-lite Quantile residual 채택 판단: PP-WLITE-Q4 최종 비교에서 `qavg_lgbres_s05_cap010`, 즉 `lgbq_full_lean_avg + clip(0.50 * LightGBM Huber 잔차, -0.10, +0.10)` 후보가 최종 후보로 선택됐다. Q5에서 `models/track6/warm_lite_quantile_residual_v0.1`로 동결했고, Q3 Q2-like 7,284행 replay max log diff `3.55e-15`, v0.1 HTTP API 24건 parity max log diff `0.0`을 확인했다. 따라서 이 문서의 현재 Warm-lite 가격 예측 프로세스는 `작가 이력 통계 생성 → Quantile full/lean q50 평균 → LightGBM Huber residual clip 보정 → 신뢰도 표시 정책 → exp()`로 설명한다

Warm-lite 내부 로직을 말로 정리하면 다음과 같다.

```text
1. 먼저 작가 매칭이 0.80 이상인지 확인한다.
2. 같은 작가의 사용 가능한 가격 이력이 1~4건인지 확인한다.
3. 같은 작가 이력에서 대상 작품과 가장 가까운 비교군을 찾는다.
   - 같은 매체/지지체 + 같은 크기 구간
   - 없으면 같은 크기 구간
   - 없으면 작가 전체 1~4건
4. 선택된 같은 작가 이력에서 로그가격 중앙값, q25/q75, IQR, 면적단가 중앙값을 만든다.
5. 대상 작품의 크기/면적/비율/입체 여부와 매체/지지체/크기 구간을 붙인다.
6. 전체 피처 기반 Quantile 모델로 q10/q50/q90과 예측구간폭을 계산한다.
7. 저표본 안정화 Quantile 모델로 저표본 흔들림을 줄인 q50을 계산한다.
8. `0.50 * full_q50 + 0.50 * lean_q50`으로 Quantile평균로그가격을 만든다.
9. LightGBM Huber residual 모델로 남은 오차를 예측하고 `clip(0.50 * residual, -0.10, +0.10)`만 더한다.
10. 이력 1건이면 로그가격은 그대로 두고 `confidence_grade=warm_lite_low`, `display_policy=wide_range_with_review_flag`를 함께 반환한다.
11. exp(최종 Warm-lite 로그가격)으로 원화 가격을 만든다.
```

## 6. Cold 모델 상세

> 상태 구분: 이 절은 Cold 성능 기준 모델(v0.3 guard+search)을 설명한다. 현재 0.1v API는 Cold adapter/artifact를 내부 연결 상태로 관리하며, `cold_prediction_v0.2_operational`처럼 이름에 v0.2가 들어간 항목은 API 버전이 아니라 Cold 내부 번들 버전이다.

### 6.1 모델 목적

- 적용 대상: 같은 작가의 학습 가격 이력이 0건이거나, 작가 매칭이 불확실한 작품 (이력 1~4건은 Warm-lite 경로로 분리되어 Cold 대상이 아님)
- Cold 성능 기준 모델 구조: Warm처럼 유사작품 기준가격을 강하게 쓰기 어려운 상황에서 작품 피처, 작가 메타, 작가명 검색 피처를 함께 사용
- 계산 관점: `검색 피처 포함 대표 예측가격 + 과대예측 방어 + 작가 검색 보정값`

- Cold 성능 기준 모델의 구성 단계:

- 대표 로그가격 생성: 검색 피처 포함 LightGBM Quantile 회귀 후보를 Quantile예측구간폭 구간별 검증 잔차로 안정화
- 과대예측 방어: `Quantile예측구간폭 >= 1.4612207078910142`이고 대표 로그가격이 낮은쪽 40% 지점보다 `0.07715547281151025 log` 이상 높을 때 낮은쪽 가격 기준으로 하향
- 최종 검색 보정: 작가 검색 결과의 갤러리/미술관 문맥 기반 보정값 추가

### 6.2 Cold 계산 순서도

Cold는 학습 단계에서 작품 피처, 작가 메타, 검색 피처로 LightGBM Quantile 모델과 보정표를 만든다. 사용 단계에서는 새 작품에 대해 저장된 검색 피처/보정 lookup과 동결 모델을 적용해 대표 로그가격을 만들고, 필요한 경우 과대예측 방어를 적용한다.

#### 6.2.1 Cold 학습/검증 단계 순서도

```text
[Cold 학습/검증 데이터]
  - 실제 로그가격이 있는 과거 작품
  - 같은 작가 이력이 없거나 Warm/Warm-lite 조건을 만족하지 않는 평가 조건
  - 작품 크기/매체/지지체, 작가 메타, 작가명 검색 스냅샷
        |
        v
[Cold 피처 생성]
  - 작품 피처: 면적, 로그면적, 가로세로비, 입체 여부
  - 범주 피처: 매체, 지지체, 크기/형태/bucket 조합
  - 작가 메타 피처: 생년, 국적, 활동량, 팔로워, 결측 여부
  - 검색 피처: 미술/전시/갤러리/시장 문맥, 검색 품질, 동명이인 위험
        |
        v
[LightGBM Quantile 회귀 학습]
  - 기준 Quantile 로그가격
  - 낮은쪽 40% 지점 로그가격
  - q10/q90 기반 Quantile예측구간폭
        |
        v
[검증 잔차 안정화값 계산]
  - 실제 로그가격 - 기초 Quantile 후보 로그가격
  - Quantile예측구간폭 구간별 잔차 중앙값 저장
        |
        v
[과대예측 방어 조건 선택]
  - validation에서 guard 조건 선택
  - 현재 조건: Quantile예측구간폭 >= 1.4612207078910142
  - 대표가격과 낮은쪽40% 지점 차이 >= 0.07715547281151025 log
        |
        v
[작가 검색 보정 lookup 생성]
  - 검색 스냅샷에서 갤러리/미술관 문맥 기반 작가별 보정값 계산
  - 실시간 학습값이 아니라 검증된 고정 보정표로 저장
        |
        v
[동결 산출물]
  - LightGBM Quantile 모델
  - 구간별 잔차 보정표
  - 과대예측 방어 조건
  - 작가 검색 보정 lookup
```

#### 6.2.2 Cold 사용 단계 순서도

```text
[작품 입력 정보 + 작가 정보]
  - 작품 크기
  - 매체/지지체
  - 작가 메타
  - 작가명
        |
        v
[작가명 기반 검색 피처 조회]
  - 저장된 검색 피처 캐시 사용
  - 검색 결과 제목, 요약, URL, 도메인을 작가 단위로 집계
  - 최종 보정에는 고정된 작가별 검색 보정 lookup 사용
        |
        v
[검색 피처 포함 대표 예측 준비]
  - 작품 피처, 작가 메타, 검색 피처를 포함한 LightGBM Quantile 회귀 후보 사용
  - Quantile예측구간폭 구간별 검증 잔차 중앙값으로 대표 로그가격 안정화
        |
        v
[Quantile예측구간폭과 낮은쪽 40% 지점 로그가격 확인]
  - Quantile예측구간폭 = 저장된 Quantile 예측 폭
  - 낮은쪽40퍼센트기준_로그가격 = LightGBM 40% Quantile 로그가격
        |
        v
[과대예측 방어]
  - Quantile예측구간폭이 넓고 대표 로그가격이 낮은쪽40퍼센트기준 로그가격보다 높으면
    대표 로그가격과 낮은쪽40퍼센트기준 로그가격을 50:50으로 혼합
        |
        v
[작가 검색 보정값 추가]
  - 갤러리/미술관 검색 문맥 기반 작가별 보정값
        |
        v
[최종 Cold 로그가격]
        |
        v
[최종 Cold 가격 = exp(최종 Cold 로그가격)]
```

- 학습 단계와 사용 단계의 차이: 학습/검증 단계에서는 실제 로그가격으로 Quantile 모델, 잔차 보정표, guard 조건, 검색 보정 lookup을 만든다. 사용 단계에서는 실제 가격 없이 동결 모델과 고정 lookup만 적용한다

### 6.3 Cold 사용 피처

#### 6.3.1 Cold 원천 입력 피처와 파생 피처 구분

```text
[원천 입력]
  - 작품 크기 문자열
  - 작품 매체/재료 문자열
  - 작품 카테고리
  - 작가 메타 원본값
  - 작가명 검색 결과 스냅샷
        |
        v
[기본 파생 피처]
  - 면적, 로그면적, 가로세로비
  - 매체/지지체 카테고리
  - 크기/형태/매체 조합 구간
        |
        v
[작가 메타 파생 피처]
  - 활동량 로그값
  - 결측 여부
  - 국적/출처 범주값
        |
        v
[검색 파생 피처]
  - 미술/전시/갤러리/시장 문맥 개수
  - 검색 품질 점수
  - 동명이인 위험
  - 작품/작가 조건과의 상호작용
        |
        v
[LightGBM Quantile 회귀 후보 + 후처리]
```

| 피처 구분 | 원천 또는 직접 입력 | 파생 피처 | 계산 방식 |
|---|---|---|
| 작품 크기 | `dimensions_cm` 또는 정규화된 `width_cm`, `height_cm`, `depth_cm` | `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate` | `area_cm2 = width_cm * height_cm`, `log_area = log(area_cm2)`, `aspect_ratio`는 크기 파서가 계산한 비율 사용 |
| 작품 재료/지지체 | `medium`, `category` | `medium_category`, `support_category`, `medium_support_bucket` | 매체 문자열을 oil/acrylic 등 매체 범주와 canvas/paper 등 지지체 범주로 정규화, `medium_support_bucket = medium_category + '__' + support_category` |
| 크기/형태 구간 | `log_area`, `aspect_ratio`, `area_cm2`, `is_3d_candidate` | `size_bucket`, `shape_bucket`, `medium_size_bucket`, `support_size_bucket`, `medium_shape_bucket`, `is_large_2d`, `is_large_3d` | 학습 데이터의 로그면적 Quantile 경계로 크기 구간 생성, 가로세로비로 형태 구간 생성, 매체/지지체와 조합 |
| 작가 기본 메타 | `artist_meta_birth_year`, `artist_meta_nationality`, `artist_meta_nationality_ko` | `artist_meta_birth_year_missing` 등 | 원본값을 숫자/범주로 정규화하고 결측 여부를 별도 피처로 생성 |
| 작가 활동/인기도 | `artist_meta_total_works`, `artist_meta_for_sale_works`, `artist_meta_followers`, `artist_meta_career_stage` | `artist_meta_total_works_log`, `artist_meta_for_sale_works_log`, `artist_meta_followers_log`, `artist_meta_*_missing` | `log1p(max(value, 0))`로 긴 꼬리 분포를 완화하고 결측 여부를 함께 반영 |
| 검색 원천값 | 작가명 기반 검색 결과 제목, 요약, URL, 도메인 | 검색량, 검색 문맥, 검색 품질, 동명이인 위험 | 검색 결과 텍스트와 도메인을 작가 단위로 집계 |
| 검색 상호작용 | 검색 품질, 작품 크기, 작가 팔로워, 작가 경력 단계 | `search_quality_x_log_area`, `search_art_match_x_followers_log`, `search_exhibition_x_career_stage`, `search_size_quality_bucket` | 검색 신호와 작품/작가 조건을 곱하거나 범주 조합으로 생성 |
| 검색 보정 lookup | 작가별 검색 스냅샷 집계값 | 작가별 검색 보정 로그값 | 갤러리/미술관 문맥 등으로 만든 작가별 보정값을 고정 lookup으로 사용 |

#### 6.3.2 Cold 주요 파생 피처 계산식

| 파생 피처 | 계산식 또는 생성 방식 | 역할 |
|---|---|---|
| `log_area` | `log(area_cm2)` | 크기 효과를 로그 스케일로 반영 |
| `size_bucket` | 학습 데이터 `log_area` Quantile 경계로 구간화 | 크기대별 가격 차이 반영 |
| `shape_bucket` | `aspect_ratio < 0.65: tall`, `<= 1.55: balanced`, `<= 2.5: wide`, `> 2.5: extreme_wide` | 세로형/균형형/가로형/극단형 구분 |
| `medium_size_bucket` | `medium_category + '__' + size_bucket` | 매체별 크기 효과 반영 |
| `support_size_bucket` | `support_category + '__' + size_bucket` | 지지체별 크기 효과 반영 |
| `artist_meta_total_works_log` | `log1p(max(artist_meta_total_works, 0))` | 작가 활동량의 긴 꼬리 완화 |
| `artist_meta_followers_log` | `log1p(max(artist_meta_followers, 0))` | 작가 인기도의 긴 꼬리 완화 |
| `artist_meta_*_missing` | `1 if 해당 작가 메타가 비어 있음 else 0` | 정보가 없는 작가 자체의 불확실성 반영 |
| `search_result_count_log` | `log1p(search_result_count)` | 검색량의 긴 꼬리 완화 |
| `search_art_match_ratio` | `search_art_context_count / max(search_result_count, 1)` | 검색 결과가 미술 문맥에 얼마나 가까운지 반영 |
| `search_source_ratio` | `search_source_count / max(search_result_count, 1)` | 검색 출처 다양성 반영 |
| `search_quality_x_log_area` | `search_quality_score * log_area` | 검색 신뢰도와 작품 크기의 결합 효과 반영 |
| `search_art_match_x_followers_log` | `search_art_match_ratio * artist_meta_followers_log` | 작가 검색 문맥과 인기도 결합 |
| `search_exhibition_x_career_stage` | `search_exhibition_ratio * artist_meta_career_stage` | 전시 문맥과 작가 경력 단계 결합 |

- 검색 품질 점수 구성:

```text
검색품질점수 =
  0.30 * 미술문맥비율
+ 0.20 * 신뢰도메인비율
+ 0.15 * 전시문맥비율
+ 0.15 * 시장/거래문맥비율
+ 0.10 * 최근결과비율
+ 0.10 * 검색제공자커버리지점수
+ 0.10 * 작가명일치비율
- 0.30 * 동명이인위험비율
```

#### 6.3.3 LightGBM Quantile 회귀 후보의 의미

- Quantile 회귀 의미: 평균 가격 하나를 맞추는 회귀가 아니라, 조건이 비슷한 작품들의 가격 분포에서 특정 위치의 로그가격을 예측하는 방식
- 50% Quantile 의미: 같은 조건의 작품 가격을 낮은 순서로 세웠을 때 중앙에 가까운 가격
- 40% Quantile 의미: 같은 조건의 작품 가격을 낮은 순서에서 높은 순서로 세웠을 때 40% 지점에 있는 가격
- 문서 표현: `낮은쪽 40% 지점 가격`
- 주의: `낮은쪽 40% 지점 가격`은 40% 할인 또는 가격을 40% 낮춘다는 뜻이 아님
- 10%와 90% Quantile 의미: 낮은 쪽과 높은 쪽의 예측 범위를 잡기 위한 경계값
- Quantile예측구간폭 의미: 높은 Quantile 예측값과 낮은 Quantile 예측값의 차이이며, 값이 클수록 모델이 해당 작품 가격을 불확실하게 보고 있다는 뜻

| 문서용 이름 | 내부 의미 | 계산 또는 생성 방식 | Cold 성능 기준에서의 역할 |
|---|---|---|---|
| `검색피처포함_기초Quantile후보_로그가격` | 검색 피처까지 포함한 LightGBM Quantile 회귀 기반 기준 후보 | 작품 피처, 작가 메타, 검색 피처, 검색 상호작용 피처를 입력으로 LightGBM Quantile 회귀 모델이 예측 | Cold 대표 로그가격을 만들기 전의 기준값 |
| `낮은쪽40퍼센트기준_로그가격` | LightGBM 40% Quantile 로그가격 | 같은 입력 조건에서 낮은 가격부터 높은 가격까지 줄 세웠을 때 40% 지점을 예측 | 과대예측 위험이 있을 때 대표 로그가격을 낮추는 방어 기준 |
| `Quantile예측구간폭` | 높은 Quantile 예측값과 낮은 Quantile 예측값의 차이 | 예: `90%Quantile_로그가격 - 10%Quantile_로그가격` | 불확실성 측정, 구간별 잔차 안정화, 과대예측 방어 조건에 사용 |
| `검색포함_대표로그가격` | 기초 Quantile 후보를 검증 잔차로 안정화한 값 | `검색피처포함_기초Quantile후보_로그가격 + 구간별_보정값` | 과대예측 방어 전 Cold 기준가격 |

- LightGBM Quantile 회귀 후보 생성 흐름:

```text
작품 피처 + 작가 메타 피처 + 검색 피처
        |
        v
LightGBM Quantile 회귀 모델
        |
        +--> 기준 Quantile 로그가격
        +--> 낮은쪽 40% 지점 로그가격
        +--> 90% Quantile과 10% Quantile 차이 기반 Quantile예측구간폭
```

- 일반 LightGBM 회귀와의 차이:

| 구분 | 일반 LightGBM 회귀 | LightGBM Quantile 회귀 |
|---|---|---|
| 목표 | 평균적인 정답 가격에 가까운 값 예측 | 가격 분포의 특정 Quantile 위치 예측 |
| 출력 해석 | 하나의 평균형 예측값 | 중앙값, 낮은쪽 방어가격, 높은/낮은 Quantile 경계 등으로 해석 가능 |
| 이 문서에서의 사용 | Cold 성능 기준 경로의 핵심 방식은 아님 | Cold 성능 기준 경로의 기준가격, 낮은쪽 방어가격, 불확실성 폭 생성에 사용 |

#### 6.3.4 Cold 전체 피처 사용처

```text
[원천 작품/작가/검색 피처]
        |
        v
[LightGBM Quantile 회귀 후보 생성]
  - 검색피처포함_기초Quantile후보_로그가격
  - Quantile예측구간폭
  - 낮은쪽40퍼센트기준_로그가격
        |
        v
[대표 로그가격 안정화]
  - Quantile예측구간폭_구간
  - 구간별_잔차중앙값
  - 검색포함_대표로그가격
        |
        v
[과대예측 방어]
  - Quantile예측구간폭
  - 대표 로그가격 - 낮은쪽40퍼센트기준 로그가격
  - 과대예측방어_로그가격
        |
        v
[작가 검색 보정]
  - artist_key
  - search_delta_lookup
        |
        v
[최종 Cold 로그가격]
```

| 피처 또는 파생값 | 실제 사용 단계 | 사용 방식 | 예측가격에 미치는 영향 |
|---|---|---|---|
| `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio` | LightGBM Quantile 회귀 후보 생성 | 작품 크기와 형태를 모델 입력으로 사용 | 기본 가격 수준과 크기 프리미엄 반영 |
| `has_depth`, `is_3d_candidate`, `is_large_2d`, `is_large_3d` | LightGBM Quantile 회귀 후보 생성 | 입체 여부와 대형 작품 여부를 모델 입력으로 사용 | 평면/입체 및 대형 작품의 가격 패턴 반영 |
| `medium_category`, `support_category` | LightGBM Quantile 회귀 후보 생성 | 매체와 지지체 범주를 모델 입력으로 사용 | 매체/지지체별 가격 차이 반영 |
| `medium_support_bucket` | LightGBM Quantile 회귀 후보 생성 | 매체와 지지체를 하나의 조합 범주로 사용 | 재료 조합별 가격 차이 반영 |
| `size_bucket`, `shape_bucket`, `medium_size_bucket`, `support_size_bucket`, `medium_shape_bucket` | LightGBM Quantile 회귀 후보 생성 | 크기/형태/매체 조합을 범주 피처로 사용 | 단일 수치로 잡기 어려운 조합 효과 반영 |
| `artist_meta_birth_year`, `artist_meta_career_stage`, `artist_meta_nationality`, `artist_meta_nationality_ko` | LightGBM Quantile 회귀 후보 생성 | 작가 세대, 경력 단계, 국적 신호로 사용 | 작가 프로필에 따른 기준가격 차이 반영 |
| `artist_meta_total_works_log`, `artist_meta_for_sale_works_log`, `artist_meta_followers_log` | LightGBM Quantile 회귀 후보 생성 | 활동량/시장 노출도/인지도 신호로 사용 | 저이력 작가의 가격 범위 추정 보강 |
| `artist_meta_*_missing` | LightGBM Quantile 회귀 후보 생성 | 메타 정보 결측 여부를 별도 신호로 사용 | 정보 부족에 따른 불확실성 패턴 반영 |
| `search_result_count`, `search_source_count` | LightGBM Quantile 회귀 후보 생성 | 검색량과 출처 다양성을 모델 입력으로 사용 | 작가 인지도와 검색 신뢰도 반영 |
| `search_result_count_log` | LightGBM Quantile 회귀 후보 생성 | 검색량을 `log1p()`로 완화한 값 | 검색량이 많은 작가의 과도한 영향 완화 |
| `search_art_match_ratio`, `search_source_ratio` | LightGBM Quantile 회귀 후보 생성 | 미술 문맥 비율과 출처 다양성 비율을 모델 입력으로 사용 | 검색 결과의 질과 다양성 반영 |
| `search_art_context_count`, `search_exhibition_context_count`, `search_gallery_context_count`, `search_market_context_count` | LightGBM Quantile 회귀 후보 생성 | 미술/전시/갤러리/시장 문맥 개수를 사용 | 작가 활동 문맥을 가격 예측에 반영 |
| `search_exhibition_ratio`, `search_gallery_ratio`, `search_market_ratio` | LightGBM Quantile 회귀 후보 생성 | 전시/갤러리/시장 문맥 비율을 모델 입력으로 사용 | 검색 결과 수가 다른 작가 간 비교 가능하도록 정규화 |
| `search_quality_score`, `search_quality_grade` | LightGBM Quantile 회귀 후보 생성 및 검색 보정 근거 | 검색 결과의 신뢰도 점수와 등급으로 사용 | 검색 피처가 신뢰 가능한지 판단 |
| `search_homonym_context_count`, `search_homonym_risk_grade` | LightGBM Quantile 회귀 후보 생성 및 검색 보정 위험 관리 | 동명이인 위험을 입력 신호로 사용 | 무관 검색 결과가 섞이는 위험 반영 |
| `search_quality_x_log_area`, `search_art_match_x_followers_log`, `search_exhibition_x_career_stage`, `search_size_quality_bucket` | LightGBM Quantile 회귀 후보 생성 | 검색 신호와 작품/작가 조건의 상호작용으로 사용 | 특정 조건 조합에서의 가격 차이 반영 |
| `검색피처포함_기초Quantile후보_로그가격` | 대표 로그가격 안정화 | Quantile예측구간폭 구간별 잔차 보정의 기준값 | Cold 기준가격의 출발점 |
| `Quantile예측구간폭` 또는 `quantile_width_log` | 대표 로그가격 안정화 및 과대예측 방어 | 구간별 잔차 보정, 방어조건, 검수 플래그에 사용 | 불확실성이 큰 작품을 더 방어적으로 처리 |
| `Quantile예측구간폭_구간` | 대표 로그가격 안정화 | `Quantile예측구간폭`을 구간화해 같은 불확실성 수준끼리 묶음 | 불확실성 수준별 잔차 패턴 반영 |
| `구간별_잔차중앙값` | 대표 로그가격 안정화 | 같은 Quantile예측구간폭 구간의 `실제_로그가격 - 검색피처포함_기초Quantile후보_로그가격` 중앙값 | 구간별로 반복되는 치우침 보정 |
| `구간별_보정값` | 대표 로그가격 안정화 | `clip(구간별_잔차중앙값, -0.25, +0.25)` | 대표 로그가격이 과도하게 움직이지 않도록 제한 |
| `검색포함_대표로그가격` | 과대예측 방어 전 기준가격 | 기초 Quantile 후보에 구간별 보정값을 더함 | Cold 후처리의 기준가격 |
| `낮은쪽40퍼센트기준_로그가격` | 과대예측 방어 | 방어조건이 켜지면 대표 로그가격과 50:50 혼합 | 큰 과대예측 가능성을 낮춤 |
| `방어조건` | 과대예측 방어 | `Quantile예측구간폭 >= 1.4612207078910142` AND `검색포함_대표로그가격 - 낮은쪽40퍼센트기준_로그가격 >= 0.07715547281151025`일 때 활성화 | 과대예측 위험 작품만 선택적으로 하향 |
| `과대예측방어_로그가격` | 검색 보정 전 최종 후보 | 방어조건이 켜지면 대표 로그가격과 낮은쪽40퍼센트기준 로그가격을 50:50 혼합, 아니면 대표 로그가격 유지 | 큰 오차 상위 구간 완화 |
| `artist_key` | 작가 검색 보정 | 고정 검색 보정 lookup의 key로 사용 | 작가별 검색 문맥 보정값 적용 |
| `search_delta_lookup[artist_key]` | 최종 검색 보정 | `최종_Cold_로그가격 = 과대예측방어_로그가격 + 작가검색보정_로그값` | 작가별 검색 문맥에 따른 최종 로그가격 이동 |
| `작가검색보정_로그값` | 최종 검색 보정 | lookup에 있으면 작가별 보정값(±0.2 로그로 제한), 없으면 0 | 작가 검색 문맥을 최종 가격에 추가 반영 |
| `최종_Cold_로그가격` | 최종 가격 변환 | `과대예측방어_로그가격 + 작가검색보정_로그값` | `exp()` 변환 전 최종 예측값 |
| `actual_log`, `actual_price` | 평가 전용 | MdAPE, MAPE, p95 APE 계산 | 예측 시 입력으로 사용하지 않음 |
| `_track6_row_id`, `split` | 재현/검수 | 데이터 병합, split 구분, 결과 추적 | 최종 예측 산식에는 직접 사용하지 않음 |

#### 6.3.5 Cold 단계별 피처 사용과 블랙박스 해소

Cold는 한 개 모델이 모든 것을 숨겨서 바로 최종 가격을 내는 구조가 아니다. `상류 LightGBM Quantile 예측값`을 만든 뒤, 검증 잔차 기반 안정화, 과대예측 방어, 검색 lookup 보정을 순서대로 적용한다.

| 단계 | 입력 피처 또는 값 | 모델/규칙 | 출력 | 해석 |
|---|---|---|---|---|
| 작품/작가/검색 피처 생성 | 작품 크기, 매체/지지체, 작가 메타, 검색 스냅샷 | 정규화 및 파생 규칙 | `log_area`, `size_bucket`, `artist_meta_*_log`, `search_*_ratio` 등 | 원천 문자열과 숫자를 모델 입력 가능한 피처로 변환 |
| 상류 Quantile 예측 | 작품 피처 + 작가 메타 피처 + 검색 피처 + 검색 상호작용 피처 | LightGBM Quantile 회귀 | `y18_qwidth_pred_log`, `lgb_q40_pred_log`, `quantile_width_log` | 대표 가격 후보, 낮은쪽 40% 방어 후보, 불확실성 폭 생성 |
| 대표 로그가격 안정화 | `y18_qwidth_pred_log`, `quantile_width_log` | Quantile 폭 구간별 검증 잔차 중앙값 보정 | `검색포함_대표로그가격` | 같은 불확실성 구간에서 반복되는 치우침을 줄임 |
| 과대예측 방어 | `검색포함_대표로그가격`, `lgb_q40_pred_log`, `quantile_width_log` | 고정 guard 조건 + 50:50 혼합 | `과대예측방어_로그가격` | `quantile_width_log >= 1.4612207078910142`이고 대표가격이 40% 기준보다 `0.07715547281151025 log` 이상 높을 때만 하향 |
| 검색 lookup 보정 | `artist_key`, `search_delta_lookup[artist_key]` | 고정 작가별 보정표, ±0.2 log cap | `작가검색보정_로그값` | 갤러리/미술관 검색 문맥이 반복적으로 설명한 잔차를 작가 단위로 보정 |
| 검수 플래그 | 검색 lookup 커버 여부, `quantile_width_log` | 고정 규칙 | `cold_review_flag`, `cold_confidence_tier` | 검색 보정 근거가 없거나 예측 폭이 넓은 작품을 낮은 신뢰로 표시 |

학습·검증 단계와 사용 단계(운영 예측 단계)는 다음처럼 구분한다.

```text
[학습/검증 단계]
1. 실제 로그가격이 있는 데이터에서 LightGBM Quantile 모델을 학습한다.
2. out-of-fold 또는 validation 예측으로 대표 후보와 실제 로그가격의 잔차를 계산한다.
3. Quantile예측구간폭 구간별 잔차 중앙값을 계산해 대표 로그가격 안정화 값을 정한다.
4. validation에서 Quantile예측구간폭 임계값, gap 임계값, guard weight를 선택한다.
5. 검색 스냅샷에서 작가별 검색 보정값을 만들고 ±0.2 log로 제한한 lookup을 동결한다.

[사용 단계 / 운영 예측 단계]
1. 실제 가격 없이 작품/작가/검색 피처만 만든다.
2. 동결된 상류 Quantile 모델 출력 또는 캐시된 Quantile 출력값을 사용한다.
3. Quantile예측구간폭 구간에 맞는 동결 보정값을 적용한다.
4. guard 조건을 만족하면 낮은쪽40퍼센트기준 로그가격과 50:50으로 혼합한다.
5. 작가가 search_delta_lookup에 있으면 보정값을 더하고, 없으면 0을 더한다.
```

Cold에서 특히 혼동하기 쉬운 값은 다음처럼 해석한다.

| 항목 | 해석 |
|---|---|
| `y18_qwidth_pred_log` | 검색 피처와 Quantile 폭 안정화가 반영된 상류 대표 로그가격 후보. 후처리 artifact에서는 이 값을 입력으로 받음 |
| `lgb_q40_pred_log` | 과대예측 방어에 쓰는 낮은쪽 40% 지점 로그가격. 할인율이 아니라 가격 분포의 40% 분위 예측 |
| `quantile_width_log` | 높은쪽/낮은쪽 Quantile 예측 차이. 값이 클수록 모델이 해당 작품 가격을 불확실하게 본다는 뜻 |
| `구간별_잔차중앙값` | 학습/검증 때 실제 가격으로 미리 계산한 고정 보정값. 운영 예측 때 실제 가격을 새로 쓰지 않음 |
| `guard` | 학습 모델이 아니라 고정 조건부 방어 규칙. `quantile_width_log >= 1.4612207078910142`이고 대표가격과 q40의 차이가 `0.07715547281151025 log` 이상일 때만 작동 |
| `search_delta_lookup` | 실시간 검색이나 실시간 학습이 아니라 검증된 검색 스냅샷에서 만든 고정 작가별 보정표 |
| `cold_review_flag` | 모델이 틀렸다는 뜻이 아니라 검색 보정 근거 부족 또는 넓은 예측 폭 때문에 검수 필요성이 높다는 표시 |

### 6.4 Cold 모델과 산식

- 작가 검색 보정값 사용 방식: 실시간 검색 호출이 아니라 검증된 검색 스냅샷에서 만든 고정 lookup 사용

- 검색 피처 포함 대표 예측의 역할: LightGBM Quantile 회귀 후보와 Quantile예측구간폭 구간별 검증 잔차를 결합해 기준이 되는 대표 로그가격 생성

```text
검색피처포함_기초Quantile후보_로그가격
  = LightGBM_Quantile회귀후보(
      작품피처
      + 작가메타피처
      + 검색피처
      + 검색상호작용피처
    )

Quantile예측구간폭 = 저장된_Quantile예측폭

낮은쪽40퍼센트기준_로그가격 = LightGBM_40퍼센트_Quantile로그가격
```

- 대표 로그가격 안정화 방식: Quantile예측구간폭 구간별 검증 잔차 중앙값을 더해 보정

```text
Quantile예측구간폭_구간 = bucket(Quantile예측구간폭)

구간별_잔차중앙값
  = median(실제_로그가격 - 검색피처포함_기초Quantile후보_로그가격)
    within same Quantile예측구간폭_구간

구간별_보정값
  = clip(구간별_잔차중앙값, -0.25, +0.25)

검색포함_대표로그가격
  = 검색피처포함_기초Quantile후보_로그가격 + 구간별_보정값
```

- 과대예측 방어 조건:

```text
방어조건 =
  (Quantile예측구간폭 >= 1.4612207078910142)
  AND (검색포함_대표로그가격 - 낮은쪽40퍼센트기준_로그가격 >= 0.07715547281151025)
  AND (낮은쪽40퍼센트기준_로그가격 < 검색포함_대표로그가격)
```

- 방어조건 활성화 시 처리: 대표 로그가격을 낮은쪽 40% 지점 가격 쪽으로 낮춤

```text
과대예측방어_로그가격
  = 0.50 * 검색포함_대표로그가격
  + 0.50 * 낮은쪽40퍼센트기준_로그가격
```

- 방어조건 비활성화 시 처리: 대표 로그가격 유지

```text
과대예측방어_로그가격 = 검색포함_대표로그가격
```

- 최종 처리: 작가 검색 보정값 추가

```text
작가검색보정_로그값 =
  search_delta_lookup[artist_key]   # 작가별 보정값, ±0.2 로그로 제한(cap)
  if artist_key exists in lookup

작가검색보정_로그값 = 0
  if artist_key does not exist in lookup

최종_Cold_로그가격
  = 과대예측방어_로그가격 + 작가검색보정_로그값

최종_Cold_가격_KRW = exp(최종_Cold_로그가격)
```

#### 6.4.1 Cold 피처-계산 연결 순서도

```text
[입력 피처]
  - 작품 크기/매체/카테고리
  - 작가명, 작가 메타
  - 작가명 검색 결과 스냅샷
        |
        v
[작품 피처 생성]
  - area_cm2, log_area, aspect_ratio
  - medium_category, support_category
  - size_bucket, shape_bucket, medium_size_bucket
        |
        v
[작가 메타 피처 생성]
  - birth_year, career_stage, nationality
  - total_works_log, followers_log
  - artist_meta_*_missing
        |
        v
[검색 피처 생성]
  - search_result_count_log
  - search_art_match_ratio
  - search_gallery_ratio, search_market_ratio
  - search_quality_score
  - search_homonym_risk_grade
        |
        v
[LightGBM Quantile 회귀 후보]
  - 검색피처포함_기초Quantile후보_로그가격
  - 낮은쪽40퍼센트기준_로그가격
  - Quantile예측구간폭
        |
        v
[대표 로그가격 안정화]
  - Quantile예측구간폭_구간별 잔차중앙값을 더함
  - 구간별 보정값은 -0.25~+0.25 log로 제한
        |
        v
[과대예측 방어]
  - 폭이 넓고 대표가격이 낮은쪽40퍼센트기준보다 높으면 50:50 하향 혼합
        |
        v
[작가 검색 보정 lookup]
  - artist_key가 있으면 작가별 보정값 추가
  - 없으면 0
        |
        v
[최종 Cold 로그가격 -> exp() -> 원화 예측가격]
```

#### 6.4.2 Cold 계산 예시

> 아래 숫자는 계산 흐름을 설명하기 위한 예시이며, 실험 성능 지표나 특정 운영 작품의 실제 예측값이 아니다.

```text
1) 라우팅 판단:
  작가 매칭 신뢰도 = 0.58
  같은 작가 사용 가능 가격 이력 k = 0건
  0.58 < 0.80 이므로 Warm/Warm-lite 매칭 조건 미충족
  k = 0 이므로 Warm-lite 대상도 아님
  따라서 Cold 경로로 계산

2) 입력 작품 피처:
  작품 = mixed media, 65cm x 53cm
  area_cm2 = 65 * 53 = 3,445
  log_area = log(3,445) = 8.145
  aspect_ratio = 65 / 53 = 1.226
  medium_category = mixed_media
  support_category = unknown
  size_bucket = 중형 예시

3) 검색 스냅샷 원천값:
  검색 결과 수 = 12
  미술 문맥 결과 수 = 8
  갤러리/미술관 문맥 결과 수 = 3
  시장/판매 문맥 결과 수 = 2
  동명이인 위험 문맥 수 = 1
  작가 가격 이력은 0건이지만 검색 보정용 정규화 작가명은 고정 조회표(lookup)에 존재

4) 검색 파생 피처:
  search_result_count_log = log1p(12) = 2.565
  search_art_match_ratio = 8 / 12 = 0.667
  search_gallery_ratio = 3 / 12 = 0.250
  search_market_ratio = 2 / 12 = 0.167
  search_homonym_context_ratio = 1 / 12 = 0.083
  search_quality_score = 0.620  # 검색 문맥 비율과 품질 등급을 정규화한 점수

5) LightGBM Quantile 후보:
  LightGBM 입력 피처 묶음:
    작품 피처 = log_area 8.145, aspect_ratio 1.226, medium_category mixed_media, size_bucket 중형
    작가 메타 피처 = career_stage/국적/활동량/팔로워 로그값 또는 결측 플래그
    검색 피처 = search_result_count_log 2.565, search_art_match_ratio 0.667,
                search_gallery_ratio 0.250, search_market_ratio 0.167,
                search_homonym_context_ratio 0.083, search_quality_score 0.620
    검색 상호작용 피처 = search_quality_x_log_area, search_size_quality_bucket 등

  검색피처포함_기초Quantile후보_로그가격 = 17.800
  낮은쪽40퍼센트기준_로그가격 = 17.550
  Quantile예측구간폭 = 1.700

6) 대표 로그가격 안정화:
  Quantile예측구간폭 1.700이 속한 구간의 검증 잔차 중앙값 = +0.040
    - 이 값은 학습/검증 단계에서 실제 로그가격 - 기초 Quantile 후보 로그가격으로 미리 계산한 값
    - 예측 시점에는 실제 가격을 쓰지 않고, Quantile 폭 구간에 맞는 동결 보정값만 조회
  구간별_보정값 = clip(+0.040, -0.25, +0.25) = +0.040
  검색포함_대표로그가격 = 17.800 + 0.040 = 17.840

7) 과대예측 방어 조건 검사:
  Quantile예측구간폭 1.700 >= 1.4612207078910142
  검색포함_대표로그가격 - 낮은쪽40퍼센트기준 = 17.840 - 17.550 = 0.290
  0.290 >= 0.07715547281151025
  낮은쪽40퍼센트기준 17.550 < 검색포함_대표로그가격 17.840
  세 조건이 모두 참이므로 방어조건 활성화

8) 과대예측 방어 적용:
  과대예측방어_로그가격 =
    0.50 * 검색포함_대표로그가격
    + 0.50 * 낮은쪽40퍼센트기준_로그가격
  과대예측방어_로그가격 = 0.50 * 17.840 + 0.50 * 17.550 = 17.695

9) 작가 검색 보정 lookup 적용:
  search_delta_lookup[정규화작가명] = +0.060
    - 검색 스냅샷에서 갤러리/미술관 문맥이 가격 잔차를 설명한 작가별 고정 보정값
    - 실시간 검색 결과를 새로 호출하거나 즉석에서 학습하는 값이 아님
  작가검색보정_로그값 = clip(+0.060, -0.20, +0.20) = +0.060
  고정 조회표에 없었다면 이 값은 0이지만, 이 예시에서는 보정값이 존재

10) 최종 로그가격과 원화 변환:
  최종_Cold_로그가격 = 17.695 + 0.060 = 17.755
  최종_Cold_가격_KRW = exp(17.755) ~= 51,400,000원
```

### 6.5 Cold 성능 해석

- Cold 성능 기준 fixed test 3,099건 기준 성능:

| 단계 | MdAPE | MAPE | p95 APE | 해석 |
|---|---:|---:|---:|---|
| 검색포함 대표 로그가격 | 0.424663 | 0.991042 | 3.305298 | 검색 피처 포함 기준 예측 |
| 과대예측 방어 로그가격 | 0.417765 | 0.963963 | 2.537708 | 큰 오차 구간 방어 |
| 검색 보정만 추가한 로그가격 | 0.412921 | 0.875749 | 2.937449 | 평균 오차 개선 |
| 과대예측 방어 + 검색 보정 | 0.409820 | 0.849260 | 2.346465 | 평균 오차와 큰 오차를 동시에 가장 낮춤 |

- Cold 성능 기준 모델 해석: 신규/저이력 작가 상황에서 검색 문맥을 가격 예측 신호로 사용
- 불확실성 처리: 불확실성이 큰 작품은 낮은쪽 40% 지점 가격 기준으로 낮춰 p95 큰 오차를 줄임

## 7. Warm/Warm-lite/Cold 비교 요약

| 항목 | Warm | Warm-lite | Cold |
|---|---|---|---|
| 목적 | 같은 작가 이력이 5건 이상인 작품에서 정밀 비교군 기준가격을 안정적으로 보정 | 같은 작가 이력이 1~4건뿐인 작품에서 작가 실제 가격 신호를 최대한 활용 | 같은 작가 이력이 없거나 매칭이 불확실한 작품을 작품·작가 메타·검색 문맥으로 추정 |
| 적용 조건 | `작가매칭신뢰도점수 >= 0.80` AND 이력 `5건 이상` | `작가매칭신뢰도점수 >= 0.80` AND 이력 `1~4건` | 이력 `0건`, 매칭 실패, 입력 부족, 동명이인 위험 또는 검수 필요 |
| 학습 단계 요약 | 과거 Warm 데이터로 유사작품 찾기 단계, 보조안정 Warm 축, Huber 잔차 보정, 위험도 라우터를 학습/검증 후 동결 | 저이력 상황을 fold/leave-one-out으로 재현하고, 작가 이력 통계 피처 위에 LightGBM Quantile full/lean 모델과 LightGBM Huber residual 보정층을 학습/검증 후 동결 | 작품/작가/검색 피처로 LightGBM Quantile 모델, 구간별 잔차 보정표, guard 조건, 검색 보정 lookup을 학습/검증 후 동결 |
| 사용 단계 요약 | 새 작품의 같은 작가 비교군 기준가격과 보조안정 값을 만들고, 잔차 보정과 위험도 라우터를 적용 | 새 작품의 1~4건 작가 이력 통계를 만들고, full/lean Quantile q50 평균에 clipped Huber residual 보정을 더함 | 새 작품의 작품/작가/검색 피처를 동결 Quantile 모델과 보정 lookup에 넣고, 필요한 경우 과대예측 방어 적용 |
| 계산 순서 | 유사작품 비교군 생성 → w700/w850 기준가격 → Huber 잔차 보정 → 위험도 라우터 → `exp()` | 작가 이력 통계 생성 → Quantile full/lean q50 평균 → LightGBM Huber residual clip 보정 → 신뢰도 표시 정책 부여 → `exp()` | 검색 피처 조회 → LightGBM Quantile 후보 → 구간별 잔차 안정화 → 과대예측 방어 → 검색 보정 → `exp()` |
| 핵심 피처 | 같은 작가 유사작품 비교군, 보조 안정 Warm 예측 로그가격, 수축 prior, 로그면적, 비교군 표본 수, Quantile예측구간폭, 신뢰도 구간 | 작품 크기/매체/지지체, 작가 1~4건 로그가격 통계, 면적단가 통계, 이력 매칭 단계, fallback 통계 | 작품 크기/형태/매체, 작가 메타, 검색량, 검색 품질, 미술/전시/갤러리/시장 문맥, Quantile예측구간폭 |
| 대표 산식 | `최종_Warm_로그가격 = route(기본후보_보정로그가격, 대안후보_보정로그가격, 작품단위위험도)` | `최종_Warm-lite_로그가격 = lgbq_full_lean_avg + clip(0.50 * LightGBM_Huber_잔차, -0.10, +0.10)` | `최종_Cold_로그가격 = 과대예측방어_로그가격 + 작가검색보정_로그값` |
| 불확실성 처리 | 위험도가 높고 대안 후보가 0.005 log 이상 낮을 때만 보수 대안으로 교체 | 이력 1건은 `confidence_grade=warm_lite_low`, `display_policy=wide_range_with_review_flag`를 부여하되 최종 로그가격 산식은 바꾸지 않음 | `Quantile예측구간폭 >= 1.4612207078910142`이고 대표가격이 낮은쪽 40% 기준보다 `0.07715547281151025 log` 이상 높으면 50:50 하향 혼합 |
| 성능 기준 | fixed test 607행: `0.104326 / 0.235814 / 0.739416` | 실존 저이력 LOO 1,947행: `0.107246 / 0.275773 / 0.852026` | fixed test 3,099행: `0.409820 / 0.849260 / 2.346465` |
| 해석 | 기준가격을 크게 흔들지 않고 위험한 작품만 방어하는 5건 이상 경로 | Cold보다 훨씬 강한 작가 실제 가격 신호를 쓰되 소표본 위험을 등급으로 관리 | 작가 이력이 없는 상황에서 검색 문맥과 과대예측 방어를 결합하는 경로 |

## 8. 추가 성능 개선 방향

### 8.1 핵심 판단

- 현재까지의 실험 결과 기준: 추가 성능 개선의 가장 큰 병목은 모델 구조 자체보다 데이터 품질과 데이터 커버리지
- Warm 개선 방향: 이미 안정화된 기준가격을 크게 바꾸지 않는 구조로 수렴했으므로, 저신뢰 구간의 유사작품 데이터 보강이 우선
- Cold 개선 방향: 작가 이력과 비교가격이 부족한 상황을 다루는 모델이므로, 작가/작품/검색 문맥 데이터 수집이 성능 개선에 직접적인 영향을 줌
- 모델 보정의 역할: 현재 보유 데이터 안에서 오차가 반복되는 구간을 줄이는 작업
- 데이터 수집의 역할: 모델이 기준가격을 더 정확하게 잡을 수 있도록 가격 판단에 필요한 근거 자체를 늘리는 작업

### 8.2 실험 결과 기반 근거

| 관찰 내용 | 실험에서 확인된 현상 | 해석 |
|---|---|---|
| Warm은 기준가격 의존도가 높음 | WMIN8 후보는 `미세보정전_기준로그가격`에 매우 작은 `최종보정값`만 더하는 구조 | 기준가격이 잘못 잡힌 작품은 큰 보정보다 기준가격 생성 근거를 보강하는 편이 안정적 |
| Warm에서 작품 크기 피처 영향이 큼 | `PRE-PP-W`(WMIN8 이전의 별도 크기 피처 영향 점검 실험, 베이스라인이 달라 절대 수치는 WMIN8과 직접 비교 대상 아님) 크기 피처 제거 검증에서 MdAPE가 `0.2126 → 0.5671`, p95 APE가 `1.3194 → 4.9148`로 악화 | 크기, 면적, 형태, 매체/지지체 정보의 정규화 품질이 성능에 중요 |
| Warm 저신뢰 구간은 보정 상한이 자동으로 줄어듦 | `유사작품표본수`, `유사작품가격범위비율`, `Quantile예측구간폭`이 위험도 계산에 사용됨 | 유사작품 표본이 부족하거나 가격 분산이 큰 구간은 모델이 의도적으로 조심스럽게 움직임 |
| Cold 성능 기준은 검색 피처와 보수 방어로 개선됨 | 검색 보정과 과대예측 방어를 결합하면 MAPE가 `0.991042 → 0.849260`, p95 APE가 `3.305298 → 2.346465`로 개선 | 신규/저이력 작가에서는 작가 검색 문맥과 불확실성 판단이 핵심 개선 요인 |
| Cold 구간별 보정은 추가 개선 여지를 보임 | 지지체/크기 구간, tail-risk 구간, 예측구간폭 구간 보정에서 validation p95 APE가 낮아짐 | 구간별 표본이 더 충분해지면 보정값을 더 안정적으로 추정할 수 있음 |
| CatBoost(대체 gradient boosting 모델) 등 대체 모델만으로는 우위가 확인되지 않음 | 같은 split 비교에서 Cold LightGBM 기준 모델이 CatBoost 기준 모델보다 안정적 | 현재 단계에서는 모델 교체보다 데이터 보강과 구간별 검증 데이터 축적이 우선 |

### 8.3 우선 수집 데이터

| 우선순위 | 수집 데이터 | 필요한 이유 | 영향을 받는 경로 |
|---:|---|---|---|
| 1 | 같은 작가의 실제 거래/낙찰/판매 가격 | Warm/Warm-lite 기준가격의 직접 근거. Cold에는 같은 작가 기준가격으로 직접 들어가지 않고, 전체 학습 분포와 작가 메타·검색 보정 검증 데이터로 간접 기여 | Warm, Warm-lite, Cold(간접) |
| 2 | 유사작품 비교 가격 | 같은 작가 데이터가 부족할 때 기준가격을 안정화 | Warm, Cold |
| 3 | 작품 크기/형태 원천값 | 면적, 로그면적, 가로세로비, 대형 여부 계산의 원천 | Warm, Cold |
| 4 | 매체/지지체 정규화 데이터 | oil/acrylic/canvas/paper 등 재료 조합별 가격 차이 반영 | Warm, Cold |
| 5 | 제작연도와 작품 카테고리 | 작품의 시기, 장르, 희소성 차이 반영 | Warm, Cold |
| 6 | 신규/저이력 작가의 첫 가격 이력 1건+ | 현재 0.1v API에서는 가격 1건 확보 시 Cold에서 Warm-lite로 전환 가능 — PP-WCUT4 전체 기준 MdAPE `0.5429 → 0.1092`, k별 기준 Cold `0.507~0.564` → Warm-lite `0.095~0.120` | Warm-lite |
| 7 | 운영 매칭 로그(입력 작가명 ↔ 확정 artist_key) | 매칭 점수 캘리브레이션과 사전 밖 동명이인율 최종 추인 (현재 proxy 5.0%) | 라우팅 전체 |
| 8 | 작가 생년, 국적, 경력 단계 | 작가 세대와 시장 위치 반영 | Cold 중심, Warm 보조 |
| 9 | 전시 수, 갤러리/미술관 이력 | 작가 활동성과 신뢰도 반영 | Cold 중심 |
| 10 | 작가 작품 수, 판매 중 작품 수, 팔로워 수 | 작가 인지도와 시장 노출도 반영 | Cold 중심 |
| 11 | 작가명 검색 결과 검증 데이터 | 동명이인 위험 제거, 미술/전시/시장 문맥 분리 | Cold 중심 |
| 12 | 큰 오차 발생 작품의 사후 라벨 | p95 APE를 만드는 tail 구간 원인 분석 | Warm, Cold |

### 8.4 데이터 수집과 모델 개선의 연결 구조

```text
[추가 데이터 수집]
  - 거래/낙찰/판매 가격
  - 작품 크기/매체/제작연도
  - 작가 메타
  - 전시/갤러리/검색 문맥
        |
        v
[원천 데이터 정규화]
  - 가격 단위 통일
  - 크기/면적/형태 계산
  - 매체/지지체 표준화
  - 작가명/동명이인 정리
        |
        v
[파생 피처 재생성]
  - 유사작품표본수
  - 유사작품가격범위비율
  - size_bucket / support_size_bucket
  - 검색품질점수
  - Quantile예측구간폭
        |
        v
[Warm/Warm-lite/Cold 모델 재학습 또는 보정값 재산출]
  - Warm 기준가격 안정화
  - Warm 미세 보정 위험도 재계산
  - Cold LightGBM Quantile 회귀 재학습
  - Cold 구간별 잔차 보정값 재산출
        |
        v
[fixed test 기준 재검증]
  - MdAPE
  - MAPE
  - p95 APE
  - 구간별 오차
```

### 8.5 운영 관점의 결론

- 단기 개선: 문서 성능 기준 데이터에서 구간별 보정값, 과대예측 방어 조건, 검색 보정값을 정교화
- 중기 개선: Warm 저신뢰 구간과 Cold 신규/저이력 작가 구간의 비교가격과 작가 메타를 집중 보강
- 장기 개선: 작가명 검색 결과를 자동 수집하되, 동명이인/무관 결과를 검증하는 라벨링 체계 구축
- 우선순위 판단: 모델 튜닝만 반복하기보다, 오차가 큰 구간의 데이터가 실제로 부족한지 먼저 확인하고 해당 구간부터 수집
- 예상 효과: 데이터가 보강되면 기준가격 자체가 안정화되고, 보정 모델은 더 작은 폭으로도 같은 성능 개선을 낼 수 있음

## 9. 재현 가능성

- 재현 기준: 문서 성능 기준 모델별 fixed test 또는 독립 재현 파일 보유
- 주의: PP258 재현 패키지는 이전 Warm 기준선이며, WMIN8 후보 성능(`MAPE 0.235814`)의 직접 재현 근거가 아님

| 구분 | 실행 또는 확인 파일 | 결과 |
|---|---|---|
| Warm WMIN8 후보 성능 파일 | `models/track6/warm_wmin8_operational_candidate/config/warm_model_policy_wmin8.json` | fixed test 607건, MdAPE 0.104326 / MAPE 0.235814 / p95 APE 0.739416 |
| Warm WMIN8 후보 parity 검증 | `experiments/track6/PP-WMIN10_warm_wmin8_api_fixed_test_parity/reports/result_report.md` | 607/607건 성공, 최대 로그가격 차이 5.33e-15 |
| Warm WMIN2 정밀 비교군 매칭률 | `experiments/track6/PP-WMIN2_warm_artist_min1_svc_numeric/reports/result_report.md` | 최소 표본 1 적용 후 fixed test 정밀 비교군 매칭률 81.9% |
| Warm WMIN4 선행 0604 stress | `experiments/track6/PP-WMIN5_warm_min1_0604_stress/reports/result_report.md` | WMIN4 min1 선행 후보의 신규 라벨 안전성 점검. WMIN8 직접 선택 지표는 아님 |
| 이전 Warm 기준선 재현 | `experiments/track6/SUB-WARM-PP258_operational_fixed_test_submission/outputs/pp258_test_metrics.json` | PP258 기준 MAPE 0.269888. WMIN8 대비 비교 기준으로만 사용 |
| Warm-lite 이력 절단 근거 | `docs/track6/experiments/postprocessing_experiment_matrix.md` | PP-WCUT1: min5는 k=5 단절 개선, min1은 k=1부터 Cold 대비 개선 |
| Warm-lite Quantile residual 성능 검증 | `experiments/track6/PP-WLITE-Q3_quantile_residual_correction_validation/reports/result_report.md` | 1,947행, `qavg_lgbres_s05_cap010` 0.107246 / 0.275773 / 0.852026 |
| Warm-lite Quantile residual 동결 bundle | `models/track6/warm_lite_quantile_residual_v0.1/manifest.json` | selected candidate `qavg_lgbres_s05_cap010`, 현재 0.1v Warm-lite 채택 bundle |
| Warm-lite Quantile residual parity | `experiments/track6/PP-WLITE-Q5_quantile_residual_bundle_api_parity/artifacts/*.json` | bundle replay 7,284행 max log diff 3.55e-15, v0.1 HTTP API 24건 max log diff 0.0 |
| Warm-lite 경로 분리 저이력 검증 | `experiments/track6/PP-WCUT4_real_low_history_validation/reports/result_report.md` | 1,947행 기준 Warm-lite 저이력 경로 0.1092 / 0.2866 / 0.8765, Cold 0.5429 / 0.9946 / 2.5358 |
| Warm-lite vs WMIN8 svc-core 저이력 비교 | `experiments/track6/PP-WMIN9C_warm_lite_vs_wmin8_lowhistory/reports/result_report.md` | 1~4건 전체 Warm-lite 0.1092 / 0.2866 / 0.8765, WMIN8 svc-core proxy 0.1291 / 0.2932 / 0.9163 |
| 1~4건 Warm 통일 가능 여부 판단 | `experiments/track6/PP-WMIN9E_lowhistory_warm_only_decision/reports/result_report.md` | k=2/3 Warm-lite 전 지표 우세, k=1/4 혼합, 1~4 전체 Warm-lite 전 지표 우세 |
| 1~4건 WMIN8 부분 재학습 검증 | `experiments/track6/PP-WMIN11_lowhistory_full_wmin8_clean_pilot/reports/result_report.md` | 1,947행 기준 Warm-lite 0.1092 / 0.2866 / 0.8765, 부분 재학습 라우팅 후보 0.1480 / 0.2931 / 0.8716. frozen full WMIN8/PPV8 미사용 |
| 5건 이상 Warm-lite 강제 적용 비교 | `experiments/track6/PP-WMIN9D_forced_warm_warmlite_boundary/reports/result_report.md` | 607행 기준 WMIN8 0.104326 / 0.235814 / 0.739416, 강제 Warm-lite 0.108722 / 0.248054 / 0.837824 |
| 현재 0.1v 라우팅 상수 | `src/visionai/price_engine/api/official_v0_1_service.py` | match score 0.80, 이력 5건 이상 Warm, 1~4건 Warm-lite |
| 라우팅 임계 재검증 | `experiments/track6/PP-E2E1_routing_pipeline_replay/reports/result_report.md` | v2 기준 0.90 누수 61.5~71.6%, 0.80 누수 3.7~24.4% |
| Cold 재현 스크립트 | `scripts/track6/verify_cold_best_research_reproducibility.py` | fixed test 3,099건 재현 |
| Cold 성능 결과 | `models/track6/cold_prediction_v0.3/reproduction/best_research_reproducibility_check.json` | `all_passed=true`, 최대 지표 차이 1.110e-16 |

- Cold 성능 기준 모델 재현 검증 통과 항목:

| 검증 항목 | 값 |
|---|---:|
| test 작품 수 | 3,099 |
| 검색 lookup 작가 수 | 372 |
| fixed test 검색 커버리지 | 1.000000 |
| 후처리기와 독립 계산식의 로그가격 최대 차이 | 0.000e+00 |
| 재계산 지표와 기록 지표의 최대 차이 | 1.110e-16 |
| 전체 재현 통과 여부 | true |

## 10. 테스트 방식 검증

- 검증 목적: 같은 입력에 대한 결과 변동, 재현 실패, row 순서 영향, label 누수, split 중복, 반복 OOF/holdout 안정성 의심 항목 점검
- 별도 감사 문서: `docs/track6/experiments/warm_cold_test_method_validity_audit.md`
- 별도 감사 HTML: `docs/track6/experiments/warm_cold_test_method_validity_audit.html`

| 구분 | 검증 결과 | 핵심 확인 내용 |
|---|---|---|
| Warm | 통과 | fixed test와 validation OOF 지표가 저장 지표와 동일하게 재현됨 |
| Cold | 통과 | 기존 Cold 재현 검증 `all_passed=true`, 기록 지표와 재계산 지표 최대 차이 `1.110e-16` |
| 같은 입력 반복 실행 | 통과 | Warm/Cold 모두 row 순서를 랜덤으로 바꿔도 최종 예측 로그가격 차이 `0.000e+00` |
| label 누수 의심 | 통과 | `actual_price`, `actual_log`를 임의 값으로 바꿔도 최종 예측 로그가격 변화 없음 |
| split 중복 의심 | 통과 | validation/test row id 중복과 split 간 overlap 없음 |
| OOF/holdout 안정성 | 통과 | Warm은 반복 holdout/bootstrap 근거 확인, Cold guard는 row/artist holdout에서 MAPE와 p95 개선확률 유지 |

- Warm 테스트 방식 판단:

```text
fixed test 지표 최대 재현 차이       = 0.000e+00
validation OOF 지표 최대 재현 차이  = 0.000e+00
row 순서 셔플 예측 차이             = 0.000e+00
label 변경 후 예측 차이             = 0.000e+00
```

- Cold 테스트 방식 판단:

```text
기록 지표와 재계산 지표 최대 차이     = 1.110e-16
guard 임계값 재계산 차이              = 0.000e+00
후처리기와 독립 계산식 예측 차이       = 0.000e+00
row 순서 셔플 예측 차이                = 0.000e+00
label 변경 후 예측 차이                = 0.000e+00
```

- 해석:

- 고정된 문서 성능 기준 artifact에서는 같은 입력을 넣었을 때 결과가 달라지는 현상은 확인되지 않음
- 실제 가격 label은 예측값 계산에 사용되지 않고, 평가 지표 산출에만 사용됨
- validation과 test는 row id 기준으로 분리되어 있어 같은 작품이 양쪽에 동시에 들어간 흔적은 확인되지 않음
- 반복 OOF/holdout 결과는 fixed test 지표를 대체하는 값이 아니라, 후보가 특정 split에만 우연히 맞은 것이 아닌지 확인하는 안정성 근거로 사용
- 새 데이터 수집, split 변경, 재학습, 검색 피처 재생성 시 동일 감사 스크립트를 다시 실행해야 함

### 10.1 0.1v 라우팅 모니터링 하네스

- 모니터링 대상: 라우팅 로그를 모니터링 하네스에 직접 연동해 5개 항목(R1~R5)을 점검
- 상태 구분: 아래 수치는 현재 0.1v API와 같은 3-경로 정책(0.80 + Warm-lite 포함)의 모니터링 검증 결과다. 실측 성능과 동명이인율은 라벨/검수 결정이 쌓이면 갱신한다
- 연동 결과 (라우팅 로그 637건 기준, 데이터 가공 없음):

| 점검 항목 | 결과 | 해석 |
|---|---|---|
| R1 라우팅 규칙 위반 | 0건 | 0.1v 정책 기준 매칭 임계 0.80과 이력 조건을 정확히 준수 |
| R2 경로별 트래픽 비중 | Warm 97.2% / Cold 1.4% / Warm-lite 0.9% / 검수대기 0.5% | 초기 트래픽이 고이력 작가에 집중 (Warm-lite/Cold 표본 적음) |
| R3 보조정보 없이 통과한 비중 | 0.0 | 현재 Warm 트래픽은 모두 작가키 직접 일치(매칭점수 1.0)이라 보조정보 없이 통과한 사례 없음 |
| R4 Warm-lite 실측 성능 | 측정 대기 | 확정 판매 가격 라벨이 아직 부족(최소 50건 기준 미달) |
| R5 사전 밖 동명이인율 | 측정 대기 | 동명이인 검수 결정이 아직 없음(대기 92건) → 추정치 5% 유지 |

- 정직한 상태 해석:

- 하네스와 로그 연동 자체는 검증 완료 — 0.1v 정책 기준 라우팅 규칙 준수(R1 0건)와 트래픽 분포(R2)는 데이터로 확인됨
- R4(실측 성능)와 R5(동명이인율)는 운영 초기라 라벨·검수 결정이 쌓이기 전이므로 "측정 대기"가 정상 상태 — 없는 값을 만들지 않고 검증 시점의 추정치(동명이인율 5%)와 동결 기준을 유지
- 자동 측정 트리거: 확정 판매 라벨이 Warm-lite 이력 구간별 50건 이상 쌓이면 R4가, 동명이인 검수 결정이 쌓이면 R5가 자동으로 추정치를 실측치로 대체
- 동명이인율 경보 기준: 사전 밖 동명이인율이 16.7%(5건 이상 구간의 가장 보수적인 허용 한계 — 1~4건 구간 허용치는 27.8~30.4%이나, 경보는 더 엄격한 16.7% 기준 적용)를 넘으면 0.1v 매칭 임계 0.80 재검토 경보 발생

## 11. 모델 적용 방식 요약

- 현재 0.1v API 구조: Warm, Warm-lite, Cold/검수대기의 3-경로 구조. `작가매칭신뢰도점수 >= 0.80` AND 가격 이력 `5건 이상`이면 Warm, `1~4건`이면 Warm-lite, 그 외 예측 가능 입력은 Cold 또는 검수대기
- 현재 0.1v API 주의: 내부 모델 artifact 버전명과 API 버전은 분리해서 해석해야 한다. 예를 들어 `cold_prediction_v0.2_operational`은 Cold 내부 번들명이며, API 버전 표기는 이 문서 전체에서 0.1v로만 해석한다
- 문서 성능 기준 구조: Warm 5건 이상 WMIN8 후보, 1~4건 Warm-lite 0.1v 적용 경로, 0건 또는 매칭 실패 Cold 성능 기준 모델의 3-경로 구조
- Warm 적용 조건: 작가 매칭이 확실하고 같은 작가의 사용 가능한 학습 가격 이력이 5건 이상인 작품
- Warm 계산 방식: 정밀 유사작품 매칭(최소 표본 1) 기준가격 + Huber 잔차 보정, 위험도 상위 구간만 보수 대안 가중으로 조건부 교체
- Warm-lite 적용 조건: 작가 매칭이 확실하고 같은 작가의 사용 가능 가격 이력이 1~4건인 작품
- Warm-lite 계산 방식: 매칭 작가의 이력 1~4건으로 작가 가격 통계를 만들고, `LightGBM full/lean Quantile q50 평균 + clip(0.50 * LightGBM Huber residual, -0.10, +0.10)`으로 로그가격을 계산. 이력 1건은 `confidence_grade=warm_lite_low`, `display_policy=wide_range_with_review_flag`를 함께 반환
- Warm-lite 성능: 현재 채택 Quantile residual 모델은 실존 저이력 작가 1,947행 기준 MdAPE 0.107246, MAPE 0.275773, p95 APE 0.852026
- Warm-lite 유지 판단: 1~4건 전체에서 Warm-lite가 WMIN8 svc-core proxy보다 MdAPE/MAPE/p95 모두 낮고, 5건 이상에서는 WMIN8이 강제 Warm-lite보다 MdAPE/MAPE/p95 모두 낮아 현재 1~4건 Warm-lite, 5건 이상 Warm 분기를 유지한다
- 라우팅 모니터링: 매칭 임계 0.80(경계 비교 tolerance 필수), 모니터링 하네스(`monitor_warm_lite_routing.py`)로 규칙 위반·트래픽 분포·성능 경보 점검 — 라우팅 로그 637건 기준 R1 위반 0건, 상세 10.1절
- Cold 성능 기준 적용 조건: 같은 작가 이력이 0건이거나 작가 매칭이 불확실한 작품 (이력 1~4건은 Warm-lite 대상)
- Cold 성능 기준 계산 방식: 작품 피처, 작가 메타, 작가명 검색 피처를 함께 사용한 LightGBM Quantile 회귀 후보를 Quantile예측구간폭 구간별 검증 잔차로 안정화해 대표 예측가격 계산
- Cold 성능 기준 방어 방식: `Quantile예측구간폭 >= 1.4612207078910142`이고 대표 예측가격이 낮은쪽 40% 지점보다 `0.07715547281151025 log` 이상 높을 때 낮은쪽 가격 기준으로 낮춤
- Cold 성능 기준 최종 보정: 갤러리/미술관 검색 문맥 기반 작가별 보정값 추가
- Warm 후보 성능: fixed test 607건 기준 MdAPE 0.104326, MAPE 0.235814, p95 APE 0.739416. 2026-06-04 신규 라벨 stress는 WMIN4 min1 선행 후보의 안전성 근거로 별도 확인
- Cold 성능 기준 지표: fixed test 3,099건 기준 MAPE 0.849260, p95 APE 2.346465
- 최종 가격 산출: 각 경로는 로그가격 기준으로 계산한 뒤 `exp()`를 적용해 원화 예측가격으로 변환
- 재현 가능성: 재현 스크립트와 결과 파일을 통해 동일 지표 확인 가능

## 12. 내부 추적 정보

- 명칭 관리 기준: 본문에는 기능을 바로 이해할 수 있는 설명형 명칭 사용
- 재현 관리 기준: 실험 ID와 파일명은 재현 확인을 위한 별도 표에서 관리

| 문서용 이름 | 내부 추적 ID 또는 파일 | 설명 |
|---|---|---|
| Warm 이력 기반 조건부 유사작품 보정 모델 | `WMIN8 min1_route_w850_risk_q50_altlower_gap005`, 동결 `warm_wmin8_exact_runtime_candidate` | Warm 5건 이상 최종 후보 (2026-06-13 갱신, 후보 adapter parity 5.3e-15) |
| (이전) Warm 기준가격 기반 미세 보정 모델 | `PP258`, `ppopt256_pp252_residual_continue__thr=0p12__rs=0p025__ss=0p0__cap=5em05` | 이전 Warm 기준선 (참조) |
| Warm min1 검증 체인 | `PP-WMIN1~10` | proxy 검증→후보 서비스 adapter→보정 스택→2026-06-04 스트레스 평가→API parity 단계 검증 |
| 이전 Warm 재현 패키지 | `SUB-WARM-PP258_operational_fixed_test_submission` | PP258 fixed test 607건 재현 패키지, WMIN8 직접 재현 근거는 아님 |
| Warm-lite Quantile residual 기준가격 모델 | `warm_lite_quantile_residual_v0.1`, `PP-WLITE-Q1~Q5`, `PP-WCUT4`, `PP-WMIN9C/E/D` | 이력 1~4건 0.1v 채택 경로. 실존 저이력 검증, Quantile residual 성능 검증, bundle/API parity 통과 |
| 라우팅 정책(3-경로 + 임계 0.80) | `routing_policy_v0.1`, `PP-MCAL1/RMAP1/E2E1/RHO1`, `official_v0_1_service.py` | 재검증 근거·채택 조건·모니터링 하네스. 현재 0.1v 구현값은 0.80 + Warm-lite 포함 |
| Cold 검색 피처 포함 성능 기준 모델 | `COLD_BASE_RESEARCH_V1`, `v0.3 guard+search`, `guard_search_gm` | Cold fixed test 전체 지표 기준 성능 기준 모델 |
| Cold 재현 검증 | `verify_cold_best_research_reproducibility.py` | Cold 성능 기준 경로 재현 확인 |
