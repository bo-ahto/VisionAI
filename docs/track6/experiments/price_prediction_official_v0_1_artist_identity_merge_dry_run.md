# 공식 v0.1 작가 식별자 병합 dry-run

- 작성일: 2026-06-12T18:05:33+09:00
- 적용 여부: 실제 DB 미수정
- 병합 component: 57건
- 병합 대상 source artist_key: 60건
- 재배치될 가격 이력 수: 425건
- 재배치될 관측 row 수: 425건
- 예상 artist_registry row 수: 1,773 -> 1,713

## 1. 결론

- P0/P1 동일 작가 분리 후보를 바로 병합하지 않고 dry-run map으로 분리했다.
- 겹치는 후보 그룹은 연결 component로 합쳐 한 artist_key가 여러 번 이동하지 않게 했다.
- 실제 적용 전에는 component별 대표 작품, 생년, 국적, 외부 출처를 확인해야 한다.

## 2. 상위 병합 component

| component_id | canonical_artist_key | component_artist_keys_json | aliases_for_review_json | distinct_birth_years_json | combined_valid_price_count | reassigned_valid_price_count | reassigned_observation_rows | requires_human_confirmation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artistmerge_0001 | youngjin jun | ["youngjin jun", "youngjin jun 전영진"] | ["전영진"] | [1983] | 172 | 41 | 41 | False |
| artistmerge_0003 | lee hyo youn | ["hyoyoun lee", "lee hyo youn"] | ["이효윤"] | [1973] | 158 | 37 | 37 | False |
| artistmerge_0004 | kim ji hoon | ["jihoon kim 김지훈", "kim ji hoon"] | ["김지훈"] | [1985] | 76 | 25 | 25 | False |
| artistmerge_0014 | su min son | ["su min son", "sumin son"] | ["suminson"] | [1974] | 52 | 23 | 23 | False |
| artistmerge_0011 | kim jae hyeon | ["jae hyeon kim", "kim jae hyeon"] | ["김재현"] | [] | 85 | 22 | 22 | False |
| artistmerge_0012 | ho sangun | ["ho sangun", "sangun ho"] | ["호상운"] | [1984] | 44 | 20 | 20 | False |
| artistmerge_0015 | choi eun hyea | ["choi eun hyea", "eunhyea choi"] | ["최은혜"] | [1983] | 65 | 20 | 20 | False |
| artistmerge_0013 | yoo suzy | ["suzy yoo", "yoo suzy"] | ["유수즈이", "유수지"] | [1995] | 57 | 19 | 19 | False |
| artistmerge_0016 | byun sanghwan | ["byun sanghwan", "sanghwan byun"] | ["변상환"] | [1986] | 55 | 17 | 17 | False |
| artistmerge_0022 | sun hwa cho | ["seon wha jo", "sun hwa cho"] | ["조선화"] | [] | 34 | 14 | 14 | False |
| artistmerge_0002 | kim byungkwan | ["byung kwan kim", "kim byungkwan"] | ["김병관"] | [1976] | 152 | 13 | 13 | False |
| artistmerge_0006 | sojung kim | ["so jeong kim", "sojung kim"] | ["김소정"] | [] | 94 | 12 | 12 | False |
| artistmerge_0030 | seo yeongyeong | ["seo yeongyeong", "yeon gyeong seo", "yeongyeong seo"] | ["yeongyeongseo", "서영영"] | [] | 105 | 12 | 12 | False |
| artistmerge_0024 | in kyung kwon | ["in kyung kwon", "inkyung kwon"] | ["inkyungkwon", "권인경"] | [1979] | 26 | 11 | 11 | False |
| artistmerge_0017 | doha ham | ["do ha ham", "doha ham"] | ["dohaham", "함도하"] | [1978] | 62 | 10 | 10 | False |
| artistmerge_0007 | park kyunghwa | ["kyunghwa park", "park kyunghwa", "박경화 kyung hwa park"] | ["박경화"] | [1979] | 20 | 9 | 9 | False |
| artistmerge_0019 | kim jeongyeon | ["jeong yeon kim", "jeongyeon kim", "kim jeongyeon"] | ["jeongyeonkim", "김정연"] | [2001] | 16 | 9 | 9 | False |
| artistmerge_0021 | minhui jeong | ["minhee jung", "minhui jeong"] | ["정민희"] | [] | 21 | 9 | 9 | False |
| artistmerge_0040 | younju jung | ["yoonzoo jung", "younju jung"] | ["정윤주"] | [1990] | 18 | 8 | 8 | False |
| artistmerge_0041 | chae sung pil | ["chae sung pil", "sungpil chae"] | ["채성필"] | [1972] | 37 | 8 | 8 | False |
| artistmerge_0027 | lee eu | ["lee eu", "leeeu"] | ["leeeu", "이으"] | [1976] | 22 | 7 | 7 | False |
| artistmerge_0009 | taerin kim | ["kim tae rin", "taerin kim"] | ["김태린"] | [1990] | 21 | 5 | 5 | False |
| artistmerge_0026 | kang zi | ["kang zi", "kangzi"] | ["kangzi", "강지"] | [1987] | 18 | 5 | 5 | False |
| artistmerge_0043 | donah lee | ["donah lee", "donah lee 이돈아"] | ["이돈아"] | [1967] | 12 | 5 | 5 | False |
| artistmerge_0018 | seonmi kang | ["seonmi kang", "sun mee kang"] | ["강선미"] | [1971] | 132 | 4 | 4 | False |
| artistmerge_0033 | yeonsoo kim 김연수 | ["yeonsoo kim", "yeonsoo kim 김연수"] | ["김연수"] | [1984] | 17 | 4 | 4 | False |
| artistmerge_0044 | ham sup 함섭 | ["ham sup", "ham sup 함섭"] | ["함섭"] | [] | 19 | 4 | 4 | False |
| artistmerge_0005 | sunwoo kim | ["kim sunwoo", "sunwoo kim"] | ["김선우"] | [1988] | 105 | 3 | 3 | False |
| artistmerge_0035 | lee sang yong | ["lee sang yong", "sangyong lee"] | ["이상용"] | [1970] | 33 | 3 | 3 | False |
| artistmerge_0036 | seo hyun kim | ["seo hyun kim", "seohyun kim"] | ["seohyunkim"] | [1999] | 6 | 3 | 3 | False |


## 3. 산출물

- Component CSV: `experiments/track6/PP-OFFICIAL-V01_artist_identity_merge_dry_run/artist_identity_merge_components_dry_run.csv`
- Merge map CSV: `experiments/track6/PP-OFFICIAL-V01_artist_identity_merge_dry_run/artist_identity_merge_map_dry_run.csv`
- JSON: `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_merge_dry_run.json`
