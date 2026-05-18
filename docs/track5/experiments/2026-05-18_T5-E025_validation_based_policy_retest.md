# T5-E025 validation 기반 Cold 정책 재선정

- 날짜: 2026-05-18
- 관련 가설: T5-H28
- 목적: Cold 가격 보정 정책이 test 결과를 보고 고른 것인지 검증
- 사용 데이터: `track5_val_cold.csv`, `track5_test_cold.csv`, T5-E008/T5-E010 예측값
- 사용 스크립트: `scripts/track5/run_t5_e022_e025_audit_closure.py`
- 결과 파일: `data/track5/results/t5_e022_e025_audit_closure_metrics.json`

## 실험 방법

- `val_cold`를 다시 calibration 절반과 policy validation 절반으로 나눔
- calibration 절반으로 예측 가격대별 보정값 계산
- policy validation 절반에서 standard/caution 그룹별로 보정을 쓸지 결정
- 결정된 정책만 `test_cold`에 적용
- test 결과를 보고 정책을 고르지 않도록 분리함

## 주요 결과

- validation에서 선택된 정책:
- standard: baseline 유지
- caution: corrected 적용
- test baseline median APE: `0.3918`
- test corrected-all median APE: `0.4014`
- test hybrid median APE: `0.4055`
- test baseline p95 APE: `2.0152`
- test hybrid p95 APE: `2.0593`

## 해석

- validation 기준으로 정책을 고르면 기존 T5-E020의 hybrid 개선이 유지되지 않음
- test에서 좋아 보였던 보정 정책은 과적합 가능성이 있음
- Cold는 후처리 보정보다 baseline 예측과 위험 경고를 분리해 운영하는 쪽이 안전함

## 결론

- 상태: 검증 완료
- Cold 가격대 보정 정책은 최종 채택하지 않음
- 현재 운영 후보는 `Cold Quantile baseline + 위험 구간 경고 + 넓은 가격 범위 안내`로 정리
