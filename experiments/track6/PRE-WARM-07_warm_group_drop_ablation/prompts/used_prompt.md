# PRE-WARM-07 Warm group-drop ablation

- 목적: Warm 기준 모델 후보 3개에서 피처 그룹 제거 시 성능 변화를 확인한다.
- 대상 후보:
  - `PRE-WARM-01`: final artifact `base_existing_combo`
  - `PRE-WARM-05`: compact `artist_name_ko + size + artist_works`
  - `PRE-WARM-06C`: compact `artist_key + size + ho interaction`
- 제거 그룹:
  - artist
  - size
  - depth/3D
  - medium/support
  - aspect
  - artist works
  - ho interaction
- 판단 기준:
  - MdAPE 악화: 일반 정확도 기여
  - p95_APE 악화: 큰 오차 방어 기여
  - 제거 후 개선: 노이즈 또는 과분화 가능성
