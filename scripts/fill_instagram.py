#!/usr/bin/env python3
"""
Phase 2: Instagram ID補完スクリプト

入力: output/cast_raw.csv（Phase 1の出力）
出力: output/cast_filled.csv（IG ID補完済み）

処理:
1. ig_usernameが空のレコードを抽出
2. 各まとめサイトの検索機能でIG IDを探索
3. 取得したIG IDをバリデーション後に補完

実行: python scripts/fill_instagram.py
"""

import csv
import os
import re
import sys
import time
import urllib.parse

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import (
    CAST_COLUMNS,
    HEADERS,
    SHOW_SHORT_MAP,
    create_session,
    logger,
    output_path,
)


# ── IG ID除外ワード ──
IG_EXCLUDE = {
    "instagram", "www", "com", "p", "reel", "reels", "stories",
    "accounts", "login", "explore", "direct", "tags", "tv",
    "official", "japan", "abema", "netflix", "about", "help",
    "developer", "legal", "privacy", "terms", "api",
    "explore", "directory", "nametag",
}


def validate_ig_id(ig_id):
    """Instagram IDのバリデーション"""
    if not ig_id:
        return ""
    ig_id = ig_id.strip().rstrip("/").lstrip("@")
    if ig_id.lower() in IG_EXCLUDE:
        return ""
    if not re.match(r'^[a-zA-Z0-9_.]{1,30}$', ig_id):
        return ""
    # 数字のみのIDは除外（ページ番号等の誤検出）
    if ig_id.isdigit():
        return ""
    return ig_id


def extract_ig_from_text(text):
    """テキストからInstagram IDを抽出"""
    patterns = [
        re.compile(r'instagram\.com/([a-zA-Z0-9_.]+)', re.IGNORECASE),
        re.compile(r'インスタグラム[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
        re.compile(r'インスタ[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
        re.compile(r'Instagram[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
        re.compile(r'IG[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
    ]
    for pat in patterns:
        m = pat.search(text)
        if m:
            ig = validate_ig_id(m.group(1))
            if ig:
                return ig
    return ""


def extract_tiktok_from_text(text):
    """テキストからTikTok IDを抽出"""
    patterns = [
        re.compile(r'tiktok\.com/@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
        re.compile(r'TikTok[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
    ]
    for pat in patterns:
        m = pat.search(text)
        if m:
            return m.group(1).strip().rstrip("/")
    return ""


def extract_x_from_text(text):
    """テキストからX(Twitter) IDを抽出"""
    patterns = [
        re.compile(r'(?:x|twitter)\.com/([a-zA-Z0-9_]+)', re.IGNORECASE),
        re.compile(r'(?:X|Twitter)[：:\s]*@?([a-zA-Z0-9_]+)', re.IGNORECASE),
    ]
    for pat in patterns:
        m = pat.search(text)
        if m:
            xid = m.group(1)
            if xid.lower() not in {"intent", "share", "home", "search", "i", "status"}:
                return xid
    return ""


def search_fstopics(session, name, show_short, season_name):
    """
    fstopics.com でメンバーのSNS情報を検索する。

    fstopics.comは今日好きメンバーの個別記事が充実しており、
    IG/TikTok/Xの情報が記載されている場合が多い。
    """
    queries = [
        f"{name} {show_short}",
        f"{name} {show_short} {season_name}",
    ]

    for query in queries:
        search_url = f"https://fstopics.com/?s={urllib.parse.quote(query)}"
        try:
            time.sleep(2)
            resp = session.get(search_url, timeout=10)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "lxml")

            # 検索結果から最も関連性の高い記事リンクを取得
            article_links = []
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                link_text = a_tag.get_text(strip=True)
                if "fstopics.com/" in href and name in link_text:
                    article_links.append(href)

            if not article_links:
                # 名前の一部でも試す
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    link_text = a_tag.get_text(strip=True)
                    if "fstopics.com/" in href and show_short in link_text:
                        article_links.append(href)

            # 最初の記事ページを取得
            for article_url in article_links[:2]:
                time.sleep(2)
                try:
                    art_resp = session.get(article_url, timeout=10)
                    if art_resp.status_code != 200:
                        continue
                    art_text = art_resp.text
                    ig = extract_ig_from_text(art_text)
                    if ig:
                        return {
                            "ig_username": ig,
                            "tiktok_username": extract_tiktok_from_text(art_text),
                            "x_username": extract_x_from_text(art_text),
                            "source": "fstopics",
                        }
                except Exception as e:
                    logger.debug(f"fstopics記事取得失敗: {article_url}: {e}")

        except Exception as e:
            logger.debug(f"fstopics検索失敗: {search_url}: {e}")

    return {}


def search_mdpr(session, name, show_short):
    """
    mdpr.jp (モデルプレス) でメンバーのSNS情報を検索する。
    """
    search_url = (
        f"https://mdpr.jp/search?q={urllib.parse.quote(f'{name} {show_short} インスタ')}"
    )
    try:
        time.sleep(2)
        resp = session.get(search_url, timeout=10)
        if resp.status_code != 200:
            return {}

        soup = BeautifulSoup(resp.text, "lxml")
        text = soup.get_text()
        ig = extract_ig_from_text(text)
        if ig:
            return {"ig_username": ig, "source": "mdpr"}
    except Exception as e:
        logger.debug(f"mdpr検索失敗: {e}")

    return {}


def search_general(session, name, display_name, show_short, season_name):
    """
    汎用的なWebサイト検索でIG IDを探す。
    各まとめサイトの記事を検索する。
    """
    # 検索対象サイト
    search_sites = [
        ("fstopics", lambda n, s: search_fstopics(session, n, s, season_name)),
        ("mdpr", lambda n, s: search_mdpr(session, n, s)),
    ]

    # 名前の候補リスト
    name_variants = [name]
    if display_name and display_name != name:
        name_variants.append(display_name)

    for site_name, search_func in search_sites:
        for n in name_variants:
            result = search_func(n, show_short)
            if result and result.get("ig_username"):
                return result
            time.sleep(1)

    return {}


def fill_instagram_ids(input_csv, output_csv):
    """メイン処理: IG IDが空のレコードを検索で補完する"""
    if not os.path.exists(input_csv):
        logger.error(f"入力ファイルが見つかりません: {input_csv}")
        return

    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    total = len(rows)
    empty_ig = [i for i, r in enumerate(rows) if not r.get("ig_username")]
    logger.info(f"全{total}件中、IG ID未取得: {len(empty_ig)}件")

    if not empty_ig:
        logger.info("全件IG ID取得済みです。補完不要。")
        # そのままコピー
        with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return

    session = create_session()
    filled = 0

    for idx in empty_ig:
        row = rows[idx]
        name = row.get("name", "")
        display_name = row.get("display_name", "")
        show_slug = row.get("show_slug", "")
        season_name = row.get("season_name", "")

        if not name and not display_name:
            continue

        show_short = SHOW_SHORT_MAP.get(show_slug, show_slug)

        logger.info(
            f"[{idx+1}/{total}] 検索中: {name} ({display_name}) "
            f"- {show_slug} {season_name}"
        )

        result = search_general(
            session, name, display_name, show_short, season_name
        )

        if result:
            if result.get("ig_username"):
                row["ig_username"] = result["ig_username"]
                filled += 1
                logger.info(f"  -> IG発見: @{result['ig_username']} (via {result.get('source', '?')})")

            # TikTok/Xも未取得なら補完
            if not row.get("tiktok_username") and result.get("tiktok_username"):
                row["tiktok_username"] = result["tiktok_username"]
            if not row.get("x_username") and result.get("x_username"):
                row["x_username"] = result["x_username"]
        else:
            logger.info(f"  -> 見つからず")

    # CSV出力
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    remaining = len(empty_ig) - filled
    logger.info(
        f"\n=== IG ID補完完了 ===\n"
        f"補完件数: {filled}件\n"
        f"未取得残り: {remaining}件\n"
        f"出力: {output_csv}"
    )


def main():
    logger.info("=== Phase 2: Instagram ID補完 開始 ===")
    input_csv = output_path("cast_raw.csv")
    output_csv = output_path("cast_filled.csv")
    fill_instagram_ids(input_csv, output_csv)


if __name__ == "__main__":
    main()
