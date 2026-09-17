# TÀI LIỆU YÊU CẦU DỰ ÁN: NỀN TẢNG ĐẶT ĐỒ ĂN TRỰC TUYẾN (FOODIE APP)

**Khách hàng:** Chuỗi nhà hàng & Dịch vụ F&B Foodie Việt Nam
**Ngày cập nhật:** 17/09/2026
**Mục tiêu:** Xây dựng hệ thống đặt đồ ăn và giao hàng phục vụ khách hàng trên toàn quốc.

---

## 1. Yêu cầu Quản lý Người dùng & Xác thực
- **Bắt buộc:** Người dùng phải đăng ký và đăng nhập được qua số điện thoại kèm xác thực mã OTP SMS hoặc qua tài khoản Google.
- **Bắt buộc:** Quản trị viên (Admin) phải có hệ thống phân quyền chi tiết (SuperAdmin, Quản lý chi nhánh, Thu ngân, Shipper).
- **Tùy chọn:** Hỗ trợ đăng nhập sinh trắc học (FaceID / Fingerprint) khi dùng trên trình duyệt web di động nếu thiết bị có hỗ trợ.

## 2. Quản lý Danh mục, Thực đơn & Tìm kiếm
- **Bắt buộc:** Khách hàng có thể tìm kiếm món ăn theo tên món, danh mục ẩm thực, khoảng cách địa lý và mức giá.
- **Bắt buộc:** Hiển thị trạng thái mở/đóng cửa của từng chi nhánh theo thời gian thực để ngăn khách đặt món khi quán đã nghỉ.
- **Rất quan trọng:** Cho phép tùy chỉnh món ăn khi chọn (chọn size, mức đường, đá, thêm topping).
- **Tùy chọn:** Tích hợp AI thông minh để gợi ý món ăn theo thời tiết thực tế tại vị trí của khách hoặc theo tâm trạng người dùng.

## 3. Giỏ hàng, Đặt món & Thanh toán
- **Bắt buộc:** Tính toán chính xác 100% tổng giá trị đơn hàng, bao gồm tiền món, khuyến mãi, phí giao hàng theo khoảng cách GPS và thuế VAT.
- **Bắt buộc:** Tích hợp cổng thanh toán trực tuyến bảo mật: Thẻ tín dụng/ghi nợ quốc tế (Visa/Mastercard), VNPay, MoMo và hình thức trả tiền mặt khi nhận hàng (COD).
- **Rất quan trọng:** Cơ chế khóa giữ chỗ món ăn trong giỏ hàng trong 10 phút để tránh tình trạng hết hàng đột ngột khi khách đang thanh toán.
- **Tùy chọn:** Tạo ví điện tử nội bộ cho phép khách hàng nạp tiền trước và chuyển điểm thưởng cho bạn bè trong ứng dụng.

## 4. Theo dõi Đơn hàng & Vận chuyển
- **Bắt buộc:** Cập nhật trạng thái tiến trình đơn hàng theo thời gian thực (Đã nhận đơn -> Đang nấu -> Đang giao -> Hoàn tất -> Đã hủy).
- **Rất quan trọng:** Hệ thống tự động điều phối đơn hàng đến shipper gần nhất đang rảnh trong bán kính 3km.
- **Tùy chọn:** Bản đồ theo dõi lộ trình shipper dạng 3D thời gian thực với mô hình xe chạy sinh động trên màn hình.

## 5. Đánh giá, Chăm sóc Khách hàng & Marketing
- **Quan trọng vừa phải:** Cho phép khách hàng đánh giá 1-5 sao kèm hình ảnh và viết nhận xét sau khi đơn hàng được giao thành công.
- **Quan trọng vừa phải:** Quản lý mã voucher giảm giá, mã miễn phí vận chuyển theo khung giờ vàng (Flash sale).
- **Tùy chọn:** Tự động gửi thiệp chúc mừng sinh nhật kèm voucher giảm giá 50% cho khách hàng VIP vào đúng ngày sinh nhật.

## 6. Yêu cầu Phi chức năng & Bảo mật
- **Bắt buộc:** Toàn bộ dữ liệu thanh toán, mật khẩu và thông tin cá nhân của khách hàng phải được mã hóa theo tiêu chuẩn an toàn dữ liệu (PCI-DSS & HTTPS/TLS).
- **Rất quan trọng:** Hệ thống phải chịu tải tối thiểu 5.000 đơn hàng đồng thời trong các khung giờ cao điểm (11h30-13h00 và 18h30-20h00) với độ trễ phản hồi API < 1.0 giây.
- **Tùy chọn:** Hỗ trợ giao diện tự động chuyển đổi sang chế độ Dark Mode theo giờ mặt trời lặn tại địa phương của người dùng.
