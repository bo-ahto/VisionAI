# Track6 남은 한글 작가명 위험군 67개 수동 검토 리스트

입력 기준: `data/track6/quality/track6_artist_name_ko_quality_audit.csv`

분류 기준:

- `확정가능_후보`: 현재 데이터만으로도 사람이 빠르게 승인하거나 override 후보로 검토할 수 있는 항목이다. 이미 한글 원문인 경우는 `유지`로 표시했다.
- `보류_확인필요`: 공식 표기, 작가/브랜드 여부, 성/이름 순서, 언어권 음역을 확인해야 하는 항목이다. 임의 override를 넣으면 오히려 잘못된 한글명이 고정될 수 있다.

검토용 CSV:

- `docs/track6/dataset/artist_name_ko_remaining_67_manual_review.csv`

## 요약

| 분류 | artist_key 수 | rows 합계 | 처리 방향 |
|---|---:|---:|---|
| 확정가능_후보 | 22 | 47 | 사람이 승인하면 override 반영 가능 |
| 보류_확인필요 | 45 | 127 | 공식 출처 확인 후 반영하거나 split 제외/보류 정책 적용 |

## 바로 확인 가능한 후보

| rows | artist_key | 현재 한글명 | 제안 한글명 | 처리 |
|---:|---|---|---|---|
| 1 | 테레시타 페르난데즈 | 테레시타 페르난데즈 | 테레시타 페르난데즈 | 유지 |
| 7 | fr d ric bruly bouabr | 프르드리크브룰이보우아브르 | 프레데릭 브룰리 부아브레 | override 후보 |
| 6 | joshua kane gomes | 조슈아칸에곰에스 | 조슈아 케인 고메스 | override 후보 |
| 4 | orkis studio | 오기스스투디오 | 오르키스 스튜디오 | override 후보 |
| 4 | 게오르그 바젤리츠 | 게오르그 바젤리츠 | 게오르그 바젤리츠 | 유지 |
| 3 | pilgrim studio | 필그림스투디오 | 필그림 스튜디오 | override 후보 |
| 2 | cildo meireles | 시르도메이에레스 | 실도 메이렐레스 | override 후보 |
| 2 | gabriel orozco | 갑리에르오오즈코 | 가브리엘 오로스코 | override 후보 |
| 2 | philippe parreno | 프힐입페파르렌오 | 필립 파레노 | override 후보 |
| 2 | rirkrit tiravanija | 리르크리트티라바니자 | 리크릿 티라바니자 | override 후보 |
| 2 | rosemarie trockel | 로세마리에트로크케르 | 로즈마리 트로켈 | override 후보 |
| 2 | 아크마노로 나일스 | 아크마노로 나일스 | 아크마노로 나일스 | 유지 |
| 1 | adel abdessemed | 아델아브데스세메드 | 아델 압데세메드 | override 후보 |
| 1 | david douard | 데이비드도우아르드 | 다비드 두아르 | override 후보 |
| 1 | frank gehry | 프랭크게흐르이 | 프랭크 게리 | override 후보 |
| 1 | fx studio | 프엑스스투디오 | FX 스튜디오 | override 후보 |
| 1 | georg baselitz | 게오르그 바젤리츠 | 게오르그 바젤리츠 | override 후보 |
| 1 | herbert matter | 헤르베르트마트어 | 허버트 매터 | override 후보 |
| 1 | marcel duchamp | 마르세르두차므프 | 마르셀 뒤샹 | override 후보 |
| 1 | vassily kandinsky | 바스실이칸딘스크이 | 바실리 칸딘스키 | override 후보 |
| 1 | william kentridge | 윌리엄켄트리드게 | 윌리엄 켄트리지 | override 후보 |
| 1 | 아리아나 파파데메트로풀로스 | 아리아나 파파데메트로풀로스 | 아리아나 파파데메트로풀로스 | 유지 |

## 보류 확인 필요

이 그룹은 공식 출처 확인 전에는 override를 넣지 않는 편이 낫다.

주요 이유:

- 태국/동남아권 이름은 한국어 표기 규칙만으로 확정하기 어렵다.
- 한국계 이름은 성/이름 순서와 공식 활동명이 다를 수 있다.
- `GWAXNG`, `IVAAIU City`, `Unhappy Circuit`, `South-big`처럼 브랜드/작가명 여부가 불명확한 항목이 있다.
- `l gallery`는 작가명이 아니라 갤러리명이 섞였을 가능성이 있다.

전체 보류 목록은 CSV의 `보류_확인필요` 행을 기준으로 확인하면 된다.
