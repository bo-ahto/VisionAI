# Track 3 문서 관리 구조

- 목적: Track 3 문서를 역할별로 나누어 관리하기 위한 안내 문서
- 원칙
- 설명 문서와 관리 표를 분리함
- `실험 1건 = 기록 1개`
- 요약은 표로 보고, 상세 해석은 문서에서 봄

## 1. 권장 구조

### A. 종합 안내 문서

- 역할
- 처음 보는 사람이 전체 흐름을 가장 빠르게 이해하는 입구 문서
- 문서
- [`docs/track3_overview_guide.md`](/Users/bo/VisionAI/docs/track3_overview_guide.md:1)

### A-1. 문서 구조 순서도

- 역할
- 상사 보고용으로 Track 3 문서 연결 구조를 그림으로 설명
- 문서
- [`docs/track3_document_flowchart.md`](/Users/bo/VisionAI/docs/track3_document_flowchart.md:1)

### B. 기준 문서

- 역할
- Track 3 전체 실험 원칙과 기준 유지
- 문서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)

### C. 현재 의사결정 요약

- 역할
- 지금 기준으로 어떤 모델/피처/운영 정책을 후보로 보는지 한 장으로 정리
- 문서
- [`docs/track3_current_decision_summary.md`](/Users/bo/VisionAI/docs/track3_current_decision_summary.md:1)

### D. 가설 설명 문서

- 역할
- 어떤 가설을 왜 검토하는지 설명
- 문서
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)

### E. 보고용 가설 문서

- 역할
- 상사 보고용으로 가설 관리 방식과 현재 가설 목록을 간단히 설명
- 문서
- [`docs/track3_hypothesis_brief_for_report.md`](/Users/bo/VisionAI/docs/track3_hypothesis_brief_for_report.md:1)

### F. 가설 요약표

- 역할
- 현재 가설 상태를 한눈에 보기 위한 표
- 문서
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)

### G. 가설 결과 종합표

- 역할
- 가설별로 연결된 실험과 현재 결론을 한 번에 보기 위한 문서
- 문서
- [`docs/track3_hypothesis_result_summary.md`](/Users/bo/VisionAI/docs/track3_hypothesis_result_summary.md:1)

### H. 실험 결과 요약표

- 역할
- 실행된 실험 결과를 한눈에 보기 위한 표
- 문서
- [`docs/track3_experiment_results_table.md`](/Users/bo/VisionAI/docs/track3_experiment_results_table.md:1)

### I. 개별 실험 기록

- 역할
- 실험별 상세 기록 관리
- 폴더
- [`docs/track3_experiments`](/Users/bo/VisionAI/docs/track3_experiments/README.md:1)

### J. 재현 요약 문서

- 역할
- 한 날짜에 재현한 큰 흐름과 주요 결론 정리
- 문서
- [`docs/track3_reproduction_summary_20260513.md`](/Users/bo/VisionAI/docs/track3_reproduction_summary_20260513.md:1)

### K. 문서 작성 프로세스

- 역할
- 어떤 문서를 언제 만들고 업데이트할지 관리
- 문서
- [`docs/track3_documentation_process.md`](/Users/bo/VisionAI/docs/track3_documentation_process.md:1)

### L. 계획서 ↔ 가설 ↔ 실험 매핑표

- 역할
- 계획서 단계, 가설 ID, 실제 실행 실험의 연결 관계를 확인
- 문서
- [`docs/track3_plan_hypothesis_experiment_map.md`](/Users/bo/VisionAI/docs/track3_plan_hypothesis_experiment_map.md:1)

### M. 원본 결과 파일

- 역할
- 스크립트 실행 결과의 원본 수치 보관
- 위치
- `data/track3_*.json`

### N. 문서 감사 기록

- 역할
- 실험 문서가 기준에 맞게 작성됐는지 점검한 결과 보관
- 문서
- [`docs/track3_document_audit_20260513.md`](/Users/bo/VisionAI/docs/track3_document_audit_20260513.md:1)

## 2. 운영 방식

- 계획서 수정
- 전체 기준이 바뀔 때만 수정
- 가설 문서 수정
- 새 가설 추가 또는 상태 변경 시 수정
- 가설 요약표 수정
- 가설 상태가 바뀔 때 즉시 반영
- 실험 결과 요약표 수정
- 실험 종료 후 바로 반영
- 개별 실험 기록 작성
- 실험 1건마다 1개 파일 작성

## 3. 보는 순서

- 처음 볼 때
- `track3_docs_structure.md`
- `track3_document_flowchart.md`
- `track3_overview_guide.md`
- `track3_experiment_plan_v1.md`
- `track3_documentation_process.md`
- `track3_plan_hypothesis_experiment_map.md`
- `track3_current_decision_summary.md`
- `track3_hypothesis_table.md`
- `track3_hypothesis_result_summary.md`
- 진행 상황 확인할 때
- `track3_experiment_results_table.md`
- `docs/track3_experiments/INDEX.md`
- 상세 해석이 필요할 때
- 개별 실험 기록 문서
- 원본 수치 확인이 필요할 때
- `data/track3_*.json`
