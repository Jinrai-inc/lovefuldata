"""
共通設定モジュール

全スクレイピングスクリプトで使用する定数・ユーティリティを定義。
"""

import os
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── ディレクトリ設定 ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── ログ設定 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("lovefuldata")

# ── HTTP設定 ──
REQUEST_INTERVAL = 2  # 秒（サーバー負荷軽減）
REQUEST_TIMEOUT = 15  # 秒
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}

# ── CSV列定義 ──
CAST_COLUMNS = [
    "show_slug",
    "season_name",
    "name",
    "display_name",
    "ig_username",
    "tiktok_username",
    "x_username",
    "youtube_url",
    "role",
    "gender",
    "age",
    "from_area",
    "height",
    "cast_status",
    "is_continuation",
    "note",
]

SEASON_COLUMNS = [
    "show_slug",
    "season_name",
    "year",
    "badge",
    "order",
    "start_date",
    "end_date",
]

# ── 番組slug→短縮名マッピング ──
SHOW_SHORT_MAP = {
    "kyou-suki": "今日好き",
    "ookami": "オオカミくん",
    "koi-ste": "恋ステ",
    "shuffle-island": "シャッフルアイランド",
    "love-power": "ラブパワーキングダム",
    "dra-koi": "ドラ恋",
    "ainosato": "あいの里",
    "love-is-blind-jp": "ラブイズブラインド",
    "bachelor-japan": "バチェラー",
    "bachelorette-japan": "バチェロレッテ",
    "love-transit": "ラブトランジット",
    "boyfriend": "ボーイフレンド",
    "offline-love": "オフラインラブ",
    "heart-signal-jp": "ハートシグナル",
}

# ── 今日好きシーズンマッピング（正式名 v1.1） ──
KYOUSUKI_SEASONS = {
    1: "第1弾",
    2: "第2弾",
    3: "第3弾",
    4: "第4弾",
    5: "第5弾",
    6: "第6弾",
    7: "第7弾",
    8: "第8弾",
    9: "第9弾",
    10: "夏休み編2016",
    11: "ベトナム・ダナン編",
    12: "韓国編",
    13: "オーストラリア編",
    14: "リベンジ編",
    15: "東京編",
    16: "沖縄編",
    17: "ハワイ編",
    18: "香港編",
    19: "チェジュ島編",
    20: "ハワイ夏休み編",
    21: "韓国ソウル編",
    22: "台湾編",
    23: "グアム編",
    24: "バリ島・冬休み編",
    25: "卒業編(サイパン)",
    26: "青い春編",
    27: "紫陽花編",
    28: "夏空編",
    29: "金木犀編",
    30: "秋月編",
    31: "星空編",
    32: "赤い糸編",
    33: "卒業編2021",
    34: "春桜編",
    35: "鈴蘭編",
    36: "霞草編",
    37: "向日葵編",
    38: "朝顔編",
    39: "花梨編",
    40: "落葉松編",
    41: "蜜柑編",
    42: "卒業編2022",
    43: "初虹編",
    44: "小夏編",
    45: "皐月編",
    46: "セブ島編",
    47: "プーケット編",
    48: "ダナン編",
    49: "サムイ島編",
    50: "沖縄編2",
    51: "卒業編2023",
    52: "フーコック編",
    53: "パタヤ編",
    54: "チュンムン編",
    55: "夏休み編2023",
    56: "カンヌン編",
    57: "台北編",
    58: "九龍編",
    59: "バリ島編",
    60: "卒業編2024inセブ島",
    61: "ニャチャン編",
    62: "プサン編",
    63: "ホアヒン編",
    64: "夏休み編2024",
    65: "ドンタン編",
    66: "キョンジュ編",
    67: "冬休み編2024",
    68: "卒業編2025inソウル",
    69: "卒業編2025inシンガポール",
    70: "ニュージーランド編",
    71: "マクタン編",
    72: "ハロン編",
    73: "夏休み編2025inゴールドコースト",
    74: "マカオ編",
    75: "チュンチョン編",
    76: "チェンマイ編",
    77: "テグ編",
    78: "卒業編2026inドバイ",
}

# ── オオカミくん/ちゃんシーズンマッピング（統合slug: "ookami"） ──
OOKAMI_SEASONS = {
    1: "オオカミくんには騙されない",
    2: "真冬のオオカミくんには騙されない",
    3: "真夏のオオカミくんには騙されない",
    4: "太陽とオオカミくんには騙されない",
    5: "オオカミちゃんには騙されない",
    6: "白雪とオオカミくんには騙されない",
    7: "月とオオカミちゃんには騙されない",
    8: "オオカミくんには騙されない(2021)",
    9: "恋とオオカミには騙されない",
    10: "虹とオオカミには騙されない",
    11: "彼とオオカミちゃんには騙されない",
    12: "オオカミちゃんとオオカミくんには騙されない",
}

# ── teiban-navi.com スクレイピング対象URL定義 ──
TEIBAN_BASE = "https://teiban-navi.com"

# 番組グループ定義: (show_slug, url_pattern, season_range, index_url)
SCRAPE_TARGETS = []

# 今日好き: kyousuki01〜kyousuki78
# 注: 初期のシーズン(1-9)はゼロ埋め(kyousuki01)の場合あり → 両パターンを試行
for i in range(1, 79):
    if i < 10:
        urls = [f"{TEIBAN_BASE}/kyousuki0{i}", f"{TEIBAN_BASE}/kyousuki{i}"]
    else:
        urls = [f"{TEIBAN_BASE}/kyousuki{i}"]
    season_name = KYOUSUKI_SEASONS.get(i, f"第{i}弾")
    SCRAPE_TARGETS.append({
        "show_slug": "kyou-suki",
        "season_number": i,
        "season_name": season_name,
        "urls": urls,
    })

# オオカミくん/ちゃん: ookami1〜ookami12（統合slug "ookami"）
for i in range(1, 13):
    season_name = OOKAMI_SEASONS.get(i, f"シーズン{i}")
    if i < 10:
        urls = [f"{TEIBAN_BASE}/ookami0{i}", f"{TEIBAN_BASE}/ookami{i}"]
    else:
        urls = [f"{TEIBAN_BASE}/ookami{i}"]
    SCRAPE_TARGETS.append({
        "show_slug": "ookami",
        "season_number": i,
        "season_name": season_name,
        "urls": urls,
    })

# 恋ステ: koisute (ページネーション形式 /koisute/1 〜 /koisute/26)
for i in range(1, 27):
    SCRAPE_TARGETS.append({
        "show_slug": "koi-ste",
        "season_number": i,
        "season_name": f"シーズン{i}",
        "urls": [f"{TEIBAN_BASE}/koisute/{i}"],
    })

# ドラ恋: dorakoi01〜dorakoi10 + dorakoi-kankoku
for i in range(1, 11):
    if i < 10:
        urls = [f"{TEIBAN_BASE}/dorakoi0{i}", f"{TEIBAN_BASE}/dorakoi{i}"]
    else:
        urls = [f"{TEIBAN_BASE}/dorakoi{i}"]
    SCRAPE_TARGETS.append({
        "show_slug": "dra-koi",
        "season_number": i,
        "season_name": f"シーズン{i}",
        "urls": urls,
    })
SCRAPE_TARGETS.append({
    "show_slug": "dra-koi",
    "season_number": 11,
    "season_name": "韓国ドラマな恋がしたい",
    "urls": [f"{TEIBAN_BASE}/dorakoi-kankoku"],
})

# シャッフルアイランド: shuffle-island, shuffle-island2〜4
for i in range(1, 5):
    suffix = "" if i == 1 else str(i)
    SCRAPE_TARGETS.append({
        "show_slug": "shuffle-island",
        "season_number": i,
        "season_name": f"シーズン{i}",
        "urls": [f"{TEIBAN_BASE}/shuffle-island{suffix}"],
    })

# バチェラージャパン: bachelor-member-1〜5
for i in range(1, 6):
    SCRAPE_TARGETS.append({
        "show_slug": "bachelor-japan",
        "season_number": i,
        "season_name": f"シーズン{i}",
        "urls": [f"{TEIBAN_BASE}/bachelor-member-{i}", f"{TEIBAN_BASE}/bachelor{i}"],
    })


def create_session():
    """リトライ付きHTTPセッションを作成"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session


def throttled_get(session, url, interval=REQUEST_INTERVAL):
    """レート制限付きGETリクエスト"""
    time.sleep(interval)
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            logger.warning(f"404 Not Found: {url}")
            return None
        if resp.status_code == 403:
            logger.warning(f"403 Forbidden: {url}")
            return None
        resp.raise_for_status()
        return resp
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return None


def output_path(filename):
    """出力ファイルパスを返す"""
    return os.path.join(OUTPUT_DIR, filename)
