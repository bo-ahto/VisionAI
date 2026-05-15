# Track 4 클렌징 파이프라인 문서

- 목적: 추가 1차 시장 데이터가 들어왔을 때 같은 기준으로 raw 통합, 감사, 클렌징, split 생성을 반복 실행하기 위한 기준 문서
- 기준일: 2026-05-15
- 실행 스크립트: `scripts/track4/run_cleaning_pipeline.py`
- 최종 클렌징 파일: `data/track4_primary_market_cleaned_v2.csv`
- 최종 피처 후보 파일: `data/track4_primary_market_feature_candidates_v1.csv`

## 1. 기본 원칙

- 원본 수집값은 직접 수정하지 않음
- 원본 컬럼은 출처별 prefix를 붙여 보존함
- 예: `saatchi__price_raw`, `artsy__medium`, `gallery_primary__title`
- 표준화값은 별도 컬럼으로 생성함
- 예: `price_krw`, `width_cm`, `artist_name_standardized`, `medium_category`
- 학습 제외 row는 삭제하지 않음
- `is_training_candidate`와 `cleaning_exclude_reasons`로 관리함
- 출처 컬럼은 모델 피처로 사용하지 않음
- 출처는 원본 추적, 데이터 품질 감사, 분포 확인에만 사용함
- 갤러리 티어도 현재는 모델 피처에서 제외함
- 운영에서 입력받기 어려운 정보는 최종 피처 후보로 바로 채택하지 않음

## 2. 현재 입력 원본

| 출처명 | 입력 파일 | 설명 |
|---|---|---|
| `saatchi` | `data/saatchi_cleaned.csv` | Saatchi 수집/정리 데이터 |
| `artsy` | `data/artsy_kr_artworks.csv` | Artsy 한국 작가 작품 데이터 |
| `artue` | `data/artue_테스트_가격포함.csv` | Artue 가격 포함 데이터 |
| `gallery_primary` | `data/1차 시장 데이터 - 전달본_260504.csv` | 갤러리 1차 시장 전달본 |

## 3. 데이터셋 구성 방식

- 1단계: 출처별 원본 CSV를 그대로 읽음
- 원본 컬럼명은 출처 prefix를 붙여 보존함
- 예: `artsy__artist_name`, `saatchi__price_raw`
- 2단계: 출처별 row 추적 컬럼을 추가함
- `track4_source`
- `track4_source_file`
- `track4_source_row_index`
- 3단계: 모든 출처를 하나의 raw 통합본으로 합침
- 없는 컬럼은 빈칸으로 둠
- 이 단계에서는 가격/크기/재료/작가명을 정규화하지 않음
- 4단계: 가격, 크기, 작가, 재료, 중복, 갤러리 감사를 각각 별도 파일로 생성함
- 5단계: 감사 결과를 merge해서 `cleaned_v2`를 생성함
- 6단계: 모델에 넣을 후보 컬럼만 모아 `feature_candidates_v1`을 생성함
- 7단계: `artist_key` 기준으로 Warm / Cold split을 생성함

## 4. 전체 실행 방법

- 추가 데이터를 반영한 뒤 아래 명령을 실행함

```bash
python3 scripts/track4/run_cleaning_pipeline.py
```

- 이 명령은 아래 단계를 순서대로 실행함
- 중간 단계가 실패하면 전체 실행을 중단함
- 실패한 단계의 감사 리포트를 먼저 확인한 뒤 규칙을 수정함

## 5. 실행 순서

| 순서 | 단계 | 실행 스크립트 | 주요 산출물 |
|---:|---|---|---|
| 1 | raw 통합 | `build_primary_market_raw_collected.py` | `track4_primary_market_raw_collected.csv` |
| 2 | 가격 감사 | `audit_price_consistency.py` | `track4_price_consistency_audit.csv` |
| 3 | 크기 감사 | `audit_size_consistency.py` | `track4_size_consistency_audit.csv` |
| 4 | 작가 감사 | `audit_artist_consistency.py` | `track4_artist_consistency_audit.csv` |
| 5 | 재료/지지체 감사 | `audit_medium_support_consistency.py` | `track4_medium_support_consistency_audit.csv` |
| 6 | 중복 감사 | `audit_duplicate_consistency.py` | `track4_duplicate_consistency_audit.csv` |
| 7 | 갤러리 메타 감사 | `audit_gallery_metadata.py` | `track4_gallery_metadata_audit.csv` |
| 8 | 출처 편향 감사 | `audit_source_bias.py` | `track4_source_bias_audit.md` |
| 9 | cleaned_v2 생성 | `build_primary_market_cleaned_v2.py` | `track4_primary_market_cleaned_v2.csv` |
| 10 | Warm/Cold split 생성 | `create_track4_splits.py` | `data/track4_split/*.csv` |
| 11 | 컬럼별 값 재점검 | `audit_column_value_consistency.py` | `track4_column_value_consistency_audit.csv` |

## 6. 클렌징 기준

### 가격

- `price_raw`는 원문 가격 문자열을 보존함
- `price_krw`는 학습 target으로 사용할 원화 가격임
- `price_krw`가 없으면 학습 후보에서 제외함
- `Price on request`는 숫자 가격이 아니므로 학습 target으로 사용하지 않음
- 1만 원 미만은 비정상 가격 후보로 제외함
- 10억 원 초과는 과대 가격 후보로 제외함
- 1억 원 초과 10억 원 이하는 별도 high-price flag로 남김

### 크기

- 원본 크기 문자열은 `size_raw`에 보존함
- 표준 크기는 `width_cm`, `height_cm`, `depth_cm`로 정리함
- `area_cm2 = width_cm * height_cm`
- `log_area = log(area_cm2)`
- `aspect_ratio = 긴 변 / 짧은 변`
- width/height 결측 또는 0 이하이면 학습 후보에서 제외함
- 1000cm 초과, 면적 1,000,000cm2 초과, aspect ratio 10 초과는 이상값 후보로 감사함
- `depth_cm` 결측은 2D 작품에서 자연스러운 결측일 수 있으므로 단순 오류로 보지 않음
- `has_depth`로 3D 가능성을 관리함

### 작가

- `artist_name_raw`는 출처 원문 작가명임
- `artist_name_standardized`는 공백, 대소문자, 한영 혼재를 정리한 표준 작가명임
- `artist_name_ko`는 표시/검토용 한글 작가명임
- 한글 작가명은 Track 3의 매핑 로직을 재사용함
- 원본에 한글명이 있으면 원본 한글명을 우선 사용함
- 원본 한글명이 없으면 Track 3 작가명 매핑으로 보강함
- `artist_key`는 Warm/Cold split 기준으로 사용함
- 숫자형 작가명 등 식별 불가 row는 감사 이슈로 남김

### 재료/지지체

- `medium_raw`는 원문 재료 문자열임
- `medium_category`는 규칙 기반 대표 재료 분류임
- `support_category`는 규칙 기반 지지체 분류임
- 재료 원문이 없으면 학습 후보에서 제외함
- `medium_category=unknown`은 학습 후보에 남을 수 있으나 후속 실험에서 별도 검토함
- `support_category=unknown`은 현재 많이 남아 있으므로 지지체 피처 사용 시 보수적으로 처리함
- `medium_support_bucket`은 `medium_category__support_category` 형태로 생성함

### 중복

- 중복 row는 즉시 삭제하지 않음
- `duplicate_audit_status`로 중복 후보를 기록함
- `is_duplicate_representative`로 대표 row 여부를 표시함
- 대표가 아닌 중복 row는 학습 후보에서 제외함
- 원본 추적을 위해 모든 중복 후보 row는 cleaned 파일에 남김

### 갤러리/출처

- `gallery_name_raw`와 `gallery_tier_validated`는 보조 메타로 보존함
- 현재 갤러리 티어는 최종 모델 피처에서 제외함
- `track4_source`, `track4_source_file`, `track4_source_row_index`는 원본 추적용임
- 출처 정보는 모델 학습 피처로 사용하지 않음

## 7. 학습 후보 판단

- 학습 후보는 `is_training_candidate=True`인 row임
- 제외 사유는 `cleaning_exclude_reasons`에 남김
- 현재 주요 제외 사유
- 가격 없음
- 가격 비정상
- 핵심 크기 없음
- 재료 원문 없음
- 작가 식별 이슈
- 대표가 아닌 중복 row

## 8. 추가 데이터 반영 절차

- 1단계: 새 원본 파일을 `data/`에 저장함
- 2단계: `scripts/track4/build_primary_market_raw_collected.py`의 `SOURCES`에 출처명과 파일 경로를 추가함
- 3단계: 새 출처의 컬럼을 가격/크기/작가/재료 감사 스크립트에 매핑함
- 4단계: `python3 scripts/track4/run_cleaning_pipeline.py`를 실행함
- 5단계: 아래 리포트를 확인함
- `docs/track4_price_consistency_audit.md`
- `docs/track4_size_consistency_audit.md`
- `docs/track4_artist_consistency_audit.md`
- `docs/track4_medium_support_consistency_audit.md`
- `docs/track4_duplicate_consistency_audit.md`
- `docs/track4_column_value_consistency_audit.md`
- 6단계: row 수, 학습 후보 수, 주요 이슈 수가 크게 바뀌었는지 기록함
- 7단계: 문제가 없으면 split을 기준으로 모델 실험을 진행함

## 9. 추가 데이터 반영 시 반드시 확인할 숫자

- raw 통합 전체 row 수
- 출처별 row 수
- 가격 있는 row 수
- 학습 후보 row 수
- 한글 작가명 누락 수
- 작가 key 수
- Warm/Cold split 작가 겹침 여부
- `medium_category=unknown` 수
- `support_category=unknown` 수
- 크기 이상값 수
- 중복 제외 row 수

## 10. 현재 기준 최신 결과

- raw 통합 rows: `54,842`
- cleaned_v2 rows: `54,842`
- 학습 후보 rows: `34,239`
- feature 후보 파일 rows: `54,842`
- 한글 작가명 rows: `54,840`
- 학습 후보 중 한글 작가명 누락: `0`
- 학습 후보 중 `medium_category=unknown`: `26`
- 학습 후보 중 `support_category=unknown`: `2,786`
- 파생값 계산 불일치: `0`

## 11. 주의사항

- 원본 파일 컬럼명이 바뀌면 감사 스크립트의 source별 매핑도 수정해야 함
- 가격 없는 row는 예측 입력 후보로는 쓸 수 있지만 학습 target으로는 쓸 수 없음
- `Price on request`는 가격 문자열이 있어도 숫자 가격이 아니므로 학습 제외가 맞음
- `track4_source`는 모델 피처가 아니라 감사/추적용임
- `gallery_tier_validated`는 현재 매칭률과 운영 입력 가능성 문제로 모델 피처에서 제외함
- split을 다시 만들면 모델 성능 비교 기준이 바뀌므로, split 변경 시 별도 실험 ID로 기록해야 함
