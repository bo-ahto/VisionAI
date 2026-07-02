# PP-GOLD1 — Track6 Cold를 4월 골든셋에 돌려 CatBoost와 동일 셋 비교

- 작성일: 2026-06-15
- 배경: 파트너 질문 "4월 골든셋 CatBoost ~39.5% vs 이번 Track6 ~41%, 나빠진 것?" — 두 수치는
  모델·테스트셋이 달라 직접 비교 불가였음. 같은 골든셋(149건)에 Track6 cold v0.3을 돌려 사과 대 사과 비교.

## 방법

- 데이터: `data/golden_set_predictions.csv`(입력) + `golden_set_comparison.csv`(actual_krw), 149건(가로/세로·actual 결측 1건 제외)
- 모델: Track6 Cold v0.3 (pp_y2 search+external LightGBM Quantile + qr1 q40 + y16 보정 + guard+search 후처리). 실제 `ReportModelProxyAdapter`의 base/bucket 빌더·y16·v0.3 후처리 그대로 사용
- 예측 정렬 검증: frame.columns == model.feature_names_in_ (87/87), 컬럼 셔플 시 예측 불변 = 피처명 기준 정렬 확정(LGBM "feature names" 경고는 양성)
- 두 모드:
  - **serving**: 골든 작가는 Track6 DB/검색 스냅샷에 없으므로 메타 전부 결측 → 실서빙 현실
  - **matched**: CatBoost가 쓴 정보(생년, 전시 solo/group/fair)를 Track6 피처에 주입 → 동일 정보 공정 비교
  - 검색 피처는 두 모드 모두 결측(골든 130명은 검색 lookup 372명에 거의 없음 → 검색 보정 0)

## 결과 (같은 골든셋 149건)

| 모델 | MdAPE | MAPE | W30 | median_ratio |
|---|---:|---:|---:|---:|
| **Track6 cold — serving** (메타 결측, 실서빙) | **0.3736** | 0.4974 | 0.4228 | 0.977 |
| **Track6 cold — matched** (생년+전시 주입) | **0.3941** | 0.5869 | 0.3691 | 1.122 |
| CatBoost (골든 원본 재계산) | 0.3953 | 0.5052 | 0.3624 | 0.872 |
| CatBoost 보고값(`golden_set_test_result.md`) | 0.395 | 0.504 | 0.360 | — |

## 결론

- **같은 골든셋에서 Track6 cold는 CatBoost보다 나쁘지 않다. 오히려 동등~약간 우위.**
  - serving 37.4% < CatBoost 39.5% (실서빙 현실에서 더 나음)
  - matched 39.4% ≈ CatBoost 39.5% (동일 정보에서 사실상 동률)
- 따라서 리포트의 **"이번 41%"는 회귀가 아니라 다른(더 크고 어려운) Track6 fixed test(3,099건) 기준값**일 뿐. 동일 셋 비교로 모델 자체 성능 저하가 아님이 확인됨.
- 부수 관찰: Track6는 메타 주입(matched) 시 median_ratio 1.12로 약한 과대예측 → MdAPE가 serving보다 오히려 소폭 악화. 골든 작가의 전시 수(개인전 평균 7.6회)가 가격을 위로 미는 경향. 결측 default가 이 분포(중앙 404만)에 더 잘 정렬됨.

## 한계

- 검색 피처는 두 모드 모두 결측이라 Track6의 "검색 포함 최고 성능" 이점은 이 비교에 미적용(골든 작가가 검색 lookup에 없어 현실적으로도 0). 즉 이 결과는 "검색 없는 Track6"의 한국 신규 작가 성능.
- 골든셋(149건)은 작고 한국 신진/중견 + 100~500만원대 집중 분포 → 절대 수치는 Track6 fixed test(3,099)와 직접 비교 금지, 같은 셋 내 모델 간 비교로만 사용.
