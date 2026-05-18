# T6-E003 Warm 작가 피처 ablation

- 날짜: `2026-05-18`
- 관련 가설: `T6-H3`
- 상태: 검증 완료
- 목적: Warm에서 작가 식별/이력 피처가 구조-only 대비 성능을 개선하는지 확인
- 사용 데이터: Track6 name-corrected Warm feature/label split
- 사용 스크립트: `scripts/track6/run_t6_e003_warm_artist_ablation.py`
- 결과 JSON: `data/track6/results/t6_e003_warm_artist_ablation.json`
- 예측 CSV: `data/track6/predictions/t6_e003_warm_artist_ablation_predictions.csv`

## 1. 비교 피처셋

- `structure_only`: 작품 구조 피처만 사용
- `structure_plus_history`: 구조 피처 + train 기준 작가 작품 수
- `structure_plus_artist_key`: 구조 피처 + 작가 식별값
- `structure_plus_artist_key_history`: 구조 피처 + 작가 식별값 + 작가 작품 수

## 2. validation 결과

| model | median APE | p95 APE | Within-30 | Within-50 | RMSE(log) |
|---|---:|---:|---:|---:|---:|
| `structure_plus_artist_key` | `0.2737` | `1.1971` | `0.5239` | `0.7304` | `0.6249` |
| `structure_plus_artist_key_history` | `0.2835` | `1.1678` | `0.5315` | `0.7323` | `0.6106` |
| `structure_plus_history` | `0.4041` | `1.6436` | `0.3537` | `0.5870` | `0.8261` |
| `structure_only` | `0.4986` | `2.1417` | `0.3136` | `0.5010` | `0.8789` |

## 3. 핵심 해석

- 구조-only median APE: `0.4986`
- 최저 median APE: `0.2737` (`structure_plus_artist_key`)
- 구조-only 대비 개선폭: `0.2248`
- Warm에서는 학습 데이터에 같은 작가가 존재하므로 작가 식별/이력 피처가 가격대 차이를 설명할 수 있음
- 단, 이 결과는 Warm 전용이며 Cold에는 작가 피처를 적용하지 않음

## 4. 결론

- T6-H3는 validation 기준 검증 완료
- Warm 후보 피처셋은 `structure_plus_artist_key`을 우선 유지
- 다음 단계는 Cold 모델 비교(T6-E004)와 운영 가능 피처 조합 실험(T6-E005)
