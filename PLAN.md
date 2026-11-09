# Kế hoạch dự án Gợi ý game Steam (IT4613)

Cập nhật: 2026-11-10 (bản đã chốt sau buổi phỏng vấn thiết kế). Nhóm 3 người, 4 tuần.

Thuật ngữ dùng trong tài liệu này được định nghĩa trong [GLOSSARY.md](GLOSSARY.md). Các quyết định khó đảo ngược được ghi trong [docs/adr/](docs/adr/).

Quy ước từ ngữ: **review** là nhận xét của người chơi trên Steam (review thích, review chê). **Đo** là việc chấm điểm mô hình. Không dùng từ "đánh giá" để tránh nhầm hai nghĩa.

## 1. Mục tiêu và thứ tự ưu tiên

Hệ gợi ý game Steam kết hợp ba hướng: học từ cả review chê, gợi ý game tiếp theo theo chuỗi review, và gợi ý được game chưa có review (game cold-start). Phạm vi đã cắt gọn ngay từ đầu: không dùng LightGCN, M3 chỉ làm bản dựa trên nội dung.

| Ưu tiên | Module | Câu hỏi trả lời | Chương môn học |
| --- | --- | --- | --- |
| 1 (bắt buộc) | M1. Học từ review chê | Đưa review chê vào huấn luyện có giúp gợi ý tốt hơn và ít gợi ý nhầm game người dùng sẽ chê không? | Lọc cộng tác nâng cao |
| 2 (bắt buộc) | M2. Gợi ý theo chuỗi review | Thứ tự các review gần đây có giúp đoán game tiếp theo người dùng sẽ review thích không? | Gợi ý dựa trên phiên |
| 3 (bắt buộc, bản đơn giản) | M3. Game cold-start | Chỉ từ tag và mô tả, gợi ý game chưa có review được đến đâu? (đo trên game bị giấu) | Gợi ý dựa trên nội dung |
| Kết hợp | Hybrid | Gộp ba module có tốt hơn từng module riêng không? | Kết hợp các kỹ thuật |

**Nguyên tắc cắt giảm:** nếu trễ, cắt theo thứ tự: (1) chế độ tự chọn game trong demo, (2) biến thể SASRec có review chê. Luôn giữ M1, M2, M3 và hybrid.

**Đã chuyển sang hướng phát triển:** LightGCN; ánh xạ tương phản (InfoNCE) cho M3.

**Sản phẩm bàn giao:** mã nguồn nén kèm README; app demo Streamlit; báo cáo PDF đủ 6 mục slide IT4613; bài trình bày khoảng 15 phút, cả 3 người cùng trình bày.

## 2. Dữ liệu

Bộ Game Recommendations on Steam (Kaggle, antonkozyriev): hơn 41 triệu review đã làm sạch, user ID đã ẩn danh.
https://www.kaggle.com/datasets/antonkozyriev/game-recommendations-on-steam

| File | Nội dung chính | Dùng cho |
| --- | --- | --- |
| recommendations.csv | user_id, app_id, is_recommended, hours, date, review_id | Review thích/chê, chuỗi review |
| games.csv | title, date_release, giá, nền tảng, các cột tổng hợp review | Hiển thị |
| games_metadata.json | description, tags | Đặc trưng nội dung cho M3, chọn persona, lọc tag trong demo |
| users.csv | products, reviews | Lọc người dùng, phân nhóm |

Tên cột lấy theo mô tả của các dự án dùng bộ này. **Phải kiểm tra lại với file thật khi tải về** và sửa bảng này nếu khác.

**Tín hiệu**

- Review thích: is_recommended = True. Review chê: is_recommended = False. Tỷ lệ review thích trên Steam rất cao, nên cách đo M1 phải tính đến điều này (con số thật đo trong EDA).
- Mức độ gắn bó: hours (giờ chơi lúc viết review), dùng làm trọng số.

**Lưu ý về thứ tự:** date là ngày *viết review*, chỉ có ngày, không có giờ; người dùng thường review sau khi đã chơi lâu. Chuỗi trong dự án là **chuỗi review, không phải thứ tự chơi**. Báo cáo phải nói rõ điều này. Xử lý trùng ngày:

- Thứ tự chính: sắp theo date; cùng ngày thì giữ thứ tự gốc trong file (sắp xếp ổn định). Kiểm tra trong EDA xem review_id có tăng theo thời gian không; nếu có, dùng review_id làm khóa phụ.
- Tập kiểm tra độ vững: bỏ người dùng có từ 3 review trở lên trong cùng một ngày, và bỏ người dùng có hai review thích cuối cùng cùng ngày (không xác định được game cần đoán).
- Đo tỷ lệ review trùng ngày trong EDA để đưa vào báo cáo.

**Tiền xử lý**

1. Lọc k-core lặp trên **toàn bộ** dữ liệu (chỉ đọc các cột cần, dùng polars): người dùng ≥ 10 review, game ≥ 20 review, đếm cả review thích lẫn chê; lặp đến khi không còn ai bị loại.
2. Bốc mẫu 50–100 nghìn người dùng từ nhóm đã qua lọc, rồi lọc k-core lại một lần trên mẫu. Chỉ tăng cỡ mẫu khi mọi thứ đã chạy ổn.
3. Dữ liệu đầy đủ (2,2 GB) **chỉ nằm trên Kaggle**, không tải về máy. Để thử code trên máy, tạo một **mẫu thô thu nhỏ** trên Kaggle (khoảng 10 nghìn người dùng có ≥ 10 review, 4 file giống hệt cấu trúc file gốc, vài chục MB) rồi tải về. Cùng một code chạy trên máy với mẫu này và trên Kaggle với dữ liệu đầy đủ, chỉ khác đường dẫn và cỡ mẫu.
4. Sắp chuỗi review theo quy tắc trên.
5. Chuẩn hóa hours: log(1 + hours), cắt ngưỡng trên.
6. Văn bản M3: ghép tags + description, mã hóa bằng sentence-transformers.
7. Tránh rò rỉ: không dùng các cột tổng hợp từ review trong games.csv (số review, tỷ lệ review thích, xếp hạng) làm đặc trưng cho M3, vì game cold-start không có các giá trị này.

**Hai thiết lập chia tập** (xem [ADR 0001](docs/adr/0001-two-split-setups.md)). Hai thiết lập dùng chung dữ liệu đã lọc và hàm đo, chỉ khác cách chia.

- **Thiết lập A — M1, M2, Hybrid (mọi game đều có trong dữ liệu học):**
  - Leave-last-out theo thời gian: review thích cuối cùng dùng để đo (test), review thích áp chót dùng để chọn tham số (validation), phần còn lại để học (train).
  - **Mốc cắt** (xem [ADR 0002](docs/adr/0002-cut-reviews-after-test-date.md)): với mỗi người dùng, bỏ khỏi train mọi review viết sau ngày của review test.
  - Tập test tiêu cực (để đo Neg@10): với người dùng có ≥ 2 review chê không sau mốc cắt, giấu review chê gần nhất không sau mốc cắt. Người đó vẫn còn ít nhất 1 review chê trong train.
- **Thiết lập B — chỉ M3:**
  - Chọn ngẫu nhiên khoảng 10% game (trong số game đã qua lọc) làm **game bị giấu**; xóa mọi review của chúng khỏi train của thiết lập này.
  - Chia đôi game bị giấu: 5% để chọn λ (validation), 5% để đo kết quả cuối (test).
  - Đo: review thích của người dùng với game bị giấu, xếp hạng trong nhóm game bị giấu tương ứng.
  - Kiểm tra lại bằng nhóm game phát hành gần nhất.

## 3. Kiến trúc hệ thống

Ba module độc lập, mỗi module đề cử ứng viên, hybrid gộp và chọn top-10. Dữ liệu đã chia và hàm đo chung phải xong đầu tiên. Sơ đồ là thiết lập A; khả năng gợi ý game bị giấu của M3 đo riêng ở thiết lập B.

```text
Dữ liệu Steam (thiết lập A; mẫu 50–100k người dùng)
   |  review thích + chê  |  chuỗi review             |  tag, mô tả
   v                      v                           v
M1. Review chê          M2. Chuỗi review            M3. Game cold-start
(ba biến thể BPR)       (SASRec, GRU4Rec)           (độ giống nội dung)
   |  top-100             |  top-100                  |  top-20 game ít review
   v                      v                           v
Hybrid: gộp ứng viên, chấm điểm, trừ điểm game giống game đã chê
   |
   v
Top-10 kèm lý do → hiển thị trên Streamlit
```

**Độ giống nội dung** (cosine giữa embedding tags + description của M3) là cách đo "giống" duy nhất, dùng chung cho mọi chỗ trừ điểm "giống game đã chê" (phạt hậu kỳ M1, hybrid) và cho dòng lý do hiển thị (kèm tag trùng).

## 4. Chi tiết ba module và hybrid

Baseline và mô hình chuẩn dùng RecBole; ba biến thể BPR (PyTorch), M3 và hybrid (numpy) tự viết.

### M1. Học từ review chê (ưu tiên 1)

- Baseline (RecBole): Popularity, ItemKNN, BPR chỉ dùng review thích.
- Ba biến thể BPR cùng một code, để đối chứng giả định:

| Biến thể | Các cặp so sánh trong loss | Giả định |
| --- | --- | --- |
| BPR thường | thích > chưa tương tác | Bỏ qua review chê |
| BPR + chê | thích > chưa tương tác; thích > chê | Chỉ giả định game thích tốt hơn game chê |
| BPR ba mức | thích > chưa tương tác > chê | Thêm giả định: game chưa tương tác tốt hơn game bị chê |

- Giả định "chưa tương tác > chê" hợp lý nhưng chưa chắc đúng (người dùng có thể còn ghét game chưa chơi hơn game đã chê). So BPR + chê với BPR ba mức để biết giả định này có giúp không, và nêu rõ trong báo cáo.
- Review thích nhân trọng số log(1 + hours), **giống nhau cho cả ba biến thể**, để khác biệt giữa chúng chỉ nằm ở cách dùng review chê.
- Kiểm tra code: chạy BPR thường tự viết **không trọng số**; kết quả phải gần bằng BPR của RecBole.
- Phạt hậu kỳ (để so sánh): BPR thường, trừ điểm game giống game đã chê (theo độ giống nội dung).
- Fold-in cho người xem (chế độ tự chọn game): giữ cố định vector game đã học, học nhanh vector người xem từ các game họ đánh dấu thích/chê.

### M2. Gợi ý theo chuỗi review (ưu tiên 2)

Đoán game tiếp theo người dùng sẽ review thích. Chuỗi là thứ tự viết review, không phải thứ tự chơi; báo cáo dùng đúng cách gọi này.

- GRU4Rec và SASRec trong RecBole, chuỗi tối đa 50 game, chỉ gồm review thích.
- Đối chứng chính: **BPR thường** (cũng chỉ dùng review thích, chỉ khác ở chỗ không dùng thứ tự). BPR ba mức là dòng tham khảo.
- Kiểm tra độ vững: chạy lại trên tập đã bỏ người dùng nhiều review cùng ngày. Chỉ kết luận "thứ tự có ích" nếu ưu thế còn trên tập này.
- Nâng cao (nếu kịp): đưa review chê vào chuỗi kèm embedding loại review.

### M3. Game cold-start (ưu tiên 3)

- Embedding tags + description bằng sentence-transformers (ví dụ all-MiniLM-L6-v2).
- Hồ sơ người dùng = TB embedding game thích − λ × TB embedding game chê; λ chọn trên nửa validation của game bị giấu; λ = 0 là đối chứng không dùng review chê.
- Gợi ý theo cosine. Baseline: ngẫu nhiên; trùng tag với tag người dùng hay thích.
- Không dùng các cột tổng hợp từ review.

### Hybrid (thiết lập A)

1. Ứng viên: top-100 SASRec, top-100 BPR ba mức, top-20 từ M3 trong nhóm **game ít review** (20% game có số review thấp nhất trong train).
2. Chấm điểm: chuẩn hóa từng nguồn về 0–1, cộng có trọng số, trừ điểm cho game giống game đã chê (độ giống nội dung).
3. Trọng số: grid search trên validation.
4. Giải thích: "vì bạn thích X", "bạn vừa review Y", "game ít người biết, cùng tag với Z"; game bị loại ghi "giống W bạn đã chê (cùng tag …)".

Khả năng gợi ý game bị giấu được đo riêng ở thiết lập B, không tính vào điểm hybrid.

## 5. Đo mô hình

| Mục đo | Chỉ số | Cách đo |
| --- | --- | --- |
| Chung (thiết lập A) | Recall@10, NDCG@10, HitRate@10 | Review thích cuối cùng, xếp hạng trên toàn bộ game (không lấy mẫu âm) |
| M1 | Neg@10 luôn đi cùng NDCG@10; tỉ lệ Hit_thích@10 / Hit_chê@10 | Tập test tiêu cực; so ba biến thể BPR và phạt hậu kỳ; vẽ đường đánh đổi (NDCG@10, Neg@10) khi quét mức phạt |
| M2 | NDCG@10 theo độ dài chuỗi | SASRec, GRU4Rec vs BPR thường (BPR ba mức để tham khảo), trên tập gốc và tập kiểm tra độ vững |
| M3 (thiết lập B) | Recall@10, NDCG@10 trong nhóm game bị giấu | λ = 0, λ tốt nhất, ngẫu nhiên, trùng tag |
| Hybrid | Recall@10, NDCG@10, Neg@10, độ phủ | Hybrid vs từng module |
| Chất lượng danh sách | Độ đa dạng tag, tỷ lệ game ít review | Tránh chỉ gợi ý game nổi tiếng |

Quy tắc:

- Neg@10 và chỉ số tích cực tính trên cùng một lần xếp hạng (đã bỏ game có trong train).
- **Không đọc Neg@10 một mình**: mô hình gợi ý lung tung cũng có Neg@10 thấp. Chỉ kết luận "review chê có ích" khi Neg@10 giảm mà NDCG@10 không giảm quá 1 độ lệch chuẩn (qua 3 seed).
- 3 seed cho cấu hình tốt nhất (trung bình ± độ lệch chuẩn); xếp hạng trên toàn bộ game; mọi mô hình dùng chung tập chia và src/eval.
- Mỗi lần chạy tự thêm một dòng vào `artifacts/results.csv`: mô hình, thiết lập (A/B), tập (gốc/độ vững), cấu hình, seed, mọi chỉ số. Tab 4 và bảng báo cáo đọc từ file này.

Kết quả chính: bảng tổng hợp; đường đánh đổi Neg@10–NDCG@10 của ba biến thể BPR và phạt hậu kỳ; NDCG@10 theo độ dài chuỗi trên tập gốc và tập độ vững; bảng game bị giấu (thiết lập B); ablation hybrid.

## 6. Demo (Streamlit, 4 tab)

Thiết kế để người không chơi game (kể cả giảng viên) vẫn hiểu: phán đoán qua ảnh bìa và tag, không cần biết tên game.

**Chạy ở đâu:** trên laptop, không cần mạng, không cần GPU. Mọi thứ nặng (embedding nội dung, vector game của BPR, checkpoint SASRec, top-K cho persona) được tính sẵn trên Kaggle và xuất ra file. Mỗi lần gợi ý trên laptop phải xong dưới 1 giây.

**Chọn người xem là ai**

- **Persona** (chế độ chính): 4–6 persona, ví dụ "Thích game nông trại thư giãn", "Thích game bắn súng online", "Thích nhập vai có cốt truyện", "Thích giải đố indie". Mỗi persona là **một người dùng thật** trong dữ liệu, có tag nổi bật khớp mô tả và có ≥ 2 review chê (để mục "Đã loại" có nội dung).
- **Chế độ tự chọn game** (tuần 3, cắt đầu tiên nếu trễ):
  1. Người xem duyệt ảnh bìa game, lọc theo tag hoặc gõ tên.
  2. Bấm 👍 với game thích và 👎 với game chê. Cần ít nhất 3 game 👍; game 👎 là tuỳ chọn.
  3. Thứ tự bấm 👍 được coi là chuỗi review (game bấm sau cùng là "vừa review"). Kéo thả để đổi thứ tự là phần thêm nếu còn thời gian.
  4. Bấm "Gợi ý": cả 4 tab chạy như với persona. M2 và M3 nhận trực tiếp danh sách đã chọn; M1 dùng fold-in.
- Hiển thị game: ảnh header của Steam theo app_id, tên, tag nổi bật, giá, một dòng lý do.
- Ảnh tải sẵn vào app/assets cho **mọi game sau bộ lọc**. Nếu tổng vượt 500 MB thì màn hình chọn game chỉ hiện game có ảnh; game thiếu ảnh dùng ảnh thay thế. Ghi nguồn ảnh (Steam) trong báo cáo.

**Các tab**

- Tab 1 – Gợi ý cho bạn (Hybrid + M1): top-10 kèm ảnh, tag, lý do; mục "Đã loại". Công tắc phản hồi tiêu cực:
  - **Bật**: hybrid dùng BPR ba mức và trừ điểm game giống game đã chê; mục "Đã loại" hiện các game bị trừ.
  - **Tắt**: hybrid dùng BPR thường, không trừ điểm; mục "Đã loại" trống.
- Tab 2 – Review tiếp theo (M2): dòng thời gian các game được review gần nhất (ghi rõ là thứ tự viết review); SASRec đặt cạnh gợi ý không dùng thứ tự.
- Tab 3 – Game ít người biết (M3): game ít review hợp gu, kèm tag trùng với game người xem thích.
- Tab 4 – So sánh mô hình: bảng kết quả, đường đánh đổi Neg@10–NDCG@10, biểu đồ theo độ dài chuỗi, ablation hybrid.

## 7. Công nghệ và cấu trúc repo

- Python 3.11, môi trường **venv**, thư viện ghi cố định phiên bản trong `requirements.txt` (dùng chung cho laptop và Kaggle). RecBole hay lỗi với bản mới của numpy/torch, nên việc đầu tiên là tìm bộ phiên bản chạy được ở cả hai nơi.
- RecBole (Popularity, ItemKNN, BPR, GRU4Rec, SASRec); PyTorch cho ba biến thể BPR; numpy cho M3 và hybrid; sentence-transformers; polars + parquet; Streamlit + Plotly; huấn luyện trên GPU Kaggle.
- **Toàn bộ logic nằm trong `src/`.** Notebook Kaggle chỉ tải repo, gọi script trong `src/` và xuất file; không viết logic trong notebook.
- **Test tự động** (pytest) cho `src/data` và `src/eval` trên một bộ dữ liệu giả rất nhỏ tính tay được. Ví dụ: không review nào sau mốc cắt lọt vào train; Recall@10 khớp với tính tay.
- Công việc chia thành ticket trên GitHub Issues, mỗi ticket kiểm tra được trên mẫu thô thu nhỏ bằng CPU. Việc chỉ người làm được (tạo mẫu thô thu nhỏ, chạy EDA và bản đầy đủ trên Kaggle, chạy 3 seed, tổng duyệt demo khi tắt mạng) là ticket riêng ghi rõ "người làm".
- GitHub, mỗi ticket một nhánh, merge qua pull request.

```text
GameRecSys/
├── data/               # mẫu thô thu nhỏ, processed — không commit
├── configs/            # cấu hình RecBole và mô hình riêng
├── src/
│   ├── data/           # lọc k-core, bốc mẫu, sắp chuỗi, thiết lập A và B, tập độ vững
│   ├── eval/           # Recall, NDCG, HitRate, Neg@10, độ đa dạng (dùng chung)
│   ├── experiments/    # script chạy nhiều seed, ghi artifacts/results.csv
│   ├── m1_negative/    # ba biến thể BPR, phạt hậu kỳ, fold-in
│   ├── m2_sequential/  # SASRec, GRU4Rec qua RecBole; biến thể có review chê
│   ├── m3_coldstart/   # embedding nội dung, hồ sơ người dùng có λ, độ giống nội dung
│   ├── hybrid/         # gộp ứng viên, chấm điểm, giải thích
│   └── export/         # xuất embedding, checkpoint, top-K persona cho app
├── tests/              # test cho src/data và src/eval trên dữ liệu giả
├── notebooks/          # EDA, notebook Kaggle mỏng gọi src/
├── artifacts/          # embedding, top-K, results.csv
├── app/
│   └── assets/         # ảnh header tải sẵn
├── reports/            # hình, bảng, báo cáo PDF
├── docs/adr/           # các quyết định khó đảo ngược
├── GLOSSARY.md
├── PLAN.md
├── requirements.txt
└── README.md
```

## 8. Phân công

Nhóm tự chia ticket khi làm (mỗi người chạy agent trên các ticket mình nhận). Ticket không gắn tên người. Gợi ý nhóm việc theo mảng:

| Mảng | Gồm |
| --- | --- |
| Dữ liệu và đo | k-core, bốc mẫu, mẫu nhỏ, thiết lập A và B, tập độ vững, src/eval, test |
| M1 và Hybrid | Baseline RecBole, ba biến thể BPR, phạt hậu kỳ, fold-in, gộp ứng viên, giải thích |
| M2 và thí nghiệm | GRU4Rec, SASRec, kiểm tra độ vững, script chạy 3 seed, results.csv |
| M3 và demo | Embedding nội dung, λ, persona, ảnh, khung Streamlit, 4 tab, chế độ tự chọn game |

## 9. Lộ trình 4 tuần

Mốc: cuối tuần 1 dữ liệu và baseline chốt; cuối tuần 2 ba module cơ bản chạy trên mẫu 50–100k (chỉ tăng cỡ mẫu sau mốc này); cuối tuần 3 chốt kết quả và demo.

**Tuần 1: Dữ liệu và baseline**

- [ ] Tạo venv, `requirements.txt` cố định phiên bản chạy được trên laptop và Kaggle
- [ ] (Người làm, Kaggle) Tạo mẫu thô thu nhỏ, tải về máy, kiểm tra tên cột thật
- [ ] Lọc k-core, bốc mẫu, chạy được trên mẫu thô thu nhỏ và trên dữ liệu đầy đủ (Kaggle)
- [ ] Script EDA: tỷ lệ thích/chê, số người dùng có ≥ 2 review chê, phân bố giờ chơi, tỷ lệ review trùng ngày, review_id có tăng theo thời gian không, số game sau lọc
- [ ] (Người làm, Kaggle) Chạy EDA trên dữ liệu đầy đủ, mang con số về
- [ ] Tạo thiết lập A (mốc cắt + test tiêu cực), thiết lập B (game bị giấu 5% + 5%), tập độ vững; xuất định dạng RecBole; có test
- [ ] Viết src/eval: Recall, NDCG, HitRate, Neg@10, độ đa dạng; có test
- [ ] Chạy Popularity, ItemKNN, BPR (RecBole)
- [ ] Chạy thử SASRec trên mẫu nhỏ; script chạy nhiều seed ghi results.csv

**Tuần 2: Bản cơ bản của ba module**

- [ ] Ba biến thể BPR (cùng trọng số giờ chơi), bản không trọng số so với RecBole, phạt hậu kỳ; đo Recall, NDCG, Neg@10
- [ ] GRU4Rec, SASRec trên tập gốc và tập độ vững; so với BPR thường
- [ ] M3: embedding nội dung, hồ sơ có λ, đo trên thiết lập B
- [ ] Khung Streamlit đọc file kết quả, tab 4 hiển thị bảng chỉ số
- [ ] Xuất top-K của ba module cho người dùng mẫu; quyết định có tăng cỡ mẫu không

**Tuần 3: Hybrid và hoàn thiện**

- [ ] Hybrid: gộp ứng viên, chấm điểm, chọn trọng số trên validation, sinh lý do
- [ ] Chạy 3 seed cho cấu hình tốt nhất của mọi mô hình (người làm, trên Kaggle)
- [ ] Ablation hybrid; chọn persona; tải sẵn ảnh header
- [ ] Hoàn thiện tab 1, 2, 3 với persona
- [ ] Chế độ tự chọn game: màn hình chọn, fold-in BPR (cắt đầu tiên nếu trễ)
- [ ] Biến thể SASRec có review chê (nếu kịp)

**Tuần 4: Báo cáo và trình bày**

- [ ] Báo cáo PDF theo 6 mục slide yêu cầu
- [ ] Slide 15 phút, chia phần trình bày
- [ ] README hướng dẫn cài đặt, đóng gói mã nguồn
- [ ] Tổng duyệt 2 lần, có bấm giờ, chạy demo khi không có mạng

Nếu chỉ có 3 tuần: bỏ chế độ tự chọn game và biến thể SASRec có review chê, viết báo cáo song song từ tuần 2.

## 10. Rủi ro

| Rủi ro | Dấu hiệu | Dự phòng |
| --- | --- | --- |
| Quá ít người dùng có ≥ 2 review chê | Tập test tiêu cực quá nhỏ để Neg@10 có ý nghĩa | Hạ ngưỡng xuống 1 (người đó không còn review chê trong train); hoặc cắt toàn cục theo thời gian thay vì theo từng người |
| Thứ tự trong cùng ngày không xác định | Tỷ lệ trùng ngày cao; kết quả M2 đổi nhiều giữa tập gốc và tập độ vững | Báo cáo cả hai tập; chỉ kết luận về thứ tự nếu ưu thế còn trên tập độ vững |
| Dữ liệu quá lớn cho Kaggle | Hết RAM hoặc mô hình chạy quá lâu | Chỉ đọc cột cần, dùng polars; bắt đầu 50–100k người dùng; tăng ngưỡng k-core |
| Tên cột thật khác mô tả | Script đọc dữ liệu lỗi | Kiểm tra ngay khi tải, cập nhật bảng cột trong PLAN.md |
| RecBole khó dùng hoặc xung đột phiên bản | Quá 1 ngày chưa chạy được mô hình đầu tiên | Chạy ví dụ có sẵn trước; cố định phiên bản trong requirements.txt; chuyển sang định dạng .inter ngay tuần 1 |
| BPR ba mức không tốt hơn | Ngang hoặc kém BPR + chê | Vẫn là kết quả: giả định "chưa tương tác > chê" không giúp; phân tích trong thảo luận |
| BPR tự viết lệch xa RecBole | Bản không trọng số kém hơn BPR RecBole rõ rệt | Sửa code tự viết trước khi so ba biến thể |
| Ảnh quá nặng hoặc không hiển thị lúc demo | Tổng ảnh > 500 MB; mất mạng | Tải sẵn vào app/assets, có ảnh thay thế; tổng duyệt khi tắt mạng |
| Trễ tiến độ | Chưa ghép end-to-end cuối tuần 2 | Cắt chế độ tự chọn game, rồi biến thể SASRec; dồn người vào ghép và demo |

## 11. Báo cáo và trình bày

Báo cáo PDF theo 6 mục slide, nêu thẳng các giới hạn dữ liệu:

| Mục slide | Nội dung |
| --- | --- |
| Bài toán thực tế | Người chơi Steam khó chọn game; ba vấn đề: review chê bị bỏ qua, thứ tự review, game cold-start |
| Chi tiết phương pháp | Ba biến thể BPR, SASRec, M3 theo nội dung, hybrid; hai thiết lập chia tập và lý do tách; mốc cắt chống rò rỉ |
| Chức năng hệ thống | Persona, chế độ tự chọn game, 4 tab demo, ảnh chụp màn hình |
| Phần mềm, dữ liệu dùng lại | Bộ Steam Kaggle, RecBole, sentence-transformers, ảnh header Steam, paper gốc |
| Khó khăn và cách vượt qua | Dữ liệu lớn, ít review chê, review trùng ngày, xung đột cách chia M3 với các module khác |
| Tranh luận, kết luận, hướng phát triển | Review chê có giúp không (đọc cùng độ chính xác); giả định BPR ba mức; thứ tự review ≠ thứ tự chơi; game bị giấu chỉ mô phỏng game cold-start; LightGCN, ánh xạ tương phản cho M3 |

Trình bày ~15 phút: bài toán, dữ liệu, hai thiết lập 0–3; M1 3–6; M2 (tập gốc và độ vững) 6–8; M3 8–10; hybrid và demo 10–14; kết luận, giới hạn 14–15. Ghi rõ RecBole và sentence-transformers trong slide phương pháp.

## 12. Nguồn tham khảo

- Dữ liệu: https://www.kaggle.com/datasets/antonkozyriev/game-recommendations-on-steam
- RecBole (Zhao và cộng sự, arXiv 2011.01731): https://arxiv.org/abs/2011.01731
- Paper gốc: BPR (UAI 2009), GRU4Rec (ICLR 2016), SASRec (ICDM 2018).
