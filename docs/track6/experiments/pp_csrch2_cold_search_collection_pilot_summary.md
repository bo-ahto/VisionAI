# PP-CSRCH2 검색 수집 확대 파일럿 요약 — 전량 수집 보류 권고

- 실행일: 2026-06-10 / 폴더: `experiments/track6/PP-CSRCH2_cold_search_collection_expansion/` / 스크립트: `run_pp_h11_*(수집)`, `run_pp_csrch2_collection_delta_validation.py`(검증)
- 1단계: warm 작가 150명 라이브 수집 완료(naver_html, H11 운영 수집기). 145명 train 매칭.
- 2단계: 동결 H23 보정맵(high +0.2/low -0.2/none -0.0313)으로 작가별 delta 파생. **상수 -0.0313의 정체 = none 세그먼트 보정값** 확인.
- 3단계(채택 게이트): 수집 작가 145명 마스킹 pseudo-cold 12,925행 3자 비교 —

| 후보 | MdAPE / MAPE / p95 |
|---|---|
| guard-only | 0.3627 / 0.5389 / 1.3983 |
| **guard + 상수(-0.0313, 현행 v0.4)** | **0.3612 / 0.5269 / 1.3244 (3지표 최선)** |
| guard + 수집 real delta | 0.3738 / 0.5491 / 1.3821 |

## 판정: 전량 수집 보류

- **수집한 per-artist delta(±0.2)가 상수보다 전 지표 악화** — cold validation 잔차로 적합된 gm비율→delta 관계가 신규(warm) 작가에 전이되지 않음. PP-CSRCH1의 기대(미커버 MAPE 0.938→0.849)는 이 파일럿에서 재현 실패.
- **현행 v0.4 상수 fallback이 신규 작가 최적임을 데이터로 재확인** — 수집 ROI 없음(현 보정 공식 기준).
- 한계 명시: 임계값 배치 근사, 수집 대상이 고빈도 warm 작가(진짜 신규 작가와 분포 차이), 단일 seed base. 재시도 조건 = cold 운영 트래픽에서 실제 신규 작가 잔차로 보정맵을 재적합할 수 있을 때.

## Cold 트랙 완전 종결

마지막 의사결정(수집 확대)까지 데이터로 닫힘. 최종: **v0.3+v0.4(상수 fallback 활성) 기본 서빙 + v0.5(raw-input p95 방어)**, 실험 17건 전수 기록.
