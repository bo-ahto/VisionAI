# Track 4 문서 인덱스

- 목적: Track 4 관련 문서와 실험 결과를 폴더 기준으로 관리
- 기준일: 2026-05-17

## 1. 바로 볼 문서

- 실험 현황: `dashboard/experiment_dashboard.html`
- 실험 계획: `planning/experiment_plan_v1.md`
- 문서 체계: `planning/docs_structure.md`
- 가설 상태표: `tables/hypothesis_table.md`
- 실험 결과표: `tables/experiment_results_table.md`
- 데이터셋 최종 검토: `dataset/final_quality_review_2026-05-17.md`

## 2. 폴더 역할

- `planning/`
- 실험 계획, Warm / Cold 프로세스, 문서 운영 기준

- `dataset/`
- 데이터셋 구성, 클렌징 파이프라인, split, 최종 품질 검토

- `audits/`
- 가격, 크기, 작가, 재료, 중복, 출처, 컬럼 값 감사 리포트

- `tables/`
- 가설 상태표와 실험 결과 요약표

- `experiments/`
- 개별 실험 기록

- `dashboard/`
- 자동 생성 HTML 대시보드

## 3. 실험 후 업데이트 순서

- `experiments/`에 개별 실험 기록 작성
- `tables/experiment_results_table.md`에 결과 요약 추가
- `tables/hypothesis_table.md`의 상태와 현재 판단 수정
- `python3 scripts/track4/generate_experiment_dashboard.py` 실행
