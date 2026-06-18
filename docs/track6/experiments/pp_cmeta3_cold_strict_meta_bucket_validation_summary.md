# PP-CMETA3 Cold strict 메타 bucket 검증 요약

- 실행일: 2026-06-18
- 실험 폴더: `experiments/track6/PP-CMETA3_cold_strict_meta_bucket_validation`
- 실행 스크립트: `scripts/track6/run_pp_cmeta3_cold_strict_meta_bucket_validation.py`
- 목적: `artist_key`를 참고하지 않고, 작가 메타정보 + 작품정보 + 외부 live 검색/전시 정보만으로 Cold 성능이 어디까지 나오는지 확인한다.
  이번 실행은 실제 live 호출이 아니라, live 검색과 같은 schema로 저장된 동결 cache를 사용했다.

## 1. strict Cold 조건

이번 실험은 unresolved-artist Cold 조건을 따른다.

- `artist_key`를 모델 피처로 사용하지 않는다.
- 같은 작가 가격 중앙값, 평균, 작품 수, 면적단가를 사용하지 않는다.
- `search_delta_lookup[artist_key]` 같은 작가별 후처리 lookup을 사용하지 않는다.
- 허용 정보는 작품정보, 비가격성 작가 메타, 외부 live 검색 문맥, 전시/갤러리 피처, 그리고 이 정보에서 만든 bucket이다.

## 2. 실험 순서

1. `PP-CMETA1` strict 최상위 후보를 재현했다.
2. 작가 메타 bucket을 추가했다.
3. 외부 live 검색/전시 문맥 bucket을 추가했다.
4. 작품 bucket x 메타/외부 live 검색 bucket 조합 피처를 추가했다.
5. validation에서 가장 좋았던 후보에 LightGBM residual clip 보정과 q40 guard-only 후처리를 붙였다.

## 3. Test 결과

| 후보 | 정책 | MdAPE | MAPE | p95 APE | RMSE log | 해석 |
|---|---|---:|---:|---:|---:|---|
| `search_external_bucket` | base q50 | 0.440549 | 1.037633 | 3.394335 | 0.857290 | test 기준 최상위. 외부 live 검색/전시 bucket으로 중앙·평균 오차 소폭 개선 |
| `cmeta1_repro_full` | base q50 | 0.442147 | 1.048405 | 3.353732 | 0.856668 | PP-CMETA1 strict 최상위 재현 기준 |
| `meta_search_combo_bucket` | base q50 | 0.458786 | 1.004085 | 3.473269 | 0.850752 | MAPE는 개선되지만 MdAPE/p95 손실 |
| `meta_bucket_raw_lgb_residual_clip` | residual clip | 0.464247 | 1.085605 | 3.023533 | 0.888108 | p95는 개선되지만 중앙·평균 오차 손실 |
| `meta_bucket_raw` | base q50 | 0.468331 | 1.094027 | 3.003857 | 0.891367 | p95 방어는 좋지만 대표 오차 손실 |
| `meta_bucket_raw_guard_only_q40` | guard-only q40 | 0.470947 | 1.053826 | 2.876164 | 0.917438 | p95 최상위. 다만 MdAPE/RMSE 손실이 큼 |
| `cmeta1_repro_artwork_only` | base q50 | 0.482312 | 1.242417 | 4.380572 | 0.941084 | 작품 정보만 쓴 기준 |
| `bucket_only_no_raw_meta` | base q50 | 0.581683 | 1.845496 | 7.496422 | 1.119626 | raw meta 없이 bucket만 쓰면 성능 악화 |

## 4. 기준 대비 변화

기준은 `PP-CMETA1` strict 최상위 재현 후보인 `cmeta1_repro_full`이다.

| 비교 | MdAPE 변화 | MAPE 변화 | p95 APE 변화 | 해석 |
|---|---:|---:|---:|---|
| `search_external_bucket` - 기준 | -0.001598 | -0.010772 | +0.040603 | 중앙·평균 오차는 소폭 개선, tail은 소폭 악화 |
| `meta_bucket_raw_guard_only_q40` - 기준 | +0.028800 | +0.005422 | -0.477568 | tail 방어는 크게 개선, 대표 정확도 손실 |

## 5. 해석

메타 bucket만으로는 운영 기본 후보를 바꿀 만큼의 근거가 부족하다. validation에서는 `meta_bucket_raw`가 가장 좋아 보였지만, test에서는 MdAPE/MAPE가 기준보다 나빠졌다. 따라서 작가 메타 bucket은 단독 승격 후보가 아니다.

외부 live 검색/전시 bucket은 가능성이 있다. `search_external_bucket`은 strict 조건에서 `artist_key` 없이 MdAPE와 MAPE를 기준보다 소폭 개선했다. 다만 p95가 악화되어 바로 최종 Cold 후보로 승격하기에는 tail 검증이 더 필요하다.

guard-only q40는 목적이 다르다. p95는 가장 좋지만 MdAPE와 RMSE가 악화된다. 즉 전체 기본 모델이라기보다 “불확실성이 큰 입력에서 보수 가격을 함께 표시하거나 검수 우선순위를 높이는 정책”으로 보는 편이 적절하다.

## 6. 권장 다음 단계

1. `search_external_bucket`을 strict Cold challenger로 유지한다.
2. 동일 하네스에서 repeated split 또는 bootstrap으로 MdAPE/MAPE 개선이 우연인지 확인한다.
3. `search_external_bucket` 위에 guard-only를 직접 얹어 p95 악화를 줄일 수 있는지 재검증한다.
4. 외부 live 검색 피처가 동결 cache와 같은 schema/분포를 유지하는지 parity 검증한다.
5. 지금 단계에서는 official Cold 기본값을 변경하지 않고, strict Cold 차기 후보로 관리한다.

## 7. 결론

`artist_key` 없이 작가 메타정보와 작품정보만으로 성능을 확인하는 실험은 진행됐다. 결과적으로 작가 메타 bucket 단독은 충분하지 않았고, 외부 live 검색/전시 bucket을 함께 넣은 후보가 strict 조건에서 가장 설득력 있는 개선을 보였다.

현재 수치 기준 권장 후보는 `search_external_bucket`이다.

```text
MdAPE 0.440549
MAPE  1.037633
p95   3.394335
```

다만 기존 strict 기준 대비 p95가 `+0.040603` 악화되므로, 운영 모델 승격 전에는 p95 방어 실험과 repeated validation이 필요하다.
