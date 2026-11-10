"""Kiểm tra môi trường: chạy BPR của RecBole trên một bộ dữ liệu giả nhỏ.

Chạy trên laptop: ``python -m gamerecsys.experiments.recbole_smoke``
Chạy trên Kaggle (thử GPU): ``python -m gamerecsys.experiments.recbole_smoke --gpu``

Không dùng ``recbole.quick_start`` vì module đó import ``ray`` (đã bỏ khỏi môi trường,
xem docs/environment.md). Bản vá tương thích được áp khi import package ``gamerecsys``.
"""

from __future__ import annotations

import argparse
import contextlib
import random
import tempfile
from pathlib import Path

from gamerecsys.cli import ensure_utf8_output
from recbole.config import Config
from recbole.data import create_dataset, data_preparation
from recbole.model.general_recommender import BPR
from recbole.trainer import Trainer
from recbole.utils import init_seed

DATASET = "toy"
N_USERS, N_ITEMS, ITEMS_PER_USER = 60, 40, 12


def _write_toy_dataset(root: Path) -> None:
    """Ghi một file .inter giả theo định dạng atomic của RecBole."""
    rng = random.Random(0)
    folder = root / DATASET
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["user_id:token\titem_id:token\ttimestamp:float"]
    for u in range(N_USERS):
        for t, i in enumerate(rng.sample(range(N_ITEMS), ITEMS_PER_USER)):
            lines.append(f"u{u}\ti{i}\t{t}")
    (folder / f"{DATASET}.inter").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(epochs: int = 2, use_gpu: bool = False) -> dict[str, float]:
    """Huấn luyện BPR vài epoch, nạp lại checkpoint tốt nhất, trả về chỉ số trên tập test."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_toy_dataset(tmp_path)
        config = Config(
            model=BPR,
            dataset=DATASET,
            config_dict={
                "data_path": str(tmp_path),
                "checkpoint_dir": str(tmp_path / "saved"),
                "use_gpu": use_gpu,
                "epochs": epochs,
                "train_batch_size": 256,
                "eval_batch_size": 256,
                "metrics": ["Recall", "NDCG"],
                "topk": [10],
                "valid_metric": "NDCG@10",
                "show_progress": False,
                "seed": 2026,
                "reproducibility": True,
            },
        )
        init_seed(config["seed"], config["reproducibility"])
        # RecBole ghi log_tensorboard/ vào thư mục hiện tại, nên chạy trong thư mục tạm.
        with contextlib.chdir(tmp_path):
            dataset = create_dataset(config)
            train_data, valid_data, test_data = data_preparation(config, dataset)
            model = BPR(config, train_data.dataset).to(config["device"])
            trainer = Trainer(config, model)
            trainer.fit(train_data, valid_data, saved=True, show_progress=False)
            result = trainer.evaluate(test_data, load_best_model=True, show_progress=False)
        return {k: float(v) for k, v in result.items()}


def main() -> None:
    ensure_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gpu", action="store_true", help="chạy trên GPU (Kaggle)")
    args = parser.parse_args()
    result = run(use_gpu=args.gpu)
    device = "GPU" if args.gpu else "CPU"
    print(f"RecBole BPR chạy thử ({device}, dữ liệu giả) OK:", {k: round(v, 4) for k, v in result.items()})


if __name__ == "__main__":
    main()
