# PP-V2COLD1 — Track6 Cold를 v2 리포트의 28,376건 cold 테스트셋에 실행

- 작성일: 2026-06-15
- 배경: v2 리포트 §8.2 Cold slice = integrated_v3 GroupKFold OOF **28,376건**(Saatchi 21,087 + Artsy 7,289),
  CatBoost MdAPE 39.4%. 같은 28,376행 정답에 Track6 cold v0.3을 돌려 사과 대 사과 비교.

## 방법

- 행 식별·정답: `audit4_drift_fix_v1_oof_groupkfold.parquet`(28,376, y_ln_price + cb_pred_ln_price)
- 피처 조인: Saatchi `saatchi_cleaned.parquet`(artist_slug+ln_price 100% 매칭, area/medium/support/birth/solo·group·fair),
  Artsy `artsy_kr_artworks.csv`(99.6% 매칭, width/height/medium/birth, 전시 없음)
- 모델: Track6 Cold v0.3 (실제 ReportModelProxyAdapter 빌더+y16+v0.3 후처리). 예측 피처명 정렬은 PP-GOLD1에서 검증됨
- 2모드: serving(메타 결측) / matched(생년·전시 주입). 검색 피처는 두 모드 모두 결측(이 작가들 검색 lookup 미커버)

## 결과 (같은 28,376건)

| 모델 | MdAPE | MAPE | W30 | median_ratio |
|---|---:|---:|---:|---:|
| **Track6 cold — serving** (메타 결측) | **0.3889** | 0.5688 | 0.4025 | 0.904 |
| **Track6 cold — matched** (생년+전시 주입) | **0.3949** | 0.5687 | 0.3979 | 0.885 |
| CatBoost — 보고서 최종(v2 source_calibration) | 0.3938 | — | — | — |
| CatBoost — audit4 parquet(per-row 재계산) | 0.4134 | 0.7811 | 0.3822 | 1.061 |

## 결론

- **같은 28,376 cold 테스트셋에서 Track6는 CatBoost와 동등~약간 우위.**
  - Track6 serving 38.9% < CatBoost 보고값 39.4% (그리고 parquet 41.3%보다 확연히 나음)
  - Track6 matched 39.5% ≈ CatBoost 39.4%
- 골든셋(150)에 이어 v2의 28,376에서도 동일 결론 → **"이번 41%"는 모델 저하가 아니라 Track6 fixed test(3,099, 다른/더 어려운 분포) 기준값**.

## 참고 (정직한 한계)

- CatBoost 비교 기준 두 개: 보고서 최종 39.4%(source_calibration.json, per-row 없음) vs 내가 가진 per-row parquet(audit4) 41.3%. 후자는 drift-fix 감사 버전이라 최종 모델보다 약간 나쁨. Track6는 보고값 39.4%와도 사실상 동률.
- Saatchi는 area_cm2만 있어 width=height=√area로 근사(aspect_ratio≈1; log_area는 정확). Artsy는 width/height 직접 사용.
- 검색 피처 결측이라 Track6의 "검색 포함 최고 성능" 이점은 미적용(이 작가군은 현실적으로도 검색 lookup 미커버). 즉 "검색 없는 Track6" 성능.
- Track6 cold 모델은 작가 식별자를 직접 쓰지 않음(±0.2 검색 델타 372작가 제외)이라 in-sample 누수 영향은 미미.
