# <img width="150" height="52" alt="image" src="https://github.com/user-attachments/assets/5a700bfc-1d01-41c5-a837-d7888722ddc7" />

## Giới Thiệu
--
WareFlow — Phần mềm Quản lý thuê Kho lưu trữ Hàng hóa
Hệ thống quản lý thuê kho lưu trữ hàng hóa (Warehouse Management System - WMS) là một giải pháp công nghệ giúp các doanh nghiệp hoặc cá nhân quản lý mọi hoạt động liên quan đến việc ký gửi, lưu giữ và luân chuyển hàng hóa trong kho một cách tự động và khoa học.

Thay vì quản lý bằng sổ sách hay Excel dễ nhầm lẫn, hệ thống này số hóa toàn bộ quy trình từ lúc hàng vào kho cho đến khi xuất đi.

1. Các thành phần cốt lõi của hệ thống
Một hệ thống thuê kho hiện đại thường bao gồm 3 lớp quản lý chính:

Quản lý sơ đồ kho (Layout Management): Hệ thống chia kho thành các Zones (Khu vực) và Slots (Vị trí/Ô kệ). Mỗi mặt hàng khi nhập vào sẽ được chỉ định vào một vị trí chính xác trên bản đồ số, giúp việc tìm kiếm hàng hóa diễn ra trong vài giây.

Quản lý hàng hóa (Inventory): Theo dõi chi tiết mã sản phẩm (SKU), ngày nhập, hạn sử dụng, đặc tính hàng hóa (hàng dễ vỡ, hàng cần bảo quản lạnh...) và số lượng tồn kho theo thời gian thực.

Quản lý hợp đồng & Thanh toán (Billing & Contract): Tính toán chi phí thuê dựa trên diện tích sử dụng hoặc số lượng pallet. Hệ thống tự động gia hạn hợp đồng, tính phí lưu kho hàng tháng và xuất hóa đơn cho khách hàng.

2. Quy trình vận hành cơ bản
Tiếp nhận yêu cầu: Khách hàng đăng ký thuê kho và ký hợp đồng điện tử.

Nhập kho (Inbound): Hàng hóa được kiểm tra, dán nhãn (Barcode/QR Code) và hệ thống gợi ý vị trí Slot trống phù hợp.

Lưu trữ & Kiểm soát: Hệ thống theo dõi biến động hàng hóa. Nếu hàng sắp hết hạn hoặc tồn kho quá lâu, hệ thống sẽ gửi cảnh báo.

Xuất kho (Outbound): Khi có lệnh xuất, hệ thống chỉ định chính xác vị trí hàng đang nằm ở đâu để nhân viên lấy hàng nhanh nhất, tránh sai sót.

3. Lợi ích khi sử dụng hệ thống số hóa
Tối ưu diện tích: Hệ thống tính toán để sắp xếp hàng hóa khít nhất, tránh lãng phí những khoảng trống trong kho.

Chính xác tuyệt đối: Giảm thiểu 99% tình trạng thất thoát hoặc nhầm lẫn hàng hóa giữa các khách hàng khác nhau.

Minh bạch tài chính: Khách hàng thuê kho có thể tự theo dõi tình trạng hàng và chi phí thuê của mình qua giao diện web/app mà không cần gọi điện hỏi chủ kho.

Báo cáo thông minh: Tự động xuất biểu đồ doanh thu, hiệu suất khai thác kho theo từng tháng.
Hệ thống quản lý dịch vụ cho thuê kho lưu trữ hàng hóa.  
Xây dựng bằng **Python (Flask)** + **SQLite** + **HTML/CSS/JS**.

---
## 👨‍💻 Thành viên nhóm
Trần Vũ Trung Linh – Trưởng nhóm (Leader)
Nguyễn Xuân Trường – Thành viên


## 🛠️ Công nghệ sử dụng
Ngôn ngữ lập trình: Python, js (backend)
Giao diện: html , css (frontend)
Cơ sở dữ liệu: (SQLite viewer / phpmyadmin )
Công cụ: Git, GitHub
---

## Cấu trúc dự án

```
warehouse_app/
├── app/
│   ├── __init__.py          # App factory
│   ├── models/
│   │   └── __init__.py      # Tất cả models (User, Zone, Slot, Contract...)
│   ├── routes/
│   │   ├── auth.py          # Đăng nhập / Quản lý người dùng
│   │   ├── dashboard.py     # Tổng quan
│   │   ├── warehouse.py     # Sơ đồ kho (Zone & Slot)
│   │   ├── logistics.py     # Nhập / Xuất hàng hóa
│   │   ├── contracts.py     # Hợp đồng & Khách hàng
│   │   ├── billing.py       # Tài chính & Hóa đơn
│   │   └── reports.py       # Báo cáo & Thống kê
│   ├── templates/           # Giao diện HTML (Jinja2)
│   └── static/
│       ├── css/main.css     # Stylesheet chính
│       └── js/main.js       # JavaScript chính
├── .vscode/
│   ├── launch.json          # Cấu hình chạy & debug VS Code
│   └── settings.json        # Cấu hình Python
├── config.py                # Cấu hình app
├── run.py                   # Điểm khởi chạy
├── seed.py                  # Dữ liệu mẫu
└── requirements.txt         # Thư viện Python
```

---

## Hướng dẫn cài đặt & chạy

### Bước 1: Mở project trong VS Code
```bash
code warehouse_app
```

### Bước 2: Tạo môi trường ảo
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### Bước 4: Khởi tạo CSDL & dữ liệu mẫu
```bash
python seed.py
```

### Bước 5: Chạy ứng dụng
```bash
# Cách 1: Trực tiếp
python run.py

# Cách 2: Flask CLI
set FLASK_APP=run.py      # Windows
export FLASK_APP=run.py   # macOS/Linux
flask run --debug

# Cách 3: VS Code → F5 (chọn "WareFlow — Flask Run")
```

Mở trình duyệt: **http://127.0.0.1:5000**

---

## Tài khoản mặc định

| Vai trò    | Tên đăng nhập | Mật khẩu  | Phần quyền |
|------------|---------------|-----------|
| Admin      | `admin`       | `admin123`| xem được tất cả. |
| Nhân viên 1 | `nhanvien`    | `nhanvien123`| NV1Khách hàng, Hợp đồng, Tài chính (thanh toán), Xuất hàng. |
| Nhân viên 2 | `nhanvien`    | `nhanvien123`| NV2Sơ đồ kho, Khu vực, Slot (thêm/sửa/xóa). |
| Nhân viên 3 | `nhanvien`    | `nhanvien123`| NV3Báo cáo doanh thu. |
---

## Các tính năng chính

| Module | Tính năng |
|--------|-----------|
| **Sơ đồ kho** | Xem trực quan, click vào ô kho xem chi tiết, lọc theo khu vực |
| **Nhập/Xuất** | Tạo lệnh, duyệt → Bốc xếp → Hoàn thành, quét mã vạch, in biên bản |
| **Hợp đồng** | Tạo/Sửa HĐ, cảnh báo hết hạn, quản lý khách hàng |
| **Tài chính** | Tạo HĐ tự động, ghi nhận thanh toán, xuất Excel |
| **Báo cáo** | Biểu đồ doanh thu, tỷ lệ lấp đầy, audit log |


---

## Phát triển thêm

### Nâng cấp database lên PostgreSQL
```python
# config.py
SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/wareflow'
```

### Tạo migration khi thay đổi model
```bash
flask db init       # Lần đầu
flask db migrate -m "Mô tả thay đổi"
flask db upgrade
```

### Cấu hình biến môi trường
Tạo file `.env` trong thư mục gốc:
```
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///warehouse.db
FLASK_ENV=development
```
## 🧪 Trạng thái dự án

🚧 Đang phát triển.

## 📜 Quy tắc làm việc nhóm

* Không code trực tiếp trên `main`
* Mỗi chức năng phải tạo một nhánh riêng
* Tạo Pull Request trước khi merge
* Commit rõ ràng, có ý nghĩa


## 📞 Liên hệ

* Trưởng nhóm: Trần Vũ Trung Linh.
* Email: tranvutrunglinh100@gmail.com.
* sdt: (+ 84) 347035879.
