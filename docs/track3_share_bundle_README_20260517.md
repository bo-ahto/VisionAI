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
- 공식 train / warm test / cold test 데이터
- `data/track3_*.json`
- 실험 결과 JSON
- `data/production/`
- production 후보 모델과 메타데이터
- `data/track3_splits/`
- 일부 재검증/mini split 파일
- `pyproject.toml`
- Python 의존성 기준

## 4. 주요 재현 명령

```bash
python3 -m py_compile scripts/track3/*.py
python3 scripts/track3/generate_experiment_dashboard.py
python3 scripts/track3/production_train.py
python3 scripts/track3/pr16f_eval_production.py
```

## 5. 주의사항

- 이 번들은 보기 좋은 공유를 위해 문서를 HTML 중심으로 줄인 버전임
- 개별 실험 Markdown 전체가 필요한 경우 `track3_experiment_repro_bundle_20260517.zip`을 사용함
- 일부 실험은 release split을 반복 사용했으므로 운영 확정 전에는 Track 4에서 재검증 필요
