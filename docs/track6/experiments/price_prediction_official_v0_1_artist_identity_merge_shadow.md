# 공식 v0.1 작가 식별자 병합 shadow DB 영향 감사

- 작성일: 2026-06-12T18:44:53+09:00
- 운영 DB 수정 여부: 수정하지 않음
- Shadow DB: `experiments/track6/PP-OFFICIAL-V01_artist_identity_merge_shadow/price_prediction_v0_1_identity_merge_shadow.sqlite`
- 평가 병합 그룹: 57건
- 단일 작가 후보로 정리되는 그룹: 57건
- 작가 후보 수가 감소하는 그룹: 57건
- 기존 최대 이력 대비 증가 이력 합계: 425건

## 1. 결론

- 병합 후보를 shadow DB에만 적용해 작가 후보 중복과 같은 작가 가격 이력 변화를 확인했다.
- 실제 운영 DB와 운영 feature cache는 수정하지 않았다.
- 유사작품 통계 cache는 완전 재집계가 필요하므로, 이 shadow 감사는 작가 식별자/이력 수 영향 확인 용도다.

## 2. 상위 영향 그룹

| component_id | priority_tiers_json | canonical_artist_key | normalized_aliases_json | before_max_valid_price_count | after_canonical_valid_price_count | valid_price_count_gain | before_alias_candidate_count | after_alias_candidate_count | resolved_to_single_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artistmerge_0001 | ["P0_identity_merge_first"] | youngjin jun | ["전영진"] | 131 | 172 | 41 | 2 | 1 | True |
| artistmerge_0003 | ["P0_identity_merge_first"] | lee hyo youn | ["이효윤"] | 121 | 158 | 37 | 2 | 1 | True |
| artistmerge_0004 | ["P0_identity_merge_first"] | kim ji hoon | ["김지훈"] | 51 | 76 | 25 | 2 | 1 | True |
| artistmerge_0014 | ["P0_identity_merge_first"] | su min son | ["suminson"] | 29 | 52 | 23 | 2 | 1 | True |
| artistmerge_0011 | ["P0_identity_merge_first"] | kim jae hyeon | ["김재현"] | 63 | 85 | 22 | 2 | 1 | True |
| artistmerge_0012 | ["P0_identity_merge_first"] | ho sangun | ["호상운"] | 24 | 44 | 20 | 2 | 1 | True |
| artistmerge_0015 | ["P0_identity_merge_first"] | choi eun hyea | ["최은혜"] | 45 | 65 | 20 | 2 | 1 | True |
| artistmerge_0013 | ["P0_identity_merge_first"] | yoo suzy | ["유수즈이", "유수지"] | 38 | 57 | 19 | 2 | 1 | True |
| artistmerge_0016 | ["P0_identity_merge_first"] | byun sanghwan | ["변상환"] | 38 | 55 | 17 | 2 | 1 | True |
| artistmerge_0022 | ["P0_identity_merge_first"] | sun hwa cho | ["조선화"] | 20 | 34 | 14 | 2 | 1 | True |
| artistmerge_0002 | ["P0_identity_merge_first"] | kim byungkwan | ["김병관"] | 139 | 152 | 13 | 2 | 1 | True |
| artistmerge_0006 | ["P0_identity_merge_first"] | sojung kim | ["김소정"] | 82 | 94 | 12 | 2 | 1 | True |
| artistmerge_0030 | ["P0_identity_merge_first", "P1_identity_merge_review"] | seo yeongyeong | ["yeongyeongseo", "서영영"] | 93 | 105 | 12 | 2 | 1 | True |
| artistmerge_0024 | ["P0_identity_merge_first"] | in kyung kwon | ["inkyungkwon", "권인경"] | 15 | 26 | 11 | 2 | 1 | True |
| artistmerge_0017 | ["P0_identity_merge_first"] | doha ham | ["dohaham", "함도하"] | 52 | 62 | 10 | 2 | 1 | True |
| artistmerge_0007 | ["P0_identity_merge_first"] | park kyunghwa | ["박경화"] | 11 | 20 | 9 | 3 | 1 | True |
| artistmerge_0019 | ["P0_identity_merge_first"] | kim jeongyeon | ["jeongyeonkim", "김정연"] | 7 | 16 | 9 | 3 | 1 | True |
| artistmerge_0021 | ["P0_identity_merge_first"] | minhui jeong | ["정민희"] | 12 | 21 | 9 | 2 | 1 | True |
| artistmerge_0040 | ["P1_identity_merge_review"] | younju jung | ["정윤주"] | 10 | 18 | 8 | 2 | 1 | True |
| artistmerge_0041 | ["P1_identity_merge_review"] | chae sung pil | ["채성필"] | 29 | 37 | 8 | 2 | 1 | True |
| artistmerge_0027 | ["P0_identity_merge_first"] | lee eu | ["leeeu", "이으"] | 15 | 22 | 7 | 2 | 1 | True |
| artistmerge_0009 | ["P0_identity_merge_first"] | taerin kim | ["김태린"] | 16 | 21 | 5 | 2 | 1 | True |
| artistmerge_0026 | ["P0_identity_merge_first"] | kang zi | ["kangzi", "강지"] | 13 | 18 | 5 | 2 | 1 | True |
| artistmerge_0043 | ["P1_identity_merge_review"] | donah lee | ["이돈아"] | 7 | 12 | 5 | 2 | 1 | True |
| artistmerge_0018 | ["P0_identity_merge_first"] | seonmi kang | ["강선미"] | 128 | 132 | 4 | 2 | 1 | True |
| artistmerge_0033 | ["P0_identity_merge_first"] | yeonsoo kim 김연수 | ["김연수"] | 13 | 17 | 4 | 2 | 1 | True |
| artistmerge_0044 | ["P1_identity_merge_review"] | ham sup 함섭 | ["함섭"] | 15 | 19 | 4 | 2 | 1 | True |
| artistmerge_0005 | ["P0_identity_merge_first"] | sunwoo kim | ["김선우"] | 102 | 105 | 3 | 2 | 1 | True |
| artistmerge_0035 | ["P0_identity_merge_first"] | lee sang yong | ["이상용"] | 30 | 33 | 3 | 2 | 1 | True |
| artistmerge_0036 | ["P0_identity_merge_first"] | seo hyun kim | ["seohyunkim"] | 3 | 6 | 3 | 2 | 1 | True |


## 3. 산출물

- Impact CSV: `experiments/track6/PP-OFFICIAL-V01_artist_identity_merge_shadow/artist_identity_merge_shadow_impact.csv`
- JSON: `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_merge_shadow.json`
