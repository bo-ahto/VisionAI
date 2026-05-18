# Track 6 이전 트랙 방법 반영 기준

- 목적: Track3, Track4, Track5에서 사용했던 방법 중 Track6 데이터셋 구성에 반영할 내용을 정리
- 적용 범위: 작가 이름 한글화, 동명이인 필터, Warm/Cold split, 1작가 1작품 평가 방지
- 결론: Track6는 이전 트랙의 방법을 그대로 복사하지 않고, 검증된 기준만 선별해 split 단계에 반영

## 1. Track3에서 반영할 내용

- 작가명 기준 Warm / Cold 개념
  - Warm: 학습 데이터에 작가명이 있는 경우
  - Cold: 학습 데이터에 작가명이 없는 경우
- 작가명은 모델 성능에 큰 영향을 주므로 Warm 전용 피처로만 사용
- Cold 모델은 작가명 없이 작품 구조 정보만 사용
- 작가명 매칭 상태에 따라 라우팅 기준을 나눔
  - 학습 데이터에 충분히 등장하면 Warm
  - 학습 데이터에 적게 등장하면 저이력 Warm 또는 fallback 검토
  - 학습 데이터에 없으면 Cold
- 반복 split 또는 Group 기준 검증이 필요함

## 2. Track4에서 반영할 내용

- 클렌징 후 학습 후보 파일을 따로 만듦
  - raw 통합본과 모델 후보 파일을 분리
  - Track6 입력은 `data/track4_primary_market_feature_candidates_v1.csv` 사용
- 동명이인 처리 방식 반영
  - 원래 한글명은 `artist_name_ko_orig`에 보존
  - 동명이인 여부는 `is_homonym`으로 표시
  - 같은 한글명 안에서 여러 `artist_key`가 있으면 분리 후보로 봄
  - 필요한 경우 `artist_name_ko`에 `_A`, `_B` suffix가 붙은 값을 사용
- source, URL, gallery tier는 모델 피처에서 제외
  - 원본 추적과 품질 감사에는 사용
  - 최종 학습 피처에는 사용하지 않음
- Warm / Cold 프로세스를 분리
  - Warm은 작가 피처 사용 가능
  - Cold는 작가 피처 사용 금지

## 3. Track5에서 반영할 내용

- split을 먼저 고정하고 실험을 시작
- validation과 test 역할을 분리
  - validation: 피처/모델/정책 선택
  - test: 최종 확인
- Warm test 표본을 늘려 1작가 1작품 문제를 줄임
- Cold는 작가 단위로 train과 분리
- 동일 작품 후보가 train과 평가셋에 동시에 있으면 train에서 제거
- 감사 실험에서 확인된 보완점 반영
  - Cold는 `artist_key`뿐 아니라 한글 작가명 기준 중복도 제거해야 함
  - Warm은 train에 남은 작품 수 기준을 강화해야 함
  - test 결과를 보고 후처리 정책을 고르면 안 됨

## 4. Track6에 적용할 최종 원칙

- 작가 이름 한글화
  - `artist_name_ko` 결측률을 먼저 확인
  - `artist_name_ko_orig`와 `artist_name_ko` 차이를 기록
  - 한글명이 없거나 불안정한 작가는 split 전 별도 점검
- 동명이인 필터
  - 같은 `artist_name_ko_orig` 안에 여러 `artist_key`가 있는지 확인
  - `is_homonym`, `artist_entity_suffix`가 있으면 split 검증에 포함
  - Cold는 `artist_key`, `artist_name_ko`, `artist_name_ko_orig` 모두 train과 겹치지 않게 함
- 1작가 1작품 평가 방지
  - Warm 평가 작가는 train에 최소 5작품 이상 남기는 기준을 우선 적용
  - Warm 평가셋에는 가능하면 작가당 2~3작품 포함
  - Cold 평가셋도 작가당 작품 수 분포를 보고 1작품 작가 비율을 기록
  - 1작품만 있는 작가는 전체 성능과 별도 slice 성능을 함께 보고
- 운영 라우팅
  - 운영 입력은 작가 ID가 아니라 작가명일 수 있음
  - 따라서 split 검증과 모델 라우팅 모두 한글 작가명 기준 검증을 포함

## 5. Track6 진행 순서에 반영할 체크리스트

- T6-E001 split 생성 전
  - 한글 작가명 결측률 확인
  - 동명이인 후보 수 확인
  - Cold 이름 중복 제거 가능 여부 확인
  - Warm 최소 train 작품 수 기준 적용 가능 여부 확인
- T6-E001 split 생성 후
  - Cold train 겹침 `artist_key = 0`
  - Cold train 겹침 `artist_name_ko = 0`
  - Cold train 겹침 `artist_name_ko_orig = 0`
  - Warm 평가 작가 train 존재 여부 확인
  - Warm 평가 작가 train 작품 수 분포 확인
  - Warm/Cold 평가셋의 작가당 작품 수 분포 확인
- T6-E002 이후
  - split이 바뀌면 모든 모델 실험을 다시 실행
  - Track5 수치는 참고값으로만 사용
