# Track 3 재현 결과 요약

- 작성일: 2026-05-13
- 기록 유형:
- 재현 세션 요약
- 기준 문서: [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 목적: Track 3 계획서 기준 핵심 실험 재현 결과 정리
- 데이터 버전:
- `release_split regenerated on 2026-05-13`
- 데이터 나누기 기준:
- 개발 중간 검증은 `track3_splits`
- 공식 확인은 `release_split`
- 범위
- 데이터 분할 재생성
- baseline 재현
- 선형 모델 재현
- 비선형 모델 재현
- 파생 피처 실험 재현
- LightGBM 튜닝 재현
- production 학습 및 평가 재현

## 1. 실행 항목

- 실행 완료 스크립트
- `scripts/track3/split_data.py`
- `scripts/track3/split_for_release.py`
- `scripts/track3/baseline.py`
- `scripts/track3/train_linear_cold.py`
- `scripts/track3/train_linear_warm.py`
- `scripts/track3/train_tree_cold.py`
- `scripts/track3/train_tree_warm.py`
- `scripts/track3/pr7_feature_engineering.py`
- `scripts/track3/pr1_optuna_tuning.py`
- `scripts/track3/production_train.py`
- `scripts/track3/pr16f_eval_production.py`

## 2. 재생성된 데이터 분할

- 현재 `release_split` 재생성 결과
- `track3_train.csv`: 34,629 rows / 1,932 artists
- `track3_test_warm.csv`: 1,685 rows / 1,685 artists
- `track3_test_cold.csv`: 3,823 rows / 200 artists
- 주의
- 기존 문서/리포트와 row 수가 다를 수 있음
- 이번 재현 결과는 현재 코드 기준 split 재생성값을 따름

## 3. Phase 0 결과

- Cold median baseline
- `med_APE 0.754`
- Warm median baseline
- `med_APE 0.739`

### 크기 표현 비교

- `LGB both`
- `med_APE 0.472`
- `LGB area_only`
- `med_APE 0.473`
- `LGB ho_only`
- `med_APE 0.505`

### 해석

- `log_area + estimated_ho` 조합이 가장 안정적
- `estimated_ho` 단독은 약함
- baseline 대비 LGB가 크게 개선

## 4. Phase 1 선형 모델 결과

### Cold

- OLS
- `med_APE 0.544`
- Huber
- `med_APE 0.438`
- Quantile_q05
- `med_APE 0.429`
- 최고 모델
- `Quantile_q05`

### Warm

- OLS
- `med_APE 0.322 ± 0.002`
- Huber
- `med_APE 0.317 ± 0.001`
- Quantile_q05
- `med_APE 0.314 ± 0.000`
- 최고 모델
- `Quantile_q05`

### 해석

- Cold는 robust 선형 계열이 일반 선형보다 확실히 우세
- Warm도 선형 baseline은 의미 있으나 최종 후보로는 약함

## 5. Phase 2 비선형 모델 결과

### Cold

- LightGBM
- `med_APE 0.473`
- XGBoost
- `med_APE 0.491`
- CatBoost
- `med_APE 0.475`
- 최고 모델
- `LightGBM`

### Warm

- LightGBM
- `med_APE 0.119 ± 0.002`
- XGBoost
- `med_APE 0.541 ± 0.002`
- CatBoost
- `med_APE 0.185 ± 0.009`
- 최고 모델
- `LightGBM`

### 해석

- Cold는 비선형이 선형 최고를 이기지 못함
- `Cold best 선형 0.429` > `Cold best 비선형 0.473`
- Warm는 비선형이 압도적으로 우세
- `Warm best 선형 0.314` > `Warm best 비선형 0.119`

## 6. PR7 파생 피처 실험

### Cold LAD

- baseline
- `0.429`
- source
- `0.413`
- interaction
- `0.426`
- popularity
- `0.444`
- aspect
- `0.428`
- all
- `0.391`

### Warm Tuned LGB

- baseline
- `0.115`
- source
- `0.116`
- interaction
- `0.117`
- popularity
- `0.103`
- aspect
- `0.113`
- all
- `0.104`

### 해석

- Cold
- `source` 포함 시 개선되지만 운영 입력 제약으로 최종 채택 어려움
- 운영 가능한 파생 피처 중 뚜렷한 승자는 약함
- Warm
- `artist_works_log` 기반 popularity가 가장 유의미
- `source`, `interaction`은 유지 근거 약함

## 7. PR1 LightGBM Optuna 튜닝

### Cold

- default LGB
- `med_APE 0.473`
- tuned LGB
- `med_APE 0.488`
- Phase 1 LAD 기준
- `med_APE 0.429`

### Warm

- default LGB
- `med_APE 0.119 ± 0.002`
- tuned LGB
- `med_APE 0.116 ± 0.003`

### 해석

- Cold
- 튜닝해도 LGB는 LAD를 이기지 못함
- `Cold는 LAD 유지`가 타당
- Warm
- tuned LGB가 소폭 개선
- best params가 production 설정과 사실상 동일

## 8. Production 재학습 및 평가

### 저장 artifact

- [`data/production/track3_cold_lad.joblib`](/Users/bo/VisionAI/data/production/track3_cold_lad.joblib)
- [`data/production/track3_warm_lgb.txt`](/Users/bo/VisionAI/data/production/track3_warm_lgb.txt)
- [`data/production/track3_metadata.json`](/Users/bo/VisionAI/data/production/track3_metadata.json)
- [`data/production/track3_artist_counts.json`](/Users/bo/VisionAI/data/production/track3_artist_counts.json)

### release_split 기준 평가

- Cold
- `n=3,823`
- `med_APE 0.3207`
- `W30 0.4640`
- Warm
- `n=1,685`
- `med_APE 0.2056`
- `W30 0.5988`

### Cold 약점

- source 기준
- `artsy` 약함
- `artue` 약함
- medium 기준
- `other`
- `mixed`
- 일부 `acrylic`

### 해석

- 운영 구조 `Cold=LAD`, `Warm=LightGBM`는 재현 결과와 일치
- Warm는 tuned LGB 유지가 타당
- Cold는 여전히 일부 source/medium에서 약점 존재

## 9. 현재 결론

- Warm 결과 요약
- `tuned LightGBM` 유지
- production `med_APE 0.2056`
- `W30 0.5988`
- Cold 결과 요약
- `LAD / Quantile / Huber` 계열 유지
- production `med_APE 0.3207`
- `W30 0.4640`
- Cold
- 모델: `LAD / Quantile / Huber` 계열 유지
- 트리/튜닝으로는 우세 확보 실패
- Warm
- 모델: `LightGBM tuned` 유지
- `artist_works_log` 계열 피처 유지 가치 높음
- 전체
- 현재 계획서 기준 핵심 실험 라인은 재현 완료
- 결론은 기존 Track 3 방향과 대체로 일치

## 10. 다음 단계

- `pr20~pr29` 후속 실험을 현재 split 기준으로 다시 점검
- 기존 F1~F6 결론과 현재 재현 결과의 정합성 확인
- `Cold 2D` 한정 fallback 가설 여부 확인

## 11. PR20~PR29 후속 실험 재현

### 실행 완료

- `scripts/track3/pr20_size_redundancy.py`
- `scripts/track3/pr21_size_v0_v1_confirm.py`
- `scripts/track3/pr22_new_features_ablation.py`
- `scripts/track3/pr23_f1_combo_confirm.py`
- `scripts/track3/pr24_catboost_warm.py`
- `scripts/track3/pr25_rare_artist_blend.py`
- `scripts/track3/pr26_frozen_cold_benchmark.py`
- `scripts/track3/pr27_cold_regime_analysis.py`
- `scripts/track3/pr28_knn_retrieval_blend.py`
- `scripts/track3/pr29_knn_release_split_confirm.py`

### F1 — 크기 변수 단순화

- `PR20`
- Cold mini 기준 후보 신호
- `V1_log_ho`
- `V2_log_only`
- `V3_wh_only`
- Warm mini 기준
- `V3_wh_only`만 부분 후보
- `PR21` release_split confirm
- Cold
- `V0_all 0.3237`
- `V1_log_ho 0.3217`
- Warm
- `V0_all 0.2055`
- `V1_log_ho 0.2277`
- 결론
- `V0 유지`
- Cold만 비슷해 보여도 Warm에서 명확히 악화

### F2 — 신규 파생 피처 4개

- `PR22` mini 결과
- `F1_combo`
- `F2_maxside`
- `F3_square`
- `F4_area_depth`
- 모두 confirm 후보 탈락
- `F4_area_depth`는 tail risk 위험 신호
- `PR23` release_split confirm
- Cold
- `V0_base 0.3237`
- `V0+combo 0.3372`
- Warm
- `V0_base 0.2055`
- `V0+combo 0.1911`
- 결론
- Warm 단독으로는 소폭 이득이 보였지만
- Cold에서 악화
- 운영 채택 기준 미달
- `V0 유지`

### F3 — CatBoost vs LightGBM

- `PR24`
- LGB Warm
- `0.2012 ± 0.0056`
- CatBoost Warm
- `0.2679 ± 0.0060`
- 결론
- `LightGBM 유지`
- CatBoost는 현재 split 기준에서도 확실히 열세

### F4 — Rare-artist blend

- `PR25`
- baseline `V0_pure_warm`
- `0.2012 ± 0.0056`
- 모든 blend variant
- 개선 실패
- paired WR도 매우 낮음
- 결론
- `Warm 100% 유지`
- rare artist에도 Cold blend 근거 없음

### F5 / F6 — Frozen benchmark + KNN fallback

- `PR26`
- frozen cold benchmark 구축 완료
- `cold benchmark 875 rows / 100 artists`
- baseline Cold LAD
- `med_APE 0.4504`
- `PR27`
- 현재 Cold 약점 재확인
- `artue`
- `artsy`
- `mixed / other`
- `ho 50+`
- `price_low × other`
- `price_high × oil`
- `PR28` frozen benchmark KNN blend
- `V0 0.4504`
- `knn10_a50 0.4288`
- `knn10_a70 0.4352`
- 하지만 paired 기준, tail 기준 미달
- `PR29` release_split confirm
- `V0 0.3237`
- `knn10_a50 0.3628`
- `knn10_a70 0.3598`
- 결론
- `KNN blend 기각`
- release_split confirm에서 명확히 악화

### 전체 해석

- 현재 split 기준에서도 F1~F5 개선안은 운영 채택 근거 부족
- F6 frozen benchmark는 유의미한 인프라 개선
- 즉
- 모델 구조를 조금 바꾸는 실험은 반복적으로 false positive 가능성이 높음
- 현재 운영 구조
- `Cold = LAD`
- `Warm = tuned LightGBM`
- 를 유지하는 결론이 다시 확인됨

## 12. PR17 / PR19 추가 재현

### 실행 완료

- `scripts/track3/pr17_branch_models.py`
- `scripts/track3/pr19_cold_depth_signif.py`

### PR17 — 2D / 3D 분기 모델

- 가설
- `source` 없이도 `2D / 3D` 분기만으로 Cold 약점 일부를 줄일 수 있을 것이다
- 방법
- `V0`
- Warm 단일 / Cold 단일
- `V1`
- Warm만 2D / 3D 분기
- `V2`
- Cold만 2D / 3D 분기
- `V3`
- Warm / Cold 모두 2D / 3D 분기

### PR17 결과

- `V0`
- Warm `med_APE 0.2036`
- Cold `med_APE 0.4448`
- `V1`
- Warm `0.2022`
- Cold `0.4448`
- `V2`
- Warm `0.2036`
- Cold `0.4141`
- `V3`
- Warm `0.2022`
- Cold `0.4141`

### PR17 slice 해석

- Warm 2D
- `V0 0.2331`
- `V3 0.2489`
- 악화
- Warm 3D
- `V0 0.1895`
- `V3 0.1830`
- 소폭 개선
- Cold 2D
- `V0 0.6754`
- `V3 0.6474`
- 개선
- Cold 3D
- `V0 0.3108`
- `V3 0.3183`
- 악화

### PR17 판단

- Cold 전체 median 기준으로는 분기 신호가 있음
- 다만 개선이 사실상 `Cold 2D`에 집중됨
- `Warm 2D`와 `Cold 3D`는 동시에 악화
- 따라서 현 시점에서는 운영 채택보다
- `Cold 2D 한정 fallback` 후보로만 보류하는 것이 맞음

### PR19 — Cold depth_cm 유의성 재검증

- 가설
- Cold에서 `depth_cm`를 제거하거나 단순화해도 성능 손실이 크지 않을 수 있다
- 방법
- 5개 seed에서 `no_depth` 대비 `cm_only`를 비교
- 전체 / `cold_2d` / `cold_3d`를 분리 확인

### PR19 결과

- overall
- Median delta `+0.00119 ± 0.00212`
- Win rate `0.4811 ± 0.0745`
- `cm`이 더 좋은 seed `1 / 5`
- `cold_2d`
- Median delta `-0.00326 ± 0.01947`
- Win rate `0.4653 ± 0.0739`
- `cm`이 더 좋은 seed `5 / 5`
- `cold_3d`
- Median delta `+0.00036 ± 0.00227`
- Win rate `0.4876 ± 0.0871`
- `cm`이 더 좋은 seed `1 / 5`

### PR19 판단

- 전체 기준으로 `depth_cm 제거` 근거는 없음
- `cold_2d`에서는 `cm` 쪽이 일관되게 더 낫지만 효과 크기는 작지 않음
- `cold_3d`에서는 일관된 개선이 없음
- 따라서 `depth_cm`를 전역 제거하는 방향은 기각
- 대신 `2D / 3D 분기`나 `slice별 fallback` 검토 근거로 유지

### 추가 해석

- `PR17`과 `PR19`를 같이 보면
- `depth` 정보 자체를 없애는 것은 맞지 않음
- 다만 `Cold 2D`는 현재 운영 LAD의 약점 구간일 가능성이 높음
- 다음 실험은
- `Cold 2D 전용 보수적 fallback`
- 또는 `Cold 2D만 별도 expert로 두고 나머지는 기존 V0 유지`
- 같은 제한적 실험이 더 적절함

## 13. PR18 추가 재현

### 실행 완료

- `scripts/track3/pr18_branch_depth_matrix.py`

### PR18 — 분기 모델 × depth 표현 조합 multi-seed

- 가설
- `2D / 3D` 분기와 `depth` 표현 방식을 함께 조정하면
- 전체 운영 구조를 바꾸지 않고도 Cold 성능을 더 안정적으로 줄일 수 있을 것이다
- 방법
- 5개 seed
- 4개 모델 구조
- `V0`
- 단일 모델
- `V1`
- Warm만 분기
- `V2`
- Cold만 분기
- `V3`
- Warm / Cold 모두 분기
- 3개 depth 표현
- `cm_only`
- `has_only`
- `both`

### PR18 핵심 결과

- 기준 `V0_cm_only`
- Warm `0.2071 ± 0.0089`
- Cold `0.4770 ± 0.1038`
- `V0_has_only`
- Warm `0.2250 ± 0.0103`
- Cold `0.4736 ± 0.0893`
- `V0_both`
- Warm `0.2071 ± 0.0089`
- Cold `0.4710 ± 0.0918`
- `V2_cm_only`
- Warm `0.2071 ± 0.0089`
- Cold `0.4636 ± 0.0904`
- `V3_cm_only`
- Warm `0.2136 ± 0.0094`
- Cold `0.4636 ± 0.0904`

### PR18 해석

- 전체 후보 중 Cold가 가장 좋은 쪽은 `V2_cm_only`
- 즉
- `Cold만 2D / 3D 분기`
- `depth는 cm_only 유지`
- 구조가 가장 현실적인 후보
- `has_only`는 Warm / Cold 모두에서 일관되게 불리
- `both`는 `cm_only` 대비 추가 이득이 거의 없음

### PR18 slice 해석

- `V2_cm_only`
- Warm 2D
- `0.2519 → 0.2519`
- 변화 없음
- Warm 3D
- `0.1896 → 0.1896`
- 변화 없음
- Cold 2D
- `0.5883 → 0.5586`
- 개선
- Cold 3D
- `0.4199 → 0.4260`
- 악화

### PR18 판단

- `V2_cm_only`는 Cold 전체 median을 낮추는 신호는 있음
- 하지만 실제 개선은 거의 `Cold 2D`에 집중됨
- `Cold 3D`는 오히려 악화
- Warm 쪽은 사실상 변화 없음
- 따라서 `Cold 전체 모델 교체`로 보기엔 근거가 약함
- 대신
- `Cold 2D 전용 fallback`
- 또는 `Cold 2D만 expert 적용, 나머지는 기존 V0 유지`
- 같은 제한적 실험 후보로 보는 것이 적절함

### PR17 / PR18 / PR19 종합 해석

- `depth_cm`를 전역 제거하는 방향은 기각
- `has_depth`만 쓰는 단순화도 기각
- `2D / 3D` 분기는 전체 구조 변경안으로는 아직 부족
- 다만 `Cold 2D`는 반복적으로 개선 가능성이 관찰됨
- 따라서 다음 우선순위는
- `Cold 2D 한정 fallback`
- `Cold 2D 한정 expert`
- 같이 적용 범위를 좁힌 실험이 적절함
