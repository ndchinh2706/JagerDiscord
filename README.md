# Jagermeister Bot
Team Jager's Discord bot for GDGOC Tech Probation 2024.

# Danh sách thành viên
1. Đoàn Minh Yến (Mentor)
2. Nguyễn Đình Chính
3. Liêu Chí Vỹ
4. Trần Thị Thu Trang
5. Nguyễn Ngọc Phương
6. Nguyễn Duy Hiếu
   
# Jagermeister - GDGOC Probation 2024 - Jager Team
## Ý tưởng:
Jagermeister bot được phát triển nhằm hỗ trợ công tác quy trình tổ chức sự kiện và triển khai các hoạt động nhóm, giúp thành viên dễ dàng đăng ký tham gia, check-in, cập nhật tiến độ hoàn thành, thanh toán và tự động xác nhận khoản thu tự động, tránh thất thoát :)).

## Tính năng:
- [x] Thông báo sự kiện:
  - [x] Thông báo, yêu cầu đăng kí sự kiện theo role.
  - [x] Web-gui danh sách member tham gia sự kiện, xuất csv,....
- [x] Order đồ:
  - [x] Cho phép tạo order, tự động xác nhận thanh toán chuyển khoản qua QR Code.
- [x] GReminder:
  - [x] Bot sẽ thông báo đến từng người được mention theo role đã được setup trong "Thông báo sự kiện".
  - [x] Thông báo lại cho người tham gia 1h trước sự kiện
#
# Hướng dẫn sử dụng
## Tính năng đăng ký:
### A. Đăng ký người dùng mới:
Sử dụng lệnh `/signup`, bot sẽ tự động tạo direct message để bắt đầu quá trình đăng ký.
   - Nhập họ và tên
   - Nhập mã sinh viên
### B. Chỉnh sửa thông tin cá nhân:
Sử dụng lệnh `/signup`, bot sẽ tạo interaction và hỏi lại người dùng có muốn chỉnh sửa thông tin cá nhân. Nếu có, click vào nút chỉnh sửa, sau đó, truy cập DM của bot để tiến hành quá trình chỉnh sửa thông tin cá nhân. Quá trình này tương tự với quá trình đăng ký.
## Tính năng sự kiện:
####  1. Tạo sự kiện mới:
Sử dụng lệnh `/create_event` với các tham số:
   - event_name: Tên sự kiện.
   - event_datetime: Ngày diễn ra sự kiện (HH:MM DD/MM/YYYY).
   - event_deadline: Hạn chót tham gia đăng ký (HH:MM DD/MM/YYYY).
   - role1: Role được phép đăng ký tham gia.
   - role2: (optional): Role được phép đăng ký (nếu có).
   - role3: (optional): Role được phép đăng ký (nếu có).
#### 2. Đăng ký tham gia sự kiện:
Sau khi sự kiện được tạo, một bảng discordEmbed sẽ được tạo với đầy đủ nội dung, đồng thời xuất hiện 2 nút emoji reactions.
   - Reaction ✅: Đồng nghĩa với việc đăng ký tham gia sự kiện.
   - Reaction ❌: Đồng nghĩa với việc đăng ký vắng mặt sự kiện.
#### 3. Danh sách trạng thái thành viên đăng ký tham gia sự kiện:
Với mỗi sự kiện được tạo, sẽ có 1 đường link `/event/event_id`. Thông tin trong đường link sẽ bao gồm danh sách các thành viên đã đăng ký tham gia và vắng mặt, xuất danh sách dưới dạng CSV.
## Tính năng order:
### 1. Mở ticket order:
Sử dụng lệnh `/order`. Một interaction sẽ được tạo và hỏi người sử dụng lệnh có muốn mở ticket order. Sau khi đã confirm mở ticket, một side-chat channel sẽ được tạo. Channel này chỉ dành cho người order, và thành viên xử lý order với role "Order."
Trong side-chat channel, người order và người xử lý order sẽ trao đổi về nội dung order, người order thanh toán bằng cách quét mã QR được sẽ sẵn nội dung trong kênh. Hoàn thành order, admin sẽ nhấn "Đóng order" và gửi real-time, nhằm đảm bảo vững chắc cho các khoản thu, chi của channel.
### 2. Đóng order:
Click vào nút Đóng ticket dưới mỗi interaction order. Order bên dưới sẽ được đóng, xác nhận đồng order. Order và side-chat sẽ bị đóng. Hoàn thành order.
#
## Installation:
### Requirements:
- Python 3.11.9.
- (to be updated)
### Initial setup:
    $ pip install -r requirements.txt
### Usage:
    $ python main.py
