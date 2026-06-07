# Track 4 Split

- Source: `data/track3_unified_v3.csv`
- Seed: `404`
- Purpose: Track 4 train / validation / test split with separate Warm and Cold evaluation.

| File | Rows | Artists | Purpose |
|---|---:|---:|---|
| `track4_train.csv` | 33,145 | 1,816 | model fit only |
| `track4_val_warm.csv` | 1,474 | 1,474 | Warm validation |
| `track4_val_cold.csv` | 1,720 | 150 | Cold validation |
| `track4_test_warm.csv` | 1,474 | 1,474 | Warm final test |
| `track4_test_cold.csv` | 2,324 | 200 | Cold final test |

## Rules

- `track4_train.csv`만 학습에 사용한다.
- `val_warm`, `val_cold`는 모델/피처/정책 선택에 사용한다.
- `test_warm`, `test_cold`는 최종 확인 전까지 보지 않는다.
- Warm 파일의 작가는 모두 train에 남아 있다.
- Cold 파일의 작가는 train에 없다.
- 모든 transform, categorical vocabulary, scaler, artist aggregate feature는 train만 보고 fit한다.

## Audit

- `track4_split_membership.csv`: split membership and source row mapping.
- `split_metadata.json`: split policy, counts, integrity checks.
