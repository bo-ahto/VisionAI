# 공식 v0.1 작가 식별자 이관 품질 감사

- 작성일: 2026-06-12T17:50:51+09:00
- 충돌 alias 그룹: 92건
- 높은 확률의 잘못 분리 후보: 68건
- 추가 확인 필요한 분리 후보: 3건
- 분리 유지 또는 확인 전 보류 후보: 5건

## 1. 결론

- DB 이관 시 원본 `artist_key`를 그대로 사용하면서 같은 작가가 영문 표기 순서/띄어쓰기 차이로 분리된 후보가 확인됐다.
- 자동 병합은 하지 않았다. `artist_identity_review_queue`에 후보와 근거를 저장했다.
- 병합 후보는 서비스 라우팅, Warm 이력 수, 외부 피처 승격 판단에 영향을 주므로 검수 후 canonical artist_key로 정리해야 한다.

## 2. 추천 상태별 수량

| 추천 상태 | 건수 |
|---|---:|
| `likely_false_split_merge_candidate` | 68 |
| `identity_review_required` | 16 |
| `keep_separate_until_verified` | 5 |
| `possible_false_split_review` | 3 |

## 3. 높은 확률의 잘못 분리 후보 상위

| normalized_alias | candidate_count | canonical_artist_key | candidate_artist_keys_json | combined_valid_price_count | split_loss_price_count | identity_score | distinct_birth_years_json | median_price_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 전영진 | 2 | youngjin jun | ["youngjin jun", "youngjin jun 전영진"] | 172 | 41 | 1.0 | [1983] | 1.4041666666666666 |
| 이효윤 | 2 | lee hyo youn | ["hyoyoun lee", "lee hyo youn"] | 158 | 37 | 1.0 | [1973] | 2.0454545454545454 |
| 김지훈 | 2 | kim ji hoon | ["jihoon kim 김지훈", "kim ji hoon"] | 76 | 25 | 1.0 | [1985] | 1.125 |
| suminson | 2 | su min son | ["su min son", "sumin son"] | 52 | 23 | 1.0 | [1974] | 1.954 |
| 김재현 | 2 | kim jae hyeon | ["jae hyeon kim", "kim jae hyeon"] | 85 | 22 | 1.0 | [] | 1.2283737024221453 |
| 최은혜 | 2 | choi eun hyea | ["choi eun hyea", "eunhyea choi"] | 65 | 20 | 1.0 | [1983] | 1.5 |
| 호상운 | 2 | ho sangun | ["ho sangun", "sangun ho"] | 44 | 20 | 1.0 | [1984] | 1.737607973421927 |
| 유수즈이 | 2 | yoo suzy | ["suzy yoo", "yoo suzy"] | 57 | 19 | 1.0 | [1995] | 1.3924050632911393 |
| 유수지 | 2 | yoo suzy | ["suzy yoo", "yoo suzy"] | 57 | 19 | 1.0 | [1995] | 1.3924050632911393 |
| 변상환 | 2 | byun sanghwan | ["byun sanghwan", "sanghwan byun"] | 55 | 17 | 1.0 | [1986] | 1.891097308488613 |
| 조선화 | 2 | sun hwa cho | ["seon wha jo", "sun hwa cho"] | 34 | 14 | 1.0 | [] | 2.6755852842809364 |
| 김병관 | 2 | kim byungkwan | ["byung kwan kim", "kim byungkwan"] | 152 | 13 | 1.0 | [1976] | 1.8518518518518519 |
| 김소정 | 2 | sojung kim | ["so jeong kim", "sojung kim"] | 94 | 12 | 1.0 | [] | 1.255813953488372 |
| inkyungkwon | 2 | in kyung kwon | ["in kyung kwon", "inkyung kwon"] | 26 | 11 | 1.0 | [1979] | 1.7585730435874891 |
| 권인경 | 2 | in kyung kwon | ["in kyung kwon", "inkyung kwon"] | 26 | 11 | 1.0 | [1979] | 1.7585730435874891 |
| dohaham | 2 | doha ham | ["do ha ham", "doha ham"] | 62 | 10 | 1.0 | [1978] | 1.2121212121212122 |
| 함도하 | 2 | doha ham | ["do ha ham", "doha ham"] | 62 | 10 | 1.0 | [1978] | 1.2121212121212122 |
| 박경화 | 3 | park kyunghwa | ["kyunghwa park", "park kyunghwa", "박경화 kyung hwa park"] | 20 | 9 | 1.0 | [1979] | 1.0833333333333333 |
| 정민희 | 2 | minhui jeong | ["minhee jung", "minhui jeong"] | 21 | 9 | 1.0 | [] | 1.1722713864306784 |
| 정윤주 | 2 | younju jung | ["yoonzoo jung", "younju jung"] | 18 | 8 | 1.0 | [1990] | 2.0089285714285716 |
| 채성필 | 2 | chae sung pil | ["chae sung pil", "sungpil chae"] | 37 | 8 | 1.0 | [1972] | 1.0 |
| leeeu | 2 | lee eu | ["lee eu", "leeeu"] | 22 | 7 | 1.0 | [1976] | 2.5970244647232184 |
| 이으 | 2 | lee eu | ["lee eu", "leeeu"] | 22 | 7 | 1.0 | [1976] | 2.5970244647232184 |
| kangzi | 2 | kang zi | ["kang zi", "kangzi"] | 18 | 5 | 1.0 | [1987] | 1.749090909090909 |
| 강지 | 2 | kang zi | ["kang zi", "kangzi"] | 18 | 5 | 1.0 | [1987] | 1.749090909090909 |


## 4. 추가 확인 필요 후보 상위

| normalized_alias | candidate_count | canonical_artist_key | candidate_artist_keys_json | combined_valid_price_count | split_loss_price_count | identity_score | distinct_birth_years_json | median_price_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 남히조 | 2 | hijo nam | ["hijo nam", "nam hijo"] | 4 | 2 | 0.75 | [] | 1.0208732111931456 |
| 조알렉스 | 2 | alex cho | ["alex cho", "alex jo"] | 8 | 2 | 0.7300000000000001 | [] | 22.90104347826087 |
| 게오르그바젤리츠 | 2 | georg baselitz | ["georg baselitz", "게오르그 바젤리츠"] | 2 | 1 | 0.73 | [1938] | 469.1609195402299 |


## 5. 분리 유지 또는 확인 전 보류 후보 상위

| normalized_alias | candidate_count | canonical_artist_key | candidate_artist_keys_json | combined_valid_price_count | split_loss_price_count | identity_score | distinct_birth_years_json | median_price_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 김한나 | 3 | hanna kim | ["hanna kim", "hannah kim", "hannah kim 해나킴"] | 49 | 22 | 0.43000000000000005 | [1981, 1996] | 1.3851590106007068 |
| 백정원 | 2 | bac jungwon | ["bac jungwon", "jungwon bac"] | 42 | 6 | 0.07000000000000005 | [1981, 1991] | 3.544954128440367 |
| 김서연 | 2 | kelly kim 김서연 | ["kelly kim 김서연", "seoyeon kim"] | 5 | 2 | 0.07000000000000005 | [2000, 2003] | 3.3854166666666665 |
| 구자현 | 2 | koo ja hyun | ["jahyun koo", "koo ja hyun"] | 45 | 9 | 4.163336342344337e-17 | [1955, 1999] | 13.8 |
| 이은정 | 2 | eun jeong lee | ["eun jeong lee", "eunjung lee"] | 32 | 12 | 0.0 | [1990, 1995] | 58.373590982286636 |


## 6. 산출물

- CSV: `experiments/track6/PP-OFFICIAL-V01_artist_identity_migration_audit/artist_identity_review_queue.csv`
- DB table: `data/track6/service_v0_1/price_prediction_v0_1.sqlite` table `artist_identity_review_queue`
- JSON: `docs/track6/experiments/price_prediction_official_v0_1_artist_identity_migration_audit.json`
