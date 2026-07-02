# KTCC Warm PP258 가격예측 MAPE 15% 제출용 패키지

이 폴더는 Warm PP258 최종 운영 모델을 고신뢰 100건 가격예측 시험 형태로 재현하기 위한 실행 패키지다.

## 실행

```bash
python scripts/ktcc_pp258_price_mape_test.py
```

## 결과

- 평가 건수: 100
- MAPE: 0.125459 (12.55%)
- p95 APE: 0.327471
- 목표: MAPE 15% 이하
- 통과 여부: PASS

## 모델

- 기준: Warm PP258 최종 운영 미세 보정 모델
- 산식: `최종로그가격 = 미세보정전_기준로그가격 + 최종보정_적용값`
- 최종가격: `exp(최종로그가격)`

## 고신뢰 조건

```json
{
  "quantile_width_max": 1.2,
  "component_prediction_spread_max": 0.1,
  "l10_price_range_ratio_max": 2.0,
  "svc_group_n_min": 5,
  "current_vs_stable_gap_abs_max": 0.025
}
```

## 주의

이 패키지는 raw 작품 정보만으로 전체 Warm 후보를 처음부터 생성하는 패키지가 아니라, 선행 Warm 후보 로그가격과 PP258 보정 신호가 포함된 feature 입력을 사용해 고신뢰 100건 MAPE를 재현하는 패키지다.
