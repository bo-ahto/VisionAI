# Track6 Cold CatBoost 테스트 근거 정리

## 결론

- Cold에서 CatBoost는 실제로 테스트된 기록이 있다.
- 재현 가능한 성능 지표가 남아 있는 핵심 실험은 `T6-E017`과 `CM1`이다.
- `CM1`에서는 CatBoost가 Cold 모델군 비교에서 `MdAPE 0.4488`, `종합점수 94.0240`, `종합순위 1위`를 기록했다.
- 따라서 Cold 운영 후보는 `CatBoost 1순위`, `LightGBM 보조 후보`로 정리하는 것이 현재 결과와 맞다.
- 단, A~J 고정 실험 대부분은 CatBoost를 포함하지 않았으므로 A~J의 LightGBM 우세 결과만으로 CatBoost를 제외하면 안 된다.

## 언제 테스트했는가

| 실험 | 상태 | 내용 | 비고 |
|---|---|---|---|
| T6-E017 | 실행 완료 | 기준 모델 선정 단계에서 CatBoost를 Cold 후보로 테스트 | `outputs/metrics.csv`에 결과 있음 |
| CM1 | 실행 완료 | Cold 상위 피처 조합에서 CatBoost/LightGBM/기타 모델군 비교 | `outputs/result_sheet_scored.csv`에 결과 있음 |
| T6-E016 | 후보로 등록, 결과 CSV 없음 | Cold 기본 모델 비교 후보에 CatBoost 포함 | 현재 폴더에는 README/HTML 일지만 있고 outputs 지표 파일 없음 |
| T6-E035 | 후보로 등록, 결과 CSV 없음 | Cold 최종 후보 모델 비교 후보에 CatBoost 포함 | 현재 폴더에는 README/HTML 일지만 있고 outputs 지표 파일 없음 |

## 핵심 성능

| 실험 | 비교대상 | 사용 피처 | MdAPE | p95_APE | Within_30 | RMSE_log | R2 | 종합점수 | 종합순위 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| CM1 | CM1-F2: 작품 기본 피처 + 활동량/인지도 | ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_meta_total_works, artist_meta_for_sale_works, artist_meta_followers, artist_meta_is_p1 | 0.4488 | 2.9885 | 0.3304 | 0.8797 | 0.5519 | 94.0240 | 1 |
| T6-E017 | cold_basic | medium_category, support_category, ln_estimated_ho | 0.5136 | 2.4750 | 0.2938 | 0.8117 |  |  |  |

## 해석

- `T6-E017`은 초기 기준 모델 단계의 CatBoost 실행 근거다.
- `CM1`은 Cold 상위 피처 조합을 대상으로 한 모델군 비교이므로 최종 후보 판단에 더 직접적인 근거다.
- `CM1-F2`의 CatBoost는 `작품 기본 피처 + 활동량/인지도` 조합에서 가장 낮은 MdAPE를 기록했다.
- CatBoost는 범주형 피처와 비선형 관계를 함께 다루는 모델이라 `난트 재료`, `난트 지지체`, `작가 활동량/인지도` 조합에서 장점이 있다.
- LightGBM은 A~J 실험에서 반복적으로 상위권에 나왔으므로 fallback, 보조 후보, 후처리 비교 후보로 유지한다.

## 남은 확인

- A~J 고정 실험 상위 피처 조합에도 CatBoost를 동일 조건으로 다시 적용하면 더 엄밀한 최종 비교가 가능하다.
- 현재 결론에는 `CM1` 결과를 근거로 Cold 1순위 후보를 CatBoost로 명시한다.
- CatBoost가 기존 A~J/OPT 결과를 뒤집는지에 대한 직접 비교는 `cold_catboost_vs_previous_candidates.md/html`에서 확인한다.
