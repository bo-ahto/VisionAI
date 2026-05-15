# Track 3 재현 기록

- 실험 ID: `repro_phase0_pr29`
- 날짜: 2026-05-13
- 단계: 재현 검증
- 상태: 재현완료
- 기록 유형:
- 재현 세션
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 결과 파일:
- [`docs/track3_reproduction_summary_20260513.md`](/Users/bo/VisionAI/docs/track3_reproduction_summary_20260513.md:1)

## 1. 목적

- Track 3 계획서 기준 핵심 실험을 현재 코드 / 현재 split 기준으로 다시 실행
- 기존 결론이 여전히 유지되는지 확인

## 2. 가설

- 기존 Track 3 결론인 `Cold = LAD`, `Warm = tuned LightGBM`가 현재 재현에서도 유지될 것이다

## 3. 사용 데이터

- 데이터 버전:
- `release_split regenerated on 2026-05-13`
- 학습 데이터:
- `data/release_split/track3_train.csv`
- 검증 데이터:
- `data/track3_splits/*`
- 최종 확인 데이터:
- `data/release_split/track3_test_warm.csv`
- `data/release_split/track3_test_cold.csv`
- 데이터 나누기 기준:
- 개발 중간 검증은 `track3_splits`
- 공식 확인은 `release_split`

## 4. 사용 변수

- 핵심 변수:
- `medium_category`
- `support_category`
- `depth_cm`
- `width_cm`
- `height_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- 추가 변수:
- `aspect_ratio`
- `medium_ho_bucket`
- `artist_works_log`
- 제외 변수:
- `source_platform` 최종 운영 입력 제외

## 5. 사용 모델

- Cold baseline:
- LAD / Quantile / Huber / LightGBM / XGBoost / CatBoost 비교
- Warm baseline:
- Quantile / Huber / LightGBM / XGBoost / CatBoost 비교
- 주요 설정값:
- Warm 최종 후보는 `tuned LightGBM`
- Cold 최종 후보는 `LAD / Quantile / Huber` 계열
- 재현 범위는 `Phase 0 ~ Phase 2`, `PR1`, `PR7`, `PR16f`, `PR20 ~ PR29`

## 6. 변경된 요소

- 현재 코드 기준으로 split 재생성
- 현재 코드 기준으로 주요 Phase / PR 실험 재실행

## 7. 성공 기준

- Warm:
- tuned LightGBM 유지 타당성 재확인
- Cold:
- LAD 계열 유지 타당성 재확인
- 보조 기준:
- 기존 F1~F6 개선안이 현재 split에서도 반복되는지 확인

## 8. 실행 내용

- 실행 스크립트:
- `split_data.py`
- `split_for_release.py`
- `baseline.py`
- `train_linear_cold.py`
- `train_linear_warm.py`
- `train_tree_cold.py`
- `train_tree_warm.py`
- `pr7_feature_engineering.py`
- `pr1_optuna_tuning.py`
- `production_train.py`
- `pr16f_eval_production.py`
- `pr20 ~ pr29`
- 산출물:
- `data/track3_*results.json`
- `data/production/*`

## 9. 결과

### Warm

- 사용 변수 요약:
- 기본 작품 변수 + Warm용 `artist_works_log` 계열
- 선형보다 `LightGBM`이 확실히 우세
- production 평가
- `med_APE 0.2056`
- `W30 0.5988`

### Cold

- 사용 변수 요약:
- 작가 비의존 작품 구조 변수 중심
- 트리 / 튜닝보다 `LAD / Quantile / Huber` 계열이 우세
- production 평가
- `med_APE 0.3207`
- `W30 0.4640`

## 10. 해석

- 기존 운영 구조가 현재 재현에서도 유지됨
- Warm은 `artist_works_log` 계열이 유지 가치가 높음
- Cold는 구조적 약점 구간이 있으나 기존 대안들은 운영 채택 실패

## 11. 결론

- 채택 / 보류 / 중단:
- 채택
- 이유:
- `Cold = LAD`, `Warm = tuned LightGBM` 결론 재확인
- 참고 상태:
- 재현완료

## 12. 다음 액션

- `Cold 2D` 한정 fallback 가능성 검토
- depth / branch 계열 실험 별도 기록으로 분리 관리
