# GameRecSys
Hệ gợi ý game Steam kết hợp ba hướng: học từ cả game người dùng chê, gợi ý game tiếp theo theo chuỗi thời gian, và gợi ý được game mới chưa có đánh giá.

## Cài đặt nhanh (laptop, Windows)

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements-torch-cpu.txt
pip install -r requirements.txt
pip install --no-deps -r requirements-recbole.txt
pytest
```

Chi tiết, cách cài trên Kaggle và lý do chọn phiên bản: [docs/environment.md](docs/environment.md). Kế hoạch: [PLAN.md](PLAN.md). Thuật ngữ: [GLOSSARY.md](GLOSSARY.md).
