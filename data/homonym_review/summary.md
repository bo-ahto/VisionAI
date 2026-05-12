# 동명이인 분리 entity 자동 분류 결과

## 전체 수치
- TRUE_homonym 작가 (한글명 기준): **40명**
- 분리된 entity 총 수: **238개** (38명 → 238 분리 entity)

## 분류

### 1️⃣ 자동 merge 가능 (profile_url 동일)
- 묶음 수: **9개**
- 의미: 같은 한글명 안에서 URL이 동일한 entity → 같은 사람으로 자동 통합 가능
- 파일: `auto_merge.csv`

### 2️⃣ 한 플랫폼 내 분리 (정상 — 그대로 유지)
- 작가 수: **9명**
- 의미: source platform 자체가 이미 잘 구분한 것 (예: Saatchi에서 김유리 두 명을 다른 ID로)
- 파일: `single_platform.csv`

### 3️⃣ 수동 검수 필요 (여러 플랫폼 걸침)
- 작가 수: **31명**
- entity 행 수: **219개**
- 의미: 다른 플랫폼에 같은 한글명이 있어 같은 사람/다른 사람인지 사람이 봐야 함
- 파일: `manual_review.csv` ← **이게 작업 대상**

## 검수 방법

각 작가별로 entity row 비교:
1. `profile_url` 클릭 → 작가 페이지 확인
2. URL 깨졌으면 `sample_artwork_url_1/2/3` 클릭 → 작품 페이지에서 작가 확인
3. `sample_image_url_*` 직접 → 작품 이미지 즉시 확인 (Artsy/Saatchi만)
4. 같은 사람이면 → 두 entity 묶음 (merge), 다른 사람이면 → 분리 유지
