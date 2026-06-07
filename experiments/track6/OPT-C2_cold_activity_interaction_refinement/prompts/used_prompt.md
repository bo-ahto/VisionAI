# OPT-C2 Cold 활동량/인지도 상호작용 최적화 프롬프트

- 목적: A~J 실험에서 Cold 성능이 좋았던 `작품 기본 피처 + 활동량/인지도`, `활동량/인지도 x 면적`, `활동량/인지도 x 호수` 조합을 결합해 신규 작가 예측 성능의 최대치를 확인한다.
- 데이터: `data/track6_split_with_year_type_edition_size_artist_name` 고정 split 전체 사용.
- 학습/평가 연결 키: `_track6_row_id`.
- 라벨 사용: `*_labels.csv`는 학습 target과 평가 지표 계산에만 사용한다.
- 누수 방지: 가격 컬럼은 피처 파일에 넣지 않는다.
- 공통 코드: `scripts/track6/fixed_variable_experiment_runner.py`.
- 모델: Warm `Huber`, `Linear Regression`, `Ridge`; Cold `Huber`, `Quantile-LAD`, `LightGBM`.
- 숫자형 처리: 숫자형 피처는 문자열/one-hot으로 처리하지 않고 중앙값 결측 보정 후 `StandardScaler`를 적용한다.
- 주요 판단 지표: Cold `MdAPE` 1순위, `p95_APE`, `Within_30`, `RMSE_log`, `R2` 보조 확인.
- 비교 조합:
  - `작품 기본 피처 + 활동량/인지도 + 결측 flag`
  - `작품 기본 피처 + 활동량/인지도 + 정보량`
  - `위 조합 + 활동량/인지도 x 면적`
  - `위 조합 + 활동량/인지도 x 호수`
  - `위 조합 + 면적/호수 상호작용 전체`
  - `위 조합 + 기본 작가 프로필/전시`
