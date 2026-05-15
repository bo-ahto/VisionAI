# Track 3 문서 작성 및 업데이트 프로세스

- 목적: Track 3 실험 단계에서 어떤 문서를 언제 작성하고 어떻게 업데이트하는지 고정하기 위한 운영 문서
- 관련 구조 문서:
- [`docs/track3_docs_structure.md`](/Users/bo/VisionAI/docs/track3_docs_structure.md:1)
- 기준 계획서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)

## 1. 기본 원칙

- 실험보다 문서가 뒤처지지 않게 관리함
- 실험을 끝낸 뒤 한꺼번에 정리하지 않음
- `가설 -> 실험 방법 -> 실험 -> 검증 -> 결론` 흐름에 맞춰 문서를 순서대로 작성함
- 가능하면 `실험 1건 = 기록 1개`를 기본으로 함
- 다만 같은 가설 아래의 후속 변형 실험이나 재현 세션은 `묶음 기록` 허용
- 설명 문서와 관리 표를 분리함
- 어떤 형식을 쓰더라도 아래 4가지는 반드시 남김
- 사용 변수
- Warm / Cold 결과
- 해석
- 결론
- 검증 완료로 닫는 실험은 아래 항목까지 남김
- 사용 데이터
- 사용 split
- 실행 코드
- 결과 파일
- 검증 로그 요약
- 후속 가설로 이관한 내용

## 2. 문서 역할 구분

### A. 기준 문서

- 문서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 역할
- Track 3의 전체 실험 기준 유지
- 언제 수정하는가
- 실험 원칙이 바뀔 때만 수정

### B. 가설 설명 문서

- 문서
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 역할
- 현재 검토 중인 가설의 배경, 질문, 현재 판단 설명
- 언제 수정하는가
- 가설이 새로 생기거나
- 기존 가설의 해석이 달라질 때 수정

### C. 가설 요약표

- 문서
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- 역할
- 가설 상태를 한눈에 관리
- 언제 수정하는가
- 가설 상태가 바뀔 때 즉시 수정

### D. 실험 결과 요약표

- 문서
- [`docs/track3_experiment_results_table.md`](/Users/bo/VisionAI/docs/track3_experiment_results_table.md:1)
- 역할
- 실행된 실험 결과를 한눈에 관리
- 언제 수정하는가
- 실험 종료 후 바로 수정

### E. 개별 실험 기록

- 폴더
- [`docs/track3_experiments`](/Users/bo/VisionAI/docs/track3_experiments/README.md:1)
- 역할
- 단일 실험, 묶음 실험, 재현 세션의 상세 실행 내용과 결과 기록
- 언제 작성하는가
- 실험 시작 전 초안 작성
- 실험 종료 후 결과/해석/결론 보완

### F. 재현 요약 문서

- 문서
- [`docs/track3_reproduction_summary_20260513.md`](/Users/bo/VisionAI/docs/track3_reproduction_summary_20260513.md:1)
- 역할
- 대규모 재현 또는 묶음 실험 결과를 날짜 기준으로 정리
- 언제 작성하는가
- 한 번에 여러 실험을 재현하거나
- 한 세션의 종합 결론을 남길 때 작성

### G. 원본 결과 파일

- 위치
- `data/track3_*.json`
- 역할
- 스크립트 실행 결과 원본 수치 보관
- 언제 생성하는가
- 실험 스크립트 실행 시 자동 생성 또는 갱신

### H. HTML 대시보드

- 문서
- [`docs/track3_experiment_dashboard.html`](/Users/bo/VisionAI/docs/track3_experiment_dashboard.html:1)
- 역할
- 가설 상태와 실험 결과를 한 화면에서 보기 위한 보기용 문서
- 기준 데이터
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- [`docs/track3_experiment_results_table.md`](/Users/bo/VisionAI/docs/track3_experiment_results_table.md:1)
- 생성 방법
- `python3 scripts/track3/generate_experiment_dashboard.py`
- 원칙
- HTML을 직접 수정하지 않음
- 가설/실험 내용을 수정할 때는 Markdown 기준 문서를 먼저 수정함
- 기준 문서 수정 후 생성 스크립트로 HTML을 다시 만듦

## 3. 실험 단계별 문서 작성 순서

### 단계 1. 새 가설을 생각했을 때

- 먼저 확인할 문서
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 해야 할 일
- 기존 가설과 중복인지 확인
- 상위 가설의 하위 또는 후속 가설인지 확인
- 예시
- H13, H14, H15는 H2의 Cold 약점 보완 후속 가설로 연결
- 새 가설이면 가설 설명 문서에 추가
- 가설 요약표에 상태 `예정`으로 추가

### 단계 2. 실험 방법을 정할 때

- 먼저 확인할 문서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 해야 할 일
- 데이터 / split / 변수 원칙 위반이 없는지 확인
- baseline과 variant를 명확히 정함
- 성공 기준을 먼저 정함
- 공통 피처인지 Warm 전용 피처인지 Cold 전용 제약인지 구분함
- 공통 피처라면 Warm / Cold 모두 평가하도록 설계함
- 개별 실험 기록 파일 초안을 만듦

### 단계 3. 실험을 시작할 때

- 작성할 문서
- `docs/track3_experiments/YYYY-MM-DD_*.md`
- 먼저 적을 내용
- 실험 ID
- 목적
- 가설
- 사용 데이터
- 사용 변수
- 사용 모델
- 성공 기준
- 필요 시
- 묶음 기록인지 단일 기록인지 먼저 명시

### 단계 4. 실험 실행 후

- 확인할 파일
- `data/track3_*.json`
- 개별 실험 기록에 추가할 내용
- Warm 결과
- Cold 결과
- slice 결과
- 해석
- 결론
- 다음 액션

### 단계 5. 실험 종료 직후

- 바로 업데이트할 문서
- [`docs/track3_experiment_results_table.md`](/Users/bo/VisionAI/docs/track3_experiment_results_table.md:1)
- [`docs/track3_experiments/INDEX.md`](/Users/bo/VisionAI/docs/track3_experiments/INDEX.md:1)
- 마지막에 실행할 명령
- `python3 scripts/track3/generate_experiment_dashboard.py`
- 필요 시 업데이트할 문서
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- 가설 상태가 바뀌면 즉시 반영

### 단계 6. 해석이 바뀌었을 때

- 수정할 문서
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 예시
- 특정 가설이 보류에서 중단으로 바뀐 경우
- 기존에 부분 검증이던 가설이 사실상 종결된 경우

### 단계 7. 전체 기준이 바뀌었을 때

- 수정할 문서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 예시
- 공식 split이 변경된 경우
- 평가 지표 우선순위가 변경된 경우
- 운영 입력 변수 원칙이 바뀐 경우

## 4. 실험 종료 후 최소 업데이트 규칙

- 실험이 끝나면 최소한 아래 3개는 반드시 업데이트함
- 1
- 개별 실험 기록 파일
- 2
- 실험 결과 요약표
- 3
- 실험 기록 인덱스
- 4
- HTML 대시보드 자동 생성
- 추가로 필요 시
- 가설 요약표
- 가설 설명 문서
- 계획서
- 순서로 업데이트함

## 5. 어떤 문서를 언제까지 업데이트할 것인가

- 개별 실험 기록
- 실험 종료 당일 바로 업데이트
- 실험 결과 요약표
- 실험 종료 직후 바로 업데이트
- 가설 요약표
- 상태가 바뀌는 즉시 업데이트
- HTML 대시보드
- 가설 요약표 또는 실험 결과 요약표 수정 후 자동 생성
- 가설 설명 문서
- 해석 변화가 생길 때 업데이트
- 계획서
- 기준 변화가 생길 때만 업데이트

## 6. 권장 체크리스트

### 실험 시작 전

- 기존 가설과 중복인지 확인했는가
- baseline과 variant가 분명한가
- 성공 기준을 먼저 적었는가
- 운영 입력 제약을 위반하지 않는가
- 데이터 새어 나감 위험이 없는가

### 실험 종료 후

- 결과 JSON이 저장되었는가
- 개별 실험 기록을 업데이트했는가
- 실험 결과 요약표를 업데이트했는가
- 인덱스를 업데이트했는가
- HTML 대시보드를 자동 생성했는가
- 사용 변수와 Warm / Cold 결과가 문서에서 바로 보이는가
- 해석과 결론이 분리되어 적혀 있는가
- 가설 상태를 바꿔야 하는가
- 계획서까지 수정할 수준의 변화인가

## 7. 현재 Track 3 권장 운영 흐름

- 1
- 가설 문서에서 질문 확인
- 2
- 요약표에서 현재 상태 확인
- 3
- 개별 실험 기록 파일 초안 생성
- 4
- 스크립트 실행
- 5
- 결과 JSON 확인
- 6
- 개별 실험 기록 완성
- 7
- 결과 요약표 / 인덱스 업데이트
- 8
- 필요 시 가설 문서와 계획서 업데이트
- 9
- `python3 scripts/track3/generate_experiment_dashboard.py` 실행

## 8. 현재 결론

- Track 3에서는 실험만 잘하는 것보다
- 어떤 문서를 언제 업데이트하는지 고정하는 것이 중요함
- 그래야
- 가설
- 실험 방법
- 실행 결과
- 최종 결론
- 이 서로 어긋나지 않음
