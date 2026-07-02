"""Track 3 — Unified dataset builder (Artsy + Saatchi + Artue).

Codex schema v1 정합. 본 세션 Track 1 교훈 반영:
- artist_slug overlap=0 인 source는 explicit source_platform tag (학습용)
- 신규 작가 unmatched 시 수집 어려운 features 배제 (followers/total_works/gallery 등)
- Missing detection flags (has_year_made, has_birth_year, has_depth)
- Hedonic + GBM hybrid 학습 대상

운영 원칙 (필수 제약): 운영 수집 가능 / missingness explicit / source neutral.
평가 기준 (parsimony): 모델 선택 시 적은 피처로 동등 성능이면 그쪽 선호.

Schema v3 (User feedback 누적):
- v2 DROP: year_made / has_year_made / age_years (Saatchi raw에 없음)
- v2 DROP: artist_birth_year / has_birth_year / artist_age_at_execution (Saatchi/Artue raw)
- v2 DROP: attribution_class (Saatchi/Artue raw에 없음, 추정만)
- v3 DROP: nationality_region (98.4% korea, 변별력 없음)
- v3 DROP: has_nationality (100% = 1, constant)

Cold-start core (9):
- medium_category / support_category
- width_cm / height_cm / depth_cm / has_depth
- area_cm2 / log_area / orientation

Target:
- price_krw / ln_price_krw

Filters (Track 1 정합):
- price_krw 100K ~ 5B (이상치 제거)
- width_cm > 1, height_cm > 1

Output:
- data/track3_unified_v1.parquet
- data/track3_unified_v1_summary.json (row counts, distribution)

Usage:
    PYTHONPATH=src python3 scripts/track3/build_unified_dataset.py
"""
from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO / "data"
OUT_DIR = DATA_DIR
OUT_PATH = OUT_DIR / "track3_unified_v1.parquet"
OUT_SUMMARY = OUT_DIR / "track3_unified_v1_summary.json"
OUT_COLUMNS = OUT_DIR / "track3_unified_v1_columns.csv"
OUT_SAMPLE_KR = OUT_DIR / "track3_unified_v1_sample_kr.csv"
OUT_TRAIN = OUT_DIR / "track3_unified_v1_train.csv"
OUT_TRAIN_KR = OUT_DIR / "track3_unified_v1_train_kr.csv"
OUT_TRAIN_ML = OUT_DIR / "track3_unified_v1_train_ml.csv"
OUT_TRAIN_ML_KR = OUT_DIR / "track3_unified_v1_train_ml_kr.csv"

# Column 메타: 영문 → (한글명, 학습 마크, 그룹, 설명).
# 마크 의미: ★ = 학습 input 필수 / △ = 선택 (모델 의존) / · = 학습 미사용
COLUMN_SCHEMA: list[tuple[str, str, str, str, str]] = [
    ("source_platform", "소스플랫폼", "·", "IDs", "artsy/saatchi/artue — bias 위험 운영 모델 미사용"),
    ("source_listing_id", "소스 작품ID", "·", "IDs", "source 내 작품 ID (dedup용)"),
    ("artist_entity_id_raw", "작가ID", "·", "IDs", "source 내 작가 ID"),
    ("artist_name_raw", "작가명(원문)", "·", "IDs", "source 원본 영문/한글명 (debugging)"),
    ("artist_name_ko", "작가명(한글)", "★", "IDs", "한글 작가명 — cold-start 핵심 feature"),
    ("medium_category", "매체 분류", "★", "Core", "oil/acrylic/ink/watercolor/pigment/mixed/pastel/pencil/other"),
    ("support_category", "바탕 분류", "★", "Core", "canvas/paper/linen/panel/silk/metal/other"),
    ("width_cm", "가로(cm)", "△", "Core", "가로 — 선택 (트리: orientation+area로 cover)"),
    ("height_cm", "세로(cm)", "△", "Core", "세로 — 선택"),
    ("depth_cm", "깊이(cm)", "△", "Core", "깊이 (3D 작품) — measured 안 됨 → 0"),
    ("has_depth", "깊이있음", "★", "Core", "depth_cm > 0 (missing indicator)"),
    ("area_cm2", "면적(cm²)", "·", "Core", "width × height (log_area로 derive — 중복 회피)"),
    ("log_area", "면적(log)", "★", "Core", "log(area_cm2) — heavy tail 안정화"),
    ("estimated_ho", "추정 호수", "★", "Core", "한국 캔버스 호수 (F타입 보간) — 가격 segment"),
    ("orientation", "비율", "★", "Core", "portrait/landscape/square/unknown"),
    ("is_outlier", "이상값", "·", "Core", "옵션B 이상값 flag (학습 시 0만 사용 — df[df.is_outlier==0])"),
    ("price_amount_raw", "가격(원본통화)", "·", "가격", "원본 통화 가격 (USD/EUR/KRW 등)"),
    ("price_currency_raw", "원본통화", "·", "가격", "USD/KRW/EUR/GBP/HKD"),
    ("price_krw", "가격(소스KRW)", "·", "가격", "source 표기 KRW (보존만)"),
    ("was_converted", "환전여부", "·", "가격", "0=원래KRW / 1=외화환전됨"),
    ("price_krw_unified", "가격(통일KRW)", "·", "Target", "통일 환율 KRW (평가/복원 exp(pred)용)"),
    ("ln_price_krw_unified", "가격(log)", "★", "Target", "log(price_krw_unified) — 학습 target"),
]

CURRENT_YEAR = 2026  # listing year baseline (Track 1과 동일)
PRICE_MIN_KRW = 100_000
PRICE_MAX_KRW = 5_000_000_000

# Unified FX rates (Track 1 + Artsy raw 정합).
# 외화 → KRW 통일 환율. KRW는 1.0 (identity).
UNIFIED_FX_TO_KRW = {
    "USD": 1380.0,
    "EUR": 1530.0,
    "GBP": 1780.0,
    "HKD": 178.0,
    "KRW": 1.0,
}

# 작가 한글명 매핑 source files (모두 통합).
# Schema: 각 file 의 영문명(name_eng) + 한글명(name_kor) column 추출.
ARTIST_KO_MAP_SOURCES = [
    ("artist_profiles.csv", "name_eng", "name_kor"),
    ("artist_slug_mapping_expanded.csv", "en_name", "ko_name"),
    ("merged_artist_profiles.csv", "name_eng", "name_kor"),
    ("kada_artist_profiles.csv", "name_eng", "name_kor"),
    ("wikidata_korean_artists.csv", "name_en", "name_ko"),
]
# kada에서 placeholder로 사용된 한글명 — 제외
KO_NAME_PLACEHOLDERS = {"중견작가", "신진작가", "원로작가", "작고작가", "Unknown"}
HANGUL_PATTERN = re.compile(r"[가-힣]")

# 한국 성 Romanization 매핑 (Revised Romanization 표준 + 일반적 변형).
# User 단서: "1음절이면 성" — 영문 last token이 이 표에 있으면 한국 작가로 추정.
# 한국 성의 대부분 커버 (top 60 성씨로 인구 95%+ cover).
KOREAN_SURNAME_TO_KO = {
    # 5대 성 (인구 50%+)
    "kim": "김", "lee": "이", "yi": "이", "ree": "이", "rhee": "이",
    "park": "박", "bak": "박", "pak": "박",
    "choi": "최", "choe": "최",
    "jung": "정", "jeong": "정", "chung": "정", "cheong": "정",
    # 10대 성
    "kang": "강", "gang": "강",
    "cho": "조", "jo": "조",
    "yoon": "윤", "yun": "윤",
    "jang": "장", "chang": "장",
    "lim": "임", "im": "임",
    "han": "한",
    # 20대 성
    "shin": "신", "sin": "신",
    "seo": "서", "suh": "서", "sur": "서",
    "kwon": "권", "gwon": "권",
    "hwang": "황",
    "ahn": "안", "an": "안",
    "song": "송",
    "ryu": "류", "yu": "유", "you": "유", "yoo": "유",
    "hong": "홍",
    "jeon": "전", "jun": "전", "chun": "전",
    "go": "고", "ko": "고", "koh": "고",
    "moon": "문", "mun": "문",
    "yang": "양",
    "son": "손", "sohn": "손",
    "bae": "배", "pae": "배",
    "baek": "백", "paek": "백", "back": "백",
    # 30-50대 성
    "heo": "허", "huh": "허", "hur": "허",
    "yu_uh": "우",  # placeholder — 'woo' below
    "woo": "우",
    "nam": "남",
    "shim": "심", "sim": "심",
    "ha": "하",
    "no": "노", "noh": "노", "roh": "노", "row": "노",
    "ju": "주", "joo": "주", "chu": "주",
    "min": "민",
    "ryoo": "유", "ryo": "유",
    "ku": "구", "koo": "구", "gu": "구",
    "shin_uh": "신",
    "byun": "변", "byeon": "변",
    "ma": "마",
    "ohm": "엄", "uhm": "엄", "eom": "엄",
    "won": "원",
    "tak": "탁",
    "yeo": "여",
    "do": "도",
    "kil": "길", "gil": "길",
    "in": "인",
    "pyo": "표",
    "wang": "왕",
    "jeong_kr": "정",
    "sun": "선",
    "ho": "호",
    "chae": "채",
    "yeom": "염",
    "ban": "반",
    "jang_uh": "장",
    "joung": "정",
    # 추가: user 예시 + 한국 흔한 성
    "bang": "방", "pang": "방",
    "seok": "석", "suk": "석", "sok": "석",
    "oh": "오", "o": "오",
    "bac": "백",
    "yoon_kr": "윤",
    "kwak": "곽", "gwak": "곽",
    "ryu_l": "유",
    "ok": "옥",
    "jin": "진",  # 성 (보통 first name이지만 surname 가능)
    "ham": "함",
    "ku_kr": "구",
    # 추가 (v8): user 누락 보강
    "gam": "감", "kam": "감",
    "cha": "차", "char": "차",
    "ki": "기", "gi": "기",
    "ku": "구",
    "ki_kr": "기",
    # 추가 (v9): um=엄 surname 보강
    "um": "엄",
    "eom_kr": "엄",
    "kheem": "김", "gheem": "김",  # 드문 Kim 표기
    # 추가 (v11): leem=임, chon=천 등 surname variant
    "leem": "임", "leim": "임",
    "chon": "천", "cheon": "천",  # 한국 성 "천"
    "rhew": "유",
    # 추가 (v12): 드문 한국 성 + variant
    "yong": "용",
    "rhee_s": "이",
    "im_kr": "임", "yim": "임",
}

# 한국 성 중 first-token 일 가능성이 높은 5대 성 (모호 해결용).
# 예: "Choi Moon Seok" — Choi(first)와 Seok(last) 모두 성씨 매핑이 있어
# 영어식("First Last") 가정으로 Seok이 성으로 잡히는 실수를 보정.
# 본 집합에 속한 first token이 한국 성이면 Stage 3b (Last First) 우선 적용.
# 영어 흔한 first name → 한국어 표기 (음역으로 처리 불가능한 영단어).
# 예: "Eugene Ahn" 같은 한국계-영어이름 작가 처리용.
ENGLISH_FIRSTNAME_TO_KO = {
    # 한국계가 자주 쓰는 영어식 이름 + 한국식 발음
    "summer": "썸머", "winter": "윈터", "autumn": "어텀", "spring": "스프링",
    "lydia": "리디아", "lynn": "린", "noel": "노엘", "erin": "에린",
    "stone": "스톤", "rain": "레인", "moon_en": "문",
    "one": "원",  # "Sungone Jung", "Suk One" 같은 표기
    "eury": "유리", "lacey": "레이시", "karis": "카리스",
    # 추가 (v12): 빈도 audit 발견된 영어 first name
    "kris": "크리스", "denis": "데니스", "dennis": "데니스",
    "molly": "몰리", "johnny": "자니", "jenny": "제니",
    "melody": "멜로디", "stella": "스텔라", "jeremy": "제레미",
    "tina": "티나", "lina": "리나", "nina": "니나",
    "irene": "아이린", "ellen": "엘렌", "sally": "샐리",
    "betty": "베티", "amy": "에이미", "jane": "제인",
    "judy": "주디", "kelly": "켈리", "kerry": "케리",
    "polly": "폴리", "sandy": "샌디", "vicky": "비키",
    "wendy": "웬디", "yumi": "유미",
    "philip": "필립", "phillip": "필립", "kevin": "케빈",
    "henry": "헨리", "alex": "알렉스", "leo": "레오",
    "vakki": "박기",  # 한국 작가 nickname 자주 매핑
    "mia": "미아", "jenny": "제니", "rachel": "레이첼",
    "leo": "레오", "joy": "조이", "lily": "릴리",
    "sky": "스카이", "ray": "레이", "pearl": "펄",
    "rose": "로즈", "iris": "아이리스", "june": "준",
    "mark": "마크", "matt": "맷", "max": "맥스",
    "nick": "닉", "tony": "토니", "andy": "앤디",
    "billy": "빌리", "jimmy": "지미", "tommy": "토미",
    "ben": "벤", "kai": "카이", "lee_en": "리",
    "sun": "선", "luna": "루나",
    "eugene": "유진", "christine": "크리스틴", "stephanie": "스테파니",
    "stephen": "스티븐", "steven": "스티븐", "daniel": "다니엘",
    "justin": "저스틴", "brian": "브라이언", "jenny": "제니",
    "eric": "에릭", "tony": "토니", "david": "데이비드",
    "jay": "제이", "john": "존", "james": "제임스",
    "michael": "마이클", "sara": "사라", "sarah": "사라",
    "lily": "릴리", "anna": "안나", "andy": "앤디",
    "andrew": "앤드류", "anthony": "앤서니", "ben": "벤",
    "benjamin": "벤자민", "carol": "캐롤", "caroline": "캐롤라인",
    "catherine": "캐서린", "charles": "찰스", "chris": "크리스",
    "christopher": "크리스토퍼", "diana": "다이애나", "edward": "에드워드",
    "elizabeth": "엘리자베스", "emma": "엠마", "fiona": "피오나",
    "frank": "프랭크", "george": "조지", "grace": "그레이스",
    "helen": "헬렌", "henry": "헨리", "ian": "이안",
    "isabella": "이사벨라", "jack": "잭", "jason": "제이슨",
    "jennifer": "제니퍼", "jessica": "제시카", "joseph": "조셉",
    "julia": "줄리아", "karen": "카렌", "kate": "케이트",
    "kevin": "케빈", "laura": "로라", "leo": "레오",
    "lisa": "리사", "lucy": "루시", "mark": "마크",
    "martin": "마틴", "mary": "메리", "matt": "맷", "matthew": "매튜",
    "max": "맥스", "nick": "닉", "nicholas": "니콜라스",
    "oliver": "올리버", "patrick": "패트릭", "paul": "폴",
    "peter": "피터", "rachel": "레이첼", "richard": "리처드",
    "robert": "로버트", "ruth": "루스", "ryan": "라이언",
    "sam": "샘", "samuel": "사무엘", "scott": "스콧",
    "simon": "사이먼", "sophia": "소피아", "susan": "수잔",
    "thomas": "토마스", "tim": "팀", "tom": "톰",
    "victor": "빅터", "william": "윌리엄", "alex": "알렉스",
    "alice": "앨리스", "amy": "에이미", "angela": "안젤라",
    "amelia": "아멜리아", "noah": "노아", "lucas": "루카스",
    "ethan": "이단", "olivia": "올리비아", "emily": "에밀리",
}

KOREAN_SURNAME_FIRST_PRIORITY = {
    "kim", "lee", "park", "choi", "choe", "jung", "jeong", "chung",
    "kang", "cho", "jo", "yoon", "yun", "jang", "han", "shin", "sin",
    "seo", "suh", "kwon", "hwang", "ahn", "song", "hong", "bae", "baek",
    "moon", "yang", "son", "go", "ko", "ryu", "oh", "yoo", "yu",
    "no", "noh", "min", "im", "lim", "leem", "ham", "ku", "koo",
    "nam", "jeon", "rhee", "chon", "cheon",
}

# Romanization → Hangul 음절 매핑 (greedy longest match).
# 한국 이름 first name + 외국인 이름 한국어 발음 표기.
# 표 구조: 5-char → 4-char → 3-char → 2-char → 1-char (longest first match).
HANGUL_SYLLABLE_MAP: dict[str, str] = {
    # === 5-char (CV+yV+CC 등) ===
    "kyoung": "경", "kyeong": "경", "myoung": "명", "myeong": "명",
    "byoung": "병", "byeong": "병", "hyoung": "형", "hyeong": "형",
    "young": "영", "yeong": "영", "ryong": "용", "hyang": "향",
    "kwang": "광", "hwang": "황", "joong": "중", "joung": "정",
    "kyong": "경", "myong": "명", "byong": "병",
    # 추가 5-char: byung/hyeon 등 자주 누락
    "byung": "병", "pyung": "평", "tyung": "퉁", "ryung": "륭",
    "syung": "슝", "nyung": "능", "myung": "명", "dyung": "둥",
    "hyeon": "현", "kyeon": "견", "myeon": "면", "byeon": "변",
    "pyeon": "편", "ryeon": "련", "syeon": "션",
    "kweon": "권", "kwoen": "권",
    # 추가 5-char (v8): user 누락 보강
    "seung": "승", "jeung": "정", "cheung": "청", "leung": "량",
    "myeong": "명", "jeong": "정", "yeong": "영", "seong": "성",
    "jaegyu": "재규",  # whole-name shortcut
    "yoonji": "윤지",
    "saem": "샘",
    # === 6-char syllables (greedy range 6 활성화 활용) ===
    "kyeong": "경", "byeong": "병", "myeong": "명", "hyeong": "형",
    "pyeong": "평", "ryeong": "령", "syeong": "성",
    "kyoung": "경", "byoung": "병", "myoung": "명", "hyoung": "형",
    "pyoung": "평",
    "seonbi": "선비",
    # === 4-char ===
    "hyun": "현", "hyon": "현", "kyun": "균", "myun": "면",
    "byun": "변", "pyun": "편", "tyun": "튠",
    "hwan": "환", "kwan": "관", "rwan": "롼",
    "yeon": "연", "yeon": "연", "yong": "용", "yoon": "윤",
    "soon": "순", "moon": "문", "joon": "준", "doon": "둔",
    "geun": "근", "geon": "건", "seon": "선", "seul": "슬",
    "heun": "흔", "heon": "헌",
    "kyul": "규", "byul": "별", "myul": "멸", "pyul": "별",
    "syul": "슈", "tyul": "튤", "ryul": "률", "hyul": "휼",
    "ryun": "륜", "ryul": "률", "ryup": "륩",
    "deuk": "득", "seul": "슬", "neul": "늘",
    "wook": "욱", "kook": "국", "kyung": "경",
    "ahn": "안", "huh": "허", "hee": "희", "hye": "혜",
    "hyo": "효", "hyu": "휴",
    "yul": "율", "yup": "윱",
    # 추가 4-char: eun-/eul-/eum- + 자주 누락된 음절
    "eun": "은", "eul": "을", "eum": "음", "eup": "읍",
    "seok": "석", "suk": "석", "sok": "석",
    "hyuk": "혁", "hyok": "혁", "hyuck": "혁",
    # 추가 (v8): chul / choi / eui / ouk / zoo / gyu
    # chul/chol/cheol — 한국 영문 표기에서 "철" (예: "현철", "철수"). 표준 Revised는 cheol.
    "chul": "철", "chol": "철", "cheol": "철",
    "choi": "최", "choe": "최",
    "eui": "의", "ui": "의",
    "ouk": "옥", "uk": "욱",
    "zoo": "주", "zoon": "준", "joo": "주", "joon": "준",
    "gyu": "규", "kyu": "규", "gyul": "귤",
    "yoo": "유", "you": "유",
    # 추가 (v9): 한국 이름 자주 음절 보강
    "youn": "윤", "yun_kr": "윤",
    "tai": "태", "tay": "태",
    "byok": "벽", "byoek": "벽",
    "joeng": "정",
    "jihea": "지혜", "jihye": "지혜", "jihyea": "지혜",
    "kheem": "김", "gheem": "김",
    "miryang": "미향",  # 일부 영문 표기 특수
    "beom": "범", "beob": "법", "bup": "법",
    "gyo": "교", "kyo": "교",
    # 주의: "gyob"=교 같은 4-char 매핑은 추가하지 말것 — greedy가
    # "gyobeom" → gyob(교)+eom 로 잘못 분해. gyo(3)+beom(4) 분해가 정답.
    "gyom": "굠",
    "hyea": "혜", "hyae": "혜",
    "ryang": "량", "lyang": "량",
    "myang": "먕",
    # 추가 (v11): jee=지, seob=섭 등 누락 발견 케이스
    "jee": "지", "ree": "리", "lee_s": "리",
    "seob": "섭", "seop": "섭", "seub": "습", "seup": "습",
    "yeob": "엽", "yeop": "엽",
    "jeob": "접", "jeop": "접",
    "kyeob": "겁",
    "hyeob": "협", "hyeop": "협",
    "byeob": "법",
    # 추가 (v11): -jeon (전), -hoon (훈), -mook (묵), -taek (택) 등 빈출
    "jeon": "전", "jen_kr": "전",
    "cheon": "천",
    "hoon": "훈", "hwun": "훈", "hun": "훈",
    "mook": "묵", "muk_kr": "묵",
    "taek": "택", "taeg": "택",
    "gyeom": "겸", "kyeom": "겸",
    "yune": "윤", "yuen": "윤",
    "reum": "름", "leum": "름",
    "ram": "람", "lam": "람",
    "woon": "운", "wun": "운",
    "haeng": "행",
    "sook": "숙", "suk_kr": "숙",
    "hyen": "현", "hyeon_l": "현",
    "boram": "보람", "bora": "보라",
    "ryeob": "렵", "ryeop": "렵",
    "kook_kr": "국",
    "jeok": "적", "jok": "족",
    "geuk": "극", "guk": "국",
    "duek": "득", "deuk": "득",
    "yook": "육", "yuk": "육",
    "guen": "근", "geun": "근",
    "yeun": "연",
    "kook": "국",
    "ook": "욱",
    "weon": "원", "weon": "원",
    "byeok": "벽", "byok": "벽",
    "myeok": "멱",
    "saek": "색",
    "naek": "낵",
    "baek": "백", "paek": "백", "back": "백",
    # === 3-char (-ng / -k / -n / -m / -l / -p 받침) ===
    # -ang
    "bang": "방", "dang": "당", "gang": "강", "hang": "항", "jang": "장",
    "kang": "강", "mang": "망", "nang": "낭", "pang": "팡", "rang": "랑",
    "sang": "상", "tang": "탕", "wang": "왕", "yang": "양", "chang": "창",
    "lang": "랑",
    # -eng
    "deng": "뎅", "geng": "겡", "heng": "헹", "jeng": "젱",
    # -ing
    "bing": "빙", "ding": "딩", "ging": "깅", "hing": "힝", "jing": "징",
    "king": "킹", "ling": "링", "ming": "밍", "ning": "닝", "ping": "핑",
    "ring": "링", "sing": "싱", "ting": "팅", "wing": "윙", "ying": "잉",
    # -ong
    "bong": "봉", "dong": "동", "gong": "공", "hong": "홍", "jong": "종",
    "kong": "공", "long": "롱", "mong": "몽", "nong": "농", "pong": "퐁",
    "rong": "롱", "song": "송", "tong": "통", "yong": "용", "chong": "청",
    # -ung
    "bung": "붕", "dung": "둥", "gung": "궁", "hung": "흥", "jung": "정",
    "kung": "쿵", "lung": "룽", "mung": "뭉", "nung": "눙", "pung": "풍",
    "rung": "룽", "sung": "성", "tung": "퉁", "yung": "융", "chung": "충",
    # -an
    "ban": "반", "dan": "단", "gan": "간", "han": "한", "jan": "잔",
    "kan": "칸", "lan": "란", "man": "만", "nan": "난", "pan": "판",
    "ran": "란", "san": "산", "tan": "탄", "wan": "완", "yan": "얀",
    "chan": "찬", "shan": "샨",
    # -en
    "ben": "벤", "den": "덴", "gen": "겐", "hen": "헨", "jen": "젠",
    "ken": "켄", "len": "렌", "men": "맨", "nen": "넨", "pen": "펜",
    "ren": "렌", "sen": "센", "ten": "텐", "wen": "웬", "yen": "옌",
    "chen": "첸",
    # -in
    "bin": "빈", "din": "딘", "gin": "긴", "hin": "힌", "jin": "진",
    "kin": "킨", "lin": "린", "min": "민", "nin": "닌", "pin": "핀",
    "rin": "린", "sin": "신", "tin": "틴", "win": "윈", "yin": "인",
    "chin": "친", "shin": "신",
    # -im / -rim
    "bim": "빔", "dim": "딤", "gim": "김", "him": "힘", "jim": "짐",
    "kim": "킴", "lim": "림", "mim": "밈", "nim": "님", "pim": "핌",
    "rim": "림", "sim": "심", "tim": "팀", "yim": "임",
    "shim": "심", "shik": "식",
    # -wan / -won / -wun
    "hwan": "환", "kwan": "관", "rwan": "롼",
    "hwon": "환", "kwon": "권", "rwon": "권",
    # -on
    "bon": "본", "don": "돈", "gon": "곤", "hon": "혼", "jon": "존",
    "kon": "콘", "lon": "론", "mon": "몬", "non": "논", "pon": "폰",
    "ron": "론", "son": "선", "ton": "톤", "won": "원", "yon": "연",
    # -un / -oon
    "bun": "분", "dun": "둔", "gun": "군", "hun": "훈", "jun": "준",
    "kun": "쿤", "lun": "룬", "mun": "문", "nun": "눈", "pun": "푼",
    "run": "룬", "sun": "선", "tun": "툰", "yun": "윤", "chun": "천",
    # -al / -el / -il / -ol / -ul
    "bal": "발", "dal": "달", "gal": "갈", "hal": "할", "jal": "잘",
    "kal": "칼", "lal": "랄", "mal": "말", "nal": "날", "pal": "팔",
    "ral": "랄", "sal": "살", "tal": "탈", "wal": "왈", "yal": "얄",
    "bel": "벨", "del": "델", "gel": "겔", "hel": "헬", "jel": "젤",
    "bil": "빌", "dil": "딜", "gil": "길", "hil": "힐", "jil": "질",
    "kil": "킬", "mil": "밀", "nil": "닐", "pil": "필", "ril": "릴",
    "sil": "실", "til": "틸",
    "bol": "볼", "dol": "돌", "gol": "골", "hol": "홀", "jol": "졸",
    "kol": "콜", "lol": "롤", "mol": "몰", "nol": "놀", "pol": "폴",
    "rol": "롤", "sol": "솔", "tol": "톨",
    "bul": "불", "dul": "둘", "gul": "굴", "hul": "훌", "jul": "줄",
    "kul": "쿨", "mul": "물", "nul": "눌", "pul": "풀", "rul": "룰",
    "sul": "술", "tul": "툴", "yul": "율",
    # -ak / -ek / -ik / -ok / -uk
    "bak": "박", "dak": "닥", "gak": "각", "hak": "학", "jak": "작",
    "kak": "칵", "lak": "락", "mak": "막", "nak": "낙", "pak": "팍",
    "rak": "락", "sak": "삭", "tak": "탁", "wak": "왁", "yak": "약",
    "bek": "벡", "dek": "덱", "gek": "겍", "hek": "헥", "jek": "젝",
    "bik": "빅", "dik": "딕", "gik": "긱", "hik": "힉", "jik": "직",
    "kik": "킥", "mik": "믹", "nik": "닉", "pik": "픽", "rik": "릭",
    "sik": "식", "tik": "틱",
    "bok": "복", "dok": "독", "gok": "곡", "hok": "혹", "jok": "족",
    "kok": "콕", "lok": "록", "mok": "목", "nok": "녹", "pok": "폭",
    "rok": "록", "sok": "속", "tok": "톡", "wok": "왁", "yok": "욕",
    "buk": "북", "duk": "둑", "guk": "국", "huk": "훅", "juk": "죽",
    "kuk": "쿡", "luk": "룩", "muk": "묵", "nuk": "눅", "puk": "푹",
    "ruk": "룩", "suk": "석", "tuk": "툭", "wuk": "욱", "yuk": "육",
    "suk": "석", "wook": "욱",
    "hyok": "혁", "hyuk": "혁",
    # -ap / -ep / -ip / -op / -up
    "bap": "밥", "dap": "답", "gap": "갑", "hap": "합", "jap": "잡",
    "kap": "캅", "lap": "랍", "map": "맙", "nap": "납", "pap": "팝",
    "rap": "랍", "sap": "삽", "tap": "탑",
    "bep": "벱", "gep": "겝", "hep": "헵", "jep": "젭",
    "bip": "빕", "dip": "딥", "gip": "깁", "hip": "힙", "jip": "집",
    "kip": "킵", "mip": "밉", "nip": "닙", "pip": "핍", "rip": "립",
    "sip": "십", "tip": "팁",
    "bop": "봅", "dop": "돕", "gop": "곱", "hop": "홉", "jop": "좁",
    "kop": "콥", "lop": "롭", "mop": "몹", "nop": "놉", "pop": "팝",
    "rop": "롭", "sop": "솝", "top": "톱",
    "bup": "붑", "dup": "둡", "gup": "굽", "hup": "훕", "jup": "줍",
    "kup": "쿱", "mup": "뭅", "nup": "눕", "pup": "풉", "rup": "룹",
    "sup": "섭", "tup": "툽",
    # -ae 류
    "bae": "배", "dae": "대", "gae": "개", "hae": "해", "jae": "재",
    "kae": "캐", "lae": "래", "mae": "매", "nae": "내", "pae": "배",
    "rae": "래", "sae": "새", "tae": "태", "wae": "왜", "yae": "얘",
    "chae": "채", "shae": "섀",
    # -eo
    "beo": "버", "deo": "더", "geo": "거", "heo": "허", "jeo": "저",
    "keo": "커", "meo": "머", "neo": "너", "peo": "퍼", "reo": "러",
    "seo": "서", "teo": "터", "yeo": "여", "cheo": "처", "sheo": "셔",
    # -oo / -oa / -ue 등
    "boo": "부", "doo": "두", "goo": "구", "hoo": "후", "joo": "주",
    "koo": "쿠", "loo": "루", "moo": "무", "noo": "누", "poo": "푸",
    "roo": "루", "soo": "수", "too": "투", "woo": "우", "yoo": "유",
    # 자주 사용 음절 (한국 이름)
    "kim": "김", "lee": "이", "yi": "이", "park": "박",
    "ahn": "안", "hee": "희", "hye": "혜", "hyo": "효", "hyu": "휴",
    "ji": "지", "ye": "예", "jin": "진", "jun": "준",
    "kwon": "권", "sub": "섭", "sup": "섭", "hwa": "화", "kwa": "콰",
    # 추가 (v8): ki/gi/cha 등 일반 음절
    "ki": "기", "gi": "기", "cha": "차", "gam": "감", "kam": "감",
    "sy": "시", "sye": "셰",
    # 추가 (v9): 2-3 char 자주 누락
    "oh": "오",  # 1-char "o"=오와 충돌 방지
    "ok": "옥", "og": "옥",
    "il": "일", "ir": "일", "yil": "일",
    "ip": "입", "ib": "입",
    "yt": "이",
    "ae": "애",  # 이미 있음
    "ah": "아",
    "ee": "이",  # 이미 있음
    "mee": "미",
    "hea": "혜", "heah": "혜",
    "gab": "갑", "gap": "갑",
    "ub": "웁", "up": "웁",
    "ud": "우드",
    "zin": "진", "zi": "지",
    "ts": "쓰",
    "tz": "츠",
    # 추가 (v12): pyo=표 등 audit 발견
    "pyo": "표", "phyo": "표",
    "cho_s": "조", "joh": "조",
    "tt": "트", "tch": "치",
    # 추가: jam/sam/nam/dam/ham
    "jam": "잼", "sam": "샘", "ham": "햄", "dam": "댐", "nam": "남",
    "bom": "봄", "gom": "곰", "tom": "톰", "rom": "롬", "hom": "홈",
    "kom": "콤", "lom": "롬", "mom": "맘", "pom": "폼", "som": "솜",
    "dum": "둠", "gum": "굼", "hum": "험", "jum": "줌", "kum": "쿰",
    "lum": "룸", "mum": "맘", "num": "넘", "pum": "품", "rum": "룸",
    "sum": "섬", "tum": "툼", "yum": "윰",
    "yang": "양", "yong": "용", "yung": "융",
    # cha / che / chi / cho / chu / chae
    "cha": "차", "che": "체", "chi": "치", "cho": "초", "chu": "추",
    "chae": "채", "chai": "차이",
    # sha / she / shi / sho / shu
    "sha": "샤", "she": "셰", "shi": "시", "sho": "쇼", "shu": "슈",
    "shim": "심",
    # tha / the / thi / tho / thu (외국어)
    "tha": "타", "the": "더", "thi": "디", "tho": "도", "thu": "두",
    # gha 등
    "gha": "가", "ghe": "게", "ghi": "기", "gho": "고", "ghu": "구",
    # -en
    "ren": "렌",
    # === 2-char ===
    "an": "안", "ah": "아", "ae": "애", "ai": "아이", "au": "아우",
    "ba": "바", "bo": "보", "bu": "부", "be": "베", "bi": "비",
    "ca": "카", "co": "코", "cu": "쿠", "ce": "세", "ci": "시",
    "da": "다", "de": "데", "di": "디", "do": "도", "du": "두",
    "ea": "이아", "ee": "이", "eo": "어", "eu": "으", "ei": "에이",
    "fa": "파", "fe": "페", "fi": "피", "fo": "포", "fu": "푸",
    "ga": "가", "ge": "게", "gi": "기", "go": "고", "gu": "구",
    "ha": "하", "he": "헤", "hi": "히", "ho": "호", "hu": "후",
    "ja": "자", "je": "제", "ji": "지", "jo": "조", "ju": "주",
    "ka": "카", "ke": "케", "ko": "코", "ku": "쿠",
    "la": "라", "le": "레", "li": "리", "lo": "로", "lu": "루",
    "ma": "마", "me": "메", "mi": "미", "mo": "모", "mu": "무",
    "na": "나", "ne": "네", "ni": "니", "no": "노", "nu": "누",
    "oa": "오아", "oe": "외", "oi": "오이", "ou": "오우",
    "pa": "파", "pe": "페", "pi": "피", "po": "포", "pu": "푸",
    "ra": "라", "re": "레", "ri": "리", "ro": "로", "ru": "루",
    "sa": "사", "se": "세", "si": "시", "so": "소", "su": "수",
    "ta": "타", "te": "테", "ti": "티", "to": "토", "tu": "투",
    "ua": "우아", "ue": "우에", "ui": "의", "un": "운",
    "va": "바", "ve": "베", "vi": "비", "vo": "보", "vu": "부",
    "wa": "와", "we": "웨", "wi": "위", "wo": "워",
    "ya": "야", "ye": "예", "yi": "이", "yo": "요", "yu": "유",
    "za": "자", "ze": "제", "zi": "지", "zo": "조", "zu": "주",
    "en": "엔", "in": "인", "on": "온",
    "ar": "아", "er": "어", "ir": "이", "or": "오", "ur": "우",
    "ng": "응",
    # === 1-char (fallback) ===
    "a": "아", "b": "브", "c": "크", "d": "드", "e": "에",
    "f": "프", "g": "그", "h": "흐", "i": "이", "j": "즈",
    "k": "크", "l": "르", "m": "므", "n": "느", "o": "오",
    "p": "프", "q": "크", "r": "르", "s": "스", "t": "트",
    "u": "우", "v": "브", "w": "우", "x": "엑스", "y": "이", "z": "즈",
}


# ─── Medium / Support 분류 (Track 1 정합) ───
SUPPORT_RULES = [
    ("canvas", ["canvas"]),
    ("paper", ["paper", "korean paper", "jangji", "hanji", "washi"]),
    ("linen", ["linen"]),
    ("panel", ["panel", "wood", "board", "mdf"]),
    ("silk", ["silk"]),
    ("metal", ["aluminum", "aluminium", "stainless", "copper", "brass"]),
]
MEDIUM_RULES = [
    ("oil", ["oil"]),
    ("acrylic", ["acrylic"]),
    ("ink", ["ink", "sumi"]),
    ("watercolor", ["watercolor", "gouache", "aquarelle"]),
    ("pigment", ["pigment", "color on"]),
    ("mixed", ["mixed media", "mixed technique"]),
    ("pastel", ["pastel"]),
    ("pencil", ["pencil", "graphite", "charcoal"]),
]


def classify_support(text: str) -> str:
    if pd.isna(text):
        return "other"
    t = str(text).lower()
    for label, keywords in SUPPORT_RULES:
        if any(kw in t for kw in keywords):
            return label
    return "other"


def classify_medium(text: str) -> str:
    if pd.isna(text):
        return "other"
    t = str(text).lower()
    for label, keywords in MEDIUM_RULES:
        if any(kw in t for kw in keywords):
            return label
    return "other"


def parse_year(value) -> int | None:
    """Parse year from date / year string. Returns int or None."""
    if pd.isna(value):
        return None
    s = str(value)
    m = re.search(r"(\d{4})", s)
    if m:
        y = int(m.group(1))
        if 1800 <= y <= 2030:
            return y
    return None


def orientation_from_dims(w: float, h: float) -> str:
    if pd.isna(w) or pd.isna(h) or w <= 0 or h <= 0:
        return "unknown"
    ratio = h / w
    if abs(ratio - 1.0) < 0.1:
        return "square"
    return "portrait" if ratio > 1 else "landscape"


def _norm_en_variants(name: str) -> set[str]:
    """영문명 정규화 + 순서 swap variants (한국식 vs 서양식).

    예: "Lee Ufan" → {"leeufan", "ufanlee"}
    """
    if name is None or pd.isna(name) or str(name).strip() == "":
        return set()
    cleaned = re.sub(r"[^a-z\s]", "", str(name).lower())
    tokens = [t for t in cleaned.split() if t]
    if not tokens:
        return set()
    variants = {"".join(tokens)}
    if len(tokens) >= 2:
        variants.add("".join(tokens[::-1]))  # last-first ↔ first-last
    return variants


def build_artist_ko_map(data_dir: Path) -> dict[str, str]:
    """모든 매핑 source 통합 → {en_norm_variant: ko_name} dict."""
    mapping: dict[str, str] = {}
    total_rows = 0
    for fname, en_col, ko_col in ARTIST_KO_MAP_SOURCES:
        path = data_dir / fname
        if not path.exists():
            logger.warning(f"  매핑 source 없음: {fname}")
            continue
        try:
            df = pd.read_csv(path, low_memory=False)
        except Exception as e:
            logger.warning(f"  매핑 source load 실패 {fname}: {e}")
            continue
        if en_col not in df.columns or ko_col not in df.columns:
            logger.warning(f"  매핑 source col 누락 {fname}: {en_col}/{ko_col}")
            continue
        sub = df[[en_col, ko_col]].dropna()
        # 한글 character 있어야 + placeholder 제외
        sub = sub[~sub[ko_col].astype(str).isin(KO_NAME_PLACEHOLDERS)]
        sub = sub[sub[ko_col].astype(str).str.contains(HANGUL_PATTERN, na=False)]
        total_rows += len(sub)
        for _, row in sub.iterrows():
            en, ko = str(row[en_col]), str(row[ko_col])
            # 같은 영문 이름이라도 "Lee Ufan" / "Ufan Lee" 순서 차이가 있어
            # 정방향과 역방향 variant를 모두 같은 한글명에 연결한다.
            for variant in _norm_en_variants(en):
                if variant and variant not in mapping:
                    mapping[variant] = ko
    logger.info(f"  artist_name_ko mapping: {len(mapping)} entries (raw {total_rows})")

    # Manual overrides (사용자 검수 결과) — 기존 매핑을 OVERRIDE.
    # 형식: artist_name_raw, artist_name_ko
    # 위치: scripts/track3/artist_ko_manual_overrides.csv (git tracked config)
    override_path = Path(__file__).parent / "artist_ko_manual_overrides.csv"
    if override_path.exists():
        try:
            overrides = pd.read_csv(override_path)
            n_ovr = 0
            for _, row in overrides.iterrows():
                raw_name = str(row["artist_name_raw"]).strip()
                ko = str(row["artist_name_ko"]).strip()
                if not raw_name or not ko or ko.lower() == "nan":
                    continue
                # _norm_en_variants로 정규화한 모든 variant를 override
                for variant in _norm_en_variants(raw_name):
                    if variant:
                        mapping[variant] = ko  # 덮어쓰기 (manual 최우선)
                        n_ovr += 1
            logger.info(f"  Manual overrides 적용: {len(overrides)} 작가 / {n_ovr} variant")
        except Exception as e:
            logger.warning(f"  Manual overrides load 실패: {e}")

    return mapping


def _korean_surname_from_token(token: str) -> str | None:
    """영문 token이 한국 성으로 추정되면 한글 성 반환."""
    if not token:
        return None
    t = re.sub(r"[^a-z]", "", token.lower())
    return KOREAN_SURNAME_TO_KO.get(t)


def _romanize_to_hangul(text: str) -> str:
    """영문 음역 → 한글 (greedy longest match).

    한국 이름 first name + 외국인 이름 한국어 발음 표기 cover.
    예: "soyun" → "소윤", "yeji" → "예지", "smith" → "스미스"
    정확하지 않을 수 있으나 user 의도 "최대한 한글로 표기" 정합.

    주의: Track3 legacy 확정 로직이다. 신규 운영 표준화에서는 이 결과를
    canonical 한글명으로 바로 쓰지 말고 후보/검수 큐로만 보내야 한다.
    """
    s = re.sub(r"[^a-z]", "", str(text).lower())
    if not s:
        return ""
    result = []
    i = 0
    while i < len(s):
        matched = False
        # 6-char까지 검사: kyeong=경, byeong=병, myoung=명, hyoung=형 등.
        # 가장 긴 chunk부터 맞추는 greedy 방식이라 사전에 없는 이름은
        # 어색하게 쪼개질 수 있다. 예: 일부 로마자 한국 이름 오표기.
        for length in (6, 5, 4, 3, 2, 1):
            chunk = s[i : i + length]
            if chunk in HANGUL_SYLLABLE_MAP:
                result.append(HANGUL_SYLLABLE_MAP[chunk])
                i += length
                matched = True
                break
        if not matched:
            i += 1
    return "".join(result)


def _extract_first_last_tokens(name: str) -> tuple[str, str] | None:
    """영문명에서 first / last 토큰 추출. (first_concatenated, last_token)."""
    cleaned = re.sub(r"[^a-zA-Z\s\-]", "", str(name))
    tokens = [t for t in re.split(r"[\s\-]+", cleaned) if t]
    if len(tokens) < 2:
        return None
    # 한국식 영문 표기 2가지 — 본 함수는 두 후보를 모두 반환하지 않고,
    # 매칭 logic에서 각 후보 시도. 일반적 "First Last" 가정.
    return ("".join(tokens[:-1]).lower(), tokens[-1].lower())


def _capitalize_first(s: str) -> str:
    return s[0].upper() + s[1:].lower() if s else ""


def lookup_artist_name_ko(name: str, ko_map: dict[str, str]) -> str | None:
    """artist_name_raw → name_ko (5-stage cascading, 한글 우선).

    Stage 1: 매핑 dict exact lookup (영문 + name-order swap) — 가장 정확
    Stage 2: raw에 한글 있으면 추출 (예: "Songfeel 송필" → "송필")
    Stage 3: 한국 성 + 한글 음역 — 한국 작가
             "Bang Soyun" → "방소윤" (성=방, 이름=Soyun 음역)
             "Kim Hongbin" → "김홍빈" (한국식 Last First)
    Stage 4: 외국인 이름도 음역 — 비-한국 성 전체 음역
             "Smith John" → "스미스존" (외국 작가 한국어 발음 표기)
    Stage 5: None
    """
    if name is None or pd.isna(name):
        return None
    name_str = str(name).strip()
    if not name_str:
        return None

    # Stage 1: dict lookup
    # 검수/외부 매핑에 이미 등록된 이름이면
    # 자동 음역보다 항상 우선한다.
    for variant in _norm_en_variants(name_str):
        if variant in ko_map:
            return ko_map[variant]

    # Stage 2: raw에 한글 직접 있음
    if HANGUL_PATTERN.search(name_str):
        match = re.search(r"[가-힣][가-힣\s]*[가-힣]|[가-힣]", name_str)
        if match:
            return match.group(0).strip()

    # Stage 3 / 4: 영문 토큰화
    # metadata 제거: "(b.1984)", "(1965-)", "[2024]" 등 괄호 내 + 숫자
    cleaned = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", name_str)
    cleaned = re.sub(r"[^a-zA-Z\s\-]", "", cleaned)
    # len>=1 보존 — "Geon U Cha"의 "U"(우) 같은 1글자 토큰도 의미 있음
    tokens = [t for t in re.split(r"[\s\-]+", cleaned) if t]
    if not tokens:
        return None

    if len(tokens) == 1:
        # 단일 토큰 — 한국 성 → 영어 사전 → 음역 순
        # 단일 토큰은 동명이인/브랜드명 가능성이 높아
        # 신규 시스템에서는 검수 대상으로 보는 편이 안전하다.
        ko = _korean_surname_from_token(tokens[0])
        if ko:
            return ko
        tok_norm = re.sub(r"[^a-z]", "", tokens[0].lower())
        if tok_norm in ENGLISH_FIRSTNAME_TO_KO:
            return ENGLISH_FIRSTNAME_TO_KO[tok_norm]
        # 외국 단일 이름 음역
        return _romanize_to_hangul(tokens[0]) or None

    # 다중 토큰 — 모호 해결: first가 5대 성 우선 매핑이면 Stage 3b 먼저
    first_norm = re.sub(r"[^a-z]", "", tokens[0].lower())
    last_norm = re.sub(r"[^a-z]", "", tokens[-1].lower())
    ko_surname_first = _korean_surname_from_token(tokens[0])
    ko_surname_last = _korean_surname_from_token(tokens[-1])

    # Stage 3 우선 순위 결정:
    # - first가 5대 우선 surname + last도 surname → first 우선 (Choi Moon Seok)
    # - 그 외 → last 우선 (영어식 "First Last")
    use_first_as_surname = (
        ko_surname_first
        and first_norm in KOREAN_SURNAME_FIRST_PRIORITY
        and ko_surname_last is not None  # 둘 다 surname인 모호 case만
    )

    def _convert_first_part(tokens_part: list[str]) -> str:
        """first name part 변환: 영어 사전 우선, 그 외 음역."""
        out = []
        for tok in tokens_part:
            tok_norm = re.sub(r"[^a-z]", "", tok.lower())
            if tok_norm in ENGLISH_FIRSTNAME_TO_KO:
                # Matthew, John처럼 흔한 영어 이름은 사전 표기를 우선한다.
                out.append(ENGLISH_FIRSTNAME_TO_KO[tok_norm])
            else:
                # 사전에 없으면 legacy 음절표로 후보를 만든다.
                out.append(_romanize_to_hangul(tok))
        return "".join(out)

    if use_first_as_surname:
        # Stage 3b 우선 — "Last First" 한국식
        rest_ko = _convert_first_part(tokens[1:])
        return f"{ko_surname_first}{rest_ko}" if rest_ko else ko_surname_first

    # Stage 3a: "First Last" — last가 한국 성
    if ko_surname_last:
        first_ko = _convert_first_part(tokens[:-1])
        return f"{ko_surname_last}{first_ko}" if first_ko else ko_surname_last

    # Stage 3b: "Last First" (한국식) — first 토큰이 한국 성
    if ko_surname_first:
        rest_ko = _convert_first_part(tokens[1:])
        return f"{ko_surname_first}{rest_ko}" if rest_ko else ko_surname_first

    # Stage 4: 외국인 이름 — 전체 음역 (토큰별 영어 사전 우선 적용)
    full_ko = _convert_first_part(tokens)
    return full_ko if full_ko else None


def nationality_to_region(nat) -> str:
    """간단 region bucket — high-cardinality 방지."""
    if pd.isna(nat):
        return "unknown"
    t = str(nat).lower().strip()
    if any(k in t for k in ["korea", "korean", "대한민국"]):
        return "korea"
    if any(
        k in t
        for k in [
            "china",
            "chinese",
            "taiwan",
            "japan",
            "japanese",
            "vietnam",
            "thai",
            "indonesia",
            "philippines",
            "malaysia",
            "singapore",
            "asian",
        ]
    ):
        return "asia_other"
    if any(k in t for k in ["united states", "american", "usa", "u.s."]):
        return "north_america"
    if any(
        k in t
        for k in [
            "united kingdom",
            "british",
            "german",
            "french",
            "italian",
            "spanish",
            "dutch",
            "european",
            "swedish",
            "swiss",
            "polish",
        ]
    ):
        return "europe"
    return "other"


# ─── Source별 mapping ───


def load_artsy() -> pd.DataFrame:
    logger.info("Loading Artsy raw…")
    a = pd.read_csv(DATA_DIR / "artsy_kr_artworks.csv", low_memory=False)
    logger.info(f"  Artsy raw: {len(a)} rows")

    df = pd.DataFrame({"source_listing_id": a["artwork_id"].astype(str).values})
    df["source_platform"] = "artsy"
    df["medium_category"] = a["medium"].apply(classify_medium)
    df["support_category"] = a["medium"].apply(classify_support)
    df["width_cm"] = pd.to_numeric(a["width_cm"], errors="coerce")
    df["height_cm"] = pd.to_numeric(a["height_cm"], errors="coerce")
    df["depth_cm"] = pd.to_numeric(a["depth_cm"], errors="coerce")
    df["has_depth"] = (df["depth_cm"].notna() & (df["depth_cm"] > 0)).astype(int)
    df["price_krw"] = pd.to_numeric(a["price_krw"], errors="coerce")
    # Hybrid 가격 — 원본 + 통일 환율
    df["price_amount_raw"] = pd.to_numeric(a["price_amount"], errors="coerce")
    df["price_currency_raw"] = a["price_currency"].fillna("USD").astype(str)
    df["artist_entity_id_raw"] = a["artist_slug"].astype(str)
    df["artist_name_raw"] = a["artist_name"].astype(str)
    return df


def load_saatchi() -> pd.DataFrame:
    logger.info("Loading Saatchi raw…")
    s = pd.read_csv(DATA_DIR / "saatchi_kr_artworks.csv", low_memory=False)
    logger.info(f"  Saatchi raw: {len(s)} rows")

    df = pd.DataFrame({"source_listing_id": s["artwork_id"].astype(str).values})
    df["source_platform"] = "saatchi"
    df["medium_category"] = s["mediums"].apply(classify_medium)
    df["support_category"] = s["materials"].apply(classify_support)
    df["width_cm"] = pd.to_numeric(s["width_cm"], errors="coerce")
    df["height_cm"] = pd.to_numeric(s["height_cm"], errors="coerce")
    df["depth_cm"] = pd.to_numeric(s["depth_cm"], errors="coerce")
    df["has_depth"] = (df["depth_cm"].notna() & (df["depth_cm"] > 0)).astype(int)
    df["price_krw"] = pd.to_numeric(s["price_krw"], errors="coerce")
    # Hybrid 가격 — Saatchi는 USD 단일 (확인됨, 100%)
    df["price_amount_raw"] = pd.to_numeric(s["price_usd"], errors="coerce")
    df["price_currency_raw"] = "USD"
    df["artist_entity_id_raw"] = s["artist_id"].astype(str)
    df["artist_name_raw"] = (
        s["artist_first_name"].fillna("") + " " + s["artist_last_name"].fillna("")
    ).str.strip()
    return df


def load_artue() -> pd.DataFrame:
    logger.info("Loading Artue raw…")
    a = pd.read_csv(DATA_DIR / "artue_테스트_가격포함.csv", low_memory=False)
    logger.info(f"  Artue raw: {len(a)} rows")

    df = pd.DataFrame({"source_listing_id": a["Handle"].astype(str).values})
    df["source_platform"] = "artue"
    df["medium_category"] = a["Medium (EN)"].apply(classify_medium)
    df["support_category"] = a["Medium (EN)"].apply(classify_support)
    df["width_cm"] = pd.to_numeric(a["Width (cm)"], errors="coerce")
    df["height_cm"] = pd.to_numeric(a["Height (cm)"], errors="coerce")
    df["depth_cm"] = pd.to_numeric(a["Depth (cm)"], errors="coerce")
    df["has_depth"] = (df["depth_cm"].notna() & (df["depth_cm"] > 0)).astype(int)
    df["price_krw"] = pd.to_numeric(a["Price (KRW)"], errors="coerce")
    # Hybrid 가격 — Artue는 USD 표기 (확인됨, 100%)
    df["price_amount_raw"] = pd.to_numeric(a["Price (USD)"], errors="coerce")
    df["price_currency_raw"] = "USD"
    df["artist_entity_id_raw"] = a["Handle"].astype(str)
    df["artist_name_raw"] = a["Artist"].astype(str)
    return df


# ─── Derived features + filter ───


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """area_cm2 / log_area / orientation + estimated_ho + Hybrid 가격."""
    df["area_cm2"] = df["width_cm"] * df["height_cm"]
    df["log_area"] = df["area_cm2"].apply(
        lambda v: math.log(v) if pd.notna(v) and v > 0 else float("nan")
    )
    df["orientation"] = df.apply(
        lambda r: orientation_from_dims(r["width_cm"], r["height_cm"]),
        axis=1,
    )

    # 호수 (estimated_ho): 면적 → F 타입 캔버스 호수 보간.
    # 기존 visionai 모듈의 area_to_ho_f() 사용 (HO_F_TABLE 기반 np.interp).
    # 예: 60.6×50.0 cm (3030cm²) → 12호 / 72.7×60.6 cm (4406cm²) → 20호.
    from visionai.price_engine.preprocessing.dimension_parser import area_to_ho_f
    df["estimated_ho"] = df["area_cm2"].apply(
        lambda x: round(area_to_ho_f(x), 2) if pd.notna(x) and x > 0 else 0.0
    )

    # depth NaN → 0 (has_depth가 missingness 표시)
    df["depth_cm"] = df["depth_cm"].fillna(0)

    # Hybrid 가격:
    # - 원래 KRW면 그대로 (price_krw 사용), was_converted=0
    # - 외화면 통일 환율 (UNIFIED_FX_TO_KRW) 적용, was_converted=1
    def compute_unified(row):
        cur = str(row["price_currency_raw"]).upper().strip()
        amount = row["price_amount_raw"]
        if cur == "KRW":
            return row["price_krw"] if pd.notna(row["price_krw"]) else float("nan")
        if pd.isna(amount) or amount <= 0:
            return float("nan")
        rate = UNIFIED_FX_TO_KRW.get(cur)
        if rate is None:
            return float("nan")  # unknown currency
        return float(amount) * rate

    df["price_krw_unified"] = df.apply(compute_unified, axis=1)
    df["was_converted"] = (df["price_currency_raw"].str.upper().str.strip() != "KRW").astype(int)
    return df


def apply_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """가격/크기 필터. price_krw_unified 기준 (학습 target)."""
    n0 = len(df)
    drops = {}

    # price filter — unified 기준 (학습 target)
    mask = df["price_krw_unified"].notna() & (df["price_krw_unified"] > 0)
    drops["price_null_or_zero"] = (~mask).sum()
    df = df[mask].copy()

    mask = (df["price_krw_unified"] >= PRICE_MIN_KRW) & (df["price_krw_unified"] <= PRICE_MAX_KRW)
    drops["price_out_of_range"] = (~mask).sum()
    df = df[mask].copy()

    # size filter
    mask = (
        df["width_cm"].notna()
        & (df["width_cm"] > 1)
        & df["height_cm"].notna()
        & (df["height_cm"] > 1)
    )
    drops["size_invalid"] = (~mask).sum()
    df = df[mask].copy()

    # ln_price — unified 기준 (학습 target)
    df["ln_price_krw_unified"] = np.log(df["price_krw_unified"])

    # is_outlier — 옵션 B (학습 시 df[df.is_outlier==0] 필터 권장)
    # 조건:
    #   A. 명확한 입력 오류: area <50 OR >100K, 단가 <100 KRW/cm², price <200K
    #   B. 도메인 외: ho=0 (1호 미만 미니어처), ho>200 (호수표 외삽 한계),
    #               ko_len>15 (확실한 외국 작가 음역)
    unit_price = df["price_krw_unified"] / df["area_cm2"].replace(0, np.nan)
    ko_len = df["artist_name_ko"].str.len().fillna(0)
    is_out = (
        (df["area_cm2"] < 50)
        | (df["area_cm2"] > 100_000)
        | (unit_price < 100)
        | (df["price_krw_unified"] < 200_000)
        | (df["estimated_ho"] == 0)
        | (df["estimated_ho"] > 200)
        | (ko_len > 15)
    )
    df["is_outlier"] = is_out.astype(int)
    drops["is_outlier_flagged"] = int(is_out.sum())

    drops["total_in"] = n0
    drops["total_kept"] = len(df)
    drops["kept_pct"] = round(100 * len(df) / max(n0, 1), 2)
    drops["training_kept"] = int((~is_out).sum())
    drops["training_kept_pct"] = round(100 * (~is_out).sum() / max(n0, 1), 2)

    return df, drops


# ─── Main ───


def main() -> None:
    logger.info("=" * 70)
    logger.info("Track 3 unified dataset builder (Artsy + Saatchi + Artue)")
    logger.info("=" * 70)

    # 작가 한글명 매핑 build
    logger.info("Building artist_name_ko mapping...")
    ko_map = build_artist_ko_map(DATA_DIR)

    a = load_artsy()
    s = load_saatchi()
    artue = load_artue()

    unified = pd.concat([a, s, artue], ignore_index=True)
    logger.info(f"\nConcat: {len(unified)} rows total")

    # artist_name_ko apply
    unified["artist_name_ko"] = unified["artist_name_raw"].apply(
        lambda n: lookup_artist_name_ko(n, ko_map)
    )
    n_ko = unified["artist_name_ko"].notna().sum()
    logger.info(f"  artist_name_ko matched: {n_ko:,}/{len(unified):,} ({100*n_ko/len(unified):.1f}%)")

    unified = add_derived(unified)
    unified, drops = apply_filters(unified)
    logger.info(f"After filter: {len(unified)} rows kept (drops={drops})")

    # column order — schema v13 (is_outlier 추가 / 22 cols)
    cols = [
        # IDs (학습 비feature)
        "source_platform",
        "source_listing_id",
        "artist_entity_id_raw",
        "artist_name_raw",
        "artist_name_ko",
        # Cold-start core (11) — width/height/area + estimated_ho + is_outlier flag
        "medium_category",
        "support_category",
        "width_cm",
        "height_cm",
        "depth_cm",
        "has_depth",
        "area_cm2",
        "log_area",
        "estimated_ho",
        "orientation",
        "is_outlier",
        # Hybrid 가격 (4) — 원본 + 통일 환율 + 환전 flag
        "price_amount_raw",
        "price_currency_raw",
        "price_krw",
        "was_converted",
        # Target (2) — 학습용 unified
        "price_krw_unified",
        "ln_price_krw_unified",
    ]
    unified = unified[cols]

    # Save
    unified.to_parquet(OUT_PATH, index=False)
    logger.info(f"\n✅ Saved: {OUT_PATH} ({len(unified)} rows / {len(cols)} cols)")

    # Column dictionary (한글명 + 학습 마크 + 그룹 + 설명)
    dict_df = pd.DataFrame(
        COLUMN_SCHEMA, columns=["영문 컬럼명", "한글명", "학습", "그룹", "설명"]
    )
    dict_df.to_csv(OUT_COLUMNS, index=False, encoding="utf-8-sig")
    logger.info(f"✅ Columns dict: {OUT_COLUMNS}")

    # Sample (500 rows) — 한글 헤더 + ★ 마크 (Excel/Numbers view용)
    rename_map = {col: f"{mark} {ko} ({col})" for col, ko, mark, _, _ in COLUMN_SCHEMA}
    unified.head(500).rename(columns=rename_map).to_csv(
        OUT_SAMPLE_KR, index=False, encoding="utf-8-sig"
    )
    logger.info(f"✅ Sample (한글 헤더): {OUT_SAMPLE_KR}")

    # 학습용 CSV (is_outlier=0만)
    train_df = unified[unified["is_outlier"] == 0].copy()
    train_df.to_csv(OUT_TRAIN, index=False, encoding="utf-8-sig")
    logger.info(
        f"✅ Train (영문 헤더, is_outlier=0만): {OUT_TRAIN} ({len(train_df)} rows)"
    )

    # 학습용 CSV — 한글 헤더 + ★ 마크 view
    train_df.rename(columns=rename_map).to_csv(
        OUT_TRAIN_KR, index=False, encoding="utf-8-sig"
    )
    logger.info(
        f"✅ Train (한글 헤더, is_outlier=0만): {OUT_TRAIN_KR} ({len(train_df)} rows)"
    )

    # 학습용 CSV — ★ 컬럼만 (학습 input 7개 + target 1)
    ml_cols = [col for col, _, mark, _, _ in COLUMN_SCHEMA if mark == "★"]
    train_ml_df = train_df[ml_cols].copy()
    train_ml_df.to_csv(OUT_TRAIN_ML, index=False, encoding="utf-8-sig")
    logger.info(
        f"✅ Train ML (★ {len(ml_cols)} cols, 영문): {OUT_TRAIN_ML} ({len(train_ml_df)} rows)"
    )

    train_ml_df.rename(columns=rename_map).to_csv(
        OUT_TRAIN_ML_KR, index=False, encoding="utf-8-sig"
    )
    logger.info(
        f"✅ Train ML (★ {len(ml_cols)} cols, 한글): {OUT_TRAIN_ML_KR} ({len(train_ml_df)} rows)"
    )

    # Summary
    summary = {
        "rows": int(len(unified)),
        "cols": int(len(cols)),
        "by_source": unified["source_platform"].value_counts().to_dict(),
        "price_stats_unified": {
            "median_krw": int(unified["price_krw_unified"].median()),
            "mean_krw": int(unified["price_krw_unified"].mean()),
            "q05": int(unified["price_krw_unified"].quantile(0.05)),
            "q95": int(unified["price_krw_unified"].quantile(0.95)),
        },
        "fx_rates_unified": UNIFIED_FX_TO_KRW,
        "was_converted_counts": unified["was_converted"].value_counts().to_dict(),
        "currency_distribution": unified["price_currency_raw"].value_counts().to_dict(),
        "missingness_flags": {
            "has_depth": int(unified["has_depth"].sum()),
        },
        "missingness_flags_by_source": {
            src: {
                "has_depth": int(unified[unified["source_platform"] == src]["has_depth"].sum()),
                "n_rows": int((unified["source_platform"] == src).sum()),
            }
            for src in unified["source_platform"].unique()
        },
        "medium_category_top5": unified["medium_category"].value_counts().head(5).to_dict(),
        "support_category_top5": unified["support_category"].value_counts().head(5).to_dict(),
        "orientation": unified["orientation"].value_counts().to_dict(),
        "filter_drops": drops,
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    logger.info(f"✅ Summary: {OUT_SUMMARY}")

    # Print summary
    print("\n" + "=" * 70)
    print(f"Track 3 unified dataset v1 — {len(unified):,} rows / {len(cols)} cols")
    print("=" * 70)
    print(f"\nBy source: {summary['by_source']}")
    print(
        f"Price (KRW unified): median={summary['price_stats_unified']['median_krw']:,}, "
        f"mean={summary['price_stats_unified']['mean_krw']:,}"
    )
    print(f"Currency distribution: {summary['currency_distribution']}")
    print(f"Was converted (0=KRW raw / 1=외화 환전): {summary['was_converted_counts']}")
    print(f"FX rates applied: {summary['fx_rates_unified']}")
    print(f"Missingness (has_X=1 count):")
    for k, v in summary["missingness_flags"].items():
        pct = 100 * v / len(unified)
        print(f"  {k}: {v:,} ({pct:.1f}%)")
    print(f"\nPer-source missingness:")
    for src, stats in summary["missingness_flags_by_source"].items():
        n = stats["n_rows"]
        print(f"  {src} (n={n:,}): has_depth {stats['has_depth']:,} ({100*stats['has_depth']/n:.1f}%)")


if __name__ == "__main__":
    main()
