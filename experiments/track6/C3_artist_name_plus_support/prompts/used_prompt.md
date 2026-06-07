# C3 작가명 + 지지체 실험 지시 기록

- 실험 목적:
  - 작가명을 이미 넣은 상태에서도 지지체 정보가 작품 가격 예측을 개선하는지 확인한다.
  - B1의 `artist_name_ko only`를 기준선으로 사용한다.

- 비교 피처:
  - `artist_name_ko`
  - `artist_name_ko + support_category`
  - `artist_name_ko + nant_support`
  - `artist_name_ko + support_category + nant_support`

- 처리 기준:
  - `artist_name_ko`와 지지체 변수는 범주형으로 one-hot 처리한다.
  - 정답 가격은 학습 target과 평가 지표 계산에만 사용한다.

- 판단 기준:
  - Warm에서 B1 기준선보다 MdAPE 또는 RMSE(log)가 낮아지면 지지체 정보의 추가 설명력이 있다고 본다.
  - Cold는 신규 작가명 상황이라 참고값으로만 본다.
