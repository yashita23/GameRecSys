# Bỏ khỏi dữ liệu học mọi review viết sau ngày của game cần đoán

Ở thiết lập A, review thích cuối cùng của mỗi người dùng được giấu đi để mô hình đoán. Người dùng đó có thể còn review chê viết sau ngày này. Nếu giữ các review đó trong dữ liệu học, mô hình (nhất là M1 và hybrid, vốn học từ review chê) sẽ được biết trước chuyện xảy ra sau thời điểm cần đoán, và kết quả sẽ đẹp hơn thực tế. Vì vậy, với mỗi người dùng, lấy ngày của review cần đoán làm mốc và bỏ khỏi dữ liệu học mọi review viết sau mốc đó. Đổi lại, nhóm mất một ít review chê và chấp nhận điều này để kết quả đo trung thực.
