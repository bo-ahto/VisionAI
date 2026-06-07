# C2 작가명 + 재료 실험 지시 기록

- 실험 목적:
  - 작가명을 이미 넣은 상태에서도 재료 정보가 작품 가격 예측을 개선하는지 확인한다.
  - B1의 `artist_name_ko only`를 기준선으로 사용한다.

- 비교 피처:
  - `artist_name_ko`
  - `artist_name_ko + medium_category`
  - `artist_name_ko + collected_material_raw_bucket`
  - `artist_name_ko + nant_material_idx`
  - `artist_name_ko + nant_tool`
  - `artist_name_ko + nant_material_idx + nant_tool`

- 처리 기준:
  - `artist_name_ko`와 재료 변수는 범주형으로 one-hot 처리한다.
  - `collected_material_raw_bucket`은 train 기준 상위 80개 원문 재료와 other로 묶는다.
  - 정답 가격은 학습 target과 평가 지표 계산에만 사용한다.

- 판단 기준:
  - Warm에서 B1 기준선보다 MdAPE 또는 RMSE(log)가 낮아지면 재료 정보의 추가 설명력이 있다고 본다.
  - Cold는 신규 작가명 상황이라 참고값으로만 본다.
