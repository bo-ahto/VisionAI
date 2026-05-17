# Track 5 실험 결과 요약표

- 목적: Track 5 실험 실행 결과를 한눈에 관리
- 기준일: 2026-05-18
- 정렬 기준: 최신 실험이 위로 오도록 관리
- 원칙: Warm / Cold 결과는 합치지 않고 분리 기록

| 날짜 | 실험 ID | 관련 가설 | 상태 | 사용 데이터 | 사용 모델 | 사용 피처 | Warm 결과 요약 | Cold 결과 요약 | 결론 | 상세 기록 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-18 | T5-E001 | T5-H1 | 완료 | Track4 feature candidates | 모델 미사용 | split 기준 | test_warm `511`건, `215`명 | test_cold `2,896`건, `216`명, train 작가 겹침 `0` | Track5 모델 실험 기준 split으로 사용 가능 | [기록](../experiments/2026-05-18_T5-E001_split_generation.md), [보고서](../dataset/split_report.md) |

## 다음 실험 후보

- T5-E002: 구조-only baseline 생성
- T5-E003: Warm 작가 피처 ablation
- T5-E004: Cold 모델군 비교
