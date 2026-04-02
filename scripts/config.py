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
    "ookami-chan": "オオカミくん",
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

# ── 今日好きシーズンマッピング（検証済み v2.0） ──
# 番号→(season_name, year) のタプル
KYOUSUKI_SEASONS = {
    # 2017年（第1弾〜第7弾）: レギュラー化前〜初期
    1: ("第1弾", 2017),               # 2017/5/20-21 単発
    2: ("第2弾", 2017),               # 2017/8/12-13 単発
    3: ("第3弾", 2017),               # 2017/10/16〜 レギュラー化
    4: ("第4弾", 2017),
    5: ("第5弾", 2017),
    6: ("第6弾", 2018),
    7: ("第7弾", 2018),               # in サイパン
    # 2018年（第8弾〜第14弾）
    8: ("第8弾", 2018),
    9: ("第9弾", 2018),               # in 軽井沢
    10: ("グアム編", 2018),            # 2018/7/9〜8/6
    11: ("ベトナム・ダナン編", 2018),   # 2018/8/27〜
    12: ("韓国編", 2018),              # 2018/10/8〜 (釜山)
    13: ("オーストラリア編", 2018),     # 2018/11〜
    14: ("ゲレンデ編", 2018),          # 2018/12/31 大晦日SP
    # 2019年（第15弾〜第24弾）
    15: ("東京編", 2019),              # 2019/1〜
    16: ("沖縄編", 2019),              # 2019/2〜3
    17: ("ハワイ編", 2019),            # 2019/4/1〜4/29
    18: ("香港編", 2019),              # 2019/5/6〜6/3
    19: ("チェジュ島編", 2019),         # 2019/6/10〜7/8
    20: ("ハワイ夏休み編", 2019),       # 2019/7/15〜8/26
    21: ("韓国ソウル編", 2019),         # 2019/9/2〜9/30
    22: ("台湾編", 2019),              # 2019/10/7〜
    23: ("グアム編2019", 2019),         # 2019/11/11〜12/9
    24: ("冬休み編", 2019),            # 2019/12/16〜2020/1/20
    # 2020年（第25弾〜第31弾）
    25: ("卒業編", 2020),              # 2020/1/27〜3/9
    26: ("青い春編", 2020),            # 2020/4/6〜5/4
    27: ("紫陽花編", 2020),            # 2020/6/15〜7/13
    28: ("夏空編", 2020),              # 2020/7/27〜8/31
    29: ("金木犀編", 2020),            # 2020/9/7〜10/5
    30: ("秋月編", 2020),              # 2020/10/12〜11/9
    31: ("星空編", 2020),              # 2020/11/16〜12/21
    # 2021年（第32弾〜第40弾）
    32: ("赤い糸編", 2021),            # 2021/1/4〜2/1
    33: ("卒業編2021", 2021),          # 2021/2/8〜3/15
    34: ("春桜編", 2021),              # 2021/4/5〜
    35: ("鈴蘭編", 2021),              # 2021/5〜
    36: ("霞草編", 2021),              # 2021/6/14〜
    37: ("向日葵編", 2021),            # 2021/7〜
    38: ("朝顔編", 2021),              # 2021/9〜
    39: ("秋桜編", 2021),              # 2021/10/18〜 ※v1.1では花梨編だったが誤り
    40: ("花梨編", 2021),              # 2021/11〜 ※v1.1では落葉松編だったが存在しない
    # 2022年（第41弾〜第49弾）
    41: ("蜜柑編", 2022),              # 2022/1/17〜2/14
    42: ("卒業編2022", 2022),          # 2022/2/21〜
    43: ("初虹編", 2022),              # 2022/4/4〜5/2
    44: ("皐月編", 2022),              # 2022/5/9〜 ※v1.1では小夏編だったが順序誤り
    45: ("小夏編", 2022),              # 2022/6/13〜7/11
    46: ("セブ島編", 2022),            # 2022/7/25〜8/29
    47: ("プーケット編", 2022),         # 2022/9/5〜10/10
    48: ("沖縄編2", 2022),             # 2022/10/24〜11/21 ※v1.1ではダナン編だったが誤り
    49: ("ダナン編", 2022),            # 2022/11/28〜12/26
    # 2023年（第50弾〜第58弾）
    50: ("サムイ島編", 2023),           # 2023/1/16〜
    51: ("卒業編2023", 2023),          # 2023/2/20〜
    52: ("フーコック編", 2023),         # 2023/4/3〜
    53: ("パタヤ編", 2023),            # 2023/5〜
    54: ("チュンムン編", 2023),         # 2023/6/12〜
    55: ("夏休み編2023", 2023),         # 2023/7〜
    56: ("カンヌン編", 2023),           # 2023/9〜
    57: ("台北編", 2023),              # 2023/10/16〜11/13
    58: ("九龍編", 2023),              # 2023/11/20〜12/25
    # 2024年（第59弾〜第67弾）
    59: ("バリ島編", 2024),            # 2024/1〜
    60: ("卒業編2024inセブ島", 2024),   # 2024/2〜3
    61: ("ニャチャン編", 2024),         # 2024/4/1〜4/29
    62: ("プサン編", 2024),            # 2024/5/6〜6/3
    63: ("ホアヒン編", 2024),           # 2024/6/10〜7/8
    64: ("夏休み編2024", 2024),         # 2024/7/22〜9/2
    65: ("ドンタン編", 2024),           # 2024/9/9〜10/7
    66: ("キョンジュ編", 2024),         # 2024/10/21〜11/18
    67: ("冬休み編2024", 2024),         # 2024/11/25〜12/30
    # 2025年（第68弾〜第76弾）
    68: ("卒業編2025inソウル", 2025),    # 2025/1/13〜2/10
    69: ("卒業編2025inシンガポール", 2025), # 2025/2/17〜
    70: ("ニュージーランド編", 2025),    # 2025/4/7〜5/5
    71: ("マクタン編", 2025),           # 2025/5/12〜6/9
    72: ("ハロン編", 2025),            # 2025/6/16〜7/14
    73: ("夏休み編2025inゴールドコースト", 2025), # 2025/7/28〜9/8
    74: ("マカオ編", 2025),            # 放送見送り（中止）
    75: ("チュンチョン編", 2025),       # 2025/10/6〜11/10
    76: ("チェンマイ編", 2025),         # 2025/11/17〜
    # 2026年（第77弾〜第78弾）
    77: ("テグ編", 2026),              # 2026/1/12〜
    78: ("卒業編2026inドバイ", 2026),   # 2026/2/16〜
}

# ── オオカミくん/ちゃんシーズンマッピング（検証済み v2.0） ──
# 統合slug: "ookami-chan"
OOKAMI_SEASONS = {
    1: ("オオカミくんには騙されない", 2017),
    2: ("真冬のオオカミくんには騙されない", 2017),
    3: ("真夏のオオカミくんには騙されない", 2018),
    4: ("太陽とオオカミくんには騙されない", 2018),
    5: ("オオカミちゃんには騙されない", 2019),
    6: ("白雪とオオカミくんには騙されない", 2019),
    7: ("月とオオカミちゃんには騙されない", 2020),
    8: ("恋とオオカミには騙されない", 2020),
    9: ("虹とオオカミには騙されない", 2022),
    10: ("薔薇とオオカミには騙されない", 2022),
    11: ("オオカミくんには騙されないit's my turn", 2023),
    12: ("オオカミちゃんには騙されないHave a nice trip!", 2023),
}

# ── 恋ステ シーズンマッピング ──
KOISTE_SEASONS = {i: (f"シーズン{i}", 2017 + (i - 1) // 4) for i in range(1, 27)}

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
    season_data = KYOUSUKI_SEASONS.get(i, (f"第{i}弾", 0))
    season_name = season_data[0] if isinstance(season_data, tuple) else season_data
    SCRAPE_TARGETS.append({
        "show_slug": "kyou-suki",
        "season_number": i,
        "season_name": season_name,
        "urls": urls,
    })

# オオカミくん/ちゃん: ookami1〜ookami12（統合slug "ookami-chan"）
for i in range(1, 13):
    season_data = OOKAMI_SEASONS.get(i, (f"シーズン{i}", 0))
    season_name = season_data[0] if isinstance(season_data, tuple) else season_data
    if i < 10:
        urls = [f"{TEIBAN_BASE}/ookami0{i}", f"{TEIBAN_BASE}/ookami{i}"]
    else:
        urls = [f"{TEIBAN_BASE}/ookami{i}"]
    SCRAPE_TARGETS.append({
        "show_slug": "ookami-chan",
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
