"""Test môi trường: package import được và RecBole chạy được trên CPU."""

import importlib
import math

import pytest

SUBMODULES = [
    "data",
    "eval",
    "experiments",
    "m1_negative",
    "m2_sequential",
    "m3_coldstart",
    "hybrid",
    "export",
]


@pytest.mark.parametrize("name", SUBMODULES)
def test_submodule_imports(name):
    importlib.import_module(f"gamerecsys.{name}")


def test_pandas_stays_below_3_for_recbole():
    # pandas 3 bật copy-on-write: fillna(inplace=True) của RecBole lặng lẽ không làm gì.
    import pandas

    assert int(pandas.__version__.split(".")[0]) == 2, "RecBole 1.2.1 cần pandas 2.x, xem docs/environment.md"


def test_importing_package_applies_recbole_compat():
    import os

    import numpy as np

    import gamerecsys  # noqa: F401

    assert os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] == "1"
    assert np.float_ is np.float64
    assert np.complex_ is np.complex128
    assert np.unicode_ is np.str_


@pytest.mark.slow
def test_recbole_bpr_trains_and_reloads_checkpoint_on_cpu():
    from gamerecsys.experiments import recbole_smoke

    result, device = recbole_smoke.run(epochs=2)

    assert device == "cpu"
    assert set(result) == {"recall@10", "ndcg@10"}
    assert all(math.isfinite(v) and 0.0 <= v <= 1.0 for v in result.values())


def test_requesting_gpu_without_cuda_fails_loudly(monkeypatch):
    from gamerecsys.experiments import recbole_smoke

    monkeypatch.setattr(recbole_smoke.torch.cuda, "is_available", lambda: False)

    with pytest.raises(recbole_smoke.GpuUnavailableError):
        recbole_smoke.run(use_gpu=True)
