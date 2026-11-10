"""Test tạo mẫu thô thu nhỏ: 4 file cùng cấu trúc file gốc, chỉ giữ người dùng được bốc."""

import json
import zipfile

import polars as pl
import pytest

from gamerecsys.data.mini_raw import find_dataset_dir, make_mini_raw

# user 1: 12 review, user 2: 3 review (không đủ), user 3: 10 review
REVIEWS = (
    [(1, 100 + i, i % 3 != 0) for i in range(12)]
    + [(2, 100 + i, True) for i in range(3)]
    + [(3, 200 + i, i % 2 == 0) for i in range(10)]
)


@pytest.fixture
def raw_dir(tmp_path):
    src = tmp_path / "kaggle" / "input" / "game-recommendations-on-steam"
    src.mkdir(parents=True)
    pl.DataFrame(
        {
            "app_id": [a for _, a, _ in REVIEWS],
            "helpful": [0] * len(REVIEWS),
            "funny": [0] * len(REVIEWS),
            "date": ["2022-01-01"] * len(REVIEWS),
            "is_recommended": [r for _, _, r in REVIEWS],
            "hours": [1.5] * len(REVIEWS),
            "user_id": [u for u, _, _ in REVIEWS],
            "review_id": list(range(len(REVIEWS))),
        }
    ).write_csv(src / "recommendations.csv")
    all_apps = sorted({a for _, a, _ in REVIEWS} | {999})  # 999: game không ai review
    pl.DataFrame({"app_id": all_apps, "title": [f"G{a}" for a in all_apps]}).write_csv(src / "games.csv")
    with open(src / "games_metadata.json", "w", encoding="utf-8") as f:
        for a in all_apps:
            f.write(json.dumps({"app_id": a, "description": "", "tags": ["Indie"]}) + "\n")
    pl.DataFrame({"user_id": [1, 2, 3], "products": [5, 5, 5], "reviews": [12, 3, 10]}).write_csv(src / "users.csv")
    return src


def _read(out):
    rec = pl.read_csv(out / "recommendations.csv")
    games = pl.read_csv(out / "games.csv")
    users = pl.read_csv(out / "users.csv")
    meta = [json.loads(line)["app_id"] for line in (out / "games_metadata.json").read_text().splitlines()]
    return rec, games, users, meta


def test_keeps_only_sampled_users_with_enough_reviews_and_their_games(raw_dir, tmp_path):
    out = tmp_path / "mini"
    make_mini_raw(raw_dir, out, n_users=1, min_reviews=10, seed=0)

    rec, games, users, meta = _read(out)
    sampled = rec["user_id"].unique().to_list()
    assert len(sampled) == 1 and sampled[0] in {1, 3}
    expected_reviews = [r for r in REVIEWS if r[0] == sampled[0]]
    assert rec.height == len(expected_reviews)
    apps = {a for _, a, _ in expected_reviews}
    assert set(games["app_id"].to_list()) == apps
    assert set(meta) == apps
    assert users["user_id"].to_list() == sampled


def test_output_files_keep_original_columns(raw_dir, tmp_path):
    out = tmp_path / "mini"
    make_mini_raw(raw_dir, out, n_users=5, min_reviews=10, seed=0)

    for name in ["recommendations.csv", "games.csv", "users.csv"]:
        assert pl.read_csv(out / name).columns == pl.read_csv(raw_dir / name).columns


def test_asking_more_users_than_eligible_takes_all_eligible(raw_dir, tmp_path):
    summary = make_mini_raw(raw_dir, tmp_path / "mini", n_users=1000, min_reviews=10, seed=0)

    assert summary["eligible_users"] == 2
    assert summary["sampled_users"] == 2
    assert summary["reviews"] == 22


def test_same_seed_gives_same_sample(raw_dir, tmp_path):
    make_mini_raw(raw_dir, tmp_path / "a", n_users=1, min_reviews=10, seed=7)
    make_mini_raw(raw_dir, tmp_path / "b", n_users=1, min_reviews=10, seed=7)

    assert (tmp_path / "a" / "recommendations.csv").read_bytes() == (tmp_path / "b" / "recommendations.csv").read_bytes()


def test_summary_reports_real_column_names(raw_dir, tmp_path):
    summary = make_mini_raw(raw_dir, tmp_path / "mini", n_users=1, min_reviews=10, seed=0)

    assert summary["columns"]["users.csv"] == ["user_id", "products", "reviews"]
    assert "is_recommended" in summary["columns"]["recommendations.csv"]
    assert json.loads((tmp_path / "mini" / "summary.json").read_text(encoding="utf-8")) == summary


def test_zip_contains_the_four_files(raw_dir, tmp_path):
    make_mini_raw(raw_dir, tmp_path / "mini", n_users=1, min_reviews=10, seed=0, make_zip=True)

    names = set(zipfile.ZipFile(tmp_path / "mini.zip").namelist())
    assert {"recommendations.csv", "games.csv", "users.csv", "games_metadata.json"} <= names


def test_missing_column_fails_with_clear_message(raw_dir, tmp_path):
    pl.read_csv(raw_dir / "users.csv").rename({"user_id": "uid"}).write_csv(raw_dir / "users.csv")

    with pytest.raises(ValueError, match="users.csv.*user_id"):
        make_mini_raw(raw_dir, tmp_path / "mini", n_users=1, min_reviews=10, seed=0)


def test_find_dataset_dir_locates_nested_folder(raw_dir, tmp_path):
    assert find_dataset_dir(tmp_path / "kaggle" / "input") == raw_dir
