# 가격 예측 모델 성능 시험 양식 작성안

대상 시험항목: 가격 예측 모델 성능 (Regression task)  
대상 패키지: `KTCC_Warm_PP258_high_confidence_100_MAPE15_submission.zip`  
대상 모델: Warm 최종 운영 미세 보정 가격 예측 모델

## 5. 시험도구 (시험에 필요한 시험도구만 기재)

| No. | 도구명 | 용도 |
|---:|---|---|
| 1 | Python 3.9 이상 | 시험 스크립트를 실행하여 Warm 최종 운영 미세 보정 가격 예측 모델의 예측가격, Absolute Percentage Error, MAPE를 계산하고 결과 파일을 출력하는 데 사용한다. |
| 2 | Python 패키지 `numpy`, `pandas` | CSV 데이터 로딩, 수치 계산, 로그가격 변환, 예측가격 산출, MAPE 계산에 사용한다. `requirements.txt`로 설치 가능하다. |
| 3 | Visual Studio Code 1.103.0 또는 터미널 | 제출 패키지 폴더를 열고 `scripts/ktcc_pp258_price_mape_test.py` 실행 명령을 입력하여 시험을 진행하는 데 사용한다. |
| 4 | ZIP 압축 해제 도구 | 제출 압축 파일 `KTCC_Warm_PP258_high_confidence_100_MAPE15_submission.zip`을 시험용 PC에 압축 해제하는 데 사용한다. |

## 6. 의뢰자가 제시한 사항 (데이터, 스크립트, 용어)

### 6.1 의뢰자가 제시한 데이터

| No. | 데이터명 | 용량 | 확장자 | 설명 |
|---:|---|---:|---|---|
| 1 | `pp258_rank_context_features_validation_test` | 332 KB | csv | Warm 최종 운영 미세 보정 산식의 rank 기반 불확실성 및 row 위험도 계산을 재현하기 위한 validation/test 전체 1,126건 feature context 데이터. 정답 가격 없이 보정 상한 계산에 필요한 선행 Warm 예측값과 보정 신호를 포함한다. |
| 2 | `price_test_features_100` | 31 KB | csv | 가격 예측 모델 성능 평가에 사용하는 과제에서 작성한 학습에 활용되지 않은 작품 100건 시험 입력 데이터. `quantile_width`, `component_prediction_spread`, `l10_price_range_ratio`, `svc_group_n`, `current_vs_stable_gap_abs` 조건을 만족하는 작품 100건으로 구성된다. |
| 3 | `price_test_labels_100` | 4 KB | csv | 과제에서 작성한 학습에 활용되지 않은 작품 100건 시험 입력 데이터에 대응되는 정답 가격 데이터. `_track6_row_id`, `actual_log`, `actual_price`를 포함하며, 예측가격과 비교하여 Absolute Percentage Error 및 MAPE를 산출하는 데 사용한다. |
| 4 | `price_train_reference_validation_oof_519` | 173 KB | csv | 기존 Warm 실험의 validation out-of-fold 519건 reference 데이터. 최종 제출 스크립트의 MAPE 계산에는 직접 사용하지 않으며, 모델이 기존 실험 기준에서 어떤 검증 데이터 구간을 기반으로 구성되었는지 확인하기 위한 참고 데이터다. |
| 5 | `model_config` | 2 KB | json | Warm 최종 운영 미세 보정 가격 예측 모델의 파라미터, 과제에서 작성한 학습에 활용되지 않은 작품 100건 구성 조건, 성능 결과, 원 실험 후보 정보를 기록한 설정 파일이다. |

### 6.2 의뢰자가 제시한 스크립트

| No. | 스크립트명 | 설명 |
|---:|---|---|
| 1 | `ktcc_pp258_price_mape_test.py` | VS Code 또는 터미널에서 가격 예측 성능을 확인하기 위한 Python 실행 스크립트. 과제에서 작성한 학습에 활용되지 않은 작품 100건 입력 데이터와 정답 데이터를 읽고, Warm 최종 운영 미세 보정 산식으로 예측가격을 산출한 뒤 MAPE와 p95 APE 등 성능 지표를 출력한다. |

### 6.3 의뢰자가 제시한 용어

| No. | 용어 | 설명 |
|---:|---|---|
| 1 | 과제에서 작성한 학습에 활용되지 않은 작품 100건 | 가격 예측 모델 성능 평가를 위해 모델 학습에 사용하지 않은 별도 시험 데이터 100건. 예측 구간 폭, 모델 간 예측 차이, 유사작품 수 등 시험 데이터 구성 조건을 만족하는 작품으로 구성된다. |
| 2 | 로그가격 | 가격에 자연로그 `log()`를 적용한 값. 모델 내부에서는 로그가격으로 보정값을 계산하고, 최종 가격은 `exp(최종로그가격)`으로 원 가격 단위로 환산한다. |
| 3 | Warm 최종 운영 미세 보정 가격 예측 모델 | 미세 보정 전 기준 로그가격 위에 방향 분류 모델과 Huber 잔차 모델의 신호가 일치하는 경우에만 작은 보정값을 적용하는 가격 예측 모델이다. |
| 4 | MAPE | Mean Absolute Percentage Error. 각 작품의 `abs(실제가격 - 예측가격) / 실제가격`을 계산한 뒤 100건 평균을 산출한 값이다. 본 시험의 목표 기준은 15% 이하이다. |
| 5 | p95 APE | Absolute Percentage Error의 95퍼센타일 값. 큰 오차 구간의 안정성을 확인하기 위한 보조 성능 지표다. |
| 6 | quantile width | 예측 가격 구간의 폭을 나타내는 불확실성 신호. 값이 클수록 모델이 해당 작품 가격을 불확실하게 판단한 것으로 보고 보정 상한을 줄인다. |
| 7 | row 위험도 | 각 작품 row가 얼마나 보수적으로 보정되어야 하는지 나타내는 0~1 범위의 위험도 점수. 예측 구간 폭, 모델 간 예측 차이, 유사작품 수 등을 반영한다. |

## 7. 시험항목 평가 기준/방법 제시 및 시험 절차

### 7.1 시험항목 1

| 구분 | 내용 |
|---|---|
| 시험항목 명 | 가격 예측 모델 성능<br>- 시험목적: Warm 최종 운영 미세 보정 가격 예측 AI 모델이 과제에서 작성한 학습에 활용되지 않은 작품 100건 데이터에 대해 예측가격을 산출하고, 실제 가격 대비 MAPE가 15% 이하인지 확인하고자 한다. |
| 개발목표 | MAPE 15% 이하 |
| 시험구성 | 시험구성 1: 과제에서 작성한 학습에 활용되지 않은 작품 100건 가격 예측 성능 평가 |
| 시험도구 | 시험도구 1 ~ 4 |
| 시험 데이터 | 의뢰자가 제시한 데이터 1 ~ 5<br>의뢰자가 제시한 스크립트 1 |
| 시험절차 및 방법 | 1. 시험용 PC에서 제출 압축 파일 `KTCC_Warm_PP258_high_confidence_100_MAPE15_submission.zip`을 압축 해제한다.<br>2. VS Code 또는 터미널에서 압축 해제한 폴더 `KTCC_Warm_PP258_high_confidence_100_MAPE15_submission`을 연다.<br>3. Python 3.9 이상과 `numpy`, `pandas` 사용 가능 여부를 확인한다. 필요 시 `pip install -r requirements.txt`를 실행한다.<br>4. 터미널에서 `python scripts/ktcc_pp258_price_mape_test.py`를 실행한다.<br>5. 스크립트는 `data/pp258_rank_context_features_validation_test.csv`를 읽어 rank 기반 불확실성 및 row 위험도 계산 기준을 준비한다.<br>6. 스크립트는 `data/price_test_features_100.csv`의 과제에서 작성한 학습에 활용되지 않은 작품 100건 입력 데이터를 읽고, 각 row가 시험 데이터 구성 조건을 만족하는지 확인한다.<br>7. 각 row에 대해 Warm 최종 운영 미세 보정 산식을 적용한다. 계산식은 `최종로그가격 = 미세보정전_기준로그가격 + 최종보정_적용값`, `최종가격 = exp(최종로그가격)`이다.<br>8. 스크립트는 `data/price_test_labels_100.csv`의 실제 가격을 읽고, 각 row별 `Absolute Percentage Error = abs(실제가격 - 예측가격) / 실제가격`을 계산한다.<br>9. 100건의 Absolute Percentage Error 평균을 계산하여 MAPE를 산출한다.<br>10. `outputs/ktcc_pp258_price_mape_metrics.json`, `outputs/ktcc_pp258_price_mape_metrics.csv`, `outputs/ktcc_pp258_price_predictions_100.csv`에서 결과를 확인한다.<br>11. `MAPE <= 0.15`이면 가격 예측 모델 성능 목표를 만족한 것으로 판정한다. 본 제출 패키지의 실행 결과는 MAPE `0.1254585719`, 즉 `12.55%`로 PASS이다. |

### 7.2 시험 결과 확인 기준

| 항목 | 산출값 | 판정 기준 | 결과 |
|---|---:|---:|---|
| 평가 데이터 수 | 100건 | 100건 | 적합 |
| MAPE | 0.1254585719 | 0.15 이하 | PASS |
| MdAPE | 0.1006963136 | 참고 지표 | 참고 |
| p95 APE | 0.3274708354 | 참고 지표 | 참고 |
| RMSE log | 0.1660933741 | 참고 지표 | 참고 |

### 7.3 실행 명령

```bash
python scripts/ktcc_pp258_price_mape_test.py
```

### 7.4 예상 출력

```text
KTCC Warm 최종 운영 미세 보정 가격예측 MAPE 시험 결과
- 평가 건수: 100
- MdAPE: 0.1007
- MAPE: 0.1255 (12.55%)
- p95_APE: 0.3275
- 15% 이하 목표 통과 여부: PASS
```
