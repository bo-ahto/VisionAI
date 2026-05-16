# Track 3 공유용 슬림 번들 안내

- 생성일: 2026-05-17
- 목적: 상사 검토용으로 문서는 HTML 중심으로 깔끔하게 보고, 필요한 경우 코드/결과 파일로 실험을 재현할 수 있게 구성

## 1. 문서 구성

- 압축 파일에는 개별 Markdown 실험 문서를 넣지 않음
- 문서는 아래 HTML과 이 README만 포함함
- `docs/track3_experiment_dashboard.html`
- `docs/track3_modeling_results_v4.html`
- `docs/track3_f1_f6_closure_report.html`
- `docs/track3_pr17_18_branch_experiment.html`
- `docs/track3_modeling_results_v1.html`
- `docs/track3_modeling_results_v2.html`
- `docs/track3_modeling_results_v3.html`

## 2. 먼저 볼 순서

- 1순위: `docs/track3_experiment_dashboard.html`
- 전체 실험 현황과 핵심 지표 확인
- 2순위: `docs/track3_modeling_results_v4.html`
- 최종 모델 후보와 주요 결론 확인
- 3순위: `docs/track3_f1_f6_closure_report.html`
- F1~F6 실험 정리 확인
- 4순위: `docs/track3_pr17_18_branch_experiment.html`
- 2D/3D 분기 실험 확인

## 3. 재현용 포함 파일

- `scripts/track3/`
- Track 3 실험 코드
- `data/release_split/`
- 공식 학습 데이터 / Warm 평가 데이터 / Cold 평가 데이터
- `data/track3_*.json`
- 실험 결과 JSON
- `data/production/`
- 서비스 적용 후보 모델과 설명 정보
- `data/track3_splits/`
- 일부 재검증/mini split 파일
- `pyproject.toml`
- Python 의존성 기준

## 4. 주요 용어 쉽게 보기

- Warm: 학습 데이터에 이미 등장한 작가의 작품을 예측하는 상황
- Cold: 학습 데이터에 없는 신규 작가의 작품을 예측하는 상황
- 고정 평가 데이터: 같은 기준으로 성능을 비교하기 위해 미리 나눠 둔 학습/평가 데이터
- 비교 기준 모델: 새 방법이 좋아졌는지 비교하기 위해 먼저 만든 기본 모델
- 대표 오차율: 작품별 오차율의 중앙값이며, 낮을수록 좋음
- W30: 예측 가격이 실제 가격의 30% 이내에 들어온 비율이며, 높을수록 좋음
- 가격 범위 포함률: 제시한 가격 범위 안에 실제 가격이 들어온 비율
- 가격 범위 폭: 예측 가격 주변으로 얼마나 넓은 범위를 보여줘야 하는지 나타내는 값
- 큰 오차 위험: 일부 작품에서 예측이 매우 크게 빗나가는 위험
- 보조 방식: 특정 조건에서 기본 모델 대신 쓰는 보완 모델 또는 규칙
- 모델 선택 규칙: Warm/Cold 또는 2D/3D 조건에 따라 어떤 모델을 쓸지 정하는 기준
- 시점 누수 방지: 예측 당시에는 알 수 없던 미래 정보를 학습에 쓰지 않도록 막는 것

## 5. 주요 재현 명령

```bash
python3 -m py_compile scripts/track3/*.py
python3 scripts/track3/generate_experiment_dashboard.py
python3 scripts/track3/production_train.py
python3 scripts/track3/pr16f_eval_production.py
```

## 6. 주의사항

- 이 번들은 보기 좋은 공유를 위해 문서를 HTML 중심으로 줄인 버전임
- 개별 실험 Markdown 전체가 필요한 경우 `track3_experiment_repro_bundle_20260517.zip`을 사용함
- 일부 실험은 같은 고정 평가 데이터를 반복 사용했으므로 운영 확정 전에는 Track 4에서 새 데이터로 재검증 필요
