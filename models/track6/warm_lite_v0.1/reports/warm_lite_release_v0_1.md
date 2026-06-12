# Warm-lite v0.1 release
- 동결일: 2026-06-12T12:00:00 / 채택: 2026-06-12 사용자 결정
- 동결 모델 + k건 절단 추론 통계 검증 (vs WCUT2 per-k 재학습 참조):
{
 "1": {
  "MdAPE": 0.1994,
  "MAPE": 0.3818,
  "p95_APE": 1.6027,
  "wcut2_ref_MdAPE": 0.2179
 },
 "2": {
  "MdAPE": 0.1742,
  "MAPE": 0.3205,
  "p95_APE": 0.9243,
  "wcut2_ref_MdAPE": 0.1739
 },
 "3": {
  "MdAPE": 0.1763,
  "MAPE": 0.3374,
  "p95_APE": 1.0343,
  "wcut2_ref_MdAPE": 0.1597
 },
 "4": {
  "MdAPE": 0.1522,
  "MAPE": 0.3677,
  "p95_APE": 0.9716,
  "wcut2_ref_MdAPE": 0.1457
 }
}
- k=1 차등 등급(warm_lite_low) 동결, 라우팅 전제(매칭 >=0.90) 명시