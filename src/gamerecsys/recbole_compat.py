"""Cho RecBole 1.2.1 chạy được với numpy 2 và torch >= 2.6.

Import module này TRƯỚC mọi module ``recbole``. Mọi code trong dự án gọi RecBole
đều phải đi qua đây; xem lý do trong docs/environment.md.

- numpy 2 đã xoá ``np.float_``, ``np.complex_``, ``np.unicode_``, mà RecBole gán
  lại chúng khi tạo Config, nên ta trả lại các tên đó trước.
- torch >= 2.6 đổi mặc định ``torch.load(weights_only=True)``, làm hỏng việc RecBole
  nạp checkpoint (checkpoint chứa cả object Config). Biến môi trường dưới đây
  đưa về hành vi cũ. Checkpoint chỉ do chính nhóm tạo ra nên không có rủi ro.
"""

import os

os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")

import numpy as np  # noqa: E402

_REMOVED_IN_NUMPY_2 = {
    "float_": np.float64,
    "complex_": np.complex128,
    "unicode_": np.str_,
}

for _name, _value in _REMOVED_IN_NUMPY_2.items():
    if _name not in np.__dict__:
        setattr(np, _name, _value)
