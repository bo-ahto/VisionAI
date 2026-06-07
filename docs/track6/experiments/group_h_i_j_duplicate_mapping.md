# Track6 Group H/I/J 중복 매핑 검토

- 목적: H/I/J 신규 제안 중 기존 실험과 중복되는 항목을 재실행하지 않고 기존 결과에 매핑

| 신규 라벨 | 매핑 실험 | 피처 | 처리 |
|---|---|---|---|
| H2 | D8 | `artist_name_ko x log_area` | 기존 D8 artist_name x log_area 숫자형 교차항 결과를 매핑 |
| H3 | D9 | `artist_name_ko x nant_material_idx/nant_tool` | 기존 D9 artist_name x 재료 조합 결과를 매핑 |
| H4 | D10 | `artist_name_ko x nant_support` | 기존 D10 artist_name x 지지체 조합 결과를 매핑 |
| I4 | G8 | `작품 기본 피처 + 생년/전시/국적` | 기존 G8 작품 기본 피처 + 기본 작가 프로필 결과를 매핑 |
