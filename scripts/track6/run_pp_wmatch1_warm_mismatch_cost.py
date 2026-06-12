import importlib.util, sys, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0,'scripts/track6')
from run_pre_pp_experiments import artifact_features, load_scope
_s=importlib.util.spec_from_file_location("cgrp","scripts/track6/run_pp_cgrp1_cold_group_price_stats_base.py"); cgrp=importlib.util.module_from_spec(_s); _s.loader.exec_module(cgrp)
_s3=importlib.util.spec_from_file_location("cb3","scripts/track6/run_pp_cboost3_cold_hetero_blend_gate_retry.py"); cb3=importlib.util.module_from_spec(_s3); _s3.loader.exec_module(cb3)
_s1=importlib.util.spec_from_file_location("cb1","scripts/track6/run_pp_cboost1_cold_base_training_axis.py"); cb1=importlib.util.module_from_spec(_s1); _s1.loader.exec_module(cb1)
feats=artifact_features()['cold_lightgbm']
train,_,wtest=load_scope('warm', feats+['medium_support_bucket'])
need=list(dict.fromkeys(feats+['medium_support_bucket','ln_price_krw','log_area','price_krw','artist_key']))
train=train[need].reset_index(drop=True); wtest=wtest.reset_index(drop=True)
price=wtest['price_krw'].to_numpy(dtype=float)
rng=np.random.default_rng(20260612)
base=list(cgrp.LADDER)
cgrp.LADDER=[(["artist_key","medium_support_bucket","size_bucket"],1),(["artist_key","size_bucket"],1),(["artist_key"],1)]+base
tr_s=cgrp.train_with_internal_stats(train)
# 모델 1회 학습 (정상 데이터)
num_c=cb3.NUM_BASE+cgrp.GRP_FULL  # 대표 구성 1개만 사용해 단순화
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import HuberRegressor
tr_s['grp_price_proxy']=tr_s['grp_unit_area_median']+tr_s['log_area'].clip(lower=0)
pipe=Pipeline([("prep",ColumnTransformer([("num",Pipeline([("i",SimpleImputer(strategy="median")),("s",StandardScaler())]),num_c),("cat",OneHotEncoder(handle_unknown="ignore"),cb3.CAT_C)])),("m",HuberRegressor(epsilon=1.35,alpha=1e-4,max_iter=4000))])
pipe.fit(tr_s[num_c+cb3.CAT_C], tr_s['ln_price_krw'].to_numpy(dtype=float))
arts=train['artist_key'].astype(str).unique()
bucket_mode=train.groupby('artist_key')['medium_support_bucket'].agg(lambda s:s.mode().iloc[0])
def eval_with_keys(keys):
    q=wtest.copy(); q['artist_key']=keys
    qs=cgrp.assign_group_stats(train,q)
    qs['grp_price_proxy']=qs['grp_unit_area_median']+qs['log_area'].clip(lower=0)
    return cb1.mt(price, np.asarray(pipe.predict(qs[num_c+cb3.CAT_C]),dtype=float))
true_keys=wtest['artist_key'].astype(str).to_numpy()
rand_keys=np.array([rng.choice(arts[arts!=a]) for a in true_keys])
# 같은 장르(버킷) 내 혼동 — 그럴듯한 오매칭
bk=wtest['medium_support_bucket'].astype(str).to_numpy()
pool={b:[a for a in arts if str(bucket_mode.get(a,''))==b] for b in set(bk)}
sim_keys=np.array([rng.choice([x for x in pool.get(b,[a]) if x!=a] or [rng.choice(arts)]) for a,b in zip(true_keys,bk)])
out={'correct_match':eval_with_keys(true_keys),'wrong_random_artist':eval_with_keys(rand_keys),'wrong_same_genre_artist':eval_with_keys(sim_keys)}
cgrp.LADDER=base
print(json.dumps({k:{m:round(v,4) for m,v in r.items()} for k,r in out.items()}, ensure_ascii=False, indent=1))
