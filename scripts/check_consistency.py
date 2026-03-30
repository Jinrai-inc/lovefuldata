#!/usr/bin/env python3
"""
整合性チェックスクリプト

WordPressインポート前に必ず実行する。
shows / seasons / cast の参照整合性を検査する。

実行: python scripts/check_consistency.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import logger, output_path


def read_csv(path):
    """CSVを読み込む。存在しない場合は空リスト。"""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def check_consistency(shows_csv=None, seasons_csv=None, cast_csv=None):
    """
    CSVの参照整合性をチェック。全てパスしたらインポートOK。
    """
    seasons = read_csv(seasons_csv) if seasons_csv else []
    casts = read_csv(cast_csv) if cast_csv else []
    shows = read_csv(shows_csv) if shows_csv else []

    errors = []
    warnings = []

    # ── shows が提供されている場合のチェック ──
    if shows:
        show_slugs = set(r.get("slug", "") for r in shows)

        for s in seasons:
            if s["show_slug"] not in show_slugs:
                errors.append(
                    f"[seasons] show_slug '{s['show_slug']}' が shows に存在しません"
                )

        for c in casts:
            if c["show_slug"] not in show_slugs:
                errors.append(
                    f"[cast] show_slug '{c['show_slug']}' が shows に存在しません "
                    f"({c.get('name', '?')})"
                )

    # ── ★最重要: cast の (show_slug, season_name) が seasons に存在するか ──
    if seasons and casts:
        season_keys = set(
            (r["show_slug"], r["season_name"]) for r in seasons
        )
        cast_season_keys = set(
            (r["show_slug"], r["season_name"]) for r in casts
        )

        # cast → seasons 方向
        missing_in_seasons = cast_season_keys - season_keys
        if missing_in_seasons:
            for slug, sname in sorted(missing_in_seasons):
                count = sum(
                    1 for c in casts
                    if c["show_slug"] == slug and c["season_name"] == sname
                )
                errors.append(
                    f"[cast→seasons] '{sname}' (show: {slug}) が "
                    f"seasons に存在しません（{count}名が参照）"
                )

        # seasons → cast 方向（警告のみ: 空シーズンの検出）
        unused_seasons = season_keys - cast_season_keys
        if unused_seasons:
            for slug, sname in sorted(unused_seasons):
                warnings.append(
                    f"[seasons] '{sname}' (show: {slug}) を参照する cast がありません"
                )

    # ── season_name の重複チェック ──
    if seasons:
        from collections import Counter
        season_counter = Counter(
            (r["show_slug"], r["season_name"]) for r in seasons
        )
        dups = [(k, c) for k, c in season_counter.items() if c > 1]
        for (slug, sname), count in dups:
            errors.append(
                f"[seasons] 重複: '{sname}' (show: {slug}) が {count}回登録"
            )

    # ── cast の重複チェック ──
    if casts:
        from collections import Counter
        cast_counter = Counter(
            (r["show_slug"], r["season_name"], r["name"]) for r in casts
        )
        dups = [(k, c) for k, c in cast_counter.items() if c > 1]
        for (slug, sname, name), count in dups:
            warnings.append(
                f"[cast] 重複: '{name}' ({slug}/{sname}) が {count}回登録"
            )

    # ── レポート出力 ──
    print("=" * 50)
    print("整合性チェックレポート")
    print("=" * 50)
    print(f"  seasons: {len(seasons)}件")
    print(f"  cast:    {len(casts)}件")
    if shows:
        print(f"  shows:   {len(shows)}件")
    print()

    if errors:
        print(f"❌ エラー: {len(errors)}件")
        unique_errors = list(dict.fromkeys(errors))
        for e in unique_errors[:50]:
            print(f"  {e}")
        if len(unique_errors) > 50:
            print(f"  ... 他 {len(unique_errors) - 50}件")
        print()

    if warnings:
        print(f"⚠️  警告: {len(warnings)}件")
        unique_warnings = list(dict.fromkeys(warnings))
        for w in unique_warnings[:20]:
            print(f"  {w}")
        if len(unique_warnings) > 20:
            print(f"  ... 他 {len(unique_warnings) - 20}件")
        print()

    if not errors:
        print("✅ 全チェック通過。インポート可能です。")
    else:
        print("❌ エラーを修正してから再実行してください。")

    return len(errors) == 0


def main():
    seasons_csv = output_path("seasons_final.csv")
    cast_csv = output_path("cast_final.csv")

    # shows.csv はオプション（存在すればチェック）
    shows_csv = output_path("shows.csv")
    if not os.path.exists(shows_csv):
        shows_csv = None

    check_consistency(
        shows_csv=shows_csv,
        seasons_csv=seasons_csv,
        cast_csv=cast_csv,
    )


if __name__ == "__main__":
    main()
