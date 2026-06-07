# C4 작가명 + 제작연도 실험 지시 기록

- 실험 목적:
  - 작가명을 이미 넣은 상태에서도 제작연도 또는 작품 연한이 작품 가격 예측을 개선하는지 확인한다.
  - B1의 `artist_name_ko only`를 기준선으로 사용한다.

- 비교 피처:
  - `artist_name_ko`
  - `artist_name_ko + artwork_year`
  - `artist_name_ko + artwork_age`
  - `artist_name_ko + artwork_year + artwork_age`

- 처리 기준:
  - `artist_name_ko`는 범주형으로 one-hot 처리한다.
  - `artwork_year`, `artwork_age`는 숫자형으로 처리한다.
  - 숫자형은 중앙값 결측 보정 후 `StandardScaler`를 적용한다.
  - 제작연도 출처, 결측 플래그, 보강 source 컬럼은 운영 입력값이 아니므로 사용하지 않는다.
  - 정답 가격은 학습 target과 평가 지표 계산에만 사용한다.

- 판단 기준:
  - Warm에서 B1 기준선보다 MdAPE 또는 RMSE(log)가 낮아지면 제작연도 정보의 추가 설명력이 있다고 본다.
  - Cold는 신규 작가명 상황이라 참고값으로만 본다.
