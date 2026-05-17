# T4-E046 최종 결과 요약 보고서 작성

- 날짜: 2026-05-17
- 관련 가설: T4-H12, T4-H30, T4-H35
- 상태: 완료
- 목적: Track 4 실험 결과를 상사 보고와 재현 확인이 가능한 최종 문서로 고정

## 1. 확인하려는 것

- 최종 Warm / Cold 모델 후보가 무엇인지 명확히 설명할 수 있는가
- 어떤 피처를 사용하고 어떤 피처를 제외했는지 설명할 수 있는가
- 현재 성능 기준으로 서비스 적용 가능 범위를 구분할 수 있는가
- 이후 재현 시 어떤 스크립트를 실행해야 하는지 문서로 확인할 수 있는가

## 2. 사용한 근거

- 최종 artifact 결과:
  - `data/track4/results/t4_e045_final_artifact_dry_run.json`
- 최종 Warm 모델:
  - `data/track4/models/track4_warm_final_conditional_stats_ridge.joblib`
- 최종 Cold 모델:
  - `data/track4/models/track4_cold_final_full_size_quantile.joblib`
- 피처 manifest:
  - `configs/track4/feature_manifest.json`

## 3. 작성 결과

- 최종 보고서:
  - [Track 4 최종 결과 요약 보고서](../final_report_2026-05-17.md)
- 대시보드 연결:
  - [Track 4 실험 대시보드](../dashboard/experiment_dashboard.html)

## 4. 핵심 결론

- Warm:
  - 최종 후보는 Ridge 기반 조건부 작가 가격 통계 모델이다.
  - test median APE는 `0.2201`이다.
  - low_history 작가는 경고와 넓은 가격 범위가 필요하다.
- Cold:
  - 최종 후보는 Quantile 기반 작품 구조 정보 모델이다.
  - test median APE는 `0.4199`이다.
  - 단일 가격만 제시하기에는 위험이 크다.
  - low_risk만 제한적 범위 후보로 보고, mid/high risk는 강한 경고 또는 보류가 필요하다.

## 5. 재현 명령

- 피처 manifest 검사:
  - `python3 scripts/track4/check_feature_manifest.py`
- 최종 artifact 재생성:
  - `python3 scripts/track4/run_t4_e045_final_artifact_dry_run.py`
- 대시보드 재생성:
  - `python3 scripts/track4/generate_experiment_dashboard.py`

## 6. 결론

- T4-E046은 모델을 새로 학습하는 실험이 아니라, T4-E045까지의 최종 후보를 문서로 고정하는 마감 실험이다.
- Track 4는 현재 기준으로 Warm 서비스 후보와 Cold 제한적 사용 후보를 분리해 설명할 수 있는 상태다.
