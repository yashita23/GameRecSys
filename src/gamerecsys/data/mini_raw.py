"""Tạo mẫu thô thu nhỏ từ bộ dữ liệu Steam đầy đủ (chạy trên Kaggle).

Mẫu thô thu nhỏ gồm 4 file giống hệt cấu trúc 4 file gốc, nhưng chỉ giữ một nhóm
người dùng được bốc ngẫu nhiên (mỗi người có ít nhất ``min_reviews`` review) cùng
các game, metadata và users liên quan. Agent dùng mẫu này để chạy thử code trên máy;
cùng code đó chạy trên Kaggle với dữ liệu đầy đủ chỉ bằng cách đổi đường dẫn.

Chỉ cần polars và thư viện chuẩn, để chạy được ngay trên Kaggle.

Chạy trên Kaggle:
    python -m gamerecsys.data.mini_raw --out /kaggle/working/mini_raw --zip
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import polars as pl

from gamerecsys.cli import ensure_utf8_output

REVIEWS_FILE = "recommendations.csv"
GAMES_FILE = "games.csv"
METADATA_FILE = "games_metadata.json"
USERS_FILE = "users.csv"
USER_COL = "user_id"
GAME_COL = "app_id"

KAGGLE_INPUT = Path("/kaggle/input")


def find_dataset_dir(root: Path = KAGGLE_INPUT) -> Path:
    """Tìm thư mục chứa recommendations.csv bên dưới ``root`` (đường dẫn Kaggle hay đổi)."""
    hits = sorted(Path(root).rglob(REVIEWS_FILE))
    if not hits:
        raise FileNotFoundError(f"Không thấy {REVIEWS_FILE} dưới {root}. Đã gắn dataset vào notebook chưa?")
    return hits[0].parent


def _require_columns(name: str, columns: list[str], needed: list[str]) -> None:
    missing = [c for c in needed if c not in columns]
    if missing:
        raise ValueError(f"{name} thiếu cột {missing}; cột thật: {columns}. Sửa USER_COL/GAME_COL trong mini_raw.py.")


def make_mini_raw(
    src: Path,
    out: Path,
    n_users: int = 10_000,
    min_reviews: int = 10,
    seed: int = 42,
    make_zip: bool = False,
) -> dict:
    """Ghi mẫu thô thu nhỏ vào ``out`` và trả về bản tóm tắt (cũng ghi ra summary.json)."""
    src, out = Path(src), Path(out)
    out.mkdir(parents=True, exist_ok=True)

    reviews = pl.scan_csv(src / REVIEWS_FILE)
    columns = {name: pl.scan_csv(src / name).collect_schema().names() for name in (REVIEWS_FILE, GAMES_FILE, USERS_FILE)}
    _require_columns(REVIEWS_FILE, columns[REVIEWS_FILE], [USER_COL, GAME_COL])
    _require_columns(GAMES_FILE, columns[GAMES_FILE], [GAME_COL])
    _require_columns(USERS_FILE, columns[USERS_FILE], [USER_COL])

    # Sắp theo user_id trước khi bốc, vì thứ tự của group_by không cố định.
    eligible = (
        reviews.group_by(USER_COL)
        .len()
        .filter(pl.col("len") >= min_reviews)
        .select(USER_COL)
        .sort(USER_COL)
        .collect()
    )
    users = eligible.sample(n=min(n_users, eligible.height), seed=seed).sort(USER_COL)

    small_reviews = reviews.join(users.lazy(), on=USER_COL, how="semi").collect()
    small_reviews.write_csv(out / REVIEWS_FILE)

    games = small_reviews.select(GAME_COL).unique()
    pl.scan_csv(src / GAMES_FILE).join(games.lazy(), on=GAME_COL, how="semi").collect().write_csv(out / GAMES_FILE)
    pl.scan_csv(src / USERS_FILE).join(users.lazy(), on=USER_COL, how="semi").collect().write_csv(out / USERS_FILE)

    keep = set(games[GAME_COL].to_list())
    metadata_lines = 0
    with open(src / METADATA_FILE, encoding="utf-8") as fin, open(out / METADATA_FILE, "w", encoding="utf-8") as fout:
        for line in fin:
            if line.strip() and json.loads(line)[GAME_COL] in keep:
                fout.write(line if line.endswith("\n") else line + "\n")
                metadata_lines += 1

    summary = {
        "eligible_users": eligible.height,
        "sampled_users": users.height,
        "reviews": small_reviews.height,
        "games": games.height,
        "metadata_rows": metadata_lines,
        "params": {"n_users": n_users, "min_reviews": min_reviews, "seed": seed},
        "columns": columns,
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if make_zip:
        shutil.make_archive(str(out), "zip", out)
    return summary


def main() -> None:
    ensure_utf8_output()
    parser = argparse.ArgumentParser(description="Tạo mẫu thô thu nhỏ (chạy trên Kaggle).")
    parser.add_argument("--src", type=Path, default=None, help="thư mục 4 file gốc; mặc định tự tìm dưới /kaggle/input")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-users", type=int, default=10_000)
    parser.add_argument("--min-reviews", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--zip", action="store_true", help="nén thêm thành <out>.zip để tải về")
    args = parser.parse_args()

    src = args.src or find_dataset_dir()
    summary = make_mini_raw(src, args.out, args.n_users, args.min_reviews, args.seed, args.zip)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
