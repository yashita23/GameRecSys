"""GameRecSys: hệ gợi ý game Steam (IT4613). Thuật ngữ theo GLOSSARY.md."""

# Áp lớp tương thích RecBole ngay khi package được import, để mọi module con
# (gamerecsys.xxx) đã có bản vá trước khi chúng import recbole. Xem docs/environment.md.
from gamerecsys import recbole_compat  # noqa: F401

__version__ = "0.1.0"
