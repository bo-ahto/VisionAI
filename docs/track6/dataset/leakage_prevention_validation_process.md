# Track 6 데이터 검증 및 누수 방지 프로세스

- 목적: 모델 실험 전에 데이터 검증 절차를 고정해 가격/정답/출처/작가 정보 누수를 줄임
- 적용 범위: Track6 split 생성, 컬럼 품질 검증, feature/label 분리, 학습, validation 평가, test 최종 평가
- 핵심 원칙: 모델 학습/예측 코드는 정답 가격이 들어 있는 full split 파일을 직접 읽지 않음
- 학습/평가 라벨 사용 순서도: `docs/track6/dataset/train_eval_label_flow.md`

## 1. 기본 원칙

- full split CSV는 감사, 재생성, 품질 검증용으로만 사용함
- 모델 학습과 예측은 `features/warm` 또는 `features/cold` 파일만 사용함
- 정답 가격은 `labels` 파일에만 보관함
- 평가 스크립트만 예측값과 labels 파일을 결합함
- validation labels는 모델/피처 선택에 사용 가능함
- test labels는 최종 후보가 고정된 뒤 최종 확인에만 사용함
- test 결과를 보고 피처, 모델, 보정 방식, 가격 범위 정책을 다시 고르면 안 됨

## 2. 파일별 사용 규칙

| 파일 종류 | 위치 | 사용 목적 | 모델 학습/예측에서 사용 |
|---|---|---|---|
| full split | `data/track6_split/track6_*.csv` | split 감사, 품질 검증, 재생성 확인 | 금지 |
| Warm feature | `data/track6_split/features/warm/` | Warm 모델 학습/예측 입력 | 허용 |
| Cold feature | `data/track6_split/features/cold/` | Cold 모델 학습/예측 입력 | 허용 |
| label | `data/track6_split/labels/` | 평가용 정답 가격과 slice 메타 | 학습/예측 금지, 평가만 허용 |
| prediction | `data/track6/predictions/` | 모델 예측 결과 | 평가 입력 |
| manifest | `data/track6/manifests/` | 피처/라벨 분리 상태 기록 | 참고용 |

## 3. 고정 검증 순서

- 1단계: 원본 후보 데이터 및 작가 한글명 보정 데이터 확인
  - 1차 입력: `data/track4_primary_market_feature_candidates_v1.csv`
  - Track6 보정 입력: `data/track6/track6_feature_candidates_name_corrected.csv`
  - 확인: 가격, 크기, 재료, 지지체, 작가명, 동명이인 후보, 중복 작품 후보

- 2단계: split 생성
  - 실행: `python3 scripts/track6/create_track6_splits.py`
  - 산출물:
    - `data/track6_split/track6_train.csv`
    - `data/track6_split/track6_val_warm.csv`
    - `data/track6_split/track6_test_warm.csv`
    - `data/track6_split/track6_val_cold.csv`
    - `data/track6_split/track6_test_cold.csv`
  - 목적: Warm/Cold 평가 기준을 먼저 고정함

- 3단계: split 품질 검증
  - 보고서: `docs/track6/dataset/split_report.md`
  - 확인:
    - Cold 작가가 train과 겹치지 않는지
    - Cold 한글 작가명이 train과 겹치지 않는지
    - Warm 작가가 train에 존재하는지
    - Warm 평가 작가의 train 작품 수가 충분한지
    - validation/test 데이터 양이 너무 작지 않은지
    - 동일 작품 후보가 train과 평가셋에 동시에 들어가지 않았는지

- 4단계: 컬럼 품질 검증
  - 실행: `python3 scripts/track6/validate_track6_dataset_columns.py`
  - 보고서: `docs/track6/dataset/column_quality_report.md`
  - 확인:
    - 필수 컬럼 결측
    - 숫자 범위 이상값
    - 파생값 계산 불일치
    - 카테고리 unknown 비율
    - Warm/Cold split 누수

- 5단계: feature/label 분리
  - 실행: `python3 scripts/track6/export_feature_label_splits.py`
  - 보고서: `docs/track6/dataset/feature_label_pipeline_report.md`
  - 목적:
    - 가격/정답 컬럼을 feature 파일에서 제거함
    - 출처, URL, 이미지, raw 작가명 같은 운영/누수 위험 컬럼을 제거함
    - Cold feature에서 작가 식별/작가 이력 컬럼을 제거함

- 6단계: feature 누수 검사
  - 확인:
    - feature 파일의 가격성 컬럼 수가 0인지
    - `price`, `krw`, `usd`, `currency`, `amount`, `sold`, `sale`, `cost`, `fee` 계열 컬럼이 제거됐는지
    - Cold feature에 `artist_key`, `artist_name_ko`, `artist_works_log`, `artist_works_count_train`이 없는지
    - Warm feature에도 raw 작가명, URL, 출처, title raw가 없는지

- 7단계: 학습
  - 학습 입력:
    - feature 파일
    - train label 파일
  - 금지:
    - full split 직접 사용
    - validation/test label을 학습에 사용
    - test 성능을 보고 피처 선택

- 8단계: validation 예측
  - 예측 입력:
    - validation feature 파일만 사용
  - 출력:
    - validation prediction 파일 생성
  - 원칙:
    - 예측 스크립트는 validation label 파일을 읽지 않음

- 9단계: validation 평가
  - 평가 입력:
    - validation prediction 파일
    - validation label 파일
  - 사용 목적:
    - 피처 선택
    - 모델 선택
    - 하이퍼파라미터 선택
    - 가격 범위 후보 선택

- 10단계: 후보 고정
  - 고정 대상:
    - Warm 후보 모델
    - Cold 후보 모델
    - 사용 피처
    - 전처리 방식
    - 보정 방식
    - 가격 범위 정책
  - 기록:
    - 개별 실험 문서
    - 실험 결과표
    - manifest 또는 후보 고정 문서

- 11단계: test 예측
  - 예측 입력:
    - test feature 파일만 사용
  - 원칙:
    - test label은 예측 단계에서 읽지 않음
    - test는 최종 후보가 고정된 뒤 한 번만 평가함

- 12단계: test 최종 평가
  - 평가 입력:
    - test prediction 파일
    - test label 파일
  - 사용 목적:
    - 최종 성능 보고
    - 운영 가능성 판단
  - 금지:
    - test 결과를 보고 모델/피처를 다시 고른 뒤 같은 test로 재평가

## 4. 중단 기준

- feature 파일에 가격성 컬럼이 남아 있으면 실험 중단
- Cold feature에 작가 식별 또는 작가 이력 컬럼이 남아 있으면 실험 중단
- 학습 코드가 full split 파일을 직접 읽으면 실험 중단
- 학습 코드가 validation/test label을 읽으면 실험 중단
- 예측 코드가 label 파일을 읽으면 실험 중단
- test 결과를 보고 후보를 바꾸면 해당 test 결과는 최종 성능으로 사용하지 않음
- split을 다시 만들면 T6-E001부터 이후 실험을 다시 실행함

## 5. 실험 스크립트 작성 규칙

- 학습 스크립트는 feature 경로와 label 경로를 명시적으로 분리함
  - 예: `--feature-path data/track6_split/features/warm/track6_train_warm_features.csv`
  - 예: `--label-path data/track6_split/labels/track6_train_labels.csv`
- 예측 스크립트는 feature 경로만 받음
  - 예: `--feature-path data/track6_split/features/warm/track6_val_warm_warm_features.csv`
- 평가 스크립트는 prediction 경로와 label 경로만 받음
  - 예: `--prediction-path data/track6/predictions/...csv`
  - 예: `--label-path data/track6_split/labels/track6_val_warm_labels.csv`
- full split 파일을 입력으로 받는 모델 실험 스크립트는 Track6 공식 실험으로 사용하지 않음

## 6. 검증 결과 기록 방식

- 각 실험 문서에 반드시 기록:
  - 사용 feature 파일
  - 사용 label 파일
  - 사용 모델
  - 사용 피처
  - validation 또는 test 구분
  - 가격성 컬럼 누수 여부
  - Cold 작가 피처 제거 여부
  - 평가 지표
  - 결론
- 실험 결과표에는 validation 결과와 test 결과를 구분해 기록함
- test 결과가 있으면 “최종 후보 고정 후 실행 여부”를 함께 기록함

## 7. 현재 Track6 상태

- split 생성: 완료
- split 품질 검증: 완료
- 컬럼 품질 검증: fail 0, review 항목 관리
- feature/label 분리: 완료
- Warm feature 누수 의심 컬럼: 0개
- Cold feature 누수 의심 컬럼: 0개
- 다음 단계: 이 프로세스에 맞춰 baseline 모델 실험부터 진행
