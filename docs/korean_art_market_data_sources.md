# Korean Art Market - External Data Sources for Price Prediction

Research Date: 2026-03-28

---

## 1. KOREAN DOMESTIC DATA SOURCES

### 1.1 K-ARTMARKET (한국미술시장정보시스템)

- **URL**: https://k-artmarket.kr/
- **Operator**: 문화체육관광부 + 예술경영지원센터 (KAMS)
- **Access Method**: Web portal (no public API)
- **Data Fields**:
  - 작가명, 작품명, 낙찰가
  - 경매사, 경매일
  - 작품 이미지 (thumbnail)
  - 시장 동향 분석 리포트
- **Coverage**: ~80,000 거래 기록, 국내 10개 경매사, 1998년~현재
- **Cost**: 무료 (회원가입 필요)
- **Legal**: 정부 운영 공공 플랫폼. 개인 연구/비상업 목적 사용 가능. 대량 스크래핑은 이용약관 확인 필요.
- **Difficulty**: MEDIUM
  - 웹 인터페이스로만 제공, API 없음
  - 검색 기반 조회 → 대량 수집에는 스크래핑 필요
  - 공공 목적이므로 데이터 요청 가능성 있음
- **Priority**: HIGH - 가장 포괄적인 국내 경매 데이터

---

### 1.2 K-Artprice (한국미술시가감정협회)

- **URL**: https://kartprice.net/
- **Operator**: (사)한국미술시가감정협회 + 뉴시스
- **Access Method**: Web portal (no public API)
- **Data Fields**:
  - 작가별 작품 낙찰가 이력
  - 작품 이미지
  - 제작연도, 재료, 크기
  - 시가감정 정보
- **Coverage**: 국내 8개 경매사, 2015.01~2021.06 (범위 확인 필요 - 업데이트 여부)
- **Cost**: 유료 구독 (가격 미확인, 웹사이트에서 확인 필요)
- **Legal**: 상업 데이터. 스크래핑 금지 가능성 높음.
- **Difficulty**: HARD
  - API 없음, 유료 서비스
  - 데이터 범위가 제한적
- **Priority**: MEDIUM - K-ARTMARKET과 중복 가능성

---

### 1.3 서울옥션 (Seoul Auction)

- **URL**: https://www.seoulauction.com/
- **Access Method**: Web only (no API)
- **Data Fields**:
  - 경매 카탈로그 (이미지 포함)
  - 작가, 작품명, 크기, 재료, 제작연도
  - 추정가, 낙찰가
  - 경매 일자, 경매 유형 (메이저/온라인)
- **Coverage**: 1998년 설립, 한국 최대 경매사. 수만 점 경매 기록.
- **Cost**: 무료 열람 (웹사이트)
- **Legal**: **스크래핑 명시적 금지**. 저작권법, 부정경쟁방지법 적용. 무단 크롤링/스크래핑 금지.
- **Difficulty**: HARD
  - 스크래핑 법적 리스크 높음
  - 공식 데이터 제공 채널 없음
  - 직접 문의 필요 (연구 목적 데이터 제공 협상)
- **Priority**: HIGH (데이터 가치) but ACCESS RISK

---

### 1.4 케이옥션 (K-Auction)

- **URL**: https://www.k-auction.com/
- **Access Method**: Web + Mobile App
- **Data Fields**:
  - 작품 사진, 작가 정보
  - 작품 재료, 제작연도
  - 추정가, 낙찰가
  - 경매 일정
- **Coverage**: 한국 2위 경매사. 수만 점 경매 기록.
- **Cost**: 무료 열람 (웹사이트)
- **Legal**: 이용약관 확인 필요. 서울옥션과 유사한 제한 예상.
- **Difficulty**: HARD (서울옥션과 동일 이슈)
- **Priority**: HIGH (데이터 가치) but ACCESS RISK

---

### 1.5 국립현대미술관 (MMCA) 소장품 데이터

- **URL**: https://www.mmca.go.kr/
- **공공데이터포털**: https://www.data.go.kr/data/15137158/fileData.do
- **Access Method**: 공공데이터포털 파일 데이터 + 웹사이트
- **Data Fields**:
  - 전시프로그램 정보 (data.go.kr에서 제공)
  - 소장품 목록 (작가, 작품, 제작연도, 재료, 크기)
  - 전시 이력
  - 일부 저작권 만료 소장품 이미지
- **Coverage**: 4개 관 (과천, 덕수궁, 서울, 청주). 한국 근현대 미술 120년.
- **Cost**: 무료 (공공데이터)
- **Legal**: 공공데이터 — 비교적 자유로운 활용. 저작권 만료 작품 이미지 제공.
- **Difficulty**: EASY-MEDIUM
  - 공공데이터포털에서 파일 다운로드 가능
  - 소장품 데이터는 경매 가격 없음 (보조 데이터로 활용)
- **Priority**: MEDIUM - 작가 프로파일 및 전시 이력 보조 데이터

---

### 1.6 공공데이터포털 미술 관련 데이터

- **URL**: https://www.data.go.kr/
- **Available Datasets**:
  - 전국박물관미술관정보 표준데이터
  - 국립현대미술관 전시프로그램 정보
  - 예술경영지원센터 문화예술 일자리 정보
  - 국가문화예술지원시스템(NCAS) 지역별 현황
- **Access Method**: REST API (JSON/XML) + 파일 다운로드
- **Cost**: 무료 (인증키 신청 필요)
- **Legal**: 공공데이터 — 자유로운 활용
- **Difficulty**: EASY
- **Priority**: LOW-MEDIUM - 보조/맥락 데이터

---

### 1.7 기타 국내 경매사

| 경매사 | URL | 비고 |
|--------|-----|------|
| 마이아트옥션 | https://myartauction.com/ | 소규모 |
| 포털아트 | https://porart.com/ | 국내 최대 미술품 경매 (자체 주장) |
| 인사옥션 | https://www.insaauction.com/ | 소규모 |

- 동일한 스크래핑 이슈 적용
- K-ARTMARKET에 이미 이들의 낙찰 데이터 통합되어 있을 가능성

---

## 2. INTERNATIONAL DATA SOURCES

### 2.1 Artsy (Free Price Database + API)

- **URL**: https://www.artsy.net/price-database
- **Developer API**: https://developers.artsy.net/
- **Access Method**: Web (무제한 무료 검색) + Public REST API
- **Data Fields**:
  - 경매 결과 (낙찰가, 추정가)
  - 작가 프로필, 작품 이미지
  - 갤러리 정보, 전시 이력
  - Sales API: 경매 정보 (Public API에서 제한적)
- **Coverage**: 수백만 건 경매 결과. 한국 작가 포함 (이우환, 하인두, 서유영 등 확인)
- **Cost**: 무료 (Public API). Partner API는 별도 신청.
- **Legal**: 비상업적 프로덕션 사용 허용. Partner API로 더 많은 경매 데이터 접근 가능.
- **Difficulty**: EASY (Public API) / MEDIUM (Partner API 승인 필요)
- **Priority**: **VERY HIGH** - 가장 접근성 좋은 국제 경매 데이터
- **Note**: Public API는 "sold=false" 작품만 제공. 경매 가격 데이터는 Partner API 필요.

---

### 2.2 Artnet Price Database

- **URL**: https://www.artnet.com/price-database/
- **Access Method**: Web subscription
- **Data Fields**:
  - 작가명, 작품명, 미디엄
  - 경매사, 경매일, 낙찰가
  - 작품 이미지 (일러스트레이션)
  - 1985년 이후 데이터
- **Coverage**: 400만+ 경매 결과, 188,000+ 작가. 한국 작가 포함.
- **Cost**: **유료**
  - One-Day Pass: 제한 검색
  - Individual Rollover: 월 10회 검색
  - Expert/Appraiser: 연간 무제한
  - 정확한 가격은 웹사이트에서 확인 (연 $150~$2,000+ 추정)
- **Legal**: 상업 데이터베이스. API 없음. 스크래핑 금지.
- **Difficulty**: MEDIUM (구독 비용) / HARD (대량 데이터 추출)
- **Priority**: HIGH - 가장 권위있는 국제 경매 데이터베이스

---

### 2.3 Artprice

- **URL**: https://www.artprice.com/
- **Access Method**: Web subscription
- **Data Fields**:
  - 3,000만+ 경매 가격
  - 635,000+ 작가
  - 경매 결과, 인덱스
  - 1983년부터
- **Coverage**: 6,300+ 경매사 커버. 서울옥션 14위, 케이옥션 16위 (2016-2017 기준).
- **Cost**: **유료** (구독형)
- **Legal**: 상업 데이터베이스
- **Difficulty**: MEDIUM-HARD
- **Priority**: MEDIUM - Artnet과 유사하지만 접근성 낮음

---

### 2.4 Invaluable

- **URL**: https://www.invaluable.com/
- **Access Method**: Web + Catalog Upload API (경매사 전용)
- **Data Fields**:
  - 2,000+ 국제 경매사 카탈로그
  - 작품 이미지, 경매 결과
  - Christie's, Sotheby's 포함
- **Coverage**: 한국 미술/골동품 카테고리 존재
- **Cost**: 일부 무료 검색 + 유료 구독
- **Legal**: API는 소프트웨어 파트너 전용. 일반 접근 제한.
- **Difficulty**: HARD (API 접근 제한)
- **Priority**: LOW - 접근성 대비 가치 낮음

---

## 3. IMAGE DATASETS

### 3.1 WikiArt Dataset

- **URL**: https://www.wikiart.org/
- **Download Sources**:
  - Kaggle: https://www.kaggle.com/datasets/steubk/wikiart
  - Hugging Face: https://huggingface.co/datasets/huggan/wikiart
  - GitHub Crawler: https://github.com/asahi417/wikiart-image-dataset
  - GitHub Full Retriever: https://github.com/lucasdavid/wikiart
  - Internet Archive: https://archive.org/details/wikiart-dataset
- **Data Fields**:
  - 250,000+ 고해상도 이미지
  - 3,000+ 작가
  - 장르(129 클래스), 스타일(11 클래스)
  - 작가, 제목, 제작연도, 미디엄
- **Korean Artists**: 필터링하여 한국 작가 추출 가능 (정확한 수는 미확인)
- **Cost**: 무료
- **Legal**: 교육/연구 목적 사용. 상업적 사용 시 개별 저작권 확인.
- **Difficulty**: EASY
- **Priority**: HIGH - CNN 학습용 이미지 데이터 바로 활용 가능

---

### 3.2 OmniArt Dataset (Deprecated)

- **URL**: https://www.vistory-omniart.com/
- **Status**: **더 이상 이용 불가** (서비스 종료)
- **대안**:
  - The Met Dataset (메트로폴리탄 미술관)
  - SemArt Dataset
  - Ukiyo-e woodblock print dataset

---

### 3.3 Google Arts & Culture / MMCA

- **URL**: https://artsandculture.google.com/partner/national-museum-of-modern-and-contemporary-art-korea
- **Access**: 웹 브라우징, 고해상도 이미지 일부 제공
- **Korean Coverage**: MMCA 소장품 이미지
- **Cost**: 무료
- **Legal**: 이미지 다운로드/사용 제한 있음
- **Difficulty**: MEDIUM (체계적 수집 어려움)
- **Priority**: LOW

---

### 3.4 Rijksmuseum API

- **URL**: https://data.rijksmuseum.nl/
- **Access**: REST API
- **Coverage**: 한국 미술 직접 관련 없지만, 미술 이미지+메타데이터 수집 파이프라인 참고용
- **Priority**: LOW (참고용)

---

## 4. SUPPLEMENTARY DATA SOURCES

### 4.1 Korean Gallery Artist Representation

주요 한국 갤러리와 소속 작가 정보:

| 갤러리 | 주요 작가 | 데이터 가치 |
|--------|-----------|------------|
| 국제갤러리 (Kukje) | 박서보, 이우환 (단색화) | HIGH |
| 갤러리현대 (Gallery Hyundai) | 김아영, 이우환 | HIGH |
| PKM Gallery | 윤형근 | MEDIUM |
| Pace Gallery Seoul | 국제 작가 | MEDIUM |
| Lehmann Maupin Seoul | 국제 작가 | MEDIUM |

- **Access**: 각 갤러리 웹사이트에서 수동 수집
- **Data Value**: 갤러리 소속 여부는 작가 가격에 강한 영향
- **Difficulty**: MEDIUM (수동 수집, 구조화 필요)

---

### 4.2 GitHub - Aimme (미술 작품 경매가 조회)

- **URL**: https://github.com/shubug1015/aimme
- **Description**: 한국 미술 작품 정보 및 경매가 조회 서비스
- **Stack**: JavaScript, React, Next.js
- **Period**: 2021.12 ~ 2022.05
- **Note**: 데이터 소스 미공개. 코드 참고용. 프론트엔드 중심.
- **Priority**: LOW (참고용)

---

## 5. IMAGE RESOLUTION FOR CNN PRICE PREDICTION

### Research Findings

| Parameter | Recommended | Notes |
|-----------|------------|-------|
| **Standard Input** | 224x224 px | ResNet-50, VGG 기본 |
| **Higher Quality** | 299x299 px | Inception v3 기본. 5-10% 정확도 향상 |
| **Optimal Balance** | 224x224 ~ 384x384 px | 비용 대비 효과 최적 |
| **ViT-Small** | 224x224 px | Patch 16x16 기본 |
| **Original Collection** | 최소 512x512 px | 리사이즈 여유 확보 |
| **Recommended Storage** | 800x800+ px | 다양한 모델 실험 가능 |

### Key Research Insights (arxiv:2512.23078, 2024)

1. **ResNet-50 + ViT-Small**을 이미지 인코더로 사용
2. Visual embedding 차원(d_image)을 10~20,000까지 변화시켜 실험
3. **시각적 특징이 가장 유의미한 카테고리**: American Paintings/Drawings, Sculptures, Post-War/Contemporary, oil-based media
4. 데이터셋: 53,351건 거래 (Christie's, Sotheby's NY/London, Paris, Hong Kong 등)
5. **멀티모달 접근이 단일 모달보다 우수**: MAPE 30.66%, MAE 3348.73
6. **작가 정체성 + 거래 이력**이 예측력의 대부분 차지
7. **이미지는 신규 작가/첫 거래 작품에서 가장 유의미**
8. Grad-CAM 분석: 모델이 구도/스타일 단서에 주목

### Practical Image Collection Guidelines

```
수집 해상도:    최소 800x800 px (원본)
학습 리사이즈:  224x224 (ResNet-50) 또는 384x384 (ViT)
파일 형식:     JPEG (품질 85+) 또는 PNG
색공간:        sRGB
augmentation:  rotation, flipping, color jitter, random crop
```

---

## 6. RECOMMENDED DATA COLLECTION STRATEGY

### Phase 1: Low-Hanging Fruit (1-2 weeks)

| Source | Method | Expected Records | Effort |
|--------|--------|-----------------|--------|
| K-ARTMARKET | 회원가입 + 웹 수집 | ~80,000 거래 | MEDIUM |
| Artsy Public API | REST API | 한국 작가 수천 건 | EASY |
| WikiArt | Dataset download | 250,000 이미지 (한국 작가 필터링) | EASY |
| 공공데이터포털 | API/파일 다운로드 | 미술관/전시 데이터 | EASY |

### Phase 2: Extended Collection (1-2 months)

| Source | Method | Expected Records | Effort |
|--------|--------|-----------------|--------|
| Artsy Partner API | 승인 신청 | 경매 가격 데이터 | MEDIUM |
| Artnet | 유료 구독 | 한국 작가 수만 건 | MEDIUM (비용) |
| MMCA 소장품 | 공공데이터 요청 | 수천 점 메타데이터 | EASY |
| 갤러리 작가 목록 | 수동 수집 | 수백 작가 | MEDIUM |

### Phase 3: Premium/Negotiation (3+ months)

| Source | Method | Expected Records | Effort |
|--------|--------|-----------------|--------|
| 서울옥션/케이옥션 | 연구 목적 데이터 제휴 | 수만 건 | HARD |
| Artprice | 유료 구독 | 30M+ 글로벌 | HARD (비용) |
| K-Artprice | 유료 구독/협회 연락 | 수만 건 | HARD |

---

## 7. LEGAL RISK SUMMARY

| Source | Scraping Risk | API Available | Research Exception |
|--------|--------------|---------------|-------------------|
| K-ARTMARKET | MEDIUM | No | 공공 데이터, 문의 가능 |
| Seoul Auction | **HIGH** (명시적 금지) | No | 연구 협약 필요 |
| K-Auction | **HIGH** | No | 연구 협약 필요 |
| K-Artprice | HIGH | No | 유료 구독 |
| Artsy | LOW | Yes (Public) | 비상업적 사용 허용 |
| Artnet | HIGH | No | 유료 구독만 |
| WikiArt | LOW | Yes (Crawler) | 교육/연구 OK |
| 공공데이터포털 | NONE | Yes | 공공 데이터 |
| MMCA | LOW | Partial | 공공 기관 |

---

## 8. RECOMMENDED MINIMUM VIABLE DATASET

For a Korean art price prediction model MVP:

```
Target: 10,000+ auction records with images

Data Schema:
- artist_name (str)         ← K-ARTMARKET, Artsy
- artist_birth_year (int)   ← Artsy, WikiArt
- artwork_title (str)       ← K-ARTMARKET
- medium (str)              ← all sources
- dimensions_cm (float x2)  ← all sources
- year_created (int)        ← all sources
- auction_house (str)       ← K-ARTMARKET
- auction_date (date)       ← K-ARTMARKET
- estimate_low (float)      ← auction houses
- estimate_high (float)     ← auction houses
- hammer_price (float)      ← target variable
- image_url (str)           ← scrape/download
- gallery_representation (str) ← manual collection
- exhibition_count (int)    ← MMCA, Artsy
- artist_nationality (str)  ← Artsy, WikiArt
- provenance_indicators (int) ← auction catalogs
```

### Expected Model Architecture

```
Input: [tabular_features] + [image_224x224]
       ↓                    ↓
   MLP/XGBoost          ResNet-50/ViT
       ↓                    ↓
       └── fusion layer ────┘
                ↓
          price prediction
```

---

## Sources

- [K-ARTMARKET](https://k-artmarket.kr/)
- [K-Artprice](https://kartprice.net/)
- [Seoul Auction](https://www.seoulauction.com/)
- [K-Auction](https://www.k-auction.com/)
- [MMCA](https://www.mmca.go.kr/)
- [KAMS](https://www.gokams.or.kr/)
- [공공데이터포털](https://www.data.go.kr/)
- [Artsy Price Database](https://www.artsy.net/price-database)
- [Artsy API](https://developers.artsy.net/)
- [Artnet](https://www.artnet.com/price-database/)
- [Artprice](https://www.artprice.com/)
- [Invaluable](https://www.invaluable.com/)
- [WikiArt Kaggle](https://www.kaggle.com/datasets/steubk/wikiart)
- [WikiArt HuggingFace](https://huggingface.co/datasets/huggan/wikiart)
- [WikiArt GitHub Crawler](https://github.com/asahi417/wikiart-image-dataset)
- [Aimme GitHub](https://github.com/shubug1015/aimme)
- [Deep Learning for Art Market Valuation (arxiv:2512.23078)](https://arxiv.org/abs/2512.23078)
- [Multimodal Approach for Painting Price Prediction (IEEE)](https://ieeexplore.ieee.org/document/10352208/)
- [Google Arts & Culture - MMCA](https://artsandculture.google.com/partner/national-museum-of-modern-and-contemporary-art-korea)
