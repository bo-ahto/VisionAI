# H33 PR7 Warm 최고 기록 release split 재확인 기록

- 실험 ID: `H33_pr7_release_warm_reconfirm`
- 날짜: 2026-05-14
- 상태: 종결
- 관련 가설: H3, H4, H17, H31
- 실행 스크립트: [`scripts/track3/h33_pr7_release_warm_reconfirm.py`](/Users/bo/VisionAI/scripts/track3/h33_pr7_release_warm_reconfirm.py:1)
- 결과 파일: [`data/track3_h33_pr7_release_warm_reconfirm_results.json`](/Users/bo/VisionAI/data/track3_h33_pr7_release_warm_reconfirm_results.json:1)

## 1. 재실험 이유

- PR7 탐색 실험에서 Warm 최고 기록은 `0.1031`이었음
- 하지만 PR7은 dev/CV 기준 탐색 결과였고, 현재 release split 기준 최종 후보와 직접 비교되지 않았음
- 따라서 PR7의 운영 가능 피처가 현재 고정 release split에서도 유효한지 확인함

## 2. 제외한 피처

- `source_platform`
- release split에는 해당 컬럼이 없음
- 실제 운영에서도 출처를 안정적으로 입력받기 어려움
- 따라서 이번 재검증에서는 제외함

## 3. 비교 피처

| variant | 설명 |
|---|---|
| `V0_pr7_release_baseline` | PR7 기본 Warm 피처 + 작가명 |
| `V1_pr7_interaction` | `medium_ho_bucket` 추가 |
| `V2_pr7_popularity` | `artist_works_log` 추가 |
| `V3_pr7_aspect` | `aspect_ratio` 추가 |
| `V4_pr7_all_operational` | 운영 가능 PR7 피처 전체 추가 |

## 4. 결과

| variant | Warm mean median APE | std | PR7 release 기준 대비 |
|---|---:|---:|---:|
| `V0_pr7_release_baseline` | `0.2749` | `0.0072` | `+0.0000` |
| `V1_pr7_interaction` | `0.2808` | `0.0036` | `+0.0060` |
| `V2_pr7_popularity` | `0.2418` | `0.0049` | `-0.0331` |
| `V3_pr7_aspect` | `0.2580` | `0.0082` | `-0.0168` |
| `V4_pr7_all_operational` | `0.2251` | `0.0038` | `-0.0498` |

## 5. H31과 비교

- PR7 탐색 최고 기록
- `0.1031`
- H33 release split 재확인 최고
- `0.2251`
- H31 Warm 현재 최고 후보
- `0.1090`

## 6. 해석

- PR7 운영 가능 피처는 release split에서도 PR7 기준값 대비 개선을 만듦
- 특히 `artist_works_log`, `aspect_ratio`, `medium_ho_bucket`을 함께 쓰는 조합이 PR7 계열 내 최고임
- 하지만 H31의 작가 이력 피처 기반 Warm 후보에는 미치지 못함
- PR7의 `0.1031`은 현재 release split / 운영 가능 피처 기준 최종 성능으로 볼 수 없음

## 7. 결론

- 결론: 최종 후보 대체 실패
- Warm 최종 후보는 H31 `V5_plus_all_ho_and_3d` 유지
- PR7 결과는 아래 용도로만 참고
- `artist_works_log`가 유효하다는 초기 탐색 근거
- `medium_ho_bucket`, `aspect_ratio`가 운영 가능 파생 피처 후보였다는 참고 근거

## 8. 다음 할 일

- Warm은 H31 후보를 기준으로 production 반영 가능성을 검토
- H16 날짜 컬럼 문제가 해결되면 작가 이력 피처의 temporal-safe 재검증을 수행
