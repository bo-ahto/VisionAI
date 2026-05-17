# T4-E021 Track 4 실험 문서/대시보드 체계 구축

- 실험 ID: T4-E021
- 연결 가설: -
- 날짜: 2026-05-17
- 상태: 완료

## 1. 작업 목적

- Track 4 모델 실험을 시작하기 전에 문서 관리 체계를 먼저 고정
- 가설, 실험 결과, 개별 기록, 대시보드를 서로 연결
- Track 3처럼 실험이 길어져도 현재 상태를 한 화면에서 볼 수 있게 구성

## 2. 만든 문서

- `docs/track4/planning/docs_structure.md`
- Track 4 문서 역할과 업데이트 순서 정리
- `docs/track4/tables/hypothesis_table.md`
- 모델 실험 가설과 세부 목표 관리
- `docs/track4/tables/experiment_results_table.md`
- 실험 결과 요약 관리
- `docs/track4/dashboard/experiment_dashboard.html`
- 가설/결과/데이터셋 상태를 자동 생성 HTML로 표시

## 3. 만든 스크립트

- `scripts/track4/generate_experiment_dashboard.py`
- Markdown 표를 읽어서 HTML 대시보드를 생성
- 직접 HTML을 수정하지 않고 기준 Markdown 문서를 수정하는 구조

## 4. 대시보드 구성

- 상단
- 학습 후보 수
- train row 수
- Cold/train 작가 겹침
- Cold 작가 이력 누수
- Warm / Cold split 규모
- 크기 파싱 보완 상태

- 탭
- 가설 상태
- 실험 결과
- 진행 기준

- 표 관리
- 최신 가설과 최신 실험이 위쪽에 보이도록 정렬
- 표가 길어질 것을 대비해 페이지 기능 추가

## 5. 현재 판단

- Track 4는 이제 모델 실험을 실행하기 전에 가설과 연구 방법을 먼저 등록할 수 있는 상태임
- 실험 결과는 개별 기록과 결과표를 업데이트한 뒤 대시보드를 재생성하면 됨
- 데이터 준비 체크포인트와 모델 실험 가설을 분리했기 때문에 실험 실패 원인을 더 명확하게 추적할 수 있음

## 6. 다음 작업

- T4-H1 구조-only Warm / Cold baseline 실행
- 실행 후 아래 문서를 순서대로 업데이트
- `docs/track4/experiments/`
- `docs/track4/tables/experiment_results_table.md`
- `docs/track4/tables/hypothesis_table.md`
- `docs/track4/dashboard/experiment_dashboard.html`
