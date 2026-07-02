# Track 6 작가 한글명 개선 보고서

- 목적: 4글자 이상 한글식 이름 중 명백한 오표기 후보를 먼저 보정
- 입력: `data/track4_primary_market_feature_candidates_v1.csv`
- 출력: `data/track6/track6_feature_candidates_name_corrected.csv`
- override 파일: `scripts/track6/artist_ko_overrides.csv`
- 적용 작가 key 수: `205`
- 적용 rows: `5,018`
- 잔여 검토 후보 작가 key 수: `445`
- 잔여 검토 후보 rows: `2,545`

## 1. 처리 원칙

- 자동 음역으로 다시 추정하지 않음
- 확실한 한국식 이름만 `artist_ko_overrides.csv`에 등록해 적용함
- 예명, 외국 작가명, 단체명, 갤러리명처럼 애매한 값은 검토 후보로 남김
- `artist_name_ko_orig`는 보정 전 이름을 유지함
- split은 보정된 `artist_name_ko` 기준으로 다시 생성해야 함

## 2. 적용 예시

| artist_key | 기존 한글명 | 보정 한글명 | rows | 사유 |
|---|---|---|---:|---|
| `kai ax` | 카이아엑스 | 카이 액스 | `375` | `readable_foreign_name_transliteration` |
| `ivie ives` | 이비에이베스 | 아이비 아이브스 | `233` | `readable_foreign_name_transliteration` |
| `ouchul hwang` | 황오우철 | 황오철 | `124` | `obvious_bad_romanization` |
| `hagley art` | 하그레이아트 | 해글리 아트 | `114` | `readable_studio_name_transliteration` |
| `gallery hexagon` | 핵사곤갤러리 | 갤러리 헥사곤 | `100` | `readable_gallery_name_transliteration` |
| `myunggyun you` | 유명규느 | 유명균 | `93` | `obvious_bad_romanization` |
| `jinho kee` | 진호케에 | 기진호 | `85` | `obvious_bad_romanization` |
| `yohahn diko` | 디코요한 | 디코 요한 | `80` | `readable_foreign_name_transliteration` |
| `sang wooc rhee` | 이상우크 | 이상욱 | `79` | `obvious_bad_romanization` |
| `hyungjun suh` | 서현그준 | 서형준 | `76` | `obvious_bad_romanization` |
| `seung yean cho` | 조승예안 | 조승연 | `76` | `obvious_bad_romanization` |
| `weedong yoon b 1982` | 윤웨에동_A | 윤위동 | `65` | `metadata_removed_and_romanization_fixed` |
| `choonjae kim` | 김초온재 | 김춘재 | `64` | `obvious_bad_romanization` |
| `jihyeon choi` | 최지혜온 | 최지현 | `60` | `obvious_bad_romanization` |
| `kim deasung` | 김데아성 | 김대성 | `55` | `obvious_bad_romanization` |
| `choongmok yoo` | 유초온그목 | 유충목 | `54` | `obvious_bad_romanization` |
| `leysan khasan` | 레이산크하산 | 레이산 카산 | `54` | `readable_foreign_name_transliteration` |
| `kwon neung` | 권네운그 | 권능 | `52` | `obvious_bad_romanization` |
| `marina ogai` | 마린아옥아이 | 마리나 오가이 | `52` | `readable_foreign_name_transliteration` |
| `kim deok han` | 김더크한 | 김덕한 | `49` | `obvious_bad_romanization` |
| `hyegyun kim` | 김혜규느 | 김혜균 | `47` | `obvious_bad_romanization` |
| `yoo suzy` | 유수즈이 | 유수지 | `47` | `obvious_bad_romanization` |
| `deokhwan yoon` | 윤더크환 | 윤덕환 | `46` | `obvious_bad_romanization` |
| `erica choi` | 최어이카 | 최에리카 | `45` | `obvious_bad_romanization` |
| `stepper studio` | 스테퍼스튜디오 | 스테퍼 스튜디오 | `45` | `readable_studio_name_transliteration` |
| `hazzi eunjeong kim` | 김하즈지은정 | 김은정 | `44` | `obvious_bad_romanization` |
| `lookha bark` | 루크하바르크 | 박루카 | `44` | `obvious_bad_romanization` |
| `wang yeul` | 왕예우르 | 왕열 | `43` | `obvious_bad_romanization` |
| `gwanhee lee` | 이그완희 | 이관희 | `42` | `obvious_bad_romanization` |
| `chanoo park` | 박찬오오 | 박찬우 | `40` | `obvious_bad_romanization` |
| `sungone jung` | 정성온에 | 정성원 | `40` | `obvious_bad_romanization` |
| `mihei her` | 미헤이헤르 | 허미혜 | `39` | `obvious_bad_romanization` |
| `minjeong guem` | 민정구에므 | 금민정 | `39` | `obvious_bad_romanization` |
| `matthew anderson` | 매튜안데르선 | 매튜 앤더슨 | `38` | `readable_foreign_name_transliteration` |
| `ryu hoimin` | 류호이민 | 류호민 | `38` | `obvious_bad_romanization` |
| `keem jiyoung` | 케에므지영 | 김지영 | `37` | `obvious_bad_romanization` |
| `kwang bum jang` | 장광부므 | 장광범 | `37` | `obvious_bad_romanization` |
| `soon yeal yang` | 양순예아르 | 양순열 | `35` | `obvious_bad_romanization` |
| `valeriia kapitulska park lia` | 바레리이아캅이툴스카박리아 | 발레리아 카피툴스카 박리아 | `34` | `readable_foreign_name_transliteration` |
| `zhanna kan` | 즈한나칸 | 잔나 칸 | `34` | `readable_foreign_name_transliteration` |

## 3. 잔여 검토 후보 상위

| rows | artist_key | 현재 한글명 | 출처 |
|---:|---|---|---|
| `256` | `lacey kim` | 김레이시 | `saatchi` |
| `219` | `karis kim` | 김카리스 | `saatchi` |
| `121` | `lydia lee` | 이리디아 | `saatchi` |
| `79` | `jennifer lee` | 이제니퍼 | `saatchi` |
| `64` | `kris kim` | 김크리스 | `saatchi` |
| `39` | `jeremy yong` | 용제레미 | `saatchi` |
| `38` | `stella sujin` | 스텔라수진 | `artsy` |
| `27` | `melody park` | 박멜로디 | `saatchi` |
| `27` | `sambypen` | 샘바이펜 | `artsy,artue` |
| `25` | `denis lee` | 이데니스 | `saatchi` |
| `25` | `woori bai` | 우리바이 | `saatchi` |
| `24` | `min jung key` | 민정케이 | `artsy` |
| `20` | `aira choi` | 최아이라 | `saatchi` |
| `16` | `daniel kim` | 김다니엘 | `saatchi` |
| `14` | `hyosy hyosy` | 효시효시 | `saatchi` |
| `14` | `rosie park` | 박로시에 | `saatchi` |
| `13` | `duenchayphoochana phooprasert` | 두엔차이프후찬아프후프라세르트 | `artue` |
| `12` | `가이 야나이` | 가이 야나이 | `gallery_primary` |
| `11` | `chonnapas yokyai` | 초느납아스욕야이 | `artue` |
| `10` | `bareu kim` | 김바레우 | `artsy` |
| `10` | `gabby chu` | 주갑브이 | `artsy` |
| `10` | `huieun oh` | 오후이은 | `saatchi` |
| `10` | `jennifer hur` | 허제니퍼 | `artsy` |
| `10` | `kaia kim` | 김카이아 | `artsy` |
| `10` | `keunhyung park` | 박케운현그 | `artsy` |
| `10` | `kipum bae` | 배킵우므 | `saatchi` |
| `10` | `la kitki` | 라기트기 | `saatchi` |
| `10` | `minjung key` | 민정케이 | `artue` |
| `10` | `seoun gang kim` | 김서운강 | `artsy` |
| `10` | `stella park` | 박스텔라 | `artsy` |
| `10` | `teresia huwon yoo` | 유테레시아후원 | `saatchi` |
| `10` | `엠버 토플리세크` | 엠버 토플리세크 | `gallery_primary` |
| `10` | `코린 폰 레부자` | 코린 폰 레부자 | `gallery_primary` |
| `9` | `alice yaelin yang` | 양앨리스얘린 | `artsy` |
| `9` | `digital d` | 디기탈드 | `saatchi` |
| `9` | `gwaxng` | 그와엑스응 | `artsy` |
| `9` | `jack kabangu` | 잭카방우 | `artue` |
| `9` | `jason ha` | 하제이슨 | `artsy` |
| `9` | `jinhui lee` | 이진후이 | `saatchi` |
| `9` | `jinyoup chris park` | 박진유프크리스 | `saatchi` |

## 4. 다음 작업

- `data/track6/track6_feature_candidates_name_corrected.csv` 기준으로 split 재생성
- 컬럼 품질 검증과 feature/label 분리 재실행
- 잔여 후보는 수동 검수 후 `scripts/track6/artist_ko_overrides.csv`에 추가
