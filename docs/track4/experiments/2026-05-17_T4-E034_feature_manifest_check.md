# T4-E034 금지 피처 manifest 검사

- 날짜: 2026-05-17
- 연결 가설: T4-H25
- 목적: 모델 학습 전 운영 불가 피처와 누수 가능 피처가 입력 변수에 섞이지 않는지 자동으로 검사
- 사용 데이터:
- `data/track4_split/track4_train.csv`
- `data/track4_split/track4_val_warm.csv`
- `data/track4_split/track4_val_cold.csv`
- `data/track4_split/track4_test_warm.csv`
- `data/track4_split/track4_test_cold.csv`

## 가설

- 모델 학습 전에 금지 피처 manifest를 검사하면 source/gallery/price 계열 피처가 실수로 학습에 들어가는 문제를 줄일 수 있다.

## 실험 방법

- 금지 피처 manifest를 생성함
- manifest 파일: `configs/track4/feature_manifest.json`
- 금지 기준:
- `source`, `url`, `image`, `gallery`, `tier`, `price`, `title`, `exclude` 패턴 포함 피처는 모델 입력 금지
- `price_krw`, `ln_price_krw`는 정답값이므로 모델 입력 금지
- `track4_source`, URL, 이미지, 원본 제목, 원본 작가명은 원본 추적용으로만 허용
- `is_high_price_candidate`는 예측 전에 알 수 없는 분석용 flag이므로 모델 입력 금지
- 현재 Warm / Cold 후보 피처셋을 검사함
- 의도적으로 잘못된 피처셋을 넣은 negative control도 함께 검사함
- 실행 명령:

```bash
python3 scripts/track4/check_feature_manifest.py
```

## 검사 대상 피처셋

- `warm_current_candidate`
- `artist_key`
- `artist_works_log`
- `artist_works_count_train`
- `medium_category`
- `support_category`
- `log_area`
- `aspect_ratio`
- `width_cm`
- `height_cm`
- `has_depth`
- `is_3d_candidate`

- `cold_current_candidate`
- `medium_category`
- `support_category`
- `log_area`
- `aspect_ratio`
- `width_cm`
- `height_cm`
- `has_depth`
- `is_3d_candidate`

- `cold_reduced_candidate`
- `medium_category`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`

- `structure_only_baseline`
- `medium_category`
- `support_category`
- `log_area`
- `aspect_ratio`
- `has_depth`
- `is_3d_candidate`

## 결과

- 결과 파일: `data/track4/results/t4_e034_feature_manifest_check.json`
- 현재 모델 후보 피처셋 검사: 통과
- 검사한 모델 피처셋 수: 4개
- missing column: 0건
- forbidden feature violation: 0건
- negative control 검사: 통과
- `track4_source` 포함 예시: 차단됨
- `price_krw` 포함 예시: 차단됨
- `gallery_tier` 포함 예시: 차단됨

## 해석

- 현재 Warm / Cold 후보 피처셋에는 source/gallery/price 계열 피처가 들어가지 않음
- split 파일에는 원본 추적용 컬럼이 남아 있지만, manifest 기준상 모델 입력에는 사용하지 않도록 분리됨
- 이 검사는 성능 개선 실험이 아니라 재현성과 운영 안전성을 위한 사전 검문 역할임

## 결론

- T4-H25는 검증 완료로 처리함
- 후속 모델 학습 스크립트는 피처셋을 추가하거나 변경할 때 이 manifest 검사를 통과해야 함
- 최종 운영 패키지 dry-run인 T4-H30에서 이 검사를 필수 단계로 연결함
