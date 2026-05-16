# Track 3 실험 재현 번들 안내

- 생성일: 2026-05-17
- 목적: 압축 파일 하나로 Track 3 실험 문서, 코드, 결과, 데이터 split을 검토하고 주요 실험을 재현할 수 있게 구성
- 기준 프로젝트: `/Users/bo/VisionAI`

## 1. 먼저 볼 파일

- 전체 요약
- `docs/track3_overview_guide.md`
- `docs/track3_current_decision_summary.md`
- `docs/track3_experiment_dashboard.html`
- 실험 계획
- `docs/track3_experiment_plan_v1.md`
- `docs/track3_plan_hypothesis_experiment_map.md`
- 실험 결과표
- `docs/track3_experiment_results_table.md`
- `docs/track3_hypothesis_result_summary.md`
- 코드 감사
- `docs/track3_experiment_code_audit_20260515.md`

## 2. 포함된 주요 폴더

- `docs/track3*.md`
- Track 3 계획서, 결과 요약, 가설표, 문서 구조, 감사 문서
- `docs/track3*.html`
- Track 3 결과 확인용 HTML 리포트와 대시보드
- `docs/track3_experiments/`
- 가설별 개별 실험 기록
- `scripts/track3/`
- Track 3 실험 실행 코드
- `data/release_split/`
- Track 3 공식 train / warm test / cold test 데이터
- `data/track3_*.json`
- 각 실험의 실행 결과 JSON
- `data/production/`
- Track 3 production 후보 모델 및 메타데이터

## 3. 환경 준비

- Python 권장 버전: `3.11+`
- 주요 의존성
- `pandas`
- `numpy`
- `scikit-learn`
- `lightgbm`
- `xgboost`
- `catboost`
- `joblib`
- `optuna`
- 의존성 기준 파일
- `pyproject.toml`

예시 설치:

```bash
pip install -e ".[price-engine-core,price-engine-exp]"
```

## 4. 데이터 기준

- 학습 데이터
- `data/release_split/track3_train.csv`
- Warm 평가 데이터
- `data/release_split/track3_test_warm.csv`
- Cold 평가 데이터
- `data/release_split/track3_test_cold.csv`
- split 설명
- `data/release_split/README.md`
- `data/release_split/split_metadata.json`

## 5. 주요 재현 명령

- 전체 코드 문법 확인

```bash
python3 -m py_compile scripts/track3/*.py
```

- 실험 대시보드 재생성

```bash
python3 scripts/track3/generate_experiment_dashboard.py
```

- production 후보 재학습

```bash
python3 scripts/track3/production_train.py
```

- production 후보 평가

```bash
python3 scripts/track3/pr16f_eval_production.py
```

- 주요 가설 재현 예시

```bash
python3 scripts/track3/h31_warm_champion_feature_retest.py
python3 scripts/track3/h32_cold_3d_conditional_fallback.py
python3 scripts/track3/h66_warm_lgbm_retune_multiseed.py
python3 scripts/track3/h68_warm_routing_threshold.py
python3 scripts/track3/h70_h72_operational_revalidation.py
```

## 6. 결과를 읽는 기준

- Warm / Cold는 합쳐서 판단하지 않음
- Warm은 학습 데이터에 등장한 작가의 새 작품 예측
- Cold는 학습 데이터에 없는 신규 작가의 작품 예측
- 주요 지표는 `median APE`
- 낮을수록 좋은 대표 오차 지표
- 가격 범위는 `coverage`와 `range width`를 함께 봄
- coverage만 높고 range width가 너무 넓으면 서비스성이 낮음

## 7. 현재 Track 3 핵심 결론

- Warm 후보
- H66 larger-low-lr LightGBM 계열
- 작가 정보와 작가 이력 피처가 성능에 중요
- 단, 작가 이력 피처는 temporal-safe 검증이 운영 전 필요
- Cold 후보
- H32 조건부 fallback
- 전체 Cold 단일 가격 서비스는 신뢰도 한계가 있음
- Cold는 가격 범위와 신뢰도 경고 중심으로 보는 것이 안전
- 라우팅 기준
- 학습 데이터에 작가가 있으면 Warm 우선
- 학습 데이터에 작가가 없으면 Cold
- 저이력 Warm도 Cold 전환보다 Warm 유지가 유리했음

## 8. 주의사항

- Track 3 초반 실험은 탐색 성격이 있었고, 후반에 가설/문서 체계로 재정리됨
- 최종 운영 적용 전에는 Track 4에서 새 클렌징 데이터 기준으로 다시 확인해야 함
- 일부 실험은 release split을 반복 사용했으므로 운영 확정에는 추가 holdout 또는 calibration 검증이 필요함
- `source` 관련 피처는 Track 3 탐색에서는 쓰였으나, 실제 운영 입력에는 없으므로 Track 4에서는 제외 원칙으로 전환됨
