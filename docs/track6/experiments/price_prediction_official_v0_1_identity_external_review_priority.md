# 공식 v0.1 작가 식별자/외부 피처 검수 우선순위

- 작성일: 2026-06-12T18:01:46+09:00
- 우선순위 row: 82건
- 우선순위 단위: 같은 작가키 묶음을 공유하는 alias row를 합친 고유 작가키 묶음
- 최우선 병합 검수: 40건

## 1. 결론

- 외부 피처 승격보다 작가 식별자 병합 검수를 먼저 진행한다.
- 동일 작가가 분리된 후보는 Warm 이력 수, 작가 후보 표시, 외부 피처 매핑에 동시에 영향을 준다.
- 자동 병합은 하지 않으며, P0/P1 후보를 검수한 뒤 canonical artist_key 적용 dry-run을 실행한다.

## 2. 우선순위 기준

| 등급 | 의미 | 처리 |
|---|---|---|
| P0_identity_merge_first | 잘못 분리 가능성이 높고 분리 손실 또는 예측 영향이 큼 | 동일 작가 병합 여부 먼저 검수 |
| P1_identity_merge_review | 잘못 분리 가능성이 높지만 영향이 상대적으로 작음 | 병합 검수 후 dry-run |
| P2_human_review_before_promotion | 실제 동명이인/출처 충돌 가능성 또는 외부 피처 영향 존재 | 사람 검수 후 승격 판단 |
| P3_keep_or_low_impact_review | 분리 유지 가능성이 높거나 영향 낮음 | 후순위 처리 |

## 3. 상위 검수 후보

| priority_tier | normalized_alias | normalized_aliases_json | canonical_artist_key | candidate_artist_keys_json | combined_valid_price_count | split_loss_price_count | external_blocked_rows | max_abs_price_delta_pct | distinct_birth_years_json | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0_identity_merge_first | 전영진 | ["전영진"] | youngjin jun | ["youngjin jun", "youngjin jun 전영진"] | 172 | 41 | 3 | 0.5934878555913689 | [1983] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 김병관 | ["김병관"] | kim byungkwan | ["byung kwan kim", "kim byungkwan"] | 152 | 13 | 3 | 0.6227283584399849 | [1976] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 이효윤 | ["이효윤"] | lee hyo youn | ["hyoyoun lee", "lee hyo youn"] | 158 | 37 | 3 | 0.0867598328496542 | [1973] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 김지훈 | ["김지훈"] | kim ji hoon | ["jihoon kim 김지훈", "kim ji hoon"] | 76 | 25 | 3 | 0.1766546077282754 | [1985] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 김선우 | ["김선우"] | sunwoo kim | ["kim sunwoo", "sunwoo kim"] | 105 | 3 | 3 | 0.5626814686621602 | [1988] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 김소정 | ["김소정"] | sojung kim | ["so jeong kim", "sojung kim"] | 94 | 12 | 3 | 0.3431389878507685 | [] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 박경화 | ["박경화"] | park kyunghwa | ["kyunghwa park", "park kyunghwa", "박경화 kyung hwa park"] | 20 | 9 | 3 | 0.361994310576912 | [1979] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 김규리 | ["김규리"] | kyuri kim | ["kim kyuri", "kyuri kim"] | 23 | 2 | 2 | 0.5273421183663668 | [1996] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 김태린 | ["김태린"] | taerin kim | ["kim tae rin", "taerin kim"] | 21 | 5 | 2 | 0.4286757422154961 | [1990] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 박신이 | ["박신이"] | shiny park | ["park shiny", "shiny park"] | 13 | 2 | 2 | 0.4633692411223224 | [1985] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 김재현 | ["김재현"] | kim jae hyeon | ["jae hyeon kim", "kim jae hyeon"] | 85 | 22 | 3 | 0.022911141198175 | [] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 호상운 | ["호상운"] | ho sangun | ["ho sangun", "sangun ho"] | 44 | 20 | 3 | 0.0534738882362937 | [1984] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 유수즈이 | ["유수즈이", "유수지"] | yoo suzy | ["suzy yoo", "yoo suzy"] | 57 | 19 | 3 | 0.0614109126659538 | [1995] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | suminson | ["suminson"] | su min son | ["su min son", "sumin son"] | 52 | 23 | 1 | 0.0011802330143555 | [1974] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 최은혜 | ["최은혜"] | choi eun hyea | ["choi eun hyea", "eunhyea choi"] | 65 | 20 | 3 | 0.0148309292596721 | [1983] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 변상환 | ["변상환"] | byun sanghwan | ["byun sanghwan", "sanghwan byun"] | 55 | 17 | 3 | 0.0534737177657598 | [1986] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | dohaham | ["dohaham", "함도하"] | doha ham | ["do ha ham", "doha ham"] | 62 | 10 | 3 | 0.1766544981503951 | [1978] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 강선미 | ["강선미"] | seonmi kang | ["seonmi kang", "sun mee kang"] | 132 | 4 | 3 | 0.2825469521541505 | [1971] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 김정연 | ["김정연"] | kim jeongyeon | ["jeong yeon kim", "jeongyeon kim", "kim jeongyeon"] | 16 | 9 | 3 | 0.140515806921702 | [2001] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 강라희 | ["강라희"] | rahee kang | ["kang rahee", "rahee kang"] | 59 | 2 | 3 | 0.3088361270897678 | [] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 정민희 | ["정민희"] | minhui jeong | ["minhee jung", "minhui jeong"] | 21 | 9 | 2 | 0.1691096715169433 | [] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 조선화 | ["조선화"] | sun hwa cho | ["seon wha jo", "sun hwa cho"] | 34 | 14 | 2 | 0.0557723805616167 | [] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 장영은 | ["장영은"] | chang youngeun | ["chang youngeun", "youngeun jang"] | 8 | 1 | 2 | 0.2397698836137434 | [1992] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | inkyungkwon | ["inkyungkwon", "권인경"] | in kyung kwon | ["in kyung kwon", "inkyung kwon"] | 26 | 11 | 2 | 0.0197765629901714 | [1979] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | jeongyeonkim | ["jeongyeonkim"] | jeong yeon kim | ["jeong yeon kim", "jeongyeon kim"] | 9 | 4 | 2 | 0.140515806921702 | [2001] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 정직성 | ["정직성"] | zikseong jeong | ["jeong zik seong", "zikseong jeong"] | 68 | 2 | 3 | 0.176654563441802 | [1976] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | kangzi | ["kangzi", "강지"] | kang zi | ["kang zi", "kangzi"] | 18 | 5 | 2 | 0.1180015494291371 | [1987] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | leeeu | ["leeeu", "이으"] | lee eu | ["lee eu", "leeeu"] | 22 | 7 | 2 | 0.0557723099598669 | [1976] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 최은주 | ["최은주"] | eunjoo choi | ["choi eunjoo", "eunjoo choi"] | 22 | 2 | 2 | 0.1448369757592459 | [1985] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |
| P0_identity_merge_first | 최영미 | ["최영미"] | youngmi choi | ["choi youngmi", "youngmi choi"] | 6 | 1 | 2 | 0.1574041742089771 | [] | 동일 작가 병합 여부를 먼저 검수한 뒤 외부 피처 승격을 다시 산정 |


## 4. 산출물

- CSV: `experiments/track6/PP-OFFICIAL-V01_identity_external_review_priority/identity_external_review_priority.csv`
- JSON: `docs/track6/experiments/price_prediction_official_v0_1_identity_external_review_priority.json`
