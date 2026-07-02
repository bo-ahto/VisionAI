# Warm PP258 최종 운영 모델 제출용 재현 패키지

작성일: 2026-06-10 16:51:54

이 패키지는 `Warm 가격 예측 최종 운영 모델 상세 리포트`에 나온 PP258 최종 운영 모델을 fixed test 기준으로 재현하기 위한 제출 후보 패키지다.

## 중요한 전제

- 이 패키지는 제출용 고신뢰 100건 MAPE 15% 실험이 아니다.
- 이 패키지는 현재 리포트 모델의 기존 Warm fixed test 607건 기준 재현 패키지다.
- raw 작품 정보만 넣어 처음부터 Warm 후보 전체를 생성하는 API형 패키지가 아니다.
- 입력 CSV에는 최종 PP258 미세 보정에 필요한 선행 Warm 로그가격과 보정 신호가 이미 포함되어 있다.

## 실행 방법

```bash
pip install -r requirements.txt
python scripts/pp258_reproduce_fixed_test.py
```

기본 실행은 `data/pp258_model_input_validation_test.csv`를 읽고 `test` split 607건을 평가한다.

## 포함 파일

- `data/pp258_model_input_validation_test.csv`: validation/test 전체 1,126건 재현 입력
- `data/pp258_fixed_test_features.csv`: fixed test 607건 feature-only 입력
- `data/pp258_fixed_test_labels.csv`: fixed test 607건 label
- `scripts/pp258_reproduce_fixed_test.py`: PP258 최종 산식 재현 스크립트
- `outputs/pp258_test_predictions.csv`: fixed test 예측 결과
- `outputs/pp258_test_metrics.json`: fixed test 성능 지표
- `artifacts/model_config.json`: 모델 파라미터와 원 실험 정보
- `reports/`: 상세 리포트와 설명 자료

## 모델 공식 요약

```text
최종로그가격 = 미세보정전_기준로그가격 + 최종보정_적용값

최종보정_원시값
  = 0.025
    * Huber잔차예측값
    * 잔차방향일치여부
    * 적용확신도

최종보정_적용값
  = clip(최종보정_원시값, -row별_보정상한, +row별_보정상한)

최종가격 = exp(최종로그가격)
```

## fixed test 607건 재현 결과

| 지표 | 값 |
|---|---:|
| n | 607 |
| MdAPE | 0.140976 |
| MAPE | 0.269888 |
| p95 APE | 0.807325 |
| RMSE log | 0.397454 |

## validation OOF 519건 참고 결과

| 지표 | 값 |
|---|---:|
| n | 519 |
| MdAPE | 0.122707 |
| MAPE | 0.205629 |
| p95 APE | 0.637888 |
| RMSE log | 0.323337 |

## 원 실험 후보

- experiment: `PP-OPT253_258_warm_pp252_narrow_direction_residual_refinement`
- selected candidate: `ppopt256_pp252_residual_continue__thr=0p12__rs=0p025__ss=0p0__cap=5em05`
- selected protocol: `ppopt258_operational_pp252_narrow_refinement__source=ppopt256_pp252_residual_continue__thr_0p12__rs_0p025__ss_0p0__cap_5em05`
