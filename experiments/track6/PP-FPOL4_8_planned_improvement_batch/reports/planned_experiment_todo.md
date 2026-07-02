# PP-FPOL4~8 계획 실행 투두

- 작성일: 2026-06-08 15:43
- 목적: 개선 가능성이 있는 실험군을 순서대로 배치 실행하고 같은 기준으로 비교
- 기준 test: Warm fixed test 607건
- 기준 예측: `blend_svcnum_ppv8_wsvc_0.70`

| 순서 | 실험 | 상태 | 내용 |
| ---: | --- | --- | --- |
| 1 | PP-FPOL4 | pending | 작가 생년/세대 보정과 SVC/작품 보정을 2단계로 합산 |
| 2 | PP-FPOL5 | pending | FPOL4 후보에 총 보정량 cap/budget 적용 |
| 3 | PP-FPOL6 | pending | 방향별 strength와 예측가격 구간 guard 적용 |
| 4 | PP-FPOL7 | pending | SVC 신뢰도와 작품 크기 구간 gate 적용 |
| 5 | PP-FPOL8 | pending | 상위 후보 bootstrap 및 artist-fold 안정성 검증 |

## 채택/중단 기준

- 우선 채택: test MdAPE/MAPE/p95 3지표 모두 개선
- 보조 채택: MAPE 또는 p95 개선폭이 크고 MdAPE 악화가 0.001 이하
- 중단: MAPE와 p95가 동시에 악화되는 후보군