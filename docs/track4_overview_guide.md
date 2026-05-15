# Track 4 종합 안내 문서

- 목적: Track 3 결과를 보존한 상태에서 Track 4를 별도 단계로 진행하기 위한 입구 문서
- 기준일: 2026-05-15
- 작성 원칙: Track 3 문서와 산출물은 수정하지 않고, Track 4 문서/스크립트/결과 파일을 별도 이름으로 관리함

## 1. Track 4를 왜 따로 시작하는가

- Track 3는 작품 가격 예측 모델의 기본 실험 체계를 만들고 Warm / Cold 후보를 찾는 단계였음
- Track 3에서 이미 정리된 결론은 보존해야 함
- Track 4는 기존 결론을 덮어쓰는 단계가 아니라, 운영 적용 가능성을 더 엄격하게 검증하는 후속 단계로 둠
- 핵심 차이
- Track 3: 어떤 모델과 피처가 성능이 좋은지 찾는 단계
- Track 4: 그 모델을 실제 서비스 기준으로 쓸 수 있는지 검증하는 단계

## 2. Track 3에서 가져오는 기준

- Warm / Cold는 계속 분리해서 판단함
- 기준 데이터는 Track 3 release split을 우선 참조함
- Track 3 현재 후보는 비교 기준으로 보존함
- Warm 후보: H66 larger-low-lr LightGBM
- Cold 후보: H32 조건부 fallback
- 가격 범위 후보: H70 내부 calibration 기반 조건별 가격 범위
- Track 3의 핵심 리스크도 그대로 이어받음
- 작가 이력 피처의 temporal-safe 여부
- release split 반복 사용에 따른 의사결정 과적합 가능성
- Cold 가격 범위가 너무 넓은 문제
- Warm 저이력 작가 구간의 넓은 오차

## 3. Track 4의 기본 목표

- Track 4의 목표는 최종 운영 후보를 더 엄격하게 검증하는 것임
- 단순히 median APE를 더 낮추는 것만 목표로 하지 않음
- 운영에서 중요한 판단을 함께 검증함
- 어떤 입력값을 받을 것인가
- Warm / Cold 라우팅 기준을 어떻게 둘 것인가
- 가격 범위와 신뢰도 경고를 어떻게 보여줄 것인가
- 어떤 조건에서는 예측을 제한하거나 낮은 신뢰도로 표시할 것인가

## 4. Track 4에서 먼저 확인할 질문

- Track 3 최종 후보가 새 검증 방식에서도 유지되는가
- Warm 후보의 작가 이력 피처는 예측 시점 기준으로 안전하게 만들 수 있는가
- Cold는 어떤 구간까지 서비스 가능한가
- 가격 범위는 사용자에게 의미 있는 폭인가
- 신뢰도 경고 기준은 실험 근거로 설명 가능한가
- 최종 운영 모델은 재학습/재현/배포가 가능한 형태인가

## 5. Track 4 문서 구조

- 종합 안내 문서
- `docs/track4_overview_guide.md`
- 실험 계획서
- `docs/track4_experiment_plan_v1.md`
- 클렌징 파이프라인 문서
- `docs/track4_cleaning_pipeline.md`
- Warm / Cold 분리 프로세스 문서
- `docs/track4_warm_cold_process.md`
- 가설/실험 기록
- `docs/track4_experiments/`
- 실험 스크립트
- `scripts/track4/`
- 결과 파일
- `data/track4_*.json`
- `data/track4_*.csv`

## 6. Track 4 운영 원칙

- Track 3 파일명과 결과 파일은 덮어쓰지 않음
- Track 4 실험은 모두 `track4_` 접두어를 사용함
- Track 3 결과를 baseline으로 참조할 수는 있지만, Track 4 결과와 섞어서 기록하지 않음
- 가설은 Track 4 전용 ID를 사용함
- 예시: `T4-H1`, `T4-H2`
- 실험 ID도 Track 4 전용으로 관리함
- 예시: `T4-E001_temporal_safe_warm_features`

## 7. Track 4 시작 전 체크리스트

- Track 3 현재 결론을 baseline으로 고정했는지 확인
- Track 4에서 새로 검증할 목표를 정의
- Track 4에서 사용할 데이터 기준을 정의
- Track 4 가설 ID 체계를 확정
- 실험 결과 기록 형식을 확정
- Track 3 문서와 Track 4 문서를 섞어 수정하지 않도록 확인
