# 가격예측 모델 성능 시험 제출 양식

## 5. 시험도구

| No. | 도구명 | 용도 |
| --- | --- | --- |
| 1 | Python 3.9 이상 | 시험용 스크립트 실행, 가격 예측값 산출, MAPE/MdAPE/p95_APE 계산에 사용한다. |
| 2 | pandas 3.0.1 | 시험 데이터 CSV와 label CSV를 읽고, 예측 결과와 정답 가격을 조인하는 데 사용한다. |
| 3 | numpy 2.4.3 | 로그 가격 변환, 지수 변환, 오차율 계산 등 수치 연산에 사용한다. |
| 4 | scikit-learn 1.8.0 | 제출 모델의 Huber residual 보정 pipeline을 로드하고 예측하는 데 사용한다. |
| 5 | joblib 1.5.3 | 저장된 모델 artifact(`warm_high_confidence_residual_huber.joblib`)를 로드하는 데 사용한다. |
| 6 | Visual Studio Code 또는 터미널 | 시험용 폴더를 열고 `ktcc_price_mape_test.py` 스크립트를 실행하는 데 사용한다. |

## 6. 의뢰자가 제시한 사항

### 6.1 의뢰자가 제시한 데이터

| No. | 데이터명 | 용량 | 확장자 | 설명 |
| --- | --- | ---: | --- | --- |
| 1 | price_train_reference_110 | 47 KB | csv | validation split에서 고신뢰 확장 조건을 적용한 뒤 `_track6_row_id` 중복을 제거한 학습 reference 데이터 110건. 모델 보정 학습 근거와 피처 구성을 확인하기 위한 데이터다. |
| 2 | price_test_features_100 | 40 KB | csv | 시험장에서 모델 예측에 사용하는 고신뢰 테스트 입력 데이터 100건. 정답 가격은 포함하지 않는다. |
| 3 | price_test_labels_100 | 4 KB | csv | 시험 결과 검증에 사용하는 테스트 정답 데이터 100건. `_track6_row_id`, `actual_log`, `actual_price`를 포함한다. |
| 4 | warm_high_confidence_residual_huber | 4 KB | joblib | Warm/HCOEF 안정 기준가 위에 적용하는 Huber residual 보정 모델 artifact. |
| 5 | model_config | 8 KB 이하 | json | 모델명, 입력 피처, residual 보정폭, validation OOF 성능, test 성능을 기록한 설정 파일. |

### 6.2 의뢰자가 제시한 스크립트

| No. | 스크립트명 | 설명 |
| --- | --- | --- |
| 1 | ktcc_price_mape_test.py | 시험장에서 실행하는 가격예측 성능 확인 스크립트. 모델 artifact를 로드하고, 테스트 입력 100건에 대해 가격을 예측한 뒤 label과 조인하여 MAPE를 계산한다. |
| 2 | requirements.txt | 시험 스크립트 실행에 필요한 Python 패키지 버전을 명시한 파일. |

### 6.3 의뢰자가 제시한 용어

| No. | 용어명 | 설명 |
| --- | --- | --- |
| 1 | MAPE | Mean Absolute Percentage Error. `mean(abs(pred_price - actual_price) / actual_price)`로 계산하는 평균 절대비율오차다. 본 시험의 목표 지표이며 15% 이하를 목표로 한다. |
| 2 | MdAPE | Median Absolute Percentage Error. 절대비율오차의 중앙값이며, 대표적인 일반 오차 수준을 확인하기 위해 함께 산출한다. |
| 3 | p95_APE | 절대비율오차의 95 분위값. 큰 오차가 발생하는 끝단 위험을 확인하기 위한 보조 지표다. |
| 4 | 고신뢰 Warm 구간 | 예측 범위 폭, 모델 간 예측 일치도, 유사작품 표본 수, 기준가 gap 조건을 만족하는 가격예측 대상 구간이다. 신뢰도가 낮은 후보와 validation 중복 row-id는 학습 reference에서 제외한다. |
| 5 | Huber residual 보정 | Warm/HCOEF 기준 로그 가격과 실제 로그 가격의 잔차를 HuberRegressor로 학습하여 기준 예측값을 제한적으로 보정하는 방식이다. |

## 7. 시험구성 1

| 구분 | 내용 |
| --- | --- |
| 시험항목 명 | 가격 예측 모델 성능<br>시험목적: 고신뢰 Warm 가격예측 구간의 작품 100건에 대해 AI 가격예측 모델이 산출한 예측 가격의 MAPE가 15% 이하인지 확인하고자 한다. |
| 개발목표 | MAPE 15% 이하 |
| 시험구성 | 시험구성 1 |
| 시험도구 | 시험도구 1 ~ 6 |
| 시험 데이터 | 의뢰자가 제시한 데이터 1 ~ 5<br>의뢰자가 제시한 스크립트 1 ~ 2 |
| 시험절차 및 방법 | 1. 시험용 PC에서 제출 폴더 `ktcc_runtime`을 연다.<br>2. Python 3.9 이상 환경을 준비하고, 필요 시 `pip install -r requirements.txt`를 실행한다.<br>3. 실행 전 `data/price_test_features_100.csv`, `data/price_test_labels_100.csv`, `artifacts/warm_high_confidence_residual_huber.joblib` 파일이 존재하는지 확인한다.<br>4. 터미널 또는 VS Code에서 `python scripts/ktcc_price_mape_test.py`를 실행한다.<br>5. 스크립트가 모델 artifact를 로드하고 테스트 입력 100건에 대해 `final_price`를 산출한다.<br>6. 스크립트가 label 파일과 예측 결과를 `_track6_row_id` 기준으로 조인한다.<br>7. 각 row의 `absolute_percentage_error = abs(final_price - actual_price) / actual_price`를 계산한다.<br>8. 100건의 평균 절대비율오차인 MAPE를 계산한다.<br>9. `outputs/ktcc_price_mape_metrics.csv`와 콘솔 출력에서 MAPE가 15% 이하인지 확인한다.<br>10. 본 제출 패키지 기준 실행 결과는 MAPE 12.60%로 목표 기준을 만족한다. |

## 시험 결과 요약

| 항목 | 결과 |
| --- | ---: |
| 평가 건수 | 100 |
| MdAPE | 9.94% |
| MAPE | 12.60% |
| p95_APE | 31.18% |
| RMSE_log | 0.1663 |
| 15% 이하 목표 | PASS |
