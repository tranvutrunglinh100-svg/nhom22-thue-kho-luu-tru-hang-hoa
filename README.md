# WareFlow — Phần mềm Quản lý Kho Hàng

Hệ thống quản lý dịch vụ cho thuê kho lưu trữ hàng hóa.  
Xây dựng bằng **Python (Flask)** + **SQLite** + **HTML/CSS/JS**.

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

| Vai trò    | Tên đăng nhập | Mật khẩu  |
|------------|---------------|-----------|
| Admin      | `admin`       | `admin123`|
| Nhân viên  | `nhanvien`    | `staff123`|

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
