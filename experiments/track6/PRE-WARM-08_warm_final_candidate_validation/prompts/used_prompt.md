# PRE-WARM-08 Warm final candidate validation

- 목적: Warm 기준 후보를 validation/test/OOF 기준으로 비교한다.
- 후보:
  - final artifact `base_existing_combo`
  - compact `artist_name_ko + size + artist_works` no aspect
  - compact `artist_name_ko + size + artist_works`
  - compact `artist_key + size + ho interaction`
- 판단:
  - validation MdAPE 우선
  - test p95_APE와 OOF MdAPE 보조
  - 운영 가능성 별도 표시
- 주의:
  - validation feature 파일에 `artist_name_ko`가 없어 label metadata에서 보강한다.
