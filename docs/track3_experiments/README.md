# Track 3 실험 기록 폴더

- 목적: Track 3 실험 기록을 한곳에서 관리하기 위한 폴더
- 기본 원칙: 가능하면 `실험 1건 = 기록 1개`
- 예외:
- 같은 가설 아래에서 같은 날 연속으로 수행한 실험은 `묶음 기록` 허용
- 대규모 재현 세션은 `재현 기록`으로 묶어서 관리 가능
- 기록 방식: `docs/track3_experiment_plan_v1.md`의 실험 기록 원칙을 따름

## 폴더 구성

- `INDEX.md`
- 전체 실험 목록
- `TEMPLATE.md`
- 새 실험 기록 기본 양식
- `YYYY-MM-DD_*.md`
- 실제 개별 실험 기록 파일

## 기록 작성 원칙

- 실험 시작 전에 아래를 먼저 적음
- 실험 ID
- 목적
- 가설
- 사용 데이터
- 사용 변수
- 사용 모델
- 성공 기준
- 실험 종료 후 아래를 추가함
- Warm 결과
- Cold 결과
- 핵심 해석
- 결론
- 다음 액션
- 특히 아래 4가지는 모든 기록에서 반드시 잘 보이게 남김
- 사용 변수
- Warm / Cold 결과
- 해석
- 결론

## 파일명 규칙

- 권장 형식
- `YYYY-MM-DD_prXX_실험이름.md`
- 묶음 기록 예시
- `YYYY-MM-DD_pr17_pr19_주제이름.md`
- `YYYY-MM-DD_pr20_pr29_confirmatory_suite.md`
- 예시
- `2026-05-13_pr17_branch_model.md`
- `2026-05-13_pr18_depth_matrix.md`
- `2026-05-13_pr19_cold_depth_significance.md`

## 관련 기준 문서

- 실험 계획서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 재현 요약 문서
- [`docs/track3_reproduction_summary_20260513.md`](/Users/bo/VisionAI/docs/track3_reproduction_summary_20260513.md:1)
