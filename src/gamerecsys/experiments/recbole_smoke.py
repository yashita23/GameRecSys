"""Kiểm tra môi trường: chạy BPR của RecBole trên một bộ dữ liệu giả nhỏ, trên CPU.

Chạy: ``python -m gamerecsys.experiments.recbole_smoke``

Không dùng ``recbole.quick_start`` vì module đó import ``ray`` (đã bỏ khỏi môi trường,
xem docs/environment.md).
"""

from __future__ import annotations

import contextlib
import os
import random
import tempfile
from pathlib import Path

from gamerecsys import recbole_compat  # noqa: F401  (phải đứng trước recbole)

from recbole.config import Config
from recbole.data import create_dataset, data_preparation
from recbole.model.general_recommender import BPR
from recbole.trainer import Trainer
from recbole.utils import init_seed

DATASET = "toy"


def _write_toy_dataset(root: Path, n_users: int = 60, n_items: int = 40, per_user: int = 12, seed: int = 0) -> None:
    """Ghi một file .inter giả theo định dạng atomic của RecBole."""
    rng = random.Random(seed)
    folder = root / DATASET
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["user_id:token\titem_id:token\ttimestamp:float"]
    for u in range(n_users):
        for t, i in enumerate(rng.sample(range(n_items), per_user)):
            lines.append(f"u{u}\ti{i}\t{t}")
    (folder / f"{DATASET}.inter").write_text("\n".join(lines) + "\n", encoding="utf-8")


@contextlib.contextmanager
def _inside(path: Path):
    """RecBole ghi log_tensorboard/ vào thư mục hiện tại, nên chạy trong thư mục tạm."""
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def run(epochs: int = 2, seed: int = 2026) -> dict:
    """Huấn luyện BPR vài epoch, nạp lại checkpoint tốt nhất và trả về kết quả trên tập test."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_toy_dataset(tmp_path)
        config = Config(
            model=BPR,
            dataset=DATASET,
            config_dict={
                "data_path": str(tmp_path),
                "checkpoint_dir": str(tmp_path / "saved"),
                "use_gpu": False,
                "device": "cpu",
                "epochs": epochs,
                "train_batch_size": 256,
                "eval_batch_size": 256,
                "metrics": ["Recall", "NDCG"],
                "topk": [10],
                "valid_metric": "NDCG@10",
                "show_progress": False,
                "seed": seed,
                "reproducibility": True,
            },
        )
        init_seed(config["seed"], config["reproducibility"])
        with _inside(tmp_path):
            dataset = create_dataset(config)
            train_data, valid_data, test_data = data_preparation(config, dataset)
            model = BPR(config, train_data.dataset).to(config["device"])
            trainer = Trainer(config, model)
            trainer.fit(train_data, valid_data, saved=True, show_progress=False)
            result = trainer.evaluate(test_data, load_best_model=True, show_progress=False)
        return dict(result)


def main() -> None:
    result = run()
    # Chỉ in ASCII: console Windows mặc định (cp1258) không in được tiếng Việt.
    print("RecBole BPR smoke test (CPU, toy data) OK:", {k: round(float(v), 4) for k, v in result.items()})


if __name__ == "__main__":
    main()
