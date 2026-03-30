#!/usr/bin/env python3
"""
Phase 4: データ統合＆品質チェックスクリプト

入力:
  - output/cast_filled.csv（Phase 2の出力）
  - output/cast_supplement.csv（Phase 3の補完データ、任意）
出力:
  - output/cast_final.csv（最終版）
  - output/seasons_final.csv（シーズン最終版）
  - output/quality_report.txt（品質レポート）

実行: python scripts/merge_and_validate.py
"""

import csv
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import (
    CAST_COLUMNS,
    SEASON_COLUMNS,
    SHOW_SHORT_MAP,
    logger,
    output_path,
)


def load_csv(path):
    """CSVファイルを読み込む。存在しない場合は空リストを返す。"""
    if not os.path.exists(path):
        logger.warning(f"ファイルが見つかりません: {path}")
        return [], []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    return rows, fieldnames


def merge_key(row):
    """重複判定キー: show_slug + season_name + name"""
    return (
        row.get("show_slug", "").strip(),
        row.get("season_name", "").strip(),
        row.get("name", "").strip(),
    )


def merge_data(main_csv, supplement_csv, output_csv):
    """
    メインデータに補完データをマージする。
    補完データで既にメインに存在するレコードは、空欄フィールドのみ上書き。
    メインに存在しないレコードは追加。
    """
    main_rows, _ = load_csv(main_csv)
    supp_rows, _ = load_csv(supplement_csv)

    if not main_rows:
        logger.error(f"メインデータが空です: {main_csv}")
        return []

    # メインデータをキーでインデックス化
    main_index = {}
    for i, row in enumerate(main_rows):
        key = merge_key(row)
        if key not in main_index:
            main_index[key] = i

    merged_count = 0
    added_count = 0

    for supp_row in supp_rows:
        key = merge_key(supp_row)
        if key in main_index:
            # 既存レコードの空欄フィールドを補完
            main_row = main_rows[main_index[key]]
            updated = False
            for col in CAST_COLUMNS:
                if not main_row.get(col) and supp_row.get(col):
                    main_row[col] = supp_row[col]
                    updated = True
            if updated:
                merged_count += 1
        else:
            # 新規レコード追加
            # カラム不足を補完
            new_row = {col: supp_row.get(col, "") for col in CAST_COLUMNS}
            main_rows.append(new_row)
            main_index[key] = len(main_rows) - 1
            added_count += 1

    logger.info(f"マージ: {merged_count}件更新, {added_count}件追加")

    # CSV出力
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CAST_COLUMNS)
        writer.writeheader()
        writer.writerows(main_rows)

    return main_rows


def clean_data(rows):
    """データクリーニング"""
    for row in rows:
        # IG IDの正規化
        ig = row.get("ig_username", "")
        if ig:
            ig = ig.strip().rstrip("/").lstrip("@")
            if not re.match(r'^[a-zA-Z0-9_.]{1,30}$', ig):
                row["ig_username"] = ""
            else:
                row["ig_username"] = ig

        # TikTok IDの正規化
        tt = row.get("tiktok_username", "")
        if tt:
            row["tiktok_username"] = tt.strip().rstrip("/").lstrip("@")

        # X IDの正規化
        x = row.get("x_username", "")
        if x:
            row["x_username"] = x.strip().rstrip("/").lstrip("@")

        # is_continuationの正規化
        cont = row.get("is_continuation", "").upper().strip()
        row["is_continuation"] = "TRUE" if cont == "TRUE" else "FALSE"

        # genderの正規化
        gender = row.get("gender", "").lower().strip()
        if gender not in ("f", "m", "other"):
            row["gender"] = ""
        else:
            row["gender"] = gender

        # 名前のトリミング
        row["name"] = row.get("name", "").strip()
        row["display_name"] = row.get("display_name", "").strip()

    return rows


def quality_check(rows, output_report):
    """
    品質チェック。以下を検査してレポート出力:
    1. IG IDの取得率
    2. 重複レコードの検出
    3. show_slugの値チェック
    4. genderの値チェック
    5. is_continuationの値チェック
    6. IG IDフォーマットチェック
    7. 空欄率の高いカラムの特定
    """
    total = len(rows)
    if total == 0:
        logger.error("データが空です。品質チェックをスキップします。")
        return

    ig_filled = sum(1 for r in rows if r.get("ig_username"))
    tt_filled = sum(1 for r in rows if r.get("tiktok_username"))
    x_filled = sum(1 for r in rows if r.get("x_username"))
    yt_filled = sum(1 for r in rows if r.get("youtube_url"))
    name_filled = sum(1 for r in rows if r.get("name"))
    gender_filled = sum(1 for r in rows if r.get("gender"))
    area_filled = sum(1 for r in rows if r.get("from_area"))
    height_filled = sum(1 for r in rows if r.get("height"))
    age_filled = sum(1 for r in rows if r.get("age"))

    report_lines = []
    report_lines.append("=" * 50)
    report_lines.append("データ品質レポート")
    report_lines.append("=" * 50)
    report_lines.append("")
    report_lines.append(f"総レコード数: {total}")
    report_lines.append("")
    report_lines.append("--- フィールド取得率 ---")
    report_lines.append(f"  name:            {name_filled}/{total} ({name_filled/total*100:.1f}%)")
    report_lines.append(f"  ig_username:     {ig_filled}/{total} ({ig_filled/total*100:.1f}%)")
    report_lines.append(f"  tiktok_username: {tt_filled}/{total} ({tt_filled/total*100:.1f}%)")
    report_lines.append(f"  x_username:      {x_filled}/{total} ({x_filled/total*100:.1f}%)")
    report_lines.append(f"  youtube_url:     {yt_filled}/{total} ({yt_filled/total*100:.1f}%)")
    report_lines.append(f"  gender:          {gender_filled}/{total} ({gender_filled/total*100:.1f}%)")
    report_lines.append(f"  from_area:       {area_filled}/{total} ({area_filled/total*100:.1f}%)")
    report_lines.append(f"  height:          {height_filled}/{total} ({height_filled/total*100:.1f}%)")
    report_lines.append(f"  age:             {age_filled}/{total} ({age_filled/total*100:.1f}%)")
    report_lines.append("")

    # ── show_slug別集計 ──
    report_lines.append("--- show_slug別集計 ---")
    show_counts = Counter(r.get("show_slug", "") for r in rows)
    for show, count in show_counts.most_common():
        ig_count = sum(
            1 for r in rows
            if r.get("show_slug") == show and r.get("ig_username")
        )
        report_lines.append(
            f"  {show}: {count}名 (IG: {ig_count}名, "
            f"{ig_count/max(count,1)*100:.0f}%)"
        )
    report_lines.append("")

    # ── 重複チェック ──
    keys = [merge_key(r) for r in rows]
    dup_counter = Counter(keys)
    duplicates = [(k, c) for k, c in dup_counter.items() if c > 1]
    if duplicates:
        report_lines.append(f"--- 重複レコード: {len(duplicates)}件 ---")
        for (slug, season, name), count in duplicates:
            report_lines.append(f"  [{count}回] {slug} / {season} / {name}")
    else:
        report_lines.append("--- 重複レコード: なし ---")
    report_lines.append("")

    # ── IG IDフォーマットチェック ──
    invalid_ig = []
    for r in rows:
        ig = r.get("ig_username", "")
        if ig and not re.match(r'^[a-zA-Z0-9_.]{1,30}$', ig):
            invalid_ig.append((r.get("name", ""), ig))
    if invalid_ig:
        report_lines.append(f"--- 不正なIG ID: {len(invalid_ig)}件 ---")
        for name, ig in invalid_ig:
            report_lines.append(f"  {name}: {ig}")
    else:
        report_lines.append("--- 不正なIG ID: なし ---")
    report_lines.append("")

    # ── genderの値チェック ──
    invalid_gender = []
    for r in rows:
        g = r.get("gender", "")
        if g and g not in ("f", "m", "other"):
            invalid_gender.append((r.get("name", ""), g))
    if invalid_gender:
        report_lines.append(f"--- 不正なgender値: {len(invalid_gender)}件 ---")
        for name, g in invalid_gender:
            report_lines.append(f"  {name}: {g}")
    else:
        report_lines.append("--- 不正なgender値: なし ---")
    report_lines.append("")

    # ── is_continuationの値チェック ──
    invalid_cont = []
    for r in rows:
        c = r.get("is_continuation", "")
        if c and c not in ("TRUE", "FALSE"):
            invalid_cont.append((r.get("name", ""), c))
    if invalid_cont:
        report_lines.append(f"--- 不正なis_continuation値: {len(invalid_cont)}件 ---")
        for name, c in invalid_cont:
            report_lines.append(f"  {name}: {c}")
    else:
        report_lines.append("--- 不正なis_continuation値: なし ---")
    report_lines.append("")

    # ── IG ID未取得メンバー一覧（先頭30件） ──
    no_ig = [r for r in rows if not r.get("ig_username")]
    if no_ig:
        report_lines.append(f"--- IG ID未取得メンバー: {len(no_ig)}名 (先頭30件) ---")
        for r in no_ig[:30]:
            report_lines.append(
                f"  {r.get('show_slug', '')} / {r.get('season_name', '')} / "
                f"{r.get('name', '')} ({r.get('display_name', '')})"
            )
        if len(no_ig) > 30:
            report_lines.append(f"  ... 他 {len(no_ig)-30}名")
    report_lines.append("")

    report = "\n".join(report_lines)
    print(report)

    with open(output_report, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"品質レポート出力: {output_report}")


def main():
    logger.info("=== Phase 4: データ統合＆品質チェック 開始 ===")

    main_csv = output_path("cast_filled.csv")
    supplement_csv = output_path("cast_supplement.csv")
    final_csv = output_path("cast_final.csv")
    report_path = output_path("quality_report.txt")

    # ── マージ ──
    rows = merge_data(main_csv, supplement_csv, final_csv)
    if not rows:
        # 補完データがなくてもメインデータのみで処理
        main_rows, _ = load_csv(main_csv)
        if not main_rows:
            # cast_raw.csvもフォールバック
            main_rows, _ = load_csv(output_path("cast_raw.csv"))
        if not main_rows:
            logger.error("データファイルが見つかりません。先にPhase 1を実行してください。")
            return
        rows = main_rows

    # ── クリーニング ──
    rows = clean_data(rows)

    # ── 最終CSV出力 ──
    with open(final_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CAST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"最終CSV出力: {final_csv} ({len(rows)}件)")

    # ── seasons_final.csv ──
    seasons_raw = output_path("seasons_raw.csv")
    seasons_final = output_path("seasons_final.csv")
    if os.path.exists(seasons_raw):
        season_rows, _ = load_csv(seasons_raw)
        # 重複除去
        seen = set()
        unique_seasons = []
        for s in season_rows:
            key = (s.get("show_slug", ""), s.get("season_name", ""))
            if key not in seen:
                seen.add(key)
                unique_seasons.append(s)
        with open(seasons_final, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=SEASON_COLUMNS)
            writer.writeheader()
            writer.writerows(unique_seasons)
        logger.info(f"seasons_final.csv 出力: {len(unique_seasons)}件")

    # ── 品質チェック ──
    quality_check(rows, report_path)

    logger.info("=== Phase 4 完了 ===")


if __name__ == "__main__":
    main()
