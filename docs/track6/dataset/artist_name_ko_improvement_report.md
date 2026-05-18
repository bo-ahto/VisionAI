# Track 6 작가 한글명 개선 보고서

- 목적: 4글자 이상 한글식 이름 중 명백한 오표기 후보를 먼저 보정
- 입력: `data/track4_primary_market_feature_candidates_v1.csv`
- 출력: `data/track6/track6_feature_candidates_name_corrected.csv`
- override 파일: `scripts/track6/artist_ko_overrides.csv`
- 적용 작가 key 수: `51`
- 적용 rows: `1,524`
- 잔여 검토 후보 작가 key 수: `599`
- 잔여 검토 후보 rows: `6,039`

## 1. 처리 원칙

- 자동 음역으로 다시 추정하지 않음
- 확실한 한국식 이름만 `artist_ko_overrides.csv`에 등록해 적용함
- 예명, 외국 작가명, 단체명, 갤러리명처럼 애매한 값은 검토 후보로 남김
- `artist_name_ko_orig`는 보정 전 이름을 유지함
- split은 보정된 `artist_name_ko` 기준으로 다시 생성해야 함

## 2. 적용 예시

| artist_key | 기존 한글명 | 보정 한글명 | rows | 사유 |
|---|---|---|---:|---|
| `myunggyun you` | 유명규느 | 유명균 | `93` | `obvious_bad_romanization` |
| `sang wooc rhee` | 이상우크 | 이상욱 | `79` | `obvious_bad_romanization` |
| `hyungjun suh` | 서현그준 | 서형준 | `76` | `obvious_bad_romanization` |
| `seung yean cho` | 조승예안 | 조승연 | `76` | `obvious_bad_romanization` |
| `choonjae kim` | 김초온재 | 김춘재 | `64` | `obvious_bad_romanization` |
| `jihyeon choi` | 최지혜온 | 최지현 | `60` | `obvious_bad_romanization` |
| `kim deasung` | 김데아성 | 김대성 | `55` | `obvious_bad_romanization` |
| `choongmok yoo` | 유초온그목 | 유충목 | `54` | `obvious_bad_romanization` |
| `kwon neung` | 권네운그 | 권능 | `52` | `obvious_bad_romanization` |
| `kim deok han` | 김더크한 | 김덕한 | `49` | `obvious_bad_romanization` |
| `hyegyun kim` | 김혜규느 | 김혜균 | `47` | `obvious_bad_romanization` |
| `deokhwan yoon` | 윤더크환 | 윤덕환 | `46` | `obvious_bad_romanization` |
| `gwanhee lee` | 이그완희 | 이관희 | `42` | `obvious_bad_romanization` |
| `sungone jung` | 정성온에 | 정성원 | `40` | `obvious_bad_romanization` |
| `keem jiyoung` | 케에므지영 | 김지영 | `37` | `obvious_bad_romanization` |
| `kwang bum jang` | 장광부므 | 장광범 | `37` | `obvious_bad_romanization` |
| `soon yeal yang` | 양순예아르 | 양순열 | `35` | `obvious_bad_romanization` |
| `jihyung nam` | 남지현그 | 남지형 | `33` | `obvious_bad_romanization` |
| `bomyee kim` | 김봄예에 | 김봄이 | `32` | `obvious_bad_romanization` |
| `sangik seo` | 서상이크 | 서상익 | `29` | `obvious_bad_romanization` |
| `aedam kim donghyung` | 애댐김동현그 | 애담 김동형 | `26` | `track3_manual_override` |
| `gyunghwa roh` | 노규응화 | 노경화 | `25` | `obvious_bad_romanization` |
| `seo hyun sohn` | 서현소흐느 | 손서현 | `25` | `obvious_bad_romanization` |
| `cheong hyeong yeol` | 정형여르 | 정형열 | `23` | `obvious_bad_romanization` |
| `jungwon phee` | 정원프희 | 피정원 | `21` | `obvious_bad_romanization` |
| `yoon sang yuel` | 윤상유에르 | 윤상열 | `21` | `obvious_bad_romanization` |
| `sook ja rho` | 숙자르호 | 노숙자 | `20` | `obvious_bad_romanization` |
| `jungkee son` | 손정케에 | 손정기 | `19` | `obvious_bad_romanization` |
| `bahk younghoon` | 바흐크영훈 | 박영훈 | `18` | `obvious_bad_romanization` |
| `seim shon` | 세이므쇼느 | 손세임 | `18` | `obvious_bad_romanization` |
| `sukhyung kang` | 강석현그 | 강석형 | `18` | `obvious_bad_romanization` |
| `woongjoo seo` | 서운그주 | 서웅주 | `18` | `obvious_bad_romanization` |
| `bae hyung kyung` | 배현그경 | 배형경 | `17` | `obvious_bad_romanization` |
| `eunphil cho` | 조은프힐 | 조은필 | `17` | `obvious_bad_romanization` |
| `ingee chung` | 정인게에 | 정인지 | `17` | `obvious_bad_romanization` |
| `kee tae kim` | 김케에태 | 김기태 | `17` | `obvious_bad_romanization` |
| `kim sookang` | 김숙안그 | 김수강 | `17` | `obvious_bad_romanization` |
| `sangdeok ra` | 상더크라 | 라상덕 | `17` | `obvious_bad_romanization` |
| `jeayeon hong` | 홍제아연 | 홍재연 | `16` | `obvious_bad_romanization` |
| `hoh woo jung` | 정호흐우 | 정호우 | `15` | `obvious_bad_romanization` |

## 3. 잔여 검토 후보 상위

| rows | artist_key | 현재 한글명 | 출처 |
|---:|---|---|---|
| `375` | `kai ax` | 카이아엑스 | `saatchi` |
| `256` | `lacey kim` | 김레이시 | `saatchi` |
| `233` | `ivie ives` | 이비에이베스 | `saatchi` |
| `219` | `karis kim` | 김카리스 | `saatchi` |
| `124` | `ouchul hwang` | 황오우철 | `saatchi` |
| `121` | `lydia lee` | 이리디아 | `saatchi` |
| `114` | `hagley art` | 하그레이아트 | `saatchi` |
| `100` | `gallery hexagon` | 핵사곤갤러리 | `saatchi` |
| `85` | `jinho kee` | 진호케에 | `saatchi` |
| `80` | `yohahn diko` | 디코요한 | `saatchi` |
| `79` | `jennifer lee` | 이제니퍼 | `saatchi` |
| `65` | `weedong yoon b 1982` | 윤웨에동 | `artsy` |
| `64` | `kris kim` | 김크리스 | `saatchi` |
| `54` | `leysan khasan` | 레이산크하산 | `saatchi` |
| `52` | `marina ogai` | 마린아옥아이 | `saatchi` |
| `47` | `yoo suzy` | 유수즈이 | `artsy,artue` |
| `45` | `erica choi` | 최어이카 | `saatchi` |
| `45` | `stepper studio` | 스테퍼스튜디오 | `saatchi` |
| `44` | `hazzi eunjeong kim` | 김하즈지은정 | `saatchi` |
| `44` | `lookha bark` | 루크하바르크 | `saatchi` |
| `43` | `wang yeul` | 왕예우르 | `artsy` |
| `40` | `chanoo park` | 박찬오오 | `artsy` |
| `39` | `jeremy yong` | 용제레미 | `saatchi` |
| `39` | `mihei her` | 미헤이헤르 | `artsy` |
| `39` | `minjeong guem` | 민정구에므 | `artsy` |
| `38` | `matthew anderson` | 매튜안데르선 | `saatchi` |
| `38` | `ryu hoimin` | 류호이민 | `saatchi` |
| `38` | `stella sujin` | 스텔라수진 | `artsy` |
| `34` | `valeriia kapitulska park lia` | 바레리이아캅이툴스카박리아 | `saatchi` |
| `34` | `zhanna kan` | 즈한나칸 | `saatchi` |
| `33` | `diego rodarte` | 디에고로다르테 | `artue` |
| `30` | `haneyl choi` | 최한에이르 | `artsy` |
| `29` | `sophie an` | 안솝히에 | `saatchi` |
| `28` | `gbday` | 그브다이 | `artsy,artue` |
| `28` | `jenny seongryung lee` | 이제니성륭 | `saatchi` |
| `28` | `lee yimchoon` | 이임초온 | `saatchi` |
| `27` | `melody park` | 박멜로디 | `saatchi` |
| `27` | `pogoby official` | 포고브이오프피시아르 | `saatchi` |
| `27` | `sambypen` | 샘바이펜 | `artsy,artue` |
| `26` | `g sim seyeon` | 그심세연 | `artsy` |

## 4. 다음 작업

- `data/track6/track6_feature_candidates_name_corrected.csv` 기준으로 split 재생성
- 컬럼 품질 검증과 feature/label 분리 재실행
- 잔여 후보는 수동 검수 후 `scripts/track6/artist_ko_overrides.csv`에 추가
