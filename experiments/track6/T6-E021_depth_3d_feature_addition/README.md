# T6-E021 3D/depth 피처 실험

- 상태: 예정
- 실험 단계: 기본 피처 정의 상세 실험
- 단계 설명: 최종 모델 선택 전, 기본 입력 피처에 포함할지 판단하기 위한 실험
- 세부 목표: T6-G5 약점 구간 보완
- 가설: 3D 작품은 면적보다 depth/부피성 피처가 가격 설명에 더 중요할 수 있다.
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 학습에 사용된 피처: `baseline + depth_cm + has_depth + is_3d_candidate`
- 테스트에 사용된 피처: `동일 피처셋`
- 학습 정답값: `ln_price_krw`
- 비교 기준: 2D/3D slice별 성능
- 유의미함 기준: 3D 분기 또는 전용 피처 필요 여부 판단
- HTML 일지: `experiment_log.html`

## 폴더 구조

- `data/`: 실험 전용 학습/테스트 데이터
- `scripts/`: 실험 실행 코드
- `outputs/`: 결과 지표와 예측값
- `logs/`: 실행 로그
