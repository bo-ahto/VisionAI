# T4-E030 Cold 위험 구간 및 출력 정책 후보

- 실험 ID: `T4-E030`
- 연결 가설: `T4-H9`, `T4-H17`, `T4-H24`, `T4-H26`
- 날짜: 2026-05-17
- 상태: 완료

## 1. 실험 목적

- Cold 전체를 같은 방식으로 서비스해도 되는지 확인함
- Cold 예측에서 저위험/고위험 구간을 나눌 수 있는지 확인함
- 어떤 조건에서 단일 가격만 보여주기보다 넓은 범위나 신뢰도 경고가 필요한지 확인함

## 2. 확인하려는 질문

- Cold 저위험 구간은 전체보다 예측 오차가 낮은가
- 3D, support unknown, 고가 후보는 실제로 오차가 큰가
- 위험 구간을 기준으로 출력 정책을 다르게 가져갈 수 있는가

## 3. 사용 데이터

- 학습 데이터: `data/track4_split/track4_train.csv`
- 평가 데이터: `data/track4_split/track4_val_cold.csv`
- calibration 데이터: 사용하지 않음

## 4. 사용 모델

- 모델: `QuantileRegressor`
- 사용 피처:
- `medium_category`
- `log_area`
- `aspect_ratio`
- 제외 피처:
- 작가 정보
- 출처 정보
- 갤러리 정보
- URL / 이미지 정보
- 가격 정답 컬럼

## 5. 위험 flag

- `risk_3d`
- 3D 후보 작품
- `risk_support_unknown`
- 지지체 정보가 unknown인 작품
- `risk_medium_unknown`
- 재료 정보가 unknown인 작품
- `risk_large_area`
- 학습 데이터 기준 면적 상위 10% 이상
- `risk_high_price_candidate`
- 고가 후보 flag
- `risk_extreme_aspect`
- 극단 비율 flag

## 6. 위험 그룹 정의

- `low`
- 위험 flag가 0개
- `medium`
- 위험 flag가 1개
- `high`
- 위험 flag가 2개 이상

## 7. 실행 명령

```bash
python3 scripts/track4/run_t4_e030_cold_risk_policy.py
```

## 8. 결과 파일

- 결과 JSON: `data/track4/results/t4_e030_cold_risk_policy_metrics.json`
- 예측 CSV: `data/track4/predictions/t4_e030_cold_risk_policy_predictions.csv`
- 실행 스크립트: `scripts/track4/run_t4_e030_cold_risk_policy.py`

## 9. 전체 결과

| 구분 | rows | median APE | p95 APE | Within-30% | Within-50% |
|---|---:|---:|---:|---:|---:|
| Cold 전체 | 1,814 | 0.3642 | 1.1421 | 0.4305 | 0.6389 |

## 10. 위험 그룹별 결과

| 위험 그룹 | rows | median APE | p95 APE | Within-30% | Within-50% | 해석 |
|---|---:|---:|---:|---:|---:|---|
| low | 1,434 | 0.3400 | 1.1449 | 0.4623 | 0.6604 | 전체보다 median APE 낮음 |
| medium | 307 | 0.4124 | 1.0137 | 0.3355 | 0.6091 | 전체보다 median APE 높음 |
| high | 73 | 0.7080 | 1.2952 | 0.2055 | 0.3425 | 단일 가격 신뢰 낮음 |

## 11. 주요 flag별 결과

| flag | flag=false median APE | flag=true rows | flag=true median APE | flag=true p95 APE | 해석 |
|---|---:|---:|---:|---:|---|
| risk_3d | 0.3529 | 70 | 0.8286 | 1.4093 | 3D는 고위험 신호 |
| risk_support_unknown | 0.3518 | 206 | 0.5529 | 0.9928 | support unknown은 median 오차가 큼 |
| risk_large_area | 0.3646 | 174 | 0.3614 | 1.0759 | 단독 대형 면적은 강한 위험 신호 아님 |
| risk_high_price_candidate | 0.3641 | 4 | 0.9591 | 0.9852 | 표본은 작지만 고가 후보는 위험 신호 |

## 12. 해석

- Cold 저위험 구간은 전체보다 median APE가 낮음
- 위험 flag가 2개 이상인 high 그룹은 median APE `0.7080`으로 전체 `0.3642`보다 크게 나쁨
- 3D는 가장 강한 위험 신호 중 하나임
- support unknown도 median APE가 높아 신뢰도 경고 후보임
- 고가 후보는 표본이 4건뿐이라 강한 결론은 어렵지만 위험 후보로 유지함
- 대형 면적은 단독으로는 강한 위험 신호로 보기 어려움

## 13. 출력 정책 후보

- low
- 단일 가격 + 일반 가격 범위 표시 후보
- medium
- 단일 가격 + 넓은 가격 범위 또는 주의 표시 후보
- high
- 단일 가격 단독 사용 지양
- 넓은 가격 범위와 낮은 신뢰도 표시 후보

## 14. 결론

- 채택 / 보류 / 중단: 부분 채택
- 판단:
- `T4-H9`: Cold는 저위험 구간에 제한할 때 더 실용적일 수 있음
- `T4-H17`: 저위험/고위험 구간 분리는 유효한 방향임
- `T4-H24`: 위험 조건에 따라 출력 정책을 다르게 가져갈 근거가 있음
- `T4-H26`: 고가 후보는 표본이 작아 보류하되 위험 flag 후보로 유지

## 15. 후속 작업

- `T4-H18`, `T4-H29`: 위험 그룹별 가격 범위와 신뢰도 calibration
- `T4-H26`: 고가 후보는 test 또는 추가 데이터에서 재확인
- `T4-H27`: 3D fallback은 tail risk 제어 후 재실험
