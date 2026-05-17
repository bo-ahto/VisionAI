# Track 4 갤러리 메타데이터 점검

- 목적: 갤러리명과 티어 기준표 매칭 가능성을 확인
- 결론: 갤러리/티어는 기본 모델 피처가 아니라 보조 메타데이터로 보류
- 입력: `data/track4_artist_consistency_audit.csv`
- 티어 기준표: `data/art_gallery_tier_list_v3.xlsx - 전체 리스트.csv`
- 감사 CSV: `data/track4_gallery_metadata_audit.csv`
- 전체 rows: `54,842`
- 티어 매칭 rows: `331`
- 갤러리명 결측 rows: `2,783`
- 티어 미매칭 rows: `51,728`

## 1. 출처별 요약

| 출처 | rows | 갤러리명 있음 | 티어 매칭 | 결측 | 미매칭 |
|---|---:|---:|---:|---:|---:|
| artsy | `30,046` | `30,046` | `277` | `0` | `29,769` |
| artue | `2,783` | `0` | `0` | `2,783` | `0` |
| gallery_primary | `292` | `292` | `54` | `0` | `238` |
| saatchi | `21,721` | `21,721` | `0` | `0` | `21,721` |

## 2. 미매칭 상위 갤러리명

- `Saatchi Art`: `21,721`
- `Leehwaik Gallery`: `1,353`
- `Hakgojae Gallery`: `1,175`
- `Art Spoon`: `1,134`
- `The Trinity Gallery`: `1,075`
- `ATELIER AKI`: `1,012`
- `Art Sohyang`: `965`
- `2gil29gallery`: `959`
- `Kimreeaa Gallery`: `955`
- `GALLERY MAC`: `938`
- `Suppoment Gallery`: `925`
- `Gallery Grimson`: `881`
- `Gallery Joeun`: `830`
- `THEO`: `817`
- `Keumsan Gallery`: `808`
- `LEE & BAE`: `740`
- `MOOWOOSOO Gallery`: `576`
- `Gallery Playlist`: `467`
- `Art in Dongsan`: `464`
- `Arario Gallery`: `448`

## 3. 현재 판단

- 갤러리명은 출처별 결측과 표기 차이가 큼
- 티어 기준표 매칭률이 충분히 높지 않으면 모델 피처로 쓰기 어려움
- 실제 운영에서 갤러리 정보를 항상 입력받는 구조가 아니라면 기본 피처에서 제외해야 함
- 갤러리/티어는 데이터 품질 확인, 작가 DB 보완, 후속 실험 후보로 보류함

## 4. 클렌징 반영 원칙

- `gallery_name_raw`는 원본 추적용으로 유지
- `gallery_tier_validated`는 기준표 매칭이 된 경우만 보조 컬럼으로 유지
- 최종 feature 후보 파일에서는 갤러리/티어를 기본 입력 피처에서 제외
- 별도 가설에서 갤러리 정보를 운영 입력으로 받을 수 있는 경우에만 실험
