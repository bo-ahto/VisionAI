# Cold Artist-Coefficient (PP-CCOEF1 / PP-CCOEF2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-challenge the "collection-free cold point-prediction is closed" verdict by restructuring the *learning target* around the universal artist-coefficient (`price/area`), in two staged experiments on existing Track6 cold data.

**Architecture:** PP-CCOEF1 (A) trains the existing v0.2 LightGBM-Quantile stack on a size-normalized target `ln(price/area)` and reconstructs `price = exp(pred)·area`. PP-CCOEF2 (B), informed by A, builds a two-stage model: a shrunk per-warm-artist coefficient table, then an OOF metadata→coefficient regression imputed onto cold artists with fallback to A/v0.2. Both evaluate against the search-free v0.2 base under the artist-holdout gate, never touching the fixed test until a single final confirmation.

**Tech Stack:** Python 3.14 (`.venv`), lightgbm 4.6, pandas 3.0, numpy. No new dependencies.

## Global Constraints

- Single data source: `data/track6/service_v0_1/official_v0_1_cold_feature_store.csv` (has 12 artwork features + `artist_meta_*` + `artist_exhibition_*` + `gallery_tier_*` + `split_name` + `artist_key` + `price_krw`).
- Artwork feature set (12, verbatim): `width_cm, height_cm, depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium_category, support_category, size_bucket, support_size_bucket`. Categoricals: `medium_category, support_category, size_bucket, support_size_bucket`.
- LGB params verbatim from v0.2 (per-quantile `alpha`): `objective="quantile", n_estimators=430, num_leaves=31, learning_rate=0.035, min_child_samples=35, subsample=0.9, colsample_bytree=0.9, reg_alpha=0.0, reg_lambda=1.2, max_depth=-1, subsample_freq=1, n_jobs=-1, verbose=-1`. Quantiles q10/q40/q50/q90 → alpha 0.10/0.40/0.50/0.90.
- Comparison base: v0.2 q50 = **MdAPE 0.4823 / MAPE 1.242 / p95 4.380** on fixed cold test (3,099 rows / 200 artists).
- Gate (PP-CBASE1): artist 80%/70% holdout, ≥200 bootstrap runs, **MAPE and p95 improvement probability ≥ 0.90**.
- **0604 data is forbidden for cold.** Never select candidates on the fixed test — final confirmation once only. Any learned correction/shrinkage/regression is fit on OOF/folds only.
- `metrics(actual_log, pred_log)` convention (verbatim from PP-CDATA1): `actual=exp(actual_log)`, `pred=clip(exp(pred_log),1000,None)`, `ape=|pred-actual|/clip(actual,1,None)`, return MdAPE/MAPE/p95.
- Experiment folders: `experiments/track6/PP-CCOEF1_cold_size_normalized_target/`, `experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/`. Update `docs/track6/experiments/postprocessing_experiment_matrix.md` at each experiment's close.
- Commits: targeted `git add` of only the experiment's own files (Codex parallel work is uncommitted in the tree — never `git add -A`).

---

## File Structure

- `experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/common_cold.py` — shared loader, prep, metrics, leakage guard (reused by all CCOEF1 scripts and imported by CCOEF2).
- `.../PP-CCOEF1_.../scripts/run_ccoef1_fixed_test.py` — A training + reconstruction + fixed-test metrics.
- `.../PP-CCOEF1_.../scripts/run_ccoef1_holdout_gate.py` — artist-holdout bootstrap gate.
- `.../PP-CCOEF1_.../scripts/run_ccoef1_pseudocold_sensitivity.py` — pseudo-cold + area-noise sensitivity.
- `.../PP-CCOEF1_.../artifacts/*.json` — metrics outputs.
- `docs/track6/experiments/pp_ccoef1_cold_size_normalized_target_summary.md` — A summary + decision.
- `experiments/track6/PP-CCOEF2_.../scripts/run_ccoef2_stage1_coef_table.py` — warm artist coefficient table (EB shrinkage).
- `.../PP-CCOEF2_.../scripts/run_ccoef2_stage2_meta_regression.py` — OOF metadata→coefficient regression + cold inference + coverage-stratified eval.
- `docs/track6/experiments/pp_ccoef2_cold_artist_coefficient_imputation_summary.md` — B summary + decision.

---

# PP-CCOEF1 (A안) — Size-Normalized Target

### Task 1: Shared cold harness with leakage + area guards

**Files:**
- Create: `experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/common_cold.py`
- Test: `experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/test_common_cold.py`

**Interfaces:**
- Produces: `REPO: Path`, `STORE: Path`, `FEATURES: list[str]`, `CATS: list[str]`, `lgb_params(alpha: float) -> dict`, `load_splits() -> tuple[pd.DataFrame, pd.DataFrame]` (train, test; both with `ln_price`, `ln_coef`, valid `area_cm2>0`), `prep(df) -> pd.DataFrame`, `metrics(actual_log, pred_log) -> dict`, `assert_disjoint(train, test) -> None`.

- [ ] **Step 1: Write the failing test**

```python
# test_common_cold.py
from common_cold import load_splits, assert_disjoint, metrics, FEATURES
import numpy as np

def test_splits_disjoint_and_area_positive():
    train, test = load_splits()
    assert (train["area_cm2"] > 0).all() and (test["area_cm2"] > 0).all()
    assert_disjoint(train, test)  # raises if any shared artist_key
    # ln_coef identity: ln_price - ln(area) == ln_coef
    assert np.allclose(train["ln_coef"], train["ln_price"] - np.log(train["area_cm2"]))

def test_metrics_perfect_is_zero():
    # realistic prices (millions of KRW) so the 1000-KRW floor never bites
    logs = [np.log(1_000_000.0), np.log(5_000_000.0)]
    m = metrics(logs, logs)
    assert m["MdAPE"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts && ../../../../.venv/bin/python -m pytest test_common_cold.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'common_cold'`

- [ ] **Step 3: Write minimal implementation**

```python
# common_cold.py
from __future__ import annotations
import warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[4]
STORE = REPO / "data" / "track6" / "service_v0_1" / "official_v0_1_cold_feature_store.csv"

FEATURES = ["width_cm", "height_cm", "depth_cm", "area_cm2", "log_area", "aspect_ratio",
            "has_depth", "is_3d_candidate", "medium_category", "support_category",
            "size_bucket", "support_size_bucket"]
CATS = ["medium_category", "support_category", "size_bucket", "support_size_bucket"]

def lgb_params(alpha: float) -> dict:
    return dict(objective="quantile", alpha=alpha, n_estimators=430, num_leaves=31,
               learning_rate=0.035, min_child_samples=35, subsample=0.9,
               colsample_bytree=0.9, reg_alpha=0.0, reg_lambda=1.2, max_depth=-1,
               subsample_freq=1, n_jobs=-1, verbose=-1)

def load_splits() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(STORE, low_memory=False)
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["area_cm2"] = pd.to_numeric(df["area_cm2"], errors="coerce")
    df = df[(df["price_krw"] > 0) & (df["area_cm2"] > 0)].copy()
    df["ln_price"] = np.log(df["price_krw"])
    df["ln_coef"] = df["ln_price"] - np.log(df["area_cm2"])
    train = df[df["split_name"] == "train"].dropna(subset=["ln_price"]).copy()
    test = df[df["split_name"] == "test"].dropna(subset=["ln_price"]).copy()
    return train, test

def prep(df: pd.DataFrame) -> pd.DataFrame:
    x = df[FEATURES].copy()
    for c in CATS:
        x[c] = x[c].astype("category")
    for c in [f for f in FEATURES if f not in CATS]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x

def metrics(actual_log, pred_log) -> dict:
    actual = np.exp(np.asarray(actual_log, dtype=float))
    pred = np.clip(np.exp(np.asarray(pred_log, dtype=float)), 1000.0, None)
    ape = np.abs(pred - actual) / np.clip(actual, 1.0, None)
    return {"MdAPE": float(np.median(ape)), "MAPE": float(np.mean(ape)),
            "p95_APE": float(np.quantile(ape, 0.95))}

def assert_disjoint(train: pd.DataFrame, test: pd.DataFrame) -> None:
    shared = set(train["artist_key"].dropna()) & set(test["artist_key"].dropna())
    assert not shared, f"leakage: {len(shared)} shared artists"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts && ../../../../.venv/bin/python -m pytest test_common_cold.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/common_cold.py \
        experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/test_common_cold.py
git commit -m "PP-CCOEF1: shared cold harness with leakage + area guards"
```

### Task 2: A-target training, reconstruction, fixed-test metrics

**Files:**
- Create: `experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/run_ccoef1_fixed_test.py`
- Test: `experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/test_reconstruction.py`

**Interfaces:**
- Consumes: `common_cold.{load_splits, prep, metrics, lgb_params, FEATURES}`.
- Produces: `train_coef_models(train) -> dict[str, LGBMRegressor]`, `predict_price_log(models, frame) -> dict[str, np.ndarray]` (each quantile reconstructed to **price-log scale** via `coef_pred + log(area)`), writes `artifacts/fixed_test_metrics.json`.

- [ ] **Step 1: Write the failing test**

```python
# test_reconstruction.py
import numpy as np, pandas as pd
from common_cold import load_splits, prep
from run_ccoef1_fixed_test import train_coef_models, predict_price_log

def test_reconstruction_is_coef_plus_logarea():
    train, test = load_splits()
    models = train_coef_models(train.head(2000))
    out = predict_price_log(models, test.head(50))
    raw_coef = np.asarray(models["q50"].predict(prep(test.head(50))), dtype=float)
    expected = raw_coef + np.log(test.head(50)["area_cm2"].to_numpy(float))
    assert np.allclose(out["q50"], expected)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts && ../../../../.venv/bin/python -m pytest test_reconstruction.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_ccoef1_fixed_test'`

- [ ] **Step 3: Write minimal implementation**

```python
# run_ccoef1_fixed_test.py
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from lightgbm import LGBMRegressor
from common_cold import load_splits, prep, metrics, lgb_params, assert_disjoint

ART = Path(__file__).resolve().parents[1] / "artifacts"
QUANTILES = {"q10": 0.10, "q40": 0.40, "q50": 0.50, "q90": 0.90}

def train_coef_models(train):
    x = prep(train)
    y = train["ln_coef"].to_numpy(float)  # size-normalized target
    return {q: LGBMRegressor(**lgb_params(a)).fit(x, y) for q, a in QUANTILES.items()}

def predict_price_log(models, frame):
    x = prep(frame)
    log_area = np.log(frame["area_cm2"].to_numpy(float))
    return {q: np.asarray(models[q].predict(x), dtype=float) + log_area for q in models}

def main():
    train, test = load_splits()
    assert_disjoint(train, test)
    models = train_coef_models(train)
    pred = predict_price_log(models, test)
    actual_log = test["ln_price"].to_numpy(float)
    m = metrics(actual_log, pred["q50"])
    base = {"MdAPE": 0.4823, "MAPE": 1.242, "p95_APE": 4.380}
    out = {"n_test": int(len(test)), "ccoef1_q50": m, "v0_2_base": base,
           "delta": {k: m[k] - base[k] for k in m}}
    ART.mkdir(exist_ok=True)
    (ART / "fixed_test_metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts && ../../../../.venv/bin/python -m pytest test_reconstruction.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Run the experiment (record only, NOT for selection)**

Run: `cd experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts && ../../../../.venv/bin/python run_ccoef1_fixed_test.py`
Expected: prints JSON; `artifacts/fixed_test_metrics.json` created. This is a record point — the gate decision is Task 3, not this number.

- [ ] **Step 6: Commit**

```bash
git add experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/run_ccoef1_fixed_test.py \
        experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/test_reconstruction.py \
        experiments/track6/PP-CCOEF1_cold_size_normalized_target/artifacts/fixed_test_metrics.json
git commit -m "PP-CCOEF1: size-normalized target training + fixed-test record"
```

### Task 3: Artist-holdout bootstrap gate

**Files:**
- Create: `experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/run_ccoef1_holdout_gate.py`

**Interfaces:**
- Consumes: `common_cold.*`, `run_ccoef1_fixed_test.{train_coef_models, predict_price_log}`.
- Produces: `artifacts/holdout_gate.json` with `improve_prob_MAPE`, `improve_prob_p95`, `improve_prob_MdAPE`, `pass` (bool: MAPE and p95 prob ≥ 0.90).

- [ ] **Step 1: Write the gate script**

```python
# run_ccoef1_holdout_gate.py
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from lightgbm import LGBMRegressor
from common_cold import load_splits, prep, metrics, lgb_params
from run_ccoef1_fixed_test import predict_price_log

ART = Path(__file__).resolve().parents[1] / "artifacts"
RUNS, FRACS, SEED0 = 200, [0.80, 0.70], 20260622

def fit_q50(frame, target_col):
    return LGBMRegressor(**lgb_params(0.50)).fit(prep(frame), frame[target_col].to_numpy(float))

def main():
    train, _ = load_splits()
    artists = np.array(sorted(train["artist_key"].dropna().unique()))
    rng = np.random.default_rng(SEED0)
    wins = {k: [] for k in ["MdAPE", "MAPE", "p95_APE"]}
    for r in range(RUNS):
        frac = FRACS[r % len(FRACS)]
        pick = rng.choice(artists, size=int(len(artists) * frac), replace=False)
        tr = train[train["artist_key"].isin(pick)]
        ev = train[~train["artist_key"].isin(pick)]
        if ev.empty or tr.empty:
            continue
        # candidate A (coef target) vs base (direct ln_price), same features/params
        a_model = fit_q50(tr, "ln_coef")
        a_pred = np.asarray(a_model.predict(prep(ev)), dtype=float) + np.log(ev["area_cm2"].to_numpy(float))
        b_model = fit_q50(tr, "ln_price")
        b_pred = np.asarray(b_model.predict(prep(ev)), dtype=float)
        ay, by = metrics(ev["ln_price"], a_pred), metrics(ev["ln_price"], b_pred)
        for k in wins:
            wins[k].append(1.0 if ay[k] < by[k] else 0.0)
    probs = {f"improve_prob_{k}": float(np.mean(v)) for k, v in wins.items()}
    passed = probs["improve_prob_MAPE"] >= 0.90 and probs["improve_prob_p95_APE"] >= 0.90
    out = {"runs": RUNS, **probs, "pass": passed}
    ART.mkdir(exist_ok=True)
    (ART / "holdout_gate.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the gate**

Run: `cd experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts && ../../../../.venv/bin/python run_ccoef1_holdout_gate.py`
Expected: prints JSON with `pass` true/false; `artifacts/holdout_gate.json` created. (Heavy: 200 paired retrains — may take several minutes.)

- [ ] **Step 3: Commit**

```bash
git add experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/run_ccoef1_holdout_gate.py \
        experiments/track6/PP-CCOEF1_cold_size_normalized_target/artifacts/holdout_gate.json
git commit -m "PP-CCOEF1: artist-holdout bootstrap gate (coef vs direct target)"
```

### Task 4: Pseudo-cold + area-noise sensitivity guard

**Files:**
- Create: `experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/run_ccoef1_pseudocold_sensitivity.py`

**Interfaces:**
- Consumes: `common_cold.*`, `run_ccoef1_fixed_test.{train_coef_models, predict_price_log}`.
- Produces: `artifacts/sensitivity.json` with metrics on overall test and on the top/bottom 1% `area_cm2` slices (the documented failure mode: area noise multiplies into the prediction).

- [ ] **Step 1: Write the sensitivity script**

```python
# run_ccoef1_pseudocold_sensitivity.py
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from common_cold import load_splits, metrics
from run_ccoef1_fixed_test import train_coef_models, predict_price_log

ART = Path(__file__).resolve().parents[1] / "artifacts"

def main():
    train, test = load_splits()
    models = train_coef_models(train)
    pred = predict_price_log(models, test)["q50"]
    actual = test["ln_price"].to_numpy(float)
    area = test["area_cm2"].to_numpy(float)
    lo, hi = np.quantile(area, 0.01), np.quantile(area, 0.99)
    slices = {
        "overall": np.ones(len(test), bool),
        "area_bottom_1pct": area <= lo,
        "area_top_1pct": area >= hi,
        "area_mid": (area > lo) & (area < hi),
    }
    out = {name: {**metrics(actual[m], pred[m]), "n": int(m.sum())}
           for name, m in slices.items()}
    ART.mkdir(exist_ok=True)
    (ART / "sensitivity.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `cd experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts && ../../../../.venv/bin/python run_ccoef1_pseudocold_sensitivity.py`
Expected: prints per-slice metrics; `artifacts/sensitivity.json` created. Interpretation: if `area_top_1pct`/`area_bottom_1pct` MdAPE is far worse than `area_mid`, the area-noise risk is real → recommend an area-clip fallback in the summary.

- [ ] **Step 3: Commit**

```bash
git add experiments/track6/PP-CCOEF1_cold_size_normalized_target/scripts/run_ccoef1_pseudocold_sensitivity.py \
        experiments/track6/PP-CCOEF1_cold_size_normalized_target/artifacts/sensitivity.json
git commit -m "PP-CCOEF1: pseudo-cold + area-noise sensitivity slices"
```

### Task 5: A summary + decision + matrix update

**Files:**
- Create: `docs/track6/experiments/pp_ccoef1_cold_size_normalized_target_summary.md`
- Modify: `docs/track6/experiments/postprocessing_experiment_matrix.md` (append PP-CCOEF1 row)

- [ ] **Step 1: Write the summary**

Write `pp_ccoef1_cold_size_normalized_target_summary.md` containing, with numbers copied verbatim from the three artifacts JSON: (1) fixed-test q50 vs v0.2 base + delta; (2) holdout gate probs + pass/fail; (3) area sensitivity slices; (4) **Decision** — `채택 후보` if gate passed, else `기각 (크기 정규화 단독 무익)`; (5) **Hand-off to B**: state whether size-normalization reduced variance regardless of pass/fail (the directional signal B reuses).

- [ ] **Step 2: Update the matrix**

Append one row to `postprocessing_experiment_matrix.md`: `| PP-CCOEF1 | Cold | size-normalized target ln(price/area) | <pass/fail> | <one-line result> |` (match the table's existing column layout).

- [ ] **Step 3: Commit**

```bash
git add docs/track6/experiments/pp_ccoef1_cold_size_normalized_target_summary.md \
        docs/track6/experiments/postprocessing_experiment_matrix.md
git commit -m "PP-CCOEF1: summary, decision, matrix update"
```

---

# PP-CCOEF2 (B안) — Two-Stage Coefficient Imputation

> Start only after Task 5. Reuse `common_cold.py` (import via path). The B target is `ln_coef` from Stage 1, regressed on metadata. Cold metadata coverage is partial (birth 25% / exhibition 37% / followers 69%) — coverage is a first-class reported axis, not an afterthought.

### Task 6: Stage-1 warm artist coefficient table (EB shrinkage)

**Files:**
- Create: `experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts/run_ccoef2_stage1_coef_table.py`
- Test: `.../scripts/test_stage1_shrinkage.py`

**Interfaces:**
- Consumes: `common_cold.load_splits`.
- Produces: `build_coef_table(train, k=5.0) -> pd.DataFrame` with columns `artist_key, n_works, raw_coef, shrunk_coef` where `shrunk_coef = (n·raw + k·global)/(n+k)` on `ln_coef`; writes `artifacts/warm_coef_table.csv`.

- [ ] **Step 1: Write the failing test**

```python
# test_stage1_shrinkage.py
import numpy as np
from common_cold import load_splits
from run_ccoef2_stage1_coef_table import build_coef_table

def test_shrinkage_pulls_small_artists_toward_global():
    train, _ = load_splits()
    tbl = build_coef_table(train, k=5.0)
    g = train["ln_coef"].median()
    small = tbl[tbl["n_works"] == 1]
    # 1-work artists are pulled at least halfway to global vs their raw coef
    assert (np.abs(small["shrunk_coef"] - g) <= np.abs(small["raw_coef"] - g) + 1e-9).all()
    assert tbl["artist_key"].is_unique
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts && PYTHONPATH=../../PP-CCOEF1_cold_size_normalized_target/scripts ../../../../.venv/bin/python -m pytest test_stage1_shrinkage.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_ccoef2_stage1_coef_table'`

- [ ] **Step 3: Write minimal implementation**

```python
# run_ccoef2_stage1_coef_table.py
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "PP-CCOEF1_cold_size_normalized_target" / "scripts"))
import numpy as np, pandas as pd
from common_cold import load_splits

ART = Path(__file__).resolve().parents[1] / "artifacts"

def build_coef_table(train: pd.DataFrame, k: float = 5.0) -> pd.DataFrame:
    g = float(train["ln_coef"].median())
    agg = (train.groupby("artist_key")["ln_coef"]
           .agg(n_works="count", raw_coef="median").reset_index())
    agg["shrunk_coef"] = (agg["n_works"] * agg["raw_coef"] + k * g) / (agg["n_works"] + k)
    return agg

def main():
    train, _ = load_splits()
    tbl = build_coef_table(train, k=5.0)
    ART.mkdir(exist_ok=True)
    tbl.to_csv(ART / "warm_coef_table.csv", index=False)
    print(f"warm artists: {len(tbl)}, global_ln_coef median used as prior")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts && PYTHONPATH=../../PP-CCOEF1_cold_size_normalized_target/scripts ../../../../.venv/bin/python -m pytest test_stage1_shrinkage.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Run + commit**

```bash
cd experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts && PYTHONPATH=../../PP-CCOEF1_cold_size_normalized_target/scripts ../../../../.venv/bin/python run_ccoef2_stage1_coef_table.py
cd /Users/bo/VisionAI
git add experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts/run_ccoef2_stage1_coef_table.py \
        experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts/test_stage1_shrinkage.py \
        experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/artifacts/warm_coef_table.csv
git commit -m "PP-CCOEF2: stage-1 warm artist coefficient table (EB shrinkage)"
```

### Task 7: Stage-2 OOF metadata→coefficient regression + coverage-stratified cold eval

**Files:**
- Create: `experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts/run_ccoef2_stage2_meta_regression.py`
- Test: `.../scripts/test_stage2_oof_no_leak.py`

**Interfaces:**
- Consumes: `common_cold.{load_splits, prep, metrics, lgb_params}`, `run_ccoef2_stage1_coef_table.build_coef_table`, `run_ccoef1_fixed_test.{train_coef_models, predict_price_log}` (A model as fallback).
- Produces: `META: list[str]` = `["artist_meta_birth_year","artist_meta_total_works_log","artist_meta_followers_log","artist_meta_career_stage","artist_exhibition_total_count_log","gallery_tier_validated_score"]`; `coverage_mask(test) -> np.ndarray` (True where ≥1 META present); writes `artifacts/stage2_eval.json` with metrics for **covered subset** and **overall-with-fallback**, each vs v0.2 base and vs A (PP-CCOEF1).

- [ ] **Step 1: Write the failing test (OOF discipline)**

```python
# test_stage2_oof_no_leak.py
from run_ccoef2_stage2_meta_regression import oof_artist_coef_regression
from run_ccoef2_stage1_coef_table import build_coef_table
from common_cold import load_splits

def test_oof_predictions_use_held_out_folds_only():
    train, _ = load_splits()
    tbl = build_coef_table(train)
    oof = oof_artist_coef_regression(tbl, n_splits=5, seed=20260622)
    # every warm artist gets exactly one OOF prediction, none trained on itself
    assert set(oof["artist_key"]) == set(tbl["artist_key"])
    assert oof["oof_pred_coef"].notna().all()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts && PYTHONPATH=../../PP-CCOEF1_cold_size_normalized_target/scripts ../../../../.venv/bin/python -m pytest test_stage2_oof_no_leak.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'run_ccoef2_stage2_meta_regression'`

- [ ] **Step 3: Write minimal implementation**

```python
# run_ccoef2_stage2_meta_regression.py
from __future__ import annotations
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "PP-CCOEF1_cold_size_normalized_target" / "scripts"))
import numpy as np, pandas as pd
from lightgbm import LGBMRegressor
from sklearn.model_selection import KFold
from common_cold import load_splits, prep, metrics, lgb_params
from run_ccoef2_stage1_coef_table import build_coef_table
from run_ccoef1_fixed_test import train_coef_models, predict_price_log

ART = Path(__file__).resolve().parents[1] / "artifacts"
META = ["artist_meta_birth_year", "artist_meta_total_works_log", "artist_meta_followers_log",
        "artist_meta_career_stage", "artist_exhibition_total_count_log",
        "gallery_tier_validated_score"]
CAT_META = ["artist_meta_career_stage"]

def _meta_frame(df, keys):
    # one row per artist: first non-null meta per artist_key
    cols = ["artist_key"] + META
    m = df[cols].drop_duplicates("artist_key").set_index("artist_key")
    return m.reindex(keys)

def _prep_meta(m):
    x = m.copy()
    for c in CAT_META:
        x[c] = x[c].astype("category")
    for c in [f for f in META if f not in CAT_META]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x

def oof_artist_coef_regression(coef_table, n_splits=5, seed=20260622):
    train, _ = load_splits()
    keys = coef_table["artist_key"].to_numpy()
    m = _prep_meta(_meta_frame(train, keys))
    y = coef_table.set_index("artist_key").loc[keys, "shrunk_coef"].to_numpy(float)
    oof = np.full(len(keys), np.nan)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr_idx, va_idx in kf.split(keys):
        reg = LGBMRegressor(**{**lgb_params(0.50), "objective": "regression"})
        reg.fit(m.iloc[tr_idx], y[tr_idx])
        oof[va_idx] = reg.predict(m.iloc[va_idx])
    return pd.DataFrame({"artist_key": keys, "oof_pred_coef": oof})

def coverage_mask(test):
    present = np.zeros(len(test), bool)
    for c in META:
        present |= pd.to_numeric(test[c], errors="coerce").notna().to_numpy() if c not in CAT_META \
                   else test[c].notna().to_numpy()
    return present

def main():
    train, test = load_splits()
    tbl = build_coef_table(train)
    # fit final stage-2 on all warm artists (OOF only used for honesty checks)
    keys = tbl["artist_key"].to_numpy()
    m_tr = _prep_meta(_meta_frame(train, keys))
    y_tr = tbl.set_index("artist_key").loc[keys, "shrunk_coef"].to_numpy(float)
    reg = LGBMRegressor(**{**lgb_params(0.50), "objective": "regression"})
    reg.fit(m_tr, y_tr)
    # cold inference: coef_hat from metadata, price = exp(coef_hat) * area
    m_te = _prep_meta(_meta_frame(test, test["artist_key"].to_numpy()))
    coef_hat = reg.predict(m_te)
    log_area = np.log(test["area_cm2"].to_numpy(float))
    b_pred = coef_hat + log_area
    # A fallback for uncovered artists
    a_models = train_coef_models(train)
    a_pred = predict_price_log(a_models, test)["q50"]
    cov = coverage_mask(test)
    blended = np.where(cov, b_pred, a_pred)
    actual = test["ln_price"].to_numpy(float)
    base = {"MdAPE": 0.4823, "MAPE": 1.242, "p95_APE": 4.380}
    out = {
        "coverage_rate": float(cov.mean()),
        "covered_subset": {"B": metrics(actual[cov], b_pred[cov]),
                            "A": metrics(actual[cov], a_pred[cov]), "n": int(cov.sum())},
        "overall_with_fallback": {"B_blend": metrics(actual, blended),
                                  "A_only": metrics(actual, a_pred)},
        "v0_2_base": base,
    }
    ART.mkdir(exist_ok=True)
    (ART / "stage2_eval.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts && PYTHONPATH=../../PP-CCOEF1_cold_size_normalized_target/scripts ../../../../.venv/bin/python -m pytest test_stage2_oof_no_leak.py -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Run the eval (record only)**

Run: `cd experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts && PYTHONPATH=../../PP-CCOEF1_cold_size_normalized_target/scripts ../../../../.venv/bin/python run_ccoef2_stage2_meta_regression.py`
Expected: prints JSON; `artifacts/stage2_eval.json` created. Read `covered_subset` (B vs A) and `overall_with_fallback` — selection happens at the gate (Task 8 if pursued), not here.

- [ ] **Step 6: Commit**

```bash
git add experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts/run_ccoef2_stage2_meta_regression.py \
        experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/scripts/test_stage2_oof_no_leak.py \
        experiments/track6/PP-CCOEF2_cold_artist_coefficient_imputation/artifacts/stage2_eval.json
git commit -m "PP-CCOEF2: stage-2 OOF meta->coef regression + coverage-stratified cold eval"
```

### Task 8: B summary + decision + matrix update

**Files:**
- Create: `docs/track6/experiments/pp_ccoef2_cold_artist_coefficient_imputation_summary.md`
- Modify: `docs/track6/experiments/postprocessing_experiment_matrix.md` (append PP-CCOEF2 row)

- [ ] **Step 1: Write the summary**

Write the summary with numbers verbatim from `stage2_eval.json`: coverage rate; covered-subset B vs A vs base; overall-with-fallback B-blend vs A-only vs base. **Decision rule:** `채택 후보` only if covered-subset B beats A on MAPE/p95 **and** overall-with-fallback is non-worse than A — otherwise `기각`. If rejected, state the strengthened conclusion: *collection-free cold point prediction remains at the data frontier; the lever is Warm coverage expansion* (consistent with track6-cold-search-meta-diagnosis). Note pseudo-cold masking caveat: covered-subset gains may not transfer to operational new artists with sparser metadata.

- [ ] **Step 2: Update the matrix**

Append: `| PP-CCOEF2 | Cold | 2-stage meta->artist-coefficient imputation | <pass/fail> | <one-line result + coverage> |`.

- [ ] **Step 3: Commit**

```bash
git add docs/track6/experiments/pp_ccoef2_cold_artist_coefficient_imputation_summary.md \
        docs/track6/experiments/postprocessing_experiment_matrix.md
git commit -m "PP-CCOEF2: summary, decision, matrix update"
```

---

## Self-Review (completed)

- **Spec coverage:** PP-CCOEF1 target reparametrization → Tasks 2–5; falsification gate → Task 3; area-noise risk → Task 4. PP-CCOEF2 stage-1 shrinkage → Task 6; stage-2 OOF meta regression → Task 7; selection-bias/coverage guard → Tasks 7–8; comparison base v0.2 → Tasks 2,7. All spec sections mapped.
- **Placeholder scan:** No TBD/TODO; every code step shows full code; summary tasks specify exact numbers-source files.
- **Type consistency:** `ln_coef` defined in Task 1, consumed in Tasks 2,6; `predict_price_log` returns `coef+log(area)` (Task 2) and reused identically in Tasks 3,4,7; `build_coef_table` columns (`artist_key,n_works,raw_coef,shrunk_coef`) consumed unchanged in Task 7; `META` list defined once in Task 7. Consistent.
- **Note:** The artist-holdout gate (Task 3) and final fixed-test number (Task 2) are separated so candidate selection never reads the fixed test — enforced by the plan's task ordering.
