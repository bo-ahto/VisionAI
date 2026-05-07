# 03. Causal DAG — 1차 시장 가격 인과 구조

> **상태**: DRAFT (코덱스 12차 자문 결과 기반)
> **목적**: 식별 가능한 효과 vs 단순 상관관계 분리 + 본 트랙 모델의 식별 정당화

## 1. DAG 초안 (코덱스 12차 자문)

```
                    [artist_latent_quality]
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
        ▼                 ▼                  ▼
[gallery_tier]    [followers/reputation]   [medium choice]
        │                 │                  │
        │                 │                  │
        ▼                 ▼                  ▼
   [buyer pool]      [demand]         [production cost]
   [certification]                    [demand segment]
        │                 │                  │
        └─────────────────┼──────────────────┘
                          │
                          ▼
                       [PRICE]
```

추가 직접 effect:
- `size (area_cm2) ──▶ price` (production cost + buyer demand)
- `year_made ──▶ price` (vintage / freshness premium)
- `support (canvas/paper/...) ──▶ price` (medium-related cost / status)

## 2. 변수별 인과 식별 가능성

### Tier A — 식별 가능 (within-artist control)

#### `area_cm2 (size) → price`
- **Confound**: artist preference for size (some artists work big)
- **식별 design**: artist FE 통제 → within-artist size variation
- **식별 강도**: 강 (작가별 작품 충분 시)
- **Caveat**: 같은 작가 내 size 가 limited variation 인 경우 약 식별

#### `year_made → price`
- **Confound**: 작가 역량 시간에 따라 변화 (career stage)
- **식별 design**: artist FE + career_stage 통제
- **식별 강도**: 중
- **Caveat**: 작가 1-2건 작품은 식별 불가

#### `medium → price` (within-artist within-size)
- **Confound**: artist style 선호 (latent), 시기적 변화
- **식별 design**: artist FE + size band FE + medium FE
- **식별 강도**: 중-약 (작가별 medium variation 작음)

### Tier B — 약한 식별 (cross-artist comparison 필요)

#### `gallery_tier → price`
- **핵심 confound**: **Selection bias**
  - "Better artists get into better galleries"
  - 즉 gallery_tier 와 artist_latent_quality 강 상관
- **식별 어려움**: artist FE 통제 시 → gallery_tier coefficient = "같은 작가가 다른 갤러리에 걸친 사례에서만"
- **데이터 한계**: 대부분 작가는 1 gallery, switch 사례 적음
- **권고**: descriptive coefficient 만 보고, **causal claim X**

#### `gallery_city / international → price`
- **Confound**: 시장 접근성 (서울 vs 지방), buyer pool size
- **식별 design**: gallery FE 통제 후 잔차
- **식별 강도**: 약

### Tier C — 식별 불가 (현재 데이터로)

#### `followers (reputation) → price`
- **핵심 confound**: **Reverse causality**
  - High price → press coverage → followers
  - 즉 followers 가 가격을 올리는 게 아니라 가격이 followers 를 끄는 것
- **식별 어려움**:
  - **Lagged followers (2년 전 snapshot)** 있어야 약 식별 가능
  - 현재 데이터: 시점 동시 → causal claim 불가
- **권고**: predictive feature 으로만 사용, "reputation effect" claim X

#### `medium choice → price` (cross-artist)
- **Confound**: artist demand segment 의 medium 선호
- **식별 어려움**: medium 자체가 작가 의도 / 시장 기대 반영
- **권고**: 가격 예측에 사용, 효과는 descriptive

## 3. 식별 가능성 등급표 (Week 4 final report 용)

| 변수 | Tier | 식별 design | 강도 | Causal claim 가능성 |
|---|---|---|---|---|
| log(area_cm2) | A | artist FE | 강 | ✅ "size elasticity" |
| year_made | A | artist FE + age | 중 | ✅ "vintage effect" (artist 통제 후) |
| medium dummies | A | artist FE + size band | 중-약 | ⚠️ "within-artist medium effect" |
| support_factor | A | artist FE + medium | 약 | ⚠️ associational |
| career_stage | A-B | age × stage | 중 | ⚠️ Galenson 의 career-curve |
| log(followers) | C | — | — | ❌ "reputation correlate" only |
| gallery_tier | B | artist FE (제한적) | 약 | ❌ "associational, selection bias" |
| has_seoul / has_intl | B | gallery FE | 약 | ❌ associational |
| source (Artsy/Saatchi) | B | — | — | ❌ "platform difference" |

✅ = causal claim 가능 (within-artist)
⚠️ = within-restricted causal (caveat 명시)
❌ = associational only (predictive 가치만)

## 4. Identifying assumptions (mixed-effects 모델)

### Model
```
log P_{ij} = α + β'X_{ij} + u_{a(i)} + v_{g(j)} + ε_{ij}
```

### Assumptions
1. **Conditional Independence (CIA)**: `ε_{ij} ⊥ X_{ij} | u_{a(i)}, v_{g(j)}`
   - artist FE + gallery FE 통제 후 X 와 ε 독립
   - **위반 가능성**: omitted variable 존재 시 (e.g. 국제 reputation, marketing budget)
2. **Random Effect Independence**: `u_{a(i)} ⊥ X_{ij}` (RE 의 strict 가정)
   - 위반 시: artist 의 latent quality 가 X (e.g. medium choice) 에 영향 → fixed effect 사용 권고
3. **Linearity**: log-linear 가정 (`log P = β'X + ...`)
   - 검증: residual plot, Box-Cox lambda

### Robustness check
- Fixed effects (within-artist) 모델과 비교: `β` 가 RE 와 비슷하면 CIA OK 신호
- Hausman test: RE vs FE
- Cluster-robust SE (cluster on artist): valid β SE

## 5. Within-artist design (코덱스 권고: 가장 현실적)

### Specification
```
log P_{it} = α_i + β'X_{it} + γ_t + ε_{it}
```

- `α_i`: artist fixed effect (작가별 절편)
- `γ_t`: 시점 fixed effect (year_made)
- `β`: 식별 가능한 effect (within-artist within-time)

### 데이터 요건
- 작가별 ≥ 2 작품 (within-artist variation)
- 우리 데이터: median ~ 5 works/artist (N=1,240) — 충분

### 한계
- 1-2 work 작가: identifiable variation X → drop or RE shrinkage
- Time-invariant artist trait (gender, country): identification 안됨 (FE 흡수)

## 6. Sensitivity / robustness checks

### Oster (2019) bounds
- Coefficient stability across model specifications
- "How big would unobserved confounding be to nullify β?" 의 boundary

### Within-artist within-medium robustness
- 같은 작가 같은 medium 작품 비교 → size, year, support 의 더 강한 식별

### Switcher analysis (gallery effect)
- 다 갤러리 전시한 작가 subsample 만 분석
- Gallery FE coefficient 가 cross-section 결과와 일치하는지

### Sample selection check
- Saatchi vs Artsy 차이가 학습 sample 의 selection bias 인지 source effect 인지 분리

## 7. 본 트랙의 인과 framing 결론 (Week 4 report)

### 명시할 입장
> "본 모델은 미술품 가격의 attribute 별 hedonic decomposition 을 제공한다. Within-artist FE 를 활용한 size, year, medium 의 식별은 학술 표준에 가깝다. 다만 gallery_tier, reputation 의 효과는 **현재 cross-section 데이터 + observational design 의 한계로 causal interpretation 을 약화** 시킬 수밖에 없다. 향후 lagged data + repeated sales / IV design 이 가능해지면 강한 식별로 진화 가능하다."

### What this paper does
- Hedonic price function 의 partial elasticity 추정
- Artist / gallery 의 variance decomposition
- Cold-start vs warm regime 비교

### What this paper does not do
- Strong causal identification of gallery effect
- Reputation 의 causal direction
- Counterfactual price prediction (e.g. "if same work in better gallery")

## 8. 향후 확장 (논문 작성 시)

### IV candidates (현재 구체화 어려움)
- `gallery_tier` IV: 갤러리 설립연도? 회원사 여부? — weak instrument 위험
- `reputation` IV: 외부 review (Artsy editorial) lag — 현재 데이터 없음

### Repeated sales (cross-time)
- 같은 작품의 1차 → 2차 (auction) 가격 변동
- 우리 데이터: 1차 시장만 (auction 분리됨)
- 향후 통합 시 확장 가능

### Quasi-experimental design
- COVID 전후 가격 변동 (2019-2021)
- 환율 충격 시점 (KRW depreciation 2022-2023)
- 본 트랙 외 후속 연구 가능성

## 9. 다음 액션

### Week 1
- 본 DAG 를 graphviz 또는 dagitty.net 에 업로드해서 visual 산출
- 식별 등급표 (위 §3) 를 Week 2 OLS 결과와 비교 가능하게 준비

### Week 2-3
- Within-artist FE 모델과 RE 모델 결과 비교
- Hausman test 수행

### Week 4
- §7 의 framing 을 final report 에 명시
- §3 등급표 완성 (실제 estimated coefficient 와 함께)
- §8 의 향후 확장 plan 작성
