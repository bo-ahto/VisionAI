# Track 3 — Depth Feature Ablation 코드 공유

이 디렉토리는 미술 작품 가격 예측에서 깊이(depth) 정보가 모델 성능에 미치는 영향을
측정한 ablation 실험 코드를 담고 있다.

## 파일 구성

| 파일 | 설명 |
|---|---|
| `track3_depth_ablation.py` | 실험 코드 (4 variant 비교) |
| `README.md` | 이 파일 |

## 전제 조건

- Python 3.10+
- 패키지: `pandas`, `numpy`, `scikit-learn`, `lightgbm`
- 데이터: `data/release_split/track3_train.csv`, `track3_test_warm.csv`, `track3_test_cold.csv`
  (별도 zip으로 공유: `data/track3_release_split_v1.zip`)

## 실험 설계

### 4가지 Variant

| Variant | depth_cm | has_depth | 의미 |
|---|---:|---:|---|
| **D_none** | ✗ | ✗ | 깊이 정보 없음 (baseline) |
| **A_has** | ✗ | ✓ | 깊이 유무만 (binary) |
| **B_cm** | ✓ | ✗ | 실제 깊이 cm만 (실수) |
| **C_both** | ✓ | ✓ | 둘 다 |

### 평가 Protocol

- **Cold-start**: `test_cold` (3,823건, 완전 신규 작가) — LAD 모델 사용
- **Warm-start**: `test_warm` (1,685건, 학습된 작가의 신규 작품) — Tuned LightGBM 사용
- 모든 transform fit은 **train 데이터만** 사용 (leakage 방지)

### Metric

- **median APE**: 핵심 지표 (작을수록 좋음, outlier robust)
- **W30 (Within-30%)**: 실용 정확도 (클수록 좋음)
- **MAPE, RMSE_log**: 보조 지표

## 사용법

```bash
# 데이터 압축 풀기
unzip track3_release_split_v1.zip -d data/

# 실험 실행 (예상 시간: 5-10분)
python3 track3_depth_ablation.py
```

## 결과 (재현)

```
Variant       Cold med_APE   Cold W30  Warm med_APE   Warm W30
D_none              0.3277     0.4562        0.2291     0.5810
A_has               0.3177     0.4842        0.2173     0.5792
B_cm                0.3207     0.4640        0.2056     0.5988
C_both              0.2925     0.5085        0.2056     0.5988
```

### 주요 발견

1. **C_both가 overall best** — Cold med_APE -3.5%p, Warm -2.4%p 개선
2. **2D 작품에서 has_depth 부작용** — Cold 2D 0.394 → 0.604 (53% 악화)
3. **회화는 깊이 없는 게 나음** — acrylic/watercolor는 D_none이 가장 좋음
4. **3D 작품(mixed/other)은 깊이가 큰 도움** — depth_cm이 mixed media에서 most informative

### 운영 추천

두 가지 옵션의 trade-off:

- **C_both** — Overall metric 최고, 단 2D 작품에 부작용
- **B_cm** — Robust한 선택, 2D 부작용 없음 + 3D에서 충분히 도움

## 데이터 컬럼 설명

| 컬럼 | 타입 | 의미 |
|---|---|---|
| `artist_name_ko` | str | 작가 한글명 (작가 ID 역할) |
| `medium_category` | str | 매체 카테고리 (oil/acrylic/...) |
| `support_category` | str | 지지대 (canvas/paper/...) |
| `has_depth` | int | 깊이 정보 유무 (0/1) |
| `depth_cm` | float | 실제 깊이 (cm) |
| `width_cm` | float | 가로 (cm) |
| `height_cm` | float | 세로 (cm) |
| `log_area` | float | log(width × height) |
| `estimated_ho` | float | 한국 미술시장 호수 추정 |
| `orientation` | str | 방향 (landscape/portrait/square) |
| `price_krw_unified` | int | 원본 KRW 가격 |
| `ln_price_krw_unified` | float | 학습 target (log price) |

## 라이센스

내부 연구용. 외부 공유 시 출처 명시.
