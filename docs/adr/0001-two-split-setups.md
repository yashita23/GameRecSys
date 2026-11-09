# Chia dữ liệu theo hai thiết lập riêng: A cho M1, M2, hybrid; B cho M3

Muốn đo được việc gợi ý game chưa có review (M3) thì phải giấu toàn bộ review của một nhóm game. Nếu M1, M2 và hybrid dùng chung cách chia đó, các module này sẽ mất dữ liệu học, và hybrid sẽ bị trừ điểm oan mỗi khi game cần đoán là game bị giấu. Vì vậy dữ liệu chia theo hai cách, cùng xuất phát từ một dữ liệu đã lọc và cùng dùng chung hàm đo. **Thiết lập A** giữ mọi game trong dữ liệu học và giấu review thích cuối cùng của mỗi người dùng. **Thiết lập B** giấu khoảng 10% game: 5% để chọn λ, 5% để đo kết quả cuối. Kết quả của hai thiết lập không cộng hay so trực tiếp với nhau. Khả năng gợi ý game bị giấu chỉ báo cáo ở thiết lập B, không tính vào điểm của hybrid.

## Considered Options

- **Một cách chia chung có game bị giấu**: bị loại vì M1 và M2 mất dữ liệu học, và hybrid bị phạt oan.
- **Bỏ phần đo M3, chỉ trình diễn**: bị loại vì như vậy không trả lời được câu hỏi "gợi ý game chưa có review được đến đâu".
