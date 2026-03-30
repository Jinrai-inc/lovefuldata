#!/usr/bin/env python3
"""
データクリーンアップスクリプト

cast_final.csv から以下を修正:
1. show_slug の正規化（ookami-kun / ookami-chan → ookami）
2. season_name の正規化（正式マッピングに変換）
3. 誤検出レコード（「カテゴリー」等）を除去
4. 重複レコードを除去（最初の1件を残す）

実行: python scripts/cleanup.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import (
    CAST_COLUMNS,
    KYOUSUKI_SEASONS,
    OOKAMI_SEASONS,
    logger,
    output_path,
)


# 誤検出として除外するname
EXCLUDE_NAMES = {
    "カテゴリー",
    "目次",
    "まとめ",
    "関連記事",
    "おすすめ記事",
    "人気記事",
    "ランキング",
    "コメント",
    "シェア",
    "広告",
}

# ── show_slug 正規化マップ ──
SLUG_NORMALIZE = {
    "ookami-kun": "ookami-chan",
    "ookami": "ookami-chan",
}

# ── 今日好き season_name 正規化マップ（旧名→正式名） ──
# config.py の KYOUSUKI_SEASONS から逆引きテーブルを作成
KYOUSUKI_CANONICAL = {v: v for v in KYOUSUKI_SEASONS.values()}

# 旧スクリプトで生成された可能性のある別名→正式名マッピング
SEASON_NAME_FIXES = {
    # 今日好き: 旧名 → 正式名
    "卒業編2026(ドバイ)": "卒業編2026inドバイ",
    "チェンマイ編2": "マカオ編",
    "ダナン編2": "チュンムン編",
    "バンコク編": "パタヤ編",
    "セブ島編2": "プーケット編",
    "紫陽花編2": "小夏編",
    "卒業編": "リベンジ編",
    "バレンタイン編": "オーストラリア編",
    "冬休み編2017": "韓国編",
    "秋桜編2016": "ベトナム・ダナン編",
    "グアム編": "グアム編",  # 同名（変更なし）
    "冬休み編": "香港編",
    "秋桜編2017": "チェジュ島編",
    "夏休み編": "沖縄編",
    "ハワイ編": "ハワイ編",  # 同名
    "卒業編2018": "チェジュ島編",  # 要確認
    "ハワイ編2018": "ハワイ夏休み編",
    "夏休み編2018": "韓国ソウル編",
    "秋桜編2018": "台湾編",
    "冬休み編2018": "グアム編",
    "卒業編2019": "バリ島・冬休み編",
    "夏休み編2019": "卒業編(サイパン)",
    "文化祭編": "青い春編",
    "冬休み編2019": "紫陽花編",
    "春桜編2020": "夏空編",
    "卒業編2020": "金木犀編",
    "向日葵編2020": "秋月編",
    "金木犀編": "星空編",
    "紅葉編": "赤い糸編",
    "冬桜編": "卒業編2021",
    "春桜編": "春桜編",  # 要確認（34弾）
    # オオカミ: 旧名 → 正式名
    "オオカミくんには騙されない(シーズン1)": "オオカミくんには騙されない",
    "真冬のオオカミくんには騙されない(シーズン2)": "真冬のオオカミくんには騙されない",
    "真夏のオオカミくんには騙されない(シーズン3)": "真夏のオオカミくんには騙されない",
    "太陽とオオカミくんには騙されない(シーズン4)": "太陽とオオカミくんには騙されない",
    "オオカミちゃんには騙されない(シーズン5)": "オオカミちゃんには騙されない",
    "白雪とオオカミくんには騙されない(シーズン6)": "白雪とオオカミくんには騙されない",
    "月とオオカミちゃんには騙されない(シーズン7)": "月とオオカミちゃんには騙されない",
    "オオカミくんには騙されない(シーズン8)": "オオカミくんには騙されない(2021)",
    "恋とオオカミには騙されない(シーズン9)": "恋とオオカミには騙されない",
    "虹とオオカミには騙されない(シーズン10)": "虹とオオカミには騙されない",
    "彼とオオカミちゃんには騙されない(シーズン11)": "彼とオオカミちゃんには騙されない",
    "オオカミちゃんとオオカミくんには騙されない(シーズン12)": "オオカミちゃんとオオカミくんには騙されない",
    "花束とオオカミちゃんには騙されない(シーズン13)": "花束とオオカミちゃんには騙されない",
}


def cleanup(input_csv, output_csv):
    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    original_count = len(rows)

    # 1. show_slug と season_name の正規化
    normalized_slug = 0
    normalized_season = 0
    for row in rows:
        # show_slug 正規化
        old_slug = row.get("show_slug", "")
        if old_slug in SLUG_NORMALIZE:
            row["show_slug"] = SLUG_NORMALIZE[old_slug]
            normalized_slug += 1

        # season_name 正規化
        old_season = row.get("season_name", "")
        if old_season in SEASON_NAME_FIXES:
            row["season_name"] = SEASON_NAME_FIXES[old_season]
            normalized_season += 1

    # 2. 誤検出レコードを除去
    cleaned = []
    removed_fake = 0
    for row in rows:
        name = row.get("name", "").strip()
        if name in EXCLUDE_NAMES or not name:
            removed_fake += 1
            continue
        cleaned.append(row)

    # 3. 重複レコードを除去（最初の1件を残す）
    seen = set()
    deduped = []
    removed_dup = 0
    for row in cleaned:
        key = (
            row.get("show_slug", "").strip(),
            row.get("season_name", "").strip(),
            row.get("name", "").strip(),
        )
        if key in seen:
            removed_dup += 1
            continue
        seen.add(key)
        deduped.append(row)

    # 出力
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CAST_COLUMNS)
        writer.writeheader()
        writer.writerows(deduped)

    logger.info("クリーンアップ完了:")
    logger.info(f"  元データ: {original_count}件")
    logger.info(f"  show_slug正規化: {normalized_slug}件")
    logger.info(f"  season_name正規化: {normalized_season}件")
    logger.info(f"  誤検出除去: {removed_fake}件")
    logger.info(f"  重複除去: {removed_dup}件")
    logger.info(f"  最終データ: {len(deduped)}件")
    logger.info(f"  出力: {output_csv}")


def main():
    input_csv = output_path("cast_final.csv")
    output_csv = output_path("cast_final.csv")  # 上書き
    cleanup(input_csv, output_csv)


if __name__ == "__main__":
    main()
