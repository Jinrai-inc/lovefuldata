#!/usr/bin/env python3
"""
Phase 1: teiban-navi.com メインスクレイピングスクリプト

実行: python scripts/scrape_teiban.py
出力: output/cast_raw.csv, output/seasons_raw.csv
"""

import csv
import re
import sys
import os

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import (
    CAST_COLUMNS,
    SEASON_COLUMNS,
    KYOUSUKI_SEASONS,
    SCRAPE_TARGETS,
    create_session,
    logger,
    output_path,
    throttled_get,
)


# ── Instagram ID抽出 ──
IG_PATTERNS = [
    re.compile(r'instagram\.com/([a-zA-Z0-9_.]+)', re.IGNORECASE),
    re.compile(r'インスタグラム[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
    re.compile(r'Instagram[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
    re.compile(r'インスタ[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
    re.compile(r'IG[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
]

# ── TikTok ID抽出 ──
TIKTOK_PATTERNS = [
    re.compile(r'tiktok\.com/@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
    re.compile(r'TikTok[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
    re.compile(r'ティックトック[：:\s]*@?([a-zA-Z0-9_.]+)', re.IGNORECASE),
]

# ── X(Twitter) ID抽出 ──
X_PATTERNS = [
    re.compile(r'(?:x|twitter)\.com/([a-zA-Z0-9_]+)', re.IGNORECASE),
    re.compile(r'(?:X|Twitter|ツイッター)[：:\s]*@?([a-zA-Z0-9_]+)', re.IGNORECASE),
]

# ── YouTube URL抽出 ──
YT_PATTERNS = [
    re.compile(r'(https?://(?:www\.)?youtube\.com/[@a-zA-Z0-9_/%-]+)', re.IGNORECASE),
    re.compile(r'(https?://youtu\.be/[a-zA-Z0-9_-]+)', re.IGNORECASE),
    re.compile(r'Youtube[：:\s]*(https?://\S+)', re.IGNORECASE),
]

# ── IG ID除外ワード ──
IG_EXCLUDE = {
    "instagram", "www", "com", "p", "reel", "reels", "stories",
    "accounts", "login", "explore", "direct", "tags", "tv",
    "official", "japan", "abema", "netflix", "about", "help",
    "developer", "legal", "privacy", "terms", "api",
}


def validate_ig_id(ig_id):
    """Instagram IDのバリデーション"""
    if not ig_id:
        return ""
    ig_id = ig_id.strip().rstrip("/")
    if ig_id.lower() in IG_EXCLUDE:
        return ""
    if not re.match(r'^[a-zA-Z0-9_.]{1,30}$', ig_id):
        return ""
    return ig_id


def validate_social_id(social_id):
    """汎用SNS IDのバリデーション"""
    if not social_id:
        return ""
    social_id = social_id.strip().rstrip("/")
    if len(social_id) > 50:
        return ""
    return social_id


def extract_with_patterns(text, patterns, validator=None):
    """パターンリストから最初にマッチしたものを返す"""
    for pat in patterns:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip("/")
            if validator:
                val = validator(val)
            if val:
                return val
    return ""


def get_season_name_from_page(soup, season_number, show_slug):
    """ページタイトルからシーズン名を自動抽出"""
    if show_slug == "kyou-suki":
        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text()
            # パターン: 「今日好き第77弾(テグ編)」or「今日好き卒業編2026(ドバイ)」
            m = re.search(r'[（(]([^）)]+)[）)]', title_text)
            if m:
                return m.group(1)
            # パターン: 「第XX弾」の後の編名
            m = re.search(r'第\d+弾\s*[（(]?([^\s）)｜|]+編)', title_text)
            if m:
                return m.group(1)
        return KYOUSUKI_SEASONS.get(season_number, f"第{season_number}弾")
    return None


def detect_gender_from_context(text, heading_text=""):
    """コンテキストから性別を推定"""
    combined = heading_text + " " + text
    if re.search(r'女子メンバー|女子高生|女の子|♀', combined):
        return "f"
    if re.search(r'男子メンバー|男子高生|男の子|♂', combined):
        return "m"
    return ""


def parse_member_block(text, html_block, show_slug, season_name, gender_hint=""):
    """
    1つのメンバーブロックからデータを抽出する。

    text: HTMLタグ除去済みテキスト
    html_block: 元のHTMLブロック（リンク抽出用）
    """
    member = {col: "" for col in CAST_COLUMNS}
    member["show_slug"] = show_slug
    member["season_name"] = season_name
    member["is_continuation"] = "FALSE"
    member["gender"] = gender_hint

    # ── Instagram ID ──
    # まずHTMLからリンクを探す（最も信頼性が高い）
    if hasattr(html_block, 'find_all'):
        for a_tag in html_block.find_all("a", href=True):
            href = a_tag["href"]
            m = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', href)
            if m:
                ig = validate_ig_id(m.group(1))
                if ig:
                    member["ig_username"] = ig
                    break
    # テキストからも探す（リンクが見つからない場合）
    if not member["ig_username"]:
        member["ig_username"] = extract_with_patterns(
            text, IG_PATTERNS, validate_ig_id
        )

    # ── TikTok ID ──
    if hasattr(html_block, 'find_all'):
        for a_tag in html_block.find_all("a", href=True):
            href = a_tag["href"]
            m = re.search(r'tiktok\.com/@?([a-zA-Z0-9_.]+)', href)
            if m:
                member["tiktok_username"] = validate_social_id(m.group(1))
                break
    if not member["tiktok_username"]:
        member["tiktok_username"] = extract_with_patterns(
            text, TIKTOK_PATTERNS, validate_social_id
        )

    # ── X(Twitter) ID ──
    if hasattr(html_block, 'find_all'):
        for a_tag in html_block.find_all("a", href=True):
            href = a_tag["href"]
            m = re.search(r'(?:x|twitter)\.com/([a-zA-Z0-9_]+)', href)
            if m:
                xid = m.group(1)
                if xid.lower() not in {"intent", "share", "home", "search", "i"}:
                    member["x_username"] = validate_social_id(xid)
                    break
    if not member["x_username"]:
        member["x_username"] = extract_with_patterns(
            text, X_PATTERNS, validate_social_id
        )

    # ── YouTube URL ──
    if hasattr(html_block, 'find_all'):
        for a_tag in html_block.find_all("a", href=True):
            href = a_tag["href"]
            if "youtube.com/" in href or "youtu.be/" in href:
                member["youtube_url"] = href.strip()
                break
    if not member["youtube_url"]:
        member["youtube_url"] = extract_with_patterns(text, YT_PATTERNS)

    # ── 名前の抽出 ──
    # パターン1: 「名前（よみがな）」
    name_m = re.search(r'^(.+?)[（(]([^）)]+)[）)]', text.strip())
    if name_m:
        member["name"] = name_m.group(1).strip()
        member["display_name"] = name_m.group(2).strip()
    else:
        # パターン2: テキスト最初の行が名前
        first_line = text.strip().split("\n")[0].strip()
        if first_line and len(first_line) < 30:
            member["name"] = first_line

    # ── 出身地 ──
    area_m = re.search(r'出身地?[：:]\s*(.+?)[\s\n]', text)
    if area_m:
        member["from_area"] = area_m.group(1).strip()

    # ── 年齢 ──
    age_m = re.search(r'年齢[：:]\s*(\d+)', text)
    if age_m:
        member["age"] = age_m.group(1)

    # ── 身長 ──
    height_m = re.search(r'身長[：:]\s*(\d{2,3})\s*(?:cm|㎝)?', text)
    if height_m:
        member["height"] = height_m.group(1)

    # ── 継続メンバー判定 ──
    if re.search(r'継続参加|継続メンバー|リベンジ|継続', text):
        member["is_continuation"] = "TRUE"

    # ── 事務所・特記事項をnoteに ──
    notes = []
    agency_m = re.search(r'([^\s\n]+?)所属', text)
    if agency_m:
        agency = agency_m.group(1).strip()
        if len(agency) < 30:
            notes.append(f"{agency}所属")

    # MBTI
    mbti_m = re.search(r'MBTI[：:\s]*([A-Z]{4})', text)
    if mbti_m:
        notes.append(f"MBTI:{mbti_m.group(1)}")

    member["note"] = " / ".join(notes)

    return member


def find_member_blocks(soup):
    """
    ページからメンバーブロックを検出する。

    teiban-navi.comの構造パターン:
    - h2/h3タグでメンバー名 → 次のh2/h3までがプロフィールブロック
    - tableタグにプロフィールがまとまっている場合もある
    - divやpタグの連続でプロフィール情報が記述されている場合もある
    """
    blocks = []

    # ── 戦略1: h2/h3タグをメンバー区切りとして使用 ──
    headings = soup.find_all(["h2", "h3"])
    content_area = soup.find("div", class_=re.compile(r'entry|article|content|post'))
    if not content_area:
        content_area = soup.find("article")
    if not content_area:
        content_area = soup.find("main")
    if not content_area:
        content_area = soup

    for i, heading in enumerate(headings):
        heading_text = heading.get_text(strip=True)
        # メンバー名っぽい見出しかチェック（短い日本語テキスト）
        if not heading_text or len(heading_text) > 50:
            continue
        # 「目次」「まとめ」「関連記事」等の見出しを除外
        if re.match(r'(目次|まとめ|関連|おすすめ|人気|ランキング|カップル|主題歌|放送)', heading_text):
            continue

        # この見出しから次の見出しまでの要素を収集
        block_elements = []
        elem = heading.find_next_sibling()
        while elem:
            if elem.name in ["h2", "h3"]:
                break
            block_elements.append(elem)
            elem = elem.find_next_sibling()

        if block_elements:
            # ブロックのテキストとHTMLを結合
            from bs4 import Tag
            combined_html = BeautifulSoup("", "html.parser")
            block_text_parts = [heading_text]
            for el in block_elements:
                if isinstance(el, Tag):
                    combined_html.append(el.__copy__())
                    block_text_parts.append(el.get_text(separator="\n"))

            block_text = "\n".join(block_text_parts)

            # SNS情報やプロフィール情報を含むブロックのみ対象
            has_profile = bool(re.search(
                r'インスタ|Instagram|TikTok|出身|身長|年齢|生年月日|'
                r'所属|事務所|instagram\.com|tiktok\.com|'
                r'[a-zA-Z0-9_.]{3,}',
                block_text
            ))

            if has_profile:
                blocks.append({
                    "heading": heading_text,
                    "text": block_text,
                    "html": combined_html,
                })

    return blocks


def detect_gender_section(soup):
    """
    ページ内の「女子メンバー」「男子メンバー」セクションを検出し、
    各見出しの性別ヒントを返す。

    Returns: dict[heading_text] -> gender ("f" or "m")
    """
    gender_map = {}
    current_gender = ""

    for heading in soup.find_all(["h2", "h3"]):
        text = heading.get_text(strip=True)
        if re.search(r'女子|女の子|girl', text, re.IGNORECASE):
            current_gender = "f"
            continue
        elif re.search(r'男子|男の子|boy', text, re.IGNORECASE):
            current_gender = "m"
            continue

        if current_gender:
            gender_map[text] = current_gender

    return gender_map


def scrape_page(session, target):
    """1つのシーズンページをスクレイピングしてメンバーリストを返す"""
    show_slug = target["show_slug"]
    season_name = target["season_name"]
    season_number = target["season_number"]

    # 複数URLを試行
    resp = None
    for url in target["urls"]:
        resp = throttled_get(session, url)
        if resp:
            break

    if not resp:
        logger.warning(
            f"スキップ: {show_slug} {season_name} - 全URLアクセス失敗"
        )
        return [], None

    soup = BeautifulSoup(resp.text, "lxml")

    # シーズン名をページタイトルから更新
    page_season = get_season_name_from_page(soup, season_number, show_slug)
    if page_season:
        season_name = page_season

    # 性別セクション検出
    gender_map = detect_gender_section(soup)

    # メンバーブロック検出
    blocks = find_member_blocks(soup)
    logger.info(
        f"{show_slug} {season_name}: {len(blocks)}名のメンバーブロック検出"
    )

    members = []
    for block in blocks:
        gender_hint = gender_map.get(block["heading"], "")
        member = parse_member_block(
            text=block["text"],
            html_block=block["html"],
            show_slug=show_slug,
            season_name=season_name,
            gender_hint=gender_hint,
        )
        # 名前が空の場合は見出しテキストを使用
        if not member["name"]:
            member["name"] = block["heading"]
        if not member["display_name"]:
            # 見出しからよみがなを取得
            m = re.search(r'[（(]([^）)]+)[）)]', block["heading"])
            if m:
                member["display_name"] = m.group(1)
                member["name"] = block["heading"].split("（")[0].split("(")[0].strip()

        members.append(member)

    # シーズン情報
    season_info = {
        "show_slug": show_slug,
        "season_name": season_name,
        "year": "",
        "badge": "",
        "order": str(season_number),
        "start_date": "",
        "end_date": "",
    }

    # 年の推定（ページテキストから）
    page_text = soup.get_text()
    year_m = re.search(r'(20\d{2})年', page_text)
    if year_m:
        season_info["year"] = year_m.group(1)

    return members, season_info


def main():
    logger.info("=== Phase 1: teiban-navi.com スクレイピング開始 ===")

    session = create_session()
    all_members = []
    all_seasons = []

    total_targets = len(SCRAPE_TARGETS)
    for i, target in enumerate(SCRAPE_TARGETS):
        logger.info(
            f"[{i+1}/{total_targets}] {target['show_slug']} "
            f"{target['season_name']} をスクレイピング中..."
        )

        members, season_info = scrape_page(session, target)

        if members:
            all_members.extend(members)
        if season_info:
            all_seasons.append(season_info)

    # ── CSV出力: cast_raw.csv ──
    cast_csv = output_path("cast_raw.csv")
    with open(cast_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CAST_COLUMNS)
        writer.writeheader()
        writer.writerows(all_members)
    logger.info(f"cast_raw.csv 出力完了: {len(all_members)}件")

    # ── CSV出力: seasons_raw.csv ──
    seasons_csv = output_path("seasons_raw.csv")
    with open(seasons_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=SEASON_COLUMNS)
        writer.writeheader()
        writer.writerows(all_seasons)
    logger.info(f"seasons_raw.csv 出力完了: {len(all_seasons)}件")

    # ── サマリー ──
    ig_count = sum(1 for m in all_members if m.get("ig_username"))
    logger.info(f"\n=== サマリー ===")
    logger.info(f"総メンバー数: {len(all_members)}")
    logger.info(f"Instagram ID取得数: {ig_count} ({ig_count/max(len(all_members),1)*100:.1f}%)")
    logger.info(f"シーズン数: {len(all_seasons)}")


if __name__ == "__main__":
    main()
