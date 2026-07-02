# 공식 v0.1 작가 병합 후 예측 영향 감사

- 작성일: 2026-06-12T20:08:22+09:00
- 운영 DB 수정 여부: 수정하지 않음
- 평가 component: 57건
- 병합 후 alias 단일 resolve: 57건
- alias review_required: 57 -> 0
- direct 가격 변동 row: 2건
- direct route 변경 row: 2건
- direct cold -> warm row: 2건
- direct 고영향 row(절대 변화율 50% 이상): 1건
- direct 가격 평균 절대 변화율: 4.4083%
- direct 가격 p95 절대 변화율: 0.0000%

## 1. 결론

- 병합 전/후 DB를 감사용 복사본으로 만들어 같은 입력의 resolve와 가격 예측 변화를 비교했다.
- 운영 DB에는 예측 이벤트를 남기지 않았다.
- 병합 후 작가명 기반 후보 중복이 제거되어, 병합 후보 component는 단일 작가 후보로 resolve된다.
- 가격 변동은 병합으로 같은 작가 이력과 유사작품 통계가 합쳐지기 때문에 발생한다.
- 가격 변화가 큰 component는 자동 적용하지 않고 별도 보류 검수 대상으로 둔다.

## 2. 가격 변동 상위

| component_id | canonical_artist_key | aliases_for_review_json | direct_before_price_krw | direct_after_price_krw | direct_price_delta_pct | direct_before_route | direct_after_route | direct_before_similar_sample_count | direct_after_similar_sample_count | direct_before_confidence_score | direct_after_confidence_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artistmerge_0052 | jae sam lee | ["이재샘"] | 32251971 | 112012092 | 2.473030904064747 | cold | warm | 5 | 5 | 0.62 | 0.7375 |
| artistmerge_0036 | seo hyun kim | ["seohyunkim"] | 5354958 | 5142226 | -0.03972617525665 | cold | warm | 117 | 2 | 0.62 | 0.685 |
| artistmerge_0047 | aeri lee 이애리 | ["이애리"] | 38406440 | 38406440 | 0.0 | warm | warm | 3 | 4 | 0.7025 | 0.72 |
| artistmerge_0008 | kyuri kim | ["김규리"] | 9925432 | 9925432 | 0.0 | warm | warm | 8 | 8 | 0.79 | 0.79 |
| artistmerge_0010 | shiny park | ["박신이"] | 6060460 | 6060460 | 0.0 | warm | warm | 1 | 1 | 0.6675 | 0.6675 |
| artistmerge_0020 | rahee kang | ["강라희"] | 28742441 | 28742441 | 0.0 | warm | warm | 10 | 10 | 0.825 | 0.825 |
| artistmerge_0025 | zikseong jeong | ["정직성"] | 46927387 | 46927387 | 0.0 | warm | warm | 4 | 4 | 0.72 | 0.72 |
| artistmerge_0028 | eunjoo choi | ["최은주"] | 6917897 | 6917897 | 0.0 | warm | warm | 2 | 2 | 0.685 | 0.685 |
| artistmerge_0031 | byung taek jeon | ["전병택"] | 23706253 | 23706253 | 0.0 | warm | warm | 10 | 11 | 0.825 | 0.8425 |
| artistmerge_0032 | sieun kim | ["김시은"] | 1741832 | 1741832 | 0.0 | warm | warm | 2 | 2 | 0.685 | 0.685 |
| artistmerge_0037 | lee sujin b 1983 | ["이수진"] | 8815571 | 8815571 | 0.0 | warm | warm | 2 | 3 | 0.685 | 0.7025 |
| artistmerge_0045 | kim young jin | ["김영진"] | 8452233 | 8452233 | 0.0 | cold | cold | 1747 | 1747 | 0.62 | 0.62 |
| artistmerge_0046 | seonyoung park | ["박선영"] | 5037324 | 5037324 | 0.0 | warm | warm | 3 | 4 | 0.7025 | 0.72 |
| artistmerge_0048 | byungjin kim | ["byungjinkim", "김병진"] | 33788719 | 33788719 | 0.0 | warm | warm | 20 | 20 | 1.0 | 1.0 |
| artistmerge_0001 | youngjin jun | ["전영진"] | 25654280 | 25654280 | 0.0 | warm | warm | 44 | 53 | 1.0 | 1.0 |
| artistmerge_0023 | chang youngeun | ["장영은"] | 36253605 | 36253605 | 0.0 | warm | warm | 1 | 1 | 0.6675 | 0.6675 |
| artistmerge_0029 | youngmi choi | ["최영미"] | 14012880 | 14012880 | 0.0 | warm | warm | 2 | 2 | 0.685 | 0.685 |
| artistmerge_0034 | eun young kim | ["eunyoungkim", "김은영"] | 7243519 | 7243519 | 0.0 | cold | cold | 2187 | 2187 | 0.62 | 0.62 |
| artistmerge_0038 | doyeon kim | ["김도연"] | 15533421 | 15533421 | 0.0 | warm | warm | 1 | 1 | 0.6675 | 0.6675 |
| artistmerge_0039 | yerim lee | ["이예림"] | 9121545 | 9121545 | 0.0 | cold | cold | 1747 | 1747 | 0.62 | 0.62 |
| artistmerge_0049 | hye kyung lee 이혜경 | ["이혜경"] | 13436425 | 13436425 | 0.0 | warm | warm | 4 | 1 | 0.72 | 0.6675 |
| artistmerge_0050 | sunyoung moon | ["sunyoungmoon", "문선영"] | 21514980 | 21514980 | 0.0 | cold | cold | 438 | 438 | 0.62 | 0.62 |
| artistmerge_0051 | jeonghee son | ["손정희"] | 18604919 | 18604919 | 0.0 | warm | warm | 10 | 10 | 0.825 | 0.825 |
| artistmerge_0053 | jihyun im | ["임지현"] | 6464262 | 6464262 | 0.0 | cold | cold | 1253 | 1253 | 0.62 | 0.62 |
| artistmerge_0054 | 정수정 | ["정수정"] | 42729184 | 42729184 | 0.0 | warm | warm | 1 | 1 | 0.6675 | 0.6675 |
| artistmerge_0055 | lee kang so | ["이강소"] | 6900007 | 6900007 | 0.0 | cold | cold | 1747 | 1747 | 0.62 | 0.62 |
| artistmerge_0056 | kee tae kim | ["keetaekim", "김케에태"] | 30737252 | 30737252 | 0.0 | warm | warm | 14 | 14 | 0.895 | 0.895 |
| artistmerge_0042 | hye jin stella kim | ["김혜진"] | 18082907 | 18082907 | 0.0 | warm | warm | 14 | 14 | 0.895 | 0.895 |
| artistmerge_0035 | lee sang yong | ["이상용"] | 41275689 | 41275689 | 0.0 | warm | warm | 7 | 7 | 0.7725 | 0.7725 |
| artistmerge_0003 | lee hyo youn | ["이효윤"] | 28834539 | 28834539 | 0.0 | warm | warm | 7 | 15 | 0.7725 | 0.9125 |


## 3. 산출물

- Impact CSV: `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_prediction_impact/artist_identity_post_merge_prediction_impact.csv`
- Before audit DB: `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_prediction_impact/before_prediction_impact_audit.sqlite`
- After audit DB: `experiments/track6/PP-OFFICIAL-V01_artist_identity_post_merge_prediction_impact/after_prediction_impact_audit.sqlite`
- JSON: `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_post_merge_prediction_impact.json`
