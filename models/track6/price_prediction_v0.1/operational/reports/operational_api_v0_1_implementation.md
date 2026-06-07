# 가격 예측 API v0.1 구현 메모

- 구현일: 2026-06-05
- 기준 모델: `price_prediction_v0.1`
- API 서버: `visionai.price_engine.api.operational_v0_1_server:app`
- 운영 모델 패키지: `models/track6/price_prediction_v0.1/operational`

## 1. 구현 범위

| Method | Path | 상태 | 용도 |
| --- | --- | --- | --- |
| GET | `/health` | 구현 | 서버와 모델 로드 상태 확인 |
| GET | `/test/v0.1` | 구현 | 로컬 테스트 프론트 |
| GET | `/test/v0.1/result` | 구현 | 예측 후 결과 화면 URL |
| GET | `/api/v1/price-models/current` | 구현 | 현재 모델 버전, 표시 정책, 환율 기준 조회 |
| POST | `/api/v1/artists:resolve` | 구현 | 작가명/작가키를 v0.1 `artist_key`로 매핑 |
| POST | `/api/v1/artworks/price-estimate` | 구현 | 단일 작품 가격 예측 |

## 2. 운영 기준

- Warm 예측만 v0.1 자동 가격 예측 대상으로 적용
- Cold는 `reference_range_only` 정책으로 두고 자동 가격 예측은 보류
- 서비스 기본 예측값: `service_primary_pred_price_krw`
- 서비스 주 후보: `pp_v8_compact_blend_mape_guarded`
- 가격 범위: L10 quantile q10/q90 기반
- 신뢰도: 유사 작품 표본 수와 quantile 가격 범위 폭 기준

## 3. 실행

```bash
PYTHONPATH=src MPLCONFIGDIR=/private/tmp uvicorn \
  visionai.price_engine.api.operational_v0_1_server:app \
  --host 0.0.0.0 \
  --port 8000
```

## 4. 환경 변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `PRICE_PREDICTION_V01_MODEL_ROOT` | `models/track6/price_prediction_v0.1` | v0.1 모델 루트 경로 |
| `MPLCONFIGDIR` | 없음 | CatBoost/sklearn import 중 matplotlib cache 경고 방지용. 운영 컨테이너에서는 쓰기 가능한 경로 권장 |

## 5. 요청 예시

### 5.0 로컬 테스트 프론트

```text
http://127.0.0.1:8010/test/v0.1
```

- 작가 확인: `/api/v1/artists:resolve` 호출
- 가격 예측: `/api/v1/artworks/price-estimate` 호출
- 결과 영역: 예측 가격, 가격 범위, 신뢰도, 유사 작품 기준, 1차 시장 가격 카드, warning, 원본 JSON 표시

### 5.1 작가 매핑

```bash
curl -X POST http://localhost:8000/api/v1/artists:resolve \
  -H 'Content-Type: application/json' \
  -d '{
    "artist": {
      "name_en": "Seongeun Moon"
    },
    "options": {
      "max_candidates": 5
    }
  }'
```

### 5.2 가격 예측

```bash
curl -X POST http://localhost:8000/api/v1/artworks/price-estimate \
  -H 'Content-Type: application/json' \
  -d '{
    "artwork": {
      "external_artwork_id": "smoke_001",
      "title": "After The Flight",
      "artist": {
        "artist_key": "seongeun moon",
        "name_en": "Seongeun Moon"
      },
      "year": 2026,
      "dimensions": {
        "width_cm": 24.0,
        "height_cm": 41.0,
        "depth_cm": 1.8
      },
      "medium": {
        "medium_category": "acrylic",
        "support_category": "canvas"
      },
      "category": "Painting",
      "artwork_url": "https://example.com/artwork/smoke_001"
    },
    "options": {
      "include_comparable_samples": true,
      "max_comparable_samples": 3
    }
  }'
```

## 6. 검증

```bash
PYTHONPATH=src MPLCONFIGDIR=/private/tmp pytest \
  tests/price_engine/test_operational_v0_1_api.py
```

로컬 HTTP 확인:

```bash
python3 - <<'PY'
import urllib.request
with urllib.request.urlopen('http://127.0.0.1:8010/test/v0.1', timeout=10) as r:
    print(r.status, len(r.read()))
PY
```

## 7. 주의 사항

- `/artists:resolve`에서 `resolved=false`이면 가격 예측 전에 사용자가 후보를 선택하는 흐름을 권장
- `박서보`처럼 같은 한글명에 여러 내부 artist_key가 있는 경우 `requires_selection=true`가 될 수 있음
- API 응답에는 내부 실험 코드를 직접 노출하지 않고, 서비스 후보/표시 정책 중심으로 반환
- `market_price_card`는 개별 작품 예측가가 아니라 유사 작품 묶음의 호당가 통계
- v0.1 고정 환율은 API 응답과 모델 문서에 함께 노출되며, 운영 DB 적용 시 예측 시점 환율 스냅샷 저장 권장
