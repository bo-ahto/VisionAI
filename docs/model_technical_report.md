# VisionAI 1차 시장 가격 예측 모델 기술 보고서

> **작성일**: 2026-04-17
> **모델 버전**: v3 (CatBoost + XGBoost 라우팅)
> **학습 데이터**: 29,361건 / 1,589명 작가
> **대상**: 한국 신진/중견 작가 회화 작품의 1차 시장(갤러리) 가격 예측

---

## 1. 문제 정의

### 1.1 목적

미술 작품의 적정 가격을 산출하는 것은 정보 비대칭이 큰 1차 시장에서 핵심 과제이다. 본 모델은 작품의 물리적 속성(크기, 매체)과 작가의 경력 정보를 기반으로 **갤러리 리스팅 가격**을 예측한다.

### 1.2 수학적 정의

작품 $i$의 가격을 $P_i$ (KRW)라 하면, 예측 문제는 다음과 같다:

$$\hat{P}_i = f(\mathbf{x}_i; \theta)$$

여기서 $\mathbf{x}_i \in \mathbb{R}^{37}$은 37차원 피처 벡터, $\theta$는 모델 파라미터.

가격 분포는 강한 양의 왜도(right-skewed)를 보이므로, 로그 변환을 적용한다:

$$y_i = \ln(P_i)$$

예측 모델은 $y_i$를 타겟으로 학습하며, 최종 가격은 역변환으로 구한다:

$$\hat{P}_i = \exp(\hat{y}_i)$$

### 1.3 평가 지표

**MdAPE (Median Absolute Percentage Error)**:

$$\text{MdAPE} = \text{median}\left(\left|\frac{\hat{P}_i - P_i}{P_i}\right| \times 100\right)$$

MdAPE를 사용하는 이유: 가격 분포가 극단적으로 왜곡되어(평균 993만원, 중앙 414만원) 평균 기반 MAPE보다 중앙값 기반 MdAPE가 모델의 "일반적 성능"을 더 정확히 반영한다.

**W30 (Within 30% Error Rate)**:

$$\text{W30} = \frac{1}{N}\sum_{i=1}^{N}\mathbb{1}\left[\left|\frac{\hat{P}_i - P_i}{P_i}\right| \leq 0.3\right] \times 100$$

---

## 2. 가격 결정 이론적 배경

### 2.1 헤도닉 가격 모델 (Hedonic Price Model)

미술품 가격은 Rosen(1974)의 헤도닉 가격 이론에 기반하여 분해할 수 있다 (Lancaster(1966)의 특성이론을 가격 결정에 적용):

$$\ln(P) = \alpha + \sum_{k=1}^{K}\beta_k x_k + \epsilon$$

여기서 $x_k$는 가격에 영향을 주는 특성(크기, 매체, 작가 명성 등), $\beta_k$는 각 특성의 한계 가격 기여도.

### 2.2 한국 미술 시장의 호당 가격제 (號當 價格制)

한국 1차 시장에서는 전통적으로 **호당 가격제**가 사용된다:

$$P = \alpha \cdot H^{\beta}$$

여기서 $H$는 호수(캔버스 번호), $\alpha$는 작가별 호당 기준가, $\beta$는 크기 탄력성.

본 연구의 실증 분석 결과:

| 항목 | 값 | 의미 |
|------|:---:|------|
| $\beta$ (전체) | 0.817 | 호수 1% 증가 시 가격 0.82% 증가 |
| $\beta$ (KRW 작품) | 0.749 | 원화 작품은 크기 탄력성이 낮음 |

$\beta < 1$은 **크기에 대한 수확 체감**을 의미한다. 즉, 호수가 2배가 되어도 가격은 2배가 되지 않고 약 1.76배($2^{0.817}$)가 된다.

### 2.3 작가 프리미엄 (Artist Premium)

동일 크기/매체라도 작가에 따라 가격이 크게 달라진다. 이를 **작가 프리미엄** $\alpha_j$로 표현한다:

$$\ln(P_{ij}) = \alpha_j + \beta \ln(H_i) + \gamma \mathbf{z}_i + \epsilon_{ij}$$

여기서 $\alpha_j$는 작가 $j$의 고유 효과, $\mathbf{z}_i$는 매체/지지체 등 작품 속성.

본 모델에서 작가 프리미엄은 명시적으로 추정하지 않고, GBDT(Gradient Boosted Decision Trees)가 **작가별 작품수, 팔로워, 전시 이력** 등의 피처를 통해 암묵적으로 학습한다.

---

## 3. 피처 엔지니어링

37개 피처를 5개 카테고리로 분류한다.

### 3.1 크기 피처 (9개, 중요도 합계 21.1%)

| 피처 | 수식 | 중요도 | 설명 |
|------|------|:------:|------|
| `ho` | $H = \arg\min_h |A - A_h^{ref}|$ | 1.63% | F형 기준 호수 |
| `ho_power` | $H^{0.74}$ | 1.99% | 호당 가격제 비선형 보정 |
| `ln_ho` | $\ln(H+1)$ | 3.13% | 로그 호수 |
| `area_cm2` | $W \times H$ (cm²) | 5.67% | 면적 |
| `ln_area` | $\ln(A)$ | 3.75% | 로그 면적 |
| `aspect_ratio` | $\frac{\max(W,H)}{\min(W,H)}$ | 1.46% | 종횡비 |
| `is_small` | $\mathbb{1}[H \leq 3]$ | 0.73% | 소품 여부 |
| `support_factor` | 지지체별 계수 | 0.68% | 캔버스=1.0, 종이=0.8, 리넨=1.1 |
| `ho_x_support` | $H \times f_{support}$ | 2.05% | 호수×지지체 교차항 |

**호수 변환 원리**:

한국 표준 캔버스 크기(F형)의 참조 면적 테이블을 사용한다:

| 호수 | 면적(cm²) | 대략 크기 |
|:----:|:---------:|----------|
| 1 | 364 | 22×16cm |
| 10 | 2,412 | 53×46cm |
| 20 | 4,304 | 73×61cm |
| 50 | 9,128 | 117×91cm |
| 100 | 21,245 | 162×130cm |

입력된 가로×세로에서 면적을 계산하고, 가장 가까운 참조 면적의 호수를 할당한다:

$$H = \arg\min_{h \in \mathcal{H}} |W_{cm} \times H_{cm} - A_h^{ref}|$$

여기서 $\mathcal{H} = \{0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150, 200, 300, 500\}$은 F형 표준 캔버스 번호 집합 (24개).

**`ho_power` (0.74 거듭제곱)**:

실증 분석에서 가격-호수 관계의 탄력성이 약 0.74~0.82로 추정되었다. 이를 반영하여:

$$\text{ho\_power} = H^{0.74}$$

이 변환은 큰 호수에서의 가격 증가 둔화를 직접 반영한다. 예:

| 호수 | ho_power | 해석 |
|:----:|:--------:|------|
| 10 | 5.5 | 기준 |
| 20 | 9.3 | 호수 2배 → ho_power 1.7배 |
| 50 | 18.7 | 호수 5배 → ho_power 3.4배 |
| 100 | 30.2 | 호수 10배 → ho_power 5.5배 |

**`support_factor` (지지체 계수)**:

동일 호수라도 지지체에 따라 가격이 다르다. 학습 데이터에서 추정한 상대적 가격 계수:

$$f_{support} = \begin{cases} 1.0 & \text{캔버스} \\ 1.1 & \text{리넨} \\ 0.8 & \text{종이} \\ 0.9 & \text{패널} \\ 0.85 & \text{기타} \end{cases}$$

**`aspect_ratio` (종횡비)**:

$$r = \frac{\max(W,H)}{\min(W,H)}$$

정사각형($r \approx 1.0$)과 극단적 직사각형($r > 2.0$)은 가격에 다른 영향을 준다. 한국 전통 캔버스 타입과의 관계:

| 타입 | 종횡비 | 용도 |
|:----:|:------:|------|
| S (정방형) | ~1.0 | 정사각 |
| F (인물형) | 1.0~1.25 | 인물화 |
| P (풍경형) | 1.25~1.45 | 풍경화 |
| M (해경형) | 1.45+ | 파노라마 |

### 3.2 작가 피처 (8개, 중요도 합계 68.2%)

| 피처 | 수식 | 중요도 | 설명 |
|------|------|:------:|------|
| `artist_total_works` | 원본값 | 37.09% | 플랫폼 등록 총 작품수 |
| `ln_followers` | $\ln(F+1)$ | 9.97% | 로그 팔로워 |
| `profile_completeness` | $\sum \mathbb{1}[x_k \neq \emptyset]$ | 8.41% | 프로필 충실도 (0~3) |
| `artist_birth_year` | 원본값 | 7.14% | 출생 연도 |
| `has_birth_year` | $\mathbb{1}[\text{birth\_year} \neq \text{null}]$ | 2.24% | 생년 존재 여부 |
| `career_stage` | 1~4 | 1.77% | 경력 단계 |
| `for_sale_ratio` | $\frac{N_{sale}}{N_{total}}$ | 0.82% | 판매중 비율 (서빙 시 기본값 1.0) |
| `career_age` | $2026 - Y_{first}$ | 0.77% | 경력 연수 (서빙 시 기본값 0, 외부 수집으로 보강) |

**`artist_total_works` (총 작품수) — 모델 최대 기여 피처 (37.1%)**:

이 피처가 가장 중요한 이유는, 작품수가 **작가의 시장 활동 규모**를 직접 반영하기 때문이다. Artsy에 150건 등록된 작가와 5건 등록된 작가는 시장 접근성과 인지도가 근본적으로 다르다.

또한 이 피처는 **데이터 소스를 암묵적으로 구분**하는 역할도 한다:
- Artsy 작가: 평균 55건 (갤러리 기반)
- Saatchi 작가: 평균 201건 (온라인 직거래, 대량 등록)

모델은 총 작품수가 많으면 Saatchi 스타일(저가)로, 적으면 Artsy 스타일(고가)로 예측하는 패턴을 학습했다.

**`ln_followers` (로그 팔로워)**:

팔로워 수는 극단적으로 왜곡되어 있어 로그 변환을 적용한다:

$$\text{ln\_followers} = \ln(F + 1)$$

$+1$은 팔로워 0인 작가의 로그 발산을 방지한다.

| ln_followers | 실제 팔로워 | 가격 영향 |
|:------------:|:----------:|----------|
| 0 | 0 | 기준 |
| 2.3 | ~10 | 소폭 상승 |
| 4.6 | ~100 | 의미 있는 상승 |
| 6.9 | ~1,000 | 큰 상승 |

**`profile_completeness` (프로필 충실도)**:

소스에 따라 구성이 다르다:

$$\text{PC}_{Artsy} = \mathbb{1}[\text{birth\_year} \neq \emptyset] + \mathbb{1}[\text{shows} > 0] + \mathbb{1}[\text{bio} \neq \emptyset]$$

$$\text{PC}_{Saatchi} = \mathbb{1}[\text{bio} \neq \emptyset] + \mathbb{1}[\text{education} \neq \emptyset] + \mathbb{1}[\text{exhibitions} \neq \emptyset]$$

이 피처의 높은 중요도(8.41%)는 흥미로운 발견이다. **"프로필을 성실히 작성하는 작가"가 더 높은 가격을 받는** 경향이 있는데, 이는 프로필 충실도가 작가의 전문성과 시장 참여도의 프록시(proxy) 역할을 하기 때문이다.

**`has_birth_year` (생년 존재 여부)**:

생년 자체의 값(7.14%)뿐 아니라 **생년이 있는지 없는지**(2.24%)도 중요한 피처이다. 이는:
- 생년 있음 → Artsy(갤러리 기반, 고가 경향)
- 생년 없음 → Saatchi(온라인 직거래, 저가 경향)

라는 **데이터 소스 식별** 역할을 하기 때문이다.

**`career_stage` (경력 단계)**:

$$\text{stage} = \begin{cases} 4 & \text{age} \geq 60 \wedge \text{solo} \geq 5 \quad (\text{원로}) \\ 3 & \text{solo} \geq 3 \quad (\text{중견}) \\ 2 & \text{solo} \geq 1 \vee \text{group} \geq 5 \quad (\text{신진후기}) \\ 1 & \text{otherwise} \quad (\text{신진}) \end{cases}$$

**생년-가격 관계 실증**:

| 출생 연대 | 가격 중앙 | 해석 |
|:---------:|:---------:|------|
| 1920~1940 | 4,416만원 | 원로 작가 프리미엄 |
| 1940~1960 | 2,070만원 | 중견 |
| 1960~1970 | 704만원 | 중견~신진후기 |
| 1970~1980 | 690만원 | |
| 1980~1990 | 307만원 | 신진 |
| 1990~2000 | 207만원 | 신진 |
| 2000~2010 | 110만원 | 초신진 |

한 세대(10년) 차이가 약 **1.5~2배** 가격 차이를 만든다.

### 3.3 갤러리/소스 피처 (6개, 중요도 합계 2.5%)

| 피처 | 중요도 | 설명 |
|------|:------:|------|
| `gallery_name` | 1.50% | 갤러리명 (categorical) |
| `gallery_tier` | 0.30% | 갤러리 등급 (1~5) |
| `has_seoul` | 0.46% | 서울 소재 여부 |
| `gallery_city_count` | 0.11% | 갤러리 도시 수 |
| `has_international` | 0.04% | 국제 전시 여부 |
| `gallery_type` | 0.03% | 갤러리 유형 |

### 3.4 작품 속성 피처 (4개, 중요도 합계 0.6%)

| 피처 | 중요도 | 설명 |
|------|:------:|------|
| `work_age` | 0.30% | 작품 연령 (2026 - 제작연도) |
| `has_depth` | 0.25% | 3D 여부 |
| `is_unique` | 0.00% | 원작 여부 |
| `is_edition` | 0.00% | 에디션 여부 |

### 3.5 컨텍스트 피처 (8개, 중요도 합계 7.7%)

| 피처 | 중요도 | 설명 |
|------|:------:|------|
| `ho_price_level` | 2.93% | 호수별 가격 중앙값 매핑 |
| `medium_price_level` | 1.69% | 매체별 가격 중앙값 매핑 |
| `medium_category` | 1.68% | 매체 카테고리 (categorical) |
| `support_type` | 1.00% | 지지체 유형 (categorical) |
| `source` | 0.06% | 데이터 소스 (artsy/saatchi) |
| `price_currency` | 0.11% | 가격 통화 |
| `is_krw` | 0.02% | 원화 여부 |

**`ho_price_level` / `medium_price_level` (가격 레벨 매핑)**:

학습 데이터에서 호수별/매체별 가격 중앙값을 사전 계산하여 피처로 사용한다:

$$\text{ho\_price\_level}_i = \text{median}_{j \in \{H_j = H_i\}} \ln(P_j)$$

이는 **target encoding**의 변형으로, 모델이 "이 호수/매체의 일반적 가격 수준"을 직접 참조할 수 있게 한다.

---

## 4. 모델 아키텍처

### 4.1 GBDT (Gradient Boosted Decision Trees)

본 모델은 **CatBoost**와 **XGBoost** 두 가지 GBDT 앙상블을 사용한다.

GBDT의 기본 원리:

$$\hat{y}_i^{(t)} = \hat{y}_i^{(t-1)} + \eta \cdot h_t(\mathbf{x}_i)$$

여기서:
- $\hat{y}_i^{(t)}$: $t$번째 부스팅 라운드의 예측값
- $\eta$: 학습률 (learning rate)
- $h_t$: $t$번째 약한 학습기 (결정 트리)

각 라운드에서 잔차(residual)를 학습한다:

$$h_t = \arg\min_{h} \sum_{i=1}^{N} L(y_i, \hat{y}_i^{(t-1)} + h(\mathbf{x}_i))$$

$$L(y, \hat{y}) = (y - \hat{y})^2 \quad \text{(MSE, regression)}$$

### 4.2 CatBoost 특성

CatBoost(Prokhorenkova et al., 2018)는 categorical 피처를 **ordered target statistics**로 인코딩한다:

$$\hat{x}_{i,k} = \frac{\sum_{j < \sigma(i)} \mathbb{1}[x_{j,k} = x_{i,k}] \cdot y_j + a \cdot P}{\sum_{j < \sigma(i)} \mathbb{1}[x_{j,k} = x_{i,k}] + a}$$

여기서 $\sigma$는 무작위 순열, $a$는 smoothing 파라미터, $P$는 사전 확률.

이 방식의 장점:
- target leakage 방지 (자기 자신의 타겟을 사용하지 않음)
- 7개 categorical 피처 (gallery_name, medium_category 등)를 자연스럽게 처리

### 4.3 모델 라우팅

```
입력 작품
  │
  ├─ 학습 작가 매칭 (training_count ≥ 5)?
  │   ├─ Yes → XGBoost v3
  │   │       (작가 패턴 학습, MdAPE 11.7%)
  │   └─ No  → CatBoost v3
  │           (categorical 피처 강점, MdAPE 38.9%)
  │
  └─ Source ratio 보정 (Cold Start만)
      ln_price += correction[target_market]
```

**XGBoost를 학습 작가에 사용하는 이유**: XGBoost는 수치 피처의 비선형 분할에 강하고, 학습된 작가의 작품수/팔로워 등 수치 피처가 풍부할 때 CatBoost보다 우수한 성능을 보였다 (KFold MdAPE: XGBoost 11.7% vs CatBoost 17.1%).

**CatBoost를 Cold Start에 사용하는 이유**: 미학습 작가는 수치 피처가 부족하고 categorical 피처(매체, 갤러리, 소스)에 의존해야 하는데, CatBoost의 ordered target statistics가 이 상황에서 더 안정적이다.

### 4.4 하이퍼파라미터

아래는 GroupKFold 평가 시 사용된 학습 파라미터이다. 최종 저장된 모델 아티팩트의 내부 파라미터와는 차이가 있을 수 있다 (early stopping으로 실제 트리 수가 다를 수 있음).

| 파라미터 | CatBoost v3 | XGBoost v3 |
|----------|:-----------:|:----------:|
| iterations / num_boost_round | 1,500 (early stop) | 1,500 (early stop) |
| depth / max_depth | 8 | 6 |
| learning_rate | 0.03 | 0.03 |
| l2_leaf_reg / reg_lambda | 3 | 5 |
| min_data_in_leaf / min_child_weight | 20 | 30 |

> 모델 아티팩트의 정확한 내부 파라미터는 `model_test_results/integrated_v3_catboost.cbm` 및 `integrated_v3_xgboost.json`에서 확인 가능.

### 4.5 Source Ratio 보정

학습 데이터에 Artsy(갤러리, 고가)와 Saatchi(온라인 직거래, 저가)가 혼합되어 있어, Cold Start 예측 시 소스별 체계적 편향이 발생한다.

Saatchi 학습 데이터의 median ratio 1.078 (7.8% 과대 예측)을 사후 보정한다:

$$\ln(\hat{P}_{corrected}) = \ln(\hat{P}_{raw}) + c_{market}$$

$$c_{market} = \begin{cases} 0.0 & \text{gallery} \\ -0.075 & \text{online} \end{cases}$$

여기서 $0.075 = \ln(1.078)$, 실험에서 측정된 Saatchi 편향의 로그값.

---

## 5. 학습 및 평가

### 5.1 교차 검증 설계

**GroupKFold** (작가 단위 분할, K=5):
- 작가 $j$의 모든 작품을 같은 fold에 배치
- Cold Start 시뮬레이션: 검증 fold의 작가는 학습에 전혀 포함되지 않음
- **가장 현실적인 평가**: 새 작가의 작품 가격을 예측하는 실제 상황과 동일

**KFold** (무작위 분할, K=5):
- 동일 작가의 작품이 학습/검증에 분산
- 학습된 작가의 새 작품 예측 성능 평가

### 5.2 성능 결과

| 평가 | 모델 | MdAPE | W30 |
|------|------|:-----:|:---:|
| **KFold (학습 작가)** | **XGBoost** | **11.7%** | **78.8%** |
| KFold | CatBoost | 17.1% | 70.1% |
| GroupKFold (Cold Start) | CatBoost | 38.9% | 39.9% |
| GroupKFold | XGBoost | 39.4% | 40.1% |

### 5.3 가격대별 성능 (GroupKFold, CatBoost 단독)

> 아래 수치는 29,361건 전체에 대한 CatBoost GroupKFold 5-Fold OOF 평가 결과.

| 가격대 | MdAPE | 비율 | W30 | 건수 | 해석 |
|--------|:-----:|:----:|:---:|:----:|------|
| ~100만 | 80.9% | 1.81x | 23% | 5,977 | 과대 예측 (학습 중앙값으로 회귀) |
| 100~300만 | 35.8% | 1.26x | 44% | 9,036 | 양호 |
| **300~500만** | **26.2%** | **0.98x** | **55%** | 4,524 | **최적** |
| 500~1천만 | 33.5% | 0.77x | 44% | 4,827 | 양호 |
| 1천~3천만 | 48.3% | 0.56x | 27% | 3,319 | 과소 예측 |
| 3천만+ | 90.8% | 0.09x | 8% | 1,678 | 극과소 (데이터 부족) |

**300~500만원 구간이 가장 정확한 이유**: 통합 학습 데이터의 가격 중앙값(Artsy 414만, Saatchi 256만, 전체 ~300만)과 가장 겹치는 구간이며, 데이터 밀도가 높아 모델이 이 구간의 패턴을 가장 잘 학습했다.

---

## 6. 신뢰도 등급 체계

### 6.1 결정 규칙

```python
def determine_confidence(is_matched, training_count, has_birth_year, has_manual_profile):
    if is_matched and training_count >= 5:
        return ("A", 0.20)   # 높은 신뢰도
    if is_matched and training_count >= 1:
        return ("B", 0.30)   # 보통
    if has_birth_year or has_manual_profile:
        return ("C", 0.50)   # 참고용
    return ("D", 0.70)       # 추정치
```

### 6.2 가격 범위 산출

$$P_{low} = \hat{P} \times (1 - m), \quad P_{high} = \hat{P} \times (1 + m)$$

여기서 $m$은 등급별 마진: A=0.20, B=0.30, C=0.50, D=0.70.

> 이 마진은 교정된 통계적 구간이 아닌, 모델 성능 기반의 경험적 밴드이다.

---

## 7. 외부 정보 수집 파이프라인

### 7.1 수집 아키텍처

미학습 작가 요청 시, Artsy → Saatchi → 웹검색 순서로 작가 프로필을 자동 수집한다.

| 소스 | 방법 | 수집 정보 | 피처 기여 |
|------|------|----------|:---------:|
| Artsy | GraphQL API | 작품수, 팔로워, 전시, 생년 | ~54% |
| Saatchi | Constructor.io + HTML 파싱 | bio, education, exhibitions | ~18% |
| 웹검색 | DuckDuckGo | 생년 (보완) | ~9% |

### 7.2 웹검색 동명이인 처리

동명이인 오매칭은 **자신있게 틀린 예측**을 생산하므로 엄격한 5단계 필터를 적용한다:

1. 검색어에 `작가 회화` 한정어 포함
2. 미술 키워드 확인 + 비미술 키워드(배우, 가수) 제외
3. 추출 생년 범위 검증 (1930~2005)
4. **2개 이상 독립 도메인**에서 동일 생년 확인
5. pass/fail 이진 판정 (확률 점수 아닌 확실한 경우만 채택)

### 7.3 수집 효과

| 시나리오 | 등급 | MdAPE (추정) |
|----------|:----:|:-----------:|
| 크기+매체만 | D | ~60% |
| + 생년 | C | ~50% |
| + 작품수/팔로워 | B~C | ~40% |
| 학습 작가 매칭 | A | ~12% |

---

## 8. SHAP 기반 예측 설명

### 8.1 SHAP (SHapley Additive exPlanations)

Lundberg & Lee(2017)의 SHAP 값을 사용하여 각 피처의 예측 기여도를 분해한다:

$$\hat{y}_i = \phi_0 + \sum_{k=1}^{K}\phi_k(\mathbf{x}_i)$$

여기서 $\phi_0$는 기저값(학습 데이터 평균), $\phi_k$는 피처 $k$의 SHAP 값.

기저값 $\phi_0 = 14.966$ ($\approx \exp(14.966) = 317만원$).

### 8.2 기여도 해석

SHAP 값은 log scale이므로, % 기여도로 변환한다:

$$\text{contribution}_k = (\exp(\phi_k) - 1) \times 100\%$$

예시 (Cold Start, 20호 oil on canvas):
- `artist_total_works = 0`: $\phi = -0.274$ → **-24.0%** (작품수 없으면 가격 하락)
- `medium_category = oil`: $\phi = +0.151$ → **+16.3%** (유화 프리미엄)
- `gallery_name = Unknown`: $\phi = +0.158$ → **+17.1%** (미지 갤러리 보정)
- `ln_followers = 0`: $\phi = -0.134$ → **-12.5%** (팔로워 없으면 하락)

---

## 9. 모델 고도화 이력

### 9.1 버전별 실험

| 버전 | 접근법 | MdAPE | 결과 |
|:----:|--------|:-----:|------|
| v2 | Artsy+Artue+Saatchi 단순 통합 | 43.8% | 기준선 |
| **v3** | **+ source 피처 + has_birth_year + profile_completeness** | **38.7%** | **최적** |
| v4 | + 46개 피처 확장 | 40.4% | 과적합 (피처 과잉) |
| v5 | 하이퍼파라미터 탐색 | 39.0% | 한계 (데이터가 병목) |
| v6 | ratio 보정, stacking, source 분리 | 39.0% | 구조적 한계 확인 |

### 9.2 핵심 발견

**효과 있었던 것**:
- `source` 피처 추가 (-5.1%p): 모델이 소스별 가격 수준을 직접 학습
- `has_birth_year` (+2.2% 중요도): 결측 자체가 정보
- `profile_completeness` (+8.4% 중요도): 프로필 성실도 = 가격 프록시

**효과 없었던 것**:
- 피처 수 37→46 확장: 과적합으로 악화
- 하이퍼파라미터 튜닝: <0.5%p 차이
- source별 별도 모델: 통합 모델이 데이터 공유 효과로 우수

**구조적 한계 (~39%)**:
- Cold Start MdAPE가 38~39% 근처에서 수렴
- 원인: 생년 결측 72%, 고가 데이터 부족, 작가 이력 없이 크기/매체만으로 예측하는 한계

---

## 10. 참고 문헌

- Lancaster, K.J. (1966). A new approach to consumer theory. *Journal of Political Economy*, 74(2), 132-157.
- Rosen, S. (1974). Hedonic prices and implicit markets: product differentiation in pure competition. *Journal of Political Economy*, 82(1), 34-55.
- Prokhorenkova, L., et al. (2018). CatBoost: unbiased boosting with categorical features. *NeurIPS*.
- Lundberg, S.M. & Lee, S.I. (2017). A unified approach to interpreting model predictions. *NeurIPS*.
- Chen, T. & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *KDD*.
