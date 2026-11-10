"""Tiện ích dùng chung cho các lệnh ``python -m gamerecsys...``."""

import sys


def ensure_utf8_output() -> None:
    """Cho phép in tiếng Việt: console Windows mặc định (cp1258) báo lỗi khi in ký tự có dấu.

    Gọi ở đầu mỗi ``main()``.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
