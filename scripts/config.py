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
    "ookami-kun": "オオカミくん",
    "ookami-chan": "オオカミちゃん",
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

# ── 今日好きシーズンマッピング ──
KYOUSUKI_SEASONS = {
    78: "卒業編2026(ドバイ)",
    77: "テグ編",
    76: "チェンマイ編",
    75: "チュンチョン編",
    74: "チェンマイ編2",
    73: "夏休み編2025inゴールドコースト",
    72: "ハロン編",
    71: "マクタン編",
    70: "ニュージーランド編",
    69: "卒業編2025inシンガポール",
    68: "卒業編2025inソウル",
    67: "冬休み編2024",
    66: "キョンジュ編",
    65: "ドンタン編",
    64: "夏休み編2024",
    63: "ホアヒン編",
    62: "ニャチャン編",
    61: "プサン編",
    60: "卒業編2024inセブ島",
    59: "バリ島編",
    58: "九龍編",
    57: "台北編",
    56: "カンヌン編",
    55: "夏休み編2023",
    54: "ダナン編2",
    53: "バンコク編",
    52: "フーコック編",
    51: "卒業編2023",
    50: "サムイ島編",
    49: "ダナン編",
    48: "プーケット編",
    47: "セブ島編2",
    46: "セブ島編",
    45: "小夏編",
    44: "紫陽花編2",
    43: "初虹編",
    42: "卒業編2022",
    41: "蜜柑編",
    40: "朝顔編",
    39: "金木犀編2",
    38: "秋桜編",
    37: "向日葵編",
    36: "卒業編2021",
    35: "春桜編",
    34: "冬桜編",
    33: "紅葉編",
    32: "金木犀編",
    31: "向日葵編2020",
    30: "卒業編2020",
    29: "春桜編2020",
    28: "冬休み編2019",
    27: "文化祭編",
    26: "夏休み編2019",
    25: "ハワイ編",
    24: "卒業編2019",
    23: "冬休み編2018",
    22: "秋桜編2018",
    21: "夏休み編2018",
    20: "ハワイ編2018",
    19: "卒業編2018",
    18: "冬休み編",
    17: "秋桜編2017",
    16: "夏休み編",
    15: "グアム編",
    14: "卒業編",
    13: "バレンタイン編",
    12: "冬休み編2017",
    11: "秋桜編2016",
    10: "夏休み編2016",
    9: "第9弾",
    8: "第8弾",
    7: "第7弾",
    6: "第6弾",
    5: "第5弾",
    4: "第4弾",
    3: "第3弾",
    2: "第2弾",
    1: "第1弾",
}

# ── オオカミくん/ちゃんシーズンマッピング ──
OOKAMI_SEASONS = {
    1: ("ookami-kun", "オオカミくんには騙されない(シーズン1)"),
    2: ("ookami-kun", "真冬のオオカミくんには騙されない(シーズン2)"),
    3: ("ookami-kun", "真夏のオオカミくんには騙されない(シーズン3)"),
    4: ("ookami-kun", "太陽とオオカミくんには騙されない(シーズン4)"),
    5: ("ookami-chan", "オオカミちゃんには騙されない(シーズン5)"),
    6: ("ookami-chan", "白雪とオオカミくんには騙されない(シーズン6)"),
    7: ("ookami-chan", "月とオオカミちゃんには騙されない(シーズン7)"),
    8: ("ookami-kun", "オオカミくんには騙されない(シーズン8)"),
    9: ("ookami-chan", "恋とオオカミには騙されない(シーズン9)"),
    10: ("ookami-chan", "虹とオオカミには騙されない(シーズン10)"),
    11: ("ookami-chan", "彼とオオカミちゃんには騙されない(シーズン11)"),
    12: ("ookami-chan", "オオカミちゃんとオオカミくんには騙されない(シーズン12)"),
    13: ("ookami-chan", "花束とオオカミちゃんには騙されない(シーズン13)"),
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

# オオカミくん/ちゃん: ookami1〜ookami13
for i in range(1, 14):
    slug, season_name = OOKAMI_SEASONS.get(i, ("ookami-kun", f"シーズン{i}"))
    if i < 10:
        urls = [f"{TEIBAN_BASE}/ookami0{i}", f"{TEIBAN_BASE}/ookami{i}"]
    else:
        urls = [f"{TEIBAN_BASE}/ookami{i}"]
    SCRAPE_TARGETS.append({
        "show_slug": slug,
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
