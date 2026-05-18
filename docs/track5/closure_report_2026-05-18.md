# Track 5 종료 보고서

- 작성일: 2026-05-18
- 상태: 종료
- 다음 단계: Track 6에서 최종 보고용 split을 새로 구성

## 1. 종료 이유

- Track5는 Track4보다 split 구조를 개선했음
- 하지만 최종 보고 기준으로는 아래 리스크가 남음
- Cold가 `artist_key` 기준으로는 분리됐지만 한글 작가명 기준 중복이 일부 있음
- Warm은 작가 식별 정보 의존이 커서 작가명 매칭 실패 시 성능 저하 가능성이 큼
- Cold 가격 보정 정책은 validation 기준 재검증에서 채택 실패
- 일부 결과는 보조 검증으로 보완했지만, 설명 구조가 복잡해짐

## 2. Track5에서 확인한 내용

- Warm / Cold를 분리해서 평가해야 함
- Warm 모델은 작가 식별 정보가 성능 개선의 핵심임
- Cold 모델은 작가 정보 없이 구조 피처만으로 예측하되, 큰 오차 위험이 큼
- Cold는 단일 가격만 제시하기보다 신뢰도 경고 또는 가격 범위가 필요함
- test 결과로 정책을 고르면 과적합 위험이 있으므로 validation에서 정책을 고정해야 함

## 3. Track6에 넘길 기준

- Track6는 Track5 결과를 참고하되, split부터 다시 고정함
- Cold는 `artist_key`뿐 아니라 `artist_name_ko` 기준으로도 train과 겹치지 않게 구성
- Warm은 train에 남은 작품 수 기준을 더 명확히 설정
- validation은 후보 선택용, test는 최종 확인용으로만 사용
- Track5 실험 결과는 참고 기록으로 보존하고, 최종 수치는 Track6 기준으로 다시 산출

## 4. 관련 문서

- Track5 감사 리스크 점검: `docs/track5/audit_experiment_risk_review_2026-05-18.md`
- Track5 대시보드: `docs/track5/dashboard/experiment_dashboard.html`
- Track5 실험 결과표: `docs/track5/tables/experiment_results_table.md`
