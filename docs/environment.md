# Môi trường Python

Python 3.11, venv, các phiên bản thư viện ghi cố định trong ba file:

| File | Nội dung | Cài ở đâu |
| --- | --- | --- |
| `requirements-torch-cpu.txt` | torch 2.8.0 bản CPU | Chỉ laptop |
| `requirements.txt` | Mọi thư viện khác + package `gamerecsys` (editable) | Laptop và Kaggle |
| `requirements-recbole.txt` | RecBole 1.2.1, cài với `--no-deps` | Laptop và Kaggle |

## Cài trên laptop (Windows)

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-torch-cpu.txt
pip install -r requirements.txt
pip install --no-deps -r requirements-recbole.txt
```

Kiểm tra:

```bash
pytest                                            # mọi test, có cả RecBole (~1 phút)
pytest -m "not slow"                              # bỏ test chạy lâu
python -m gamerecsys.experiments.recbole_smoke    # chạy BPR của RecBole trên dữ liệu giả, CPU
```

Khi cài sẽ thấy pip báo `recbole 1.2.1 requires ray ... which is not installed`. Đây là do cố ý bỏ ray, không phải lỗi.

## Cài trên Kaggle (GPU)

Trong notebook, sau khi tải repo về:

```bash
pip install -r requirements.txt
pip install --no-deps -r requirements-recbole.txt
python -m gamerecsys.experiments.recbole_smoke
```

**Không** cài `requirements-torch-cpu.txt` trên Kaggle, vì sẽ đè mất torch GPU có sẵn. Bộ phiên bản này mới được thử trên laptop (Windows, CPU). Lần đầu chạy trên Kaggle cần chạy lệnh smoke test ở trên; nếu lỗi thì ghi lại trong issue và chỉnh file này.

## Lý do chọn phiên bản

- **RecBole 1.2.1** là bản mới nhất. Bản này có ba chỗ không hợp với thư viện mới, và cả ba đã được xử lý như sau:
  - **ray**: RecBole bắt buộc `ray<=2.6.3`, bản không có cho Python mới. Chỉ `recbole.quick_start` dùng ray, nên dự án **không dùng `quick_start`**, mà gọi thẳng `Config`, `create_dataset`, `data_preparation`, `Trainer` (xem `gamerecsys.experiments.recbole_smoke`). RecBole được cài `--no-deps`, các phụ thuộc còn lại ghi tay trong `requirements.txt`.
  - **numpy 2**: RecBole gán lại `np.float_`, `np.complex_`, `np.unicode_`, mà numpy 2 đã xoá các tên này. Module `gamerecsys.recbole_compat` trả lại các tên đó.
  - **torch >= 2.6**: `torch.load` mặc định `weights_only=True`, làm hỏng việc RecBole nạp lại checkpoint. `gamerecsys.recbole_compat` đặt biến môi trường `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1`. Cách này an toàn vì checkpoint chỉ do nhóm tự tạo.

  **Quy tắc:** mọi code gọi RecBole phải `from gamerecsys import recbole_compat` **trước** khi import `recbole`.
- **pandas 2.3.3, không lên 3.x**: pandas 3 bật copy-on-write, làm lệnh `fillna(inplace=True)` trong RecBole lặng lẽ không làm gì (giá trị thiếu không được điền). Có test chặn việc nâng nhầm lên pandas 3.
- **torch 2.8.0** (laptop): bản CPU ổn định, chạy được với lớp tương thích ở trên. Trên Kaggle dùng bản có sẵn; lớp tương thích chạy được với mọi torch 2.x.
- **numpy 2.4.6, polars, sentence-transformers, streamlit, plotly, pytest**: bản mới nhất lúc dựng môi trường (2026-11), đã chạy thử cùng nhau.

## Ghi chú Windows

Console Windows mặc định (cp1258) không in được tiếng Việt. Script in ra màn hình chỉ dùng chữ ASCII, hoặc đặt `set PYTHONUTF8=1` trước khi chạy.
