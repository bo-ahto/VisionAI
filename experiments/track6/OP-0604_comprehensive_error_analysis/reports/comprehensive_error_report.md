# 0604 테스트 종합 오차 분석

## 1. 핵심 결론

- 0604 숫자 가격 라벨 837건 기준, 운영 기본값이 원화 가격을 정확히 맞춘 사례는 0건.
- 1% 이내 근접 적중은 20건, 5% 이내 근접 적중은 98건.
- 근접 적중은 주로 같은 작가 기준선이 잡힌 작품, 반복 재료/지지체, 가격 범위가 비교적 좁은 작품에서 발생.
- 전체 MAPE 14.2852는 50달러 미만 검수 대상 8건의 영향이 매우 큼.
- 50달러 미만을 제외하면 MAPE는 0.3359, p95_APE는 0.9273으로 내려감.
- 50달러 이상에서도 큰 오차는 남아 있으며, 과대 예측은 저가 소품/소형작, 과소 예측은 고가 작품/특수 작가/큰 가격 범위에서 주로 발생.

## 2. 전체 성능과 큰 오차 영향

| 구분 | n | MdAPE | MAPE | p95_APE | RMSE_log | median_ratio | over_3x_n | under_1_3x_n | APE_1plus_n |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 전체 숫자 라벨 | 837 | 0.2342 | 14.2852 | 0.9844 | 0.9199 | 0.9341 | 12 | 58 | 39 |
| 50달러 미만 제외 | 829 | 0.2298 | 0.3359 | 0.9273 | 0.7124 | 0.9321 | 4 | 58 | 31 |
| 50달러 미만 검수 대상 | 8 | 495.3133 | 1459.7850 | 5924.4884 | 5.9949 | 496.3133 | 8 | 0 | 8 |

해석:

- `전체 숫자 라벨`의 MAPE가 비정상적으로 큰 이유는 실제 가격이 1~30달러인 라벨이 포함되어 있기 때문.
- MAPE는 실제 가격을 분모로 쓰므로 실제값이 매우 작으면 작은 금액 차이도 수백~수천 배 오차로 계산됨.
- 따라서 운영 판단은 전체 수치와 함께 50달러 미만 검수 대상 제외 기준을 같이 봐야 함.

## 3. 정확/근접 적중

| 기준 | n | 정확일치 | 1원반올림일치 | 최소_APE | 0.1%_이내 | 0.5%_이내 | 1.0%_이내 | 2.0%_이내 | 3.0%_이내 | 5.0%_이내 | 10.0%_이내 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 운영 기본값 원값 | 837 | 0 | 0 | 0.000390 | 1 (0.12%) | 9 (1.08%) | 20 (2.39%) | 47 (5.62%) | 57 (6.81%) | 98 (11.71%) | 191 (22.82%) |

해석:

- 정확 일치 0건은 모델이 정답 가격을 외우거나 복사한 구조가 아니라는 의미.
- 근접 적중은 유사 작가/유사 조건의 가격 기준선과 실제 신규 판매가가 우연히 매우 가깝게 맞은 사례.
- 서비스 화면에서 반올림 표시를 하면 같은 값처럼 보일 수 있으므로 원값 기준과 표시값 기준을 분리해 설명해야 함.

### 3.1 화면 표시 반올림 기준

| 통화 | 반올림단위 | n | 표시값일치 | 표시값일치율 |
| --- | --- | --- | --- | --- |
| KRW | 1 | 837 | 0 | 0.00% |
| KRW | 1,000 | 837 | 0 | 0.00% |
| KRW | 10,000 | 837 | 11 | 1.31% |
| KRW | 100,000 | 837 | 66 | 7.89% |
| KRW | 1,000,000 | 837 | 349 | 41.70% |
| USD | 1 | 837 | 1 | 0.12% |
| USD | 10 | 837 | 11 | 1.31% |
| USD | 100 | 837 | 71 | 8.48% |
| USD | 1,000 | 837 | 345 | 41.22% |

### 3.2 근접 적중 상위 사례

| row_id | 작가 | 작품명 | 통화 | 실제_KRW | 예측_KRW | APE | 예측/실제 | 방향 | 비교묶음 | 표본수 | 재료/지지체 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6745 | Jeongeun Han | Behold the Tilting Wings | USD | 993,600 | 993,212 | 0.0004 | 0.9996 | 과소 | artist | 5 | acrylic__canvas |
| 5369 | Molly Kim | Encounter No.11 | USD | 1,131,600 | 1,130,274 | 0.0012 | 0.9988 | 과소 | artist | 19 | oil__canvas |
| 8 | PARKHA | Still Life_FACE | USD | 966,000 | 964,820 | 0.0012 | 0.9988 | 과소 | artist | 9 | oil__canvas |
| 6 | PARKHA | Still Life_SEESAW | USD | 966,000 | 964,820 | 0.0012 | 0.9988 | 과소 | artist | 9 | oil__canvas |
| 14 | Yuzu Kim | Always There | USD | 731,400 | 732,490 | 0.0015 | 1.0015 | 과대 | artist | 5 | acrylic__canvas |
| 3161 | Jaehyug CHOI  최재혁 | Still Life #49 | USD | 16,560,000 | 16,593,008 | 0.0020 | 1.0020 | 과대 | artist_medium_support_size | 7 | oil__canvas |
| 3164 | Jaehyug CHOI  최재혁 | Still Life #51 | USD | 16,560,000 | 16,593,008 | 0.0020 | 1.0020 | 과대 | artist_medium_support_size | 7 | oil__canvas |
| 922 | Eunhyea Choi | After the Light | USD | 1,380,000 | 1,382,891 | 0.0021 | 1.0021 | 과대 | artist | 20 | acrylic__canvas |
| 134 | Jason Ha | The Gaze | USD | 469,200 | 470,608 | 0.0030 | 1.0030 | 과대 | artist | 6 | acrylic__canvas |
| 5385 | Young Jae | A Moment 2/2 | USD | 1,725,000 | 1,715,911 | 0.0053 | 0.9947 | 과소 | artist | 7 | mixed__paper |

## 4. 50달러 미만 검수 대상

| row_id | 작가 | 작품명 | 통화 | 실제_KRW | 예측_KRW | APE | 예측/실제 | 방향 | 비교묶음 | 표본수 | 재료/지지체 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6263 | Jae Youl Jeoung | Temporal wall | USD | 1,380 | 11,103,778 | 8045.2157 | 8046.2157 | 과대 | artist | 10 | other__metal |
| 6262 | Jae Youl Jeoung | A star written in Braille | USD | 1,380 | 2,742,053 | 1985.9948 | 1986.9948 | 과대 | artist | 10 | other__other |
| 4077 | Jeongyoon Park | hot wind | USD | 1,380 | 797,371 | 576.8054 | 577.8054 | 과대 | medium_size | 1,408 | acrylic__linen |
| 6264 | Jae Youl Jeoung | small talk | USD | 1,380 | 748,220 | 541.1882 | 542.1882 | 과대 | artist_size | 8 | other__paper |
| 6265 | Jae Youl Jeoung | A star written in Braille: Notes of the Star | USD | 1,380 | 621,605 | 449.4384 | 450.4384 | 과대 | artist_size | 8 | other__paper |
| 115 | HWAYEON | Happy Virus | USD | 13,800 | 622,036 | 44.0751 | 45.0751 | 과대 | global | 26,914 | other__other |
| 113 | HWAYEON | 治葬 | USD | 27,600 | 622,036 | 21.5375 | 22.5375 | 과대 | global | 26,914 | other__other |
| 114 | HWAYEON | Tin Head | USD | 41,400 | 622,036 | 14.0250 | 15.0250 | 과대 | global | 26,914 | other__other |

해석:

- 실제 가격이 1달러, 10달러, 20달러, 30달러로 들어온 라벨이 있음.
- 해당 가격이 실제 판매가인지, placeholder/입력 오류/특수 상품 가격인지 검수 필요.
- 모델은 일반 작품 가격 기준으로 예측하므로, 이런 초저가 라벨은 MAPE를 크게 왜곡함.
- 운영 평가에서는 초저가 라벨을 별도 검수 태그로 분리하는 것이 필요.

## 5. 50달러 이상 큰 오차 사례

### 5.1 APE 기준 큰 오차 상위

| row_id | 작가 | 작품명 | 통화 | 실제_KRW | 예측_KRW | APE | 예측/실제 | 방향 | 비교묶음 | 표본수 | 재료/지지체 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 24 | Dahee Yang | Glass | USD | 151,800 | 643,691 | 3.2404 | 4.2404 | 과대 | artist | 9 | oil__canvas |
| 928 | Beomsik Won | Archisculpture 032 | USD | 690,000 | 2,767,337 | 3.0106 | 4.0106 | 과대 | artist | 13 | other__paper |
| 3176 | Gilyoung JUNG 정길영 | Cutlery Rest Set (4pcs) | USD | 138,000 | 437,394 | 2.1695 | 3.1695 | 과대 | artist | 5 | other__other |
| 3645 | Sohyun Park | Cartographie Memoire_St. Etienne | USD | 1,518,000 | 4,717,582 | 2.1078 | 3.1078 | 과대 | artist | 10 | acrylic__paper |
| 6143 | Nam June Paik | Etching on Etching | USD | 6,900,000 | 18,489,371 | 1.6796 | 2.6796 | 과대 | artist_size | 12 | other__paper |
| 6144 | Nam June Paik | Rosetta Stone | USD | 6,900,000 | 18,489,371 | 1.6796 | 2.6796 | 과대 | artist_size | 12 | other__paper |
| 4098 | Yeun Song | T11- W04 | USD | 552,000 | 1,474,201 | 1.6707 | 2.6707 | 과대 | artist_size | 5 | other__metal |
| 4165 | Gyul E Kim | Equation-like Forms | USD | 3,864,000 | 9,701,027 | 1.5106 | 2.5106 | 과대 | artist_size | 10 | oil__canvas |
| 32 | Hee Sun Kim | Captured in pure white | USD | 138,000 | 341,691 | 1.4760 | 2.4760 | 과대 | artist | 7 | ink__other |
| 60 | Junho JUNG | My Small Step in the Forest | USD | 186,300 | 460,564 | 1.4722 | 2.4722 | 과대 | artist | 6 | other__other |
| 38 | Eunjung Lee | A Cat Flying in the Sky | USD | 365,700 | 878,288 | 1.4017 | 2.4017 | 과대 | artist | 12 | ink__paper |
| 36 | Eunjung Lee | Hojokdo | USD | 324,300 | 777,157 | 1.3964 | 2.3964 | 과대 | artist | 12 | ink__paper |
| 59 | Junho JUNG | My Small Step in the Forest | USD | 331,200 | 783,368 | 1.3652 | 2.3652 | 과대 | artist | 6 | other__other |
| 152 | Mi Young Um | - [Lucky Symbol '#'] "You, Like #, a Symbol Always Connecting by My Side." | USD | 372,600 | 878,898 | 1.3588 | 2.3588 | 과대 | artist | 7 | mixed__canvas |
| 5118 | Jeong Yeon Kim | No Tears Left 5cm 2 | USD | 4,374,600 | 10,248,565 | 1.3427 | 2.3427 | 과대 | artist | 5 | acrylic__canvas |

### 5.2 3배 초과 과대 예측

| row_id | 작가 | 작품명 | 통화 | 실제_KRW | 예측_KRW | APE | 예측/실제 | 방향 | 비교묶음 | 표본수 | 재료/지지체 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 24 | Dahee Yang | Glass | USD | 151,800 | 643,691 | 3.2404 | 4.2404 | 과대 | artist | 9 | oil__canvas |
| 928 | Beomsik Won | Archisculpture 032 | USD | 690,000 | 2,767,337 | 3.0106 | 4.0106 | 과대 | artist | 13 | other__paper |
| 3176 | Gilyoung JUNG 정길영 | Cutlery Rest Set (4pcs) | USD | 138,000 | 437,394 | 2.1695 | 3.1695 | 과대 | artist | 5 | other__other |
| 3645 | Sohyun Park | Cartographie Memoire_St. Etienne | USD | 1,518,000 | 4,717,582 | 2.1078 | 3.1078 | 과대 | artist | 10 | acrylic__paper |

해석:

- 3배 초과 과대 예측은 50달러 이상 기준 4건.
- 실제 가격 중앙값이 약 305달러로 낮은 편이며, 모델 예측은 작가/유사 조건 기준선을 따라 더 높은 가격대로 올라감.
- 저가 소품, edition/오브젝트성 작품, 작은 크기 작품은 일반 회화 가격 기준선과 분리할 필요가 있음.

### 5.3 3분의 1 미만 과소 예측

| row_id | 작가 | 작품명 | 통화 | 실제_KRW | 예측_KRW | APE | 예측/실제 | 방향 | 비교묶음 | 표본수 | 재료/지지체 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5752 | Bahk Younghoon | Invisible precious things NO.002 | USD | 55,200,000,000 | 29,109,338 | 0.9995 | 0.0005 | 과소 | artist | 6 | mixed__panel |
| 6423 | Hwi Kim | Surreal | USD | 2,070,000,000 | 1,405,319 | 0.9993 | 0.0007 | 과소 | artist_medium_support_size | 9 | acrylic__canvas |
| 5302 | Seo Jiin | Rainbow breeze | USD | 1,379,998,620 | 20,165,615 | 0.9854 | 0.0146 | 과소 | artist | 16 | pencil__canvas |
| 6446 | Yun Hyong-keun | Work | USD | 84,180,000 | 1,593,916 | 0.9811 | 0.0189 | 과소 | medium_support_size | 58 | oil__paper |
| 2885 | Jeon Byeong Sam | COSMOS 220830002 | USD | 34,500,000 | 1,542,873 | 0.9553 | 0.0447 | 과소 | artist | 45 | other__other |
| 6599 | Park Seo-Bo | Ecriture No.040412 | USD | 165,600,000 | 8,164,306 | 0.9507 | 0.0493 | 과소 | artist | 21 | other__paper |
| 6444 | Kim Chong Hak | Summer Gaewoon | USD | 331,200,000 | 20,038,647 | 0.9395 | 0.0605 | 과소 | medium_support_size | 1,457 | oil__canvas |
| 6445 | Lee Kang So | From an Island-02094 | USD | 51,750,000 | 3,691,263 | 0.9287 | 0.0713 | 과소 | medium_support_size | 1,388 | oil__canvas |
| 3177 | Gilyoung JUNG 정길영 | Dinnerware for 2 | USD | 5,520,000 | 412,134 | 0.9253 | 0.0747 | 과소 | artist | 5 | other__other |
| 6600 | Park Seo-Bo | Ecriture No. 040710 | USD | 524,400,000 | 40,939,567 | 0.9219 | 0.0781 | 과소 | artist_size | 8 | mixed__paper |
| 70 | Yuyeol Byeon | Impression, Algorithm and Nature — Ocean Waves II | USD | 11,136,600 | 939,621 | 0.9156 | 0.0844 | 과소 | global | 26,914 | other__paper |
| 2892 | Jong Sook Kim | ARTIFICIAL LANDSCAPE–White Material 05 | USD | 1,311,000,000 | 122,192,143 | 0.9068 | 0.0932 | 과소 | artist_size | 10 | mixed__canvas |
| 83 | Yuyeol Byeon | IMPRESSION, Algorithm and Nature | USD | 9,315,000 | 939,621 | 0.8991 | 0.1009 | 과소 | global | 26,914 | other__paper |
| 82 | Yuyeol Byeon | IMPRESSION, Algorithm and Nature - Ocean Wave | USD | 9,315,000 | 939,621 | 0.8991 | 0.1009 | 과소 | global | 26,914 | other__paper |
| 5300 | Jung Kwangmin | The Filled Void_lotus | USD | 12,420,000 | 1,300,679 | 0.8953 | 0.1047 | 과소 | artist | 17 | other__other |

해석:

- 3분의 1 미만 과소 예측은 50달러 이상 기준 58건.
- 실제 가격 중앙값이 16,500달러로 전체 중앙값보다 훨씬 높음.
- 유명 작가, 고가 작품, 특수 작품군, 초대형 작품, 검색/작가 메타로 설명되지 않는 프리미엄에서 주로 발생.
- 이 구간은 단순 중앙 예측보다 고가 위험 태그, 가격 범위 상단, 신뢰도 표시가 중요.

### 5.4 초고가 라벨 검수 대상

| row_id | 작가 | 작품명 | 통화 | 실제_KRW | 예측_KRW | APE | 예측/실제 | 방향 | 비교묶음 | 표본수 | 재료/지지체 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5752 | Bahk Younghoon | Invisible precious things NO.002 | USD | 55,200,000,000 | 29,109,338 | 0.9995 | 0.0005 | 과소 | artist | 6 | mixed__panel |
| 6423 | Hwi Kim | Surreal | USD | 2,070,000,000 | 1,405,319 | 0.9993 | 0.0007 | 과소 | artist_medium_support_size | 9 | acrylic__canvas |
| 5302 | Seo Jiin | Rainbow breeze | USD | 1,379,998,620 | 20,165,615 | 0.9854 | 0.0146 | 과소 | artist | 16 | pencil__canvas |
| 2892 | Jong Sook Kim | ARTIFICIAL LANDSCAPE–White Material 05 | USD | 1,311,000,000 | 122,192,143 | 0.9068 | 0.0932 | 과소 | artist_size | 10 | mixed__canvas |
| 6600 | Park Seo-Bo | Ecriture No. 040710 | USD | 524,400,000 | 40,939,567 | 0.9219 | 0.0781 | 과소 | artist_size | 8 | mixed__paper |
| 6444 | Kim Chong Hak | Summer Gaewoon | USD | 331,200,000 | 20,038,647 | 0.9395 | 0.0605 | 과소 | medium_support_size | 1,457 | oil__canvas |
| 3194 | Hyungdae KIM 김형대 | HALO 08-424 | USD | 176,640,000 | 148,584,923 | 0.1588 | 0.8412 | 과소 | artist_medium_support_size | 9 | acrylic__canvas |
| 6599 | Park Seo-Bo | Ecriture No.040412 | USD | 165,600,000 | 8,164,306 | 0.9507 | 0.0493 | 과소 | artist | 21 | other__paper |

해석:

- 10만 달러 이상 라벨은 8건, 100만 달러 이상 라벨은 2건.
- 일부 라벨은 신규 운영 테스트 데이터의 가격 단위, 통화, 입력값 해석을 다시 확인해야 함.
- 실제 초고가 작품이 맞다면 현재 v0.1 Warm 모델은 초고가 프리미엄을 충분히 반영하지 못함.
- 따라서 초고가 라벨은 데이터 검수와 모델 보정을 동시에 봐야 하는 구간.

## 6. 근접/큰 오차 세그먼트 비교

| 구분 | n | median_actual_usd | median_pred_usd | median_area_cm2 | median_svc_group_n | median_price_range_ratio | top_group_level | top_medium_support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 전체_50달러이상 | 829 | 2028.99 | 1717.04 | 3660.25 | 9.00 | 4.84 | artist | acrylic__canvas |
| 근접_5pct | 98 | 1914.49 | 1962.03 | 3350.15 | 8.50 | 3.99 | artist | acrylic__canvas |
| 과대_3배초과 | 4 | 305.00 | 1235.88 | 754.33 | 9.50 | 5.74 | artist | acrylic__paper |
| 과소_1_3미만 | 58 | 16500.00 | 2782.88 | 6608.43 | 20.00 | 6.88 | artist | other__paper |
| APE_100pct이상 | 31 | 270.00 | 636.88 | 900.00 | 10.00 | 5.40 | artist | other__other |

세그먼트별 상위 분포:

| 구분 | 세그먼트 | 값 | 건수 | 비중 |
| --- | --- | --- | --- | --- |
| 근접_5pct | svc_group_level | artist | 50 | 51.0% |
| 근접_5pct | svc_group_level | artist_size | 33 | 33.7% |
| 근접_5pct | svc_group_level | artist_medium_support_size | 12 | 12.2% |
| 근접_5pct | svc_group_level | medium_support_size | 3 | 3.1% |
| 근접_5pct | svc_coverage_tier | low_n | 69 | 70.4% |
| 근접_5pct | svc_coverage_tier | medium_n | 25 | 25.5% |
| 근접_5pct | svc_coverage_tier | high_n | 4 | 4.1% |
| 근접_5pct | service_confidence_tier | low | 55 | 56.1% |
| 근접_5pct | service_confidence_tier | medium | 43 | 43.9% |
| 근접_5pct | medium_support_bucket | acrylic__canvas | 40 | 40.8% |
| 근접_5pct | medium_support_bucket | oil__canvas | 22 | 22.4% |
| 근접_5pct | medium_support_bucket | mixed__paper | 7 | 7.1% |
| 근접_5pct | medium_support_bucket | other__paper | 5 | 5.1% |
| 근접_5pct | medium_support_bucket | mixed__canvas | 4 | 4.1% |
| 근접_5pct | medium_support_bucket | pigment__paper | 3 | 3.1% |
| 근접_5pct | medium_support_bucket | acrylic__linen | 2 | 2.0% |
| 근접_5pct | medium_support_bucket | ink__other | 2 | 2.0% |
| 근접_5pct | actual_currency | USD | 89 | 90.8% |
| 근접_5pct | actual_currency | KRW | 9 | 9.2% |
| 과대_3배초과 | svc_group_level | artist | 4 | 100.0% |
| 과대_3배초과 | svc_coverage_tier | low_n | 4 | 100.0% |
| 과대_3배초과 | service_confidence_tier | low | 2 | 50.0% |
| 과대_3배초과 | service_confidence_tier | medium | 2 | 50.0% |
| 과대_3배초과 | medium_support_bucket | oil__canvas | 1 | 25.0% |
| 과대_3배초과 | medium_support_bucket | other__paper | 1 | 25.0% |
| 과대_3배초과 | medium_support_bucket | other__other | 1 | 25.0% |
| 과대_3배초과 | medium_support_bucket | acrylic__paper | 1 | 25.0% |
| 과대_3배초과 | actual_currency | USD | 4 | 100.0% |
| 과소_1_3미만 | svc_group_level | artist | 23 | 39.7% |
| 과소_1_3미만 | svc_group_level | artist_size | 12 | 20.7% |
| 과소_1_3미만 | svc_group_level | medium_size | 8 | 13.8% |
| 과소_1_3미만 | svc_group_level | global | 7 | 12.1% |
| 과소_1_3미만 | svc_group_level | medium_support_size | 7 | 12.1% |
| 과소_1_3미만 | svc_group_level | artist_medium_support_size | 1 | 1.7% |
| 과소_1_3미만 | svc_coverage_tier | low_n | 25 | 43.1% |
| 과소_1_3미만 | svc_coverage_tier | high_n | 16 | 27.6% |
| 과소_1_3미만 | svc_coverage_tier | medium_n | 10 | 17.2% |
| 과소_1_3미만 | svc_coverage_tier | fallback_global | 7 | 12.1% |
| 과소_1_3미만 | service_confidence_tier | low | 39 | 67.2% |
| 과소_1_3미만 | service_confidence_tier | medium | 17 | 29.3% |
| 과소_1_3미만 | service_confidence_tier | high | 2 | 3.4% |
| 과소_1_3미만 | medium_support_bucket | other__paper | 15 | 25.9% |
| 과소_1_3미만 | medium_support_bucket | other__other | 7 | 12.1% |
| 과소_1_3미만 | medium_support_bucket | pigment__canvas | 6 | 10.3% |
| 과소_1_3미만 | medium_support_bucket | acrylic__canvas | 6 | 10.3% |
| 과소_1_3미만 | medium_support_bucket | mixed__canvas | 4 | 6.9% |
| 과소_1_3미만 | medium_support_bucket | pencil__other | 3 | 5.2% |
| 과소_1_3미만 | medium_support_bucket | mixed__other | 3 | 5.2% |
| 과소_1_3미만 | medium_support_bucket | oil__canvas | 3 | 5.2% |
| 과소_1_3미만 | actual_currency | USD | 56 | 96.6% |
| 과소_1_3미만 | actual_currency | KRW | 2 | 3.4% |
| APE_100pct이상 | svc_group_level | artist | 24 | 77.4% |
| APE_100pct이상 | svc_group_level | artist_size | 7 | 22.6% |
| APE_100pct이상 | svc_coverage_tier | low_n | 27 | 87.1% |
| APE_100pct이상 | svc_coverage_tier | medium_n | 4 | 12.9% |
| APE_100pct이상 | service_confidence_tier | medium | 16 | 51.6% |
| APE_100pct이상 | service_confidence_tier | low | 15 | 48.4% |
| APE_100pct이상 | medium_support_bucket | other__other | 8 | 25.8% |
| APE_100pct이상 | medium_support_bucket | oil__canvas | 5 | 16.1% |
| APE_100pct이상 | medium_support_bucket | ink__paper | 3 | 9.7% |
| APE_100pct이상 | medium_support_bucket | other__paper | 3 | 9.7% |
| APE_100pct이상 | medium_support_bucket | pencil__paper | 3 | 9.7% |
| APE_100pct이상 | medium_support_bucket | acrylic__canvas | 2 | 6.5% |
| APE_100pct이상 | medium_support_bucket | pigment__paper | 2 | 6.5% |
| APE_100pct이상 | medium_support_bucket | ink__other | 1 | 3.2% |
| APE_100pct이상 | actual_currency | USD | 31 | 100.0% |

## 7. 원인 정리

| 구분 | 주요 원인 | 해석 | 후속 보정 방향 |
|---|---|---|---|
| 근접 적중 | 작가 기준선과 작품 조건이 실제 가격대와 일치 | 같은 작가 과거 거래가 있는 Warm 구조가 잘 작동 | 해당 구조 유지, 안정 구간 신뢰도 상향 |
| 초저가 라벨 | 실제 가격이 1~30달러 | MAPE를 과도하게 키움 | 라벨 검수, 초저가/비작품 상품 분리 |
| 과대 예측 | 저가 소품/소형작을 일반 작품 기준선으로 예측 | 작가 기준선이 낮은 실제 판매가를 충분히 낮추지 못함 | 소품/edition/object 태그, 저가 구간 cap 보정 |
| 과소 예측 | 고가 작품/유명 작가/특수 프리미엄 | 유사 조건 통계가 고가 프리미엄을 충분히 반영하지 못함 | 고가 위험 태그, q90/상단 범위 활용, 작가 프리미엄 보정 |
| 초고가 라벨 | 10만 달러 이상 라벨 | 실제 초고가 작품인지, 통화/단위 입력 문제인지 확인 필요 | 초고가 검수 태그, 고가 작가 별도 보정 |
| 불확실 구간 | 가격 범위비가 큼 | 모델 내부에서도 가격대 판단이 넓게 흔들림 | 신뢰도 하향, 범위 중심 표시, 수동 검수 후보 |

## 8. 보고용 문장

- 0604 신규 테스트에서는 가격을 정확히 맞춘 사례는 없으나, 1% 이내로 매우 근접한 사례는 20건 확인됨.
- 잘 맞은 사례는 같은 작가의 과거 가격 기준선과 작품 조건이 실제 신규 가격과 일치한 경우가 많음.
- 오차가 큰 사례는 초저가 라벨, 저가 소품 과대 예측, 고가 작품 과소 예측으로 나뉨.
- 특히 50달러 미만 라벨 8건은 전체 MAPE를 크게 왜곡하므로 별도 검수 기준이 필요함.
- 10만 달러 이상 초고가 라벨 8건은 데이터 검수와 고가 프리미엄 보정이 모두 필요한 구간임.
- 서비스 적용 시 단일 가격만 표시하기보다 가격 범위, 신뢰도, 비교 표본 수, 검수 필요 여부를 함께 제공하는 것이 안전함.

## 9. 산출물

- `outputs/metric_summary.csv`
- `outputs/exact_near_summary.csv`
- `outputs/display_rounding_summary.csv`
- `outputs/near_top50.csv`
- `outputs/largest_errors_excluding_under50_top100.csv`
- `outputs/over_3x_excluding_under50.csv`
- `outputs/under_1_3x_excluding_under50.csv`
- `outputs/high_actual_over_100k_usd.csv`
- `reports/comprehensive_error_report.md`
- `reports/comprehensive_error_report.html`
