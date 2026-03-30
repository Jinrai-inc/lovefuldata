#!/usr/bin/env python3
"""
データクリーンアップスクリプト

cast_final.csv から以下を修正:
1. 誤検出レコード（「カテゴリー」等）を除去
2. 重複レコードを除去（最初の1件を残す）

実行: python scripts/cleanup.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import CAST_COLUMNS, logger, output_path


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


def cleanup(input_csv, output_csv):
    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    original_count = len(rows)

    # 1. 誤検出レコードを除去
    cleaned = []
    removed_fake = 0
    for row in rows:
        name = row.get("name", "").strip()
        if name in EXCLUDE_NAMES or not name:
            removed_fake += 1
            continue
        cleaned.append(row)

    # 2. 重複レコードを除去（最初の1件を残す）
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

    logger.info(f"クリーンアップ完了:")
    logger.info(f"  元データ: {original_count}件")
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
