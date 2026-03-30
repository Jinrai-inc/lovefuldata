#!/usr/bin/env python3
"""
Phase 3: 補完スクレイピングスクリプト

teiban-navi.com以外のソースからメンバー情報を補完する。

対象:
- fstopics.com: 今日好き全弾の個別メンバー記事
- mdpr.jp: モデルプレスのニュース記事

入力: output/cast_filled.csv（Phase 2の出力）
出力: output/cast_supplement.csv（補完データ）

実行: python scripts/scrape_supplement.py
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
    SHOW_SHORT_MAP,
    create_session,
    logger,
    output_path,
)

# ── IG除外ワード ──
IG_EXCLUDE = {
    "instagram", "www", "com", "p", "reel", "reels", "stories",
    "accounts", "login", "explore", "direct", "tags", "tv",
    "official", "japan", "abema", "netflix",
}


def validate_ig_id(ig_id):
    if not ig_id:
        return ""
    ig_id = ig_id.strip().rstrip("/").lstrip("@")
    if ig_id.lower() in IG_EXCLUDE:
        return ""
    if not re.match(r'^[a-zA-Z0-9_.]{1,30}$', ig_id):
        return ""
    if ig_id.isdigit():
        return ""
    return ig_id


def scrape_fstopics_index(session):
    """
    fstopics.com から今日好き関連の記事一覧を取得する。
    サイト内検索を利用して全弾のメンバー記事URLを収集。
    """
    article_urls = []
    search_terms = ["今日好き メンバー", "今日好き プロフィール", "今日好き インスタ"]

    for term in search_terms:
        url = f"https://fstopics.com/?s={urllib.parse.quote(term)}"
        try:
            time.sleep(2)
            resp = session.get(url, timeout=10)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "fstopics.com/" in href and href not in article_urls:
                    if re.search(r'kyosuki|今日好き|メンバー', href + a_tag.get_text()):
                        article_urls.append(href)
        except Exception as e:
            logger.debug(f"fstopics検索失敗: {e}")

    logger.info(f"fstopics: {len(article_urls)}件の記事URL取得")
    return article_urls


def scrape_fstopics_article(session, article_url):
    """
    fstopics.com の個別メンバー記事ページからSNS情報を取得。
    """
    try:
        time.sleep(2)
        resp = session.get(article_url, timeout=10)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        text = soup.get_text()

        members = []

        # ページタイトルからシーズン情報を取得
        title = soup.find("title")
        title_text = title.get_text() if title else ""

        # 今日好きの弾数を検出
        season_m = re.search(r'今日好き[第]?(\d+)弾', title_text)
        season_number = int(season_m.group(1)) if season_m else 0

        # h2/h3タグをメンバー区切りとして使用
        headings = soup.find_all(["h2", "h3"])
        for i, heading in enumerate(headings):
            heading_text = heading.get_text(strip=True)
            if not heading_text or len(heading_text) > 50:
                continue
            if re.match(r'(目次|まとめ|関連|おすすめ|人気|ランキング)', heading_text):
                continue

            # この見出しから次の見出しまでのテキストを収集
            block_parts = []
            block_html = heading
            elem = heading.find_next_sibling()
            while elem:
                if elem.name in ["h2", "h3"]:
                    break
                block_parts.append(elem.get_text(separator="\n"))
                elem = elem.find_next_sibling()

            block_text = "\n".join(block_parts)

            # SNS情報があるブロックのみ
            if not re.search(r'インスタ|Instagram|instagram\.com', block_text, re.IGNORECASE):
                continue

            member = {col: "" for col in CAST_COLUMNS}
            member["show_slug"] = "kyou-suki"
            member["is_continuation"] = "FALSE"

            # 名前
            name_m = re.search(r'^(.+?)[（(]([^）)]+)[）)]', heading_text)
            if name_m:
                member["name"] = name_m.group(1).strip()
                member["display_name"] = name_m.group(2).strip()
            else:
                member["name"] = heading_text

            # Instagram
            ig_patterns = [
                re.compile(r'instagram\.com/([a-zA-Z0-9_.]+)', re.IGNORECASE),
                re.compile(r'インスタ[グラム]*[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
            ]
            for pat in ig_patterns:
                m = pat.search(block_text)
                if m:
                    ig = validate_ig_id(m.group(1))
                    if ig:
                        member["ig_username"] = ig
                        break

            # TikTok
            tt_m = re.search(r'(?:TikTok|tiktok\.com/@?)([a-zA-Z0-9_.]+)', block_text, re.IGNORECASE)
            if tt_m:
                member["tiktok_username"] = tt_m.group(1).strip().rstrip("/")

            # X
            x_m = re.search(r'(?:x\.com|twitter\.com)/([a-zA-Z0-9_]+)', block_text, re.IGNORECASE)
            if x_m:
                member["x_username"] = x_m.group(1)

            # 出身地
            area_m = re.search(r'出身[地：:]\s*(.+?)[\s\n]', block_text)
            if area_m:
                member["from_area"] = area_m.group(1).strip()

            # 身長
            height_m = re.search(r'身長[：:]\s*(\d{2,3})\s*(?:cm|㎝)?', block_text)
            if height_m:
                member["height"] = height_m.group(1)

            # 年齢
            age_m = re.search(r'年齢[：:]\s*(\d+)', block_text)
            if age_m:
                member["age"] = age_m.group(1)

            if member["ig_username"]:
                members.append(member)

        return members

    except Exception as e:
        logger.warning(f"fstopics記事スクレイピング失敗: {article_url}: {e}")
        return []


def scrape_fstopics_all(session):
    """fstopics.comから全メンバー情報を取得"""
    logger.info("=== fstopics.com スクレイピング開始 ===")

    article_urls = scrape_fstopics_index(session)
    all_members = []

    for i, url in enumerate(article_urls):
        logger.info(f"[{i+1}/{len(article_urls)}] {url}")
        members = scrape_fstopics_article(session, url)
        if members:
            all_members.extend(members)
            logger.info(f"  -> {len(members)}名のメンバー情報取得")

    logger.info(f"fstopics: 合計{len(all_members)}名のメンバー情報取得")
    return all_members


def main():
    logger.info("=== Phase 3: 補完スクレイピング 開始 ===")

    session = create_session()
    supplement_members = []

    # fstopics.com から補完データ取得
    fstopics_members = scrape_fstopics_all(session)
    supplement_members.extend(fstopics_members)

    # CSV出力
    output_csv = output_path("cast_supplement.csv")
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CAST_COLUMNS)
        writer.writeheader()
        writer.writerows(supplement_members)

    logger.info(
        f"\n=== 補完スクレイピング完了 ===\n"
        f"補完データ: {len(supplement_members)}件\n"
        f"出力: {output_csv}"
    )


if __name__ == "__main__":
    main()
