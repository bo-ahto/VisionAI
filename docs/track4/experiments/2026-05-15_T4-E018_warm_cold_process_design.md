# T4-E018 Warm / Cold 분리 프로세스 설계

- 날짜: 2026-05-15
- 상태: 완료
- 연결 가설: T4-H1~T4-H5
- 목적: Track 4 모델 실험을 Warm과 Cold로 분리해서 진행하기 위한 절차를 명확히 문서화

## 1. 배경

- Track 4는 클렌징 파이프라인까지는 정리되었음
- 이후 모델 실험에서는 Warm / Cold를 섞어 판단하면 안 됨
- Warm은 작가 정보 활용 여부가 핵심이고, Cold는 작가 정보 없이 어느 수준까지 가능한지가 핵심임
- 따라서 데이터 검증, 피처, 모델, 평가, 운영 라우팅을 Warm / Cold로 나누어 관리해야 함

## 2. 작업 내용

- Warm / Cold 분리 프로세스 문서 추가
- `docs/track4/planning/warm_cold_process.md`
- Track 4 실험 계획서에 Warm / Cold 분리 실행 순서 추가
- `docs/track4/planning/experiment_plan_v1.md`
- Track 4 종합 안내 문서에 프로세스 문서 링크 추가
- `docs/track4/planning/overview_guide.md`

## 3. 핵심 결정

- `track4_train.csv`는 Warm / Cold 모델이 모두 사용하는 공통 학습 데이터임
- Warm / Cold는 학습 파일이 다른 것이 아니라 평가 대상 작가가 train에 있는지 없는지로 구분함
- Warm 모델은 작가명, 작가 작품 수, 작가 이력 피처를 검증할 수 있음
- Cold 모델은 신규 작가 상황이므로 작가명 효과와 작가별 과거 가격 통계를 사용하지 않음
- 성능은 Warm / Cold를 합산하지 않고 따로 기록함

## 4. 프로세스 요약

| 단계 | Warm | Cold |
|---|---|---|
| split 검증 | test_warm 작가가 train에 모두 있어야 함 | test_cold 작가가 train에 없어야 함 |
| 기본 모델 | 작품 구조 정보만 사용 | 작품 구조 정보만 사용 |
| 피처 확장 | 작가 정보/작가 이력 추가 검증 | 작가 피처 제외, 구조/재료/크기 중심 |
| 모델 비교 | LightGBM 계열 중심, 선형/트리 비교 | LAD/Quantile/Huber/Ridge와 트리 비교 |
| 약점 분석 | 저이력 작가, 고가, 큰 오차 구간 | 2D/3D, 대형, unknown, tail risk |
| 운영 출력 | 단일 가격 + 범위 + 저신뢰 경고 | 범위/경고 중심, 고위험 제한 검토 |

## 5. 다음 작업

- T4 split 검증 결과를 모델 실험 시작 전 별도 기록으로 고정
- Warm 구조-only baseline과 작가 피처 모델 비교 실행
- Cold 구조-only baseline과 robust 모델 비교 실행
- 이후 공통 피처 ablation을 Warm / Cold 모두에서 분리 기록
