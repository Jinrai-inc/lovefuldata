#!/usr/bin/env python3
"""
seasons.csv 自動生成スクリプト

cast_final.csv から全ユニークな (show_slug, season_name) を抽出し、
seasons.csv を自動生成する。

これにより cast が参照する全シーズンが必ず seasons テーブルに存在することを保証する。

実行: python scripts/generate_seasons.py
"""

import csv
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import SEASON_COLUMNS, logger, output_path


def generate_seasons_from_cast(cast_csv_path, output_seasons_csv):
    """
    cast.csv から全ユニークな (show_slug, season_name) を抽出し、
    seasons.csv を自動生成する。
    """
    if not os.path.exists(cast_csv_path):
        logger.error(f"ファイルが見つかりません: {cast_csv_path}")
        return

    with open(cast_csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cast_rows = list(reader)

    # ユニークな (show_slug, season_name) ペアを抽出（出現順を保持）
    seen = OrderedDict()
    for row in cast_rows:
        key = (row["show_slug"], row["season_name"])
        if key not in seen:
            seen[key] = {
                "show_slug": row["show_slug"],
                "season_name": row["season_name"],
                "year": "",
                "badge": "",
                "order": 0,
                "start_date": "",
                "end_date": "",
            }

    # order を show_slug ごとに自動採番（出現順）
    show_order = {}
    for key, season in seen.items():
        slug = season["show_slug"]
        if slug not in show_order:
            show_order[slug] = 0
        show_order[slug] += 1
        season["order"] = show_order[slug]

    # year を season_name から推測
    for key, season in seen.items():
        m = re.search(r"(20\d{2})", season["season_name"])
        if m:
            season["year"] = m.group(1)

    # CSV出力
    with open(output_seasons_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=SEASON_COLUMNS)
        writer.writeheader()
        for season in seen.values():
            writer.writerow(season)

    logger.info(f"seasons.csv 生成完了: {len(seen)}シーズン")

    # 整合性チェック
    season_keys = set(seen.keys())
    cast_keys = set((r["show_slug"], r["season_name"]) for r in cast_rows)
    missing = cast_keys - season_keys
    if missing:
        logger.warning(f"不整合: {len(missing)}件")
        for m in missing:
            logger.warning(f"  {m}")
    else:
        logger.info("整合性OK: cast の全 season_name が seasons に存在")

    # show_slug 別のサマリー
    logger.info("--- show_slug 別シーズン数 ---")
    for slug, count in show_order.items():
        logger.info(f"  {slug}: {count}シーズン")


def main():
    cast_csv = output_path("cast_final.csv")
    seasons_csv = output_path("seasons_final.csv")
    generate_seasons_from_cast(cast_csv, seasons_csv)


if __name__ == "__main__":
    main()
