# GameRecSys

Hệ gợi ý game Steam học từ cả review thích lẫn review chê, dùng thứ tự review và gợi ý được game chưa có review.

## Review và người dùng

**Review**:
Một lần người dùng viết nhận xét về một game trên Steam, kèm lựa chọn thích hoặc chê, số giờ chơi lúc viết và ngày viết.
_Avoid_: đánh giá (dành cho việc đo mô hình), tương tác, rating

**Review thích**:
Review mà người dùng chọn "Recommended".
_Avoid_: đánh giá tích cực, phản hồi dương

**Review chê**:
Review mà người dùng chọn "Not Recommended".
_Avoid_: đánh giá tiêu cực, game bị ghét

**Chuỗi review**:
Các review của một người dùng xếp theo ngày viết. Đây là thứ tự viết review, không phải thứ tự chơi game.
_Avoid_: chuỗi chơi, lịch sử chơi, phiên

**Persona**:
Một người dùng thật trong dữ liệu, được chọn để đại diện cho một gu chơi game dễ hiểu (ví dụ "thích game nông trại thư giãn") khi trình diễn demo.
_Avoid_: người dùng giả, hồ sơ mẫu

**Người xem**:
Người đang dùng app demo. Người xem không có trong dữ liệu học.
_Avoid_: người dùng (dành cho người có review trong dữ liệu)

**Chế độ tự chọn game**:
Cách dùng demo trong đó người xem tự đánh dấu một số game thích hoặc chê, rồi nhận gợi ý như một persona. Thứ tự đánh dấu thích được coi là chuỗi review.
_Avoid_: chế độ tự chọn tag, custom mode

## Phân loại game

**Game bị giấu**:
Game đã có review nhưng bị nhóm cố ý giấu toàn bộ review khỏi dữ liệu học, để thử xem hệ thống có gợi ý được game chưa có review hay không.
_Avoid_: game mới

**Game ít review**:
Game có review trong dữ liệu học nhưng số review thấp.
_Avoid_: game mới, game hiếm

**Game cold-start**:
Game mới phát hành thật, chưa có review nào. Đây là tình huống ngoài đời mà game bị giấu dùng để mô phỏng.
_Avoid_: game mới

## Đo mô hình

**Thiết lập A**:
Cách chia dữ liệu trong đó mọi game đều có trong dữ liệu học, và review thích cuối cùng của mỗi người dùng được giấu để đoán. Dùng cho M1, M2 và hybrid.
_Avoid_: tập chính, split chung

**Thiết lập B**:
Cách chia dữ liệu trong đó một nhóm game bị giấu toàn bộ review. Chỉ dùng để đo M3.
_Avoid_: tập cold-start

**Đo**:
Việc chấm điểm chất lượng gợi ý của một mô hình bằng các chỉ số như Recall@10, NDCG@10.
_Avoid_: đánh giá

**Neg@10**:
Tỷ lệ người dùng có ít nhất một game họ sẽ review chê lọt vào 10 game được gợi ý. Chỉ số này luôn phải đọc cùng một chỉ số độ chính xác.
_Avoid_: tỷ lệ gợi ý sai
