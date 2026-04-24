# ============================================================
# MODULE 1: MODELS - Toàn bộ cấu trúc CSDL
# File: app/models/__init__.py
# ============================================================

from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, date
from enum import Enum as PyEnum


# ─────────────────────────────────────────
# ENUM DEFINITIONS
# ─────────────────────────────────────────

class SlotStatus(PyEnum):
    EMPTY       = 'empty'         # Trống
    RENTED      = 'rented'        # Đang thuê
    MAINTENANCE = 'maintenance'   # Bảo trì
    CLEANING    = 'cleaning'      # Cần vệ sinh


class OrderType(PyEnum):
    INBOUND  = 'inbound'   # Nhập hàng
    OUTBOUND = 'outbound'  # Xuất hàng


class OrderStatus(PyEnum):
    PENDING    = 'pending'     # Chờ xử lý
    PROCESSING = 'processing'  # Đang bốc xếp
    DONE       = 'done'        # Hoàn thành
    CANCELLED  = 'cancelled'   # Đã huỷ


class ContractStatus(PyEnum):
    ACTIVE   = 'active'    # Còn hiệu lực
    EXPIRING = 'expiring'  # Sắp hết hạn
    EXPIRED  = 'expired'   # Đã hết hạn


class InvoiceStatus(PyEnum):
    UNPAID  = 'unpaid'   # Còn nợ
    PAID    = 'paid'     # Đã thanh toán
    OVERDUE = 'overdue'  # Quá hạn


class UserRole(PyEnum):
    ADMIN    = 'admin'
    STAFF    = 'staff'
    CUSTOMER = 'customer'


# ─────────────────────────────────────────
# MODEL: User (Người dùng)
# ─────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name    = db.Column(db.String(150))
    phone        = db.Column(db.String(20))
    role         = db.Column(db.String(20), default=UserRole.STAFF.value)
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        import hashlib, os
        salt = os.urandom(16).hex()
        hashed = hashlib.sha256((salt + password).encode()).hexdigest()
        self.password_hash = f"sha256${salt}${hashed}"

    def check_password(self, password):
        try:
            method, salt, hashed = self.password_hash.split('$')
            import hashlib
            return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
        except Exception:
            return False
    def is_admin(self):
        return self.role == UserRole.ADMIN.value

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─────────────────────────────────────────
# MODEL: Customer (Khách hàng / Bên thuê)
# ─────────────────────────────────────────

class Customer(db.Model):
    __tablename__ = 'customers'

    id           = db.Column(db.Integer, primary_key=True)
    code         = db.Column(db.String(20), unique=True)   # KH-001
    name         = db.Column(db.String(150), nullable=False)
    tax_code     = db.Column(db.String(20))                # Mã số thuế
    address      = db.Column(db.String(250))
    contact_name = db.Column(db.String(100))
    phone        = db.Column(db.String(20))
    email        = db.Column(db.String(120))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ
    contracts    = db.relationship('Contract', backref='customer', lazy='dynamic')
    orders       = db.relationship('Order', backref='customer', lazy='dynamic')

    def __repr__(self):
        return f'<Customer {self.name}>'


# ─────────────────────────────────────────
# MODULE 1A: QUẢN LÝ KHÔNG GIAN KHO
# ─────────────────────────────────────────

class Zone(db.Model):
    """Khu vực kho (Zone A - Hàng khô, Zone B - Hàng lạnh, ...)"""
    __tablename__ = 'zones'

    id           = db.Column(db.Integer, primary_key=True)
    code         = db.Column(db.String(10), unique=True, nullable=False)  # 'A', 'B'
    name         = db.Column(db.String(100), nullable=False)               # 'Khu vực A'
    description  = db.Column(db.String(200))                               # 'Hàng khô'
    max_area_m2  = db.Column(db.Float, default=0)                         # Diện tích tối đa
    max_weight_kg = db.Column(db.Float, default=0)                        # Tải trọng tối đa
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ
    slots = db.relationship('Slot', backref='zone', lazy='dynamic',
                            cascade='all, delete-orphan')

    @property
    def total_slots(self):
        return self.slots.count()

    @property
    def empty_slots(self):
        return self.slots.filter_by(status=SlotStatus.EMPTY.value).count()

    @property
    def rented_slots(self):
        return self.slots.filter_by(status=SlotStatus.RENTED.value).count()

    @property
    def occupancy_rate(self):
        total = self.total_slots
        if total == 0:
            return 0
        return round(self.rented_slots / total * 100, 1)

    def __repr__(self):
        return f'<Zone {self.code}: {self.name}>'


class Slot(db.Model):
    """Vị trí lưu trữ (Pallet / Lô hàng) trong từng khu vực"""
    __tablename__ = 'slots'

    id           = db.Column(db.Integer, primary_key=True)
    code         = db.Column(db.String(20), unique=True, nullable=False)  # 'A01', 'B03'
    zone_id      = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    row_number   = db.Column(db.Integer)          # Dãy kệ
    floor_number = db.Column(db.Integer)          # Tầng
    area_m2      = db.Column(db.Float, default=0)
    volume_m3    = db.Column(db.Float, default=0)
    max_weight_kg = db.Column(db.Float, default=0)
    status       = db.Column(db.String(20), default=SlotStatus.EMPTY.value)
    notes        = db.Column(db.Text)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    # Quan hệ
    contract_slots = db.relationship('ContractSlot', backref='slot', lazy='dynamic')

    @property
    def current_contract(self):
        """Trả về hợp đồng đang thuê vị trí này (nếu có)"""
        cs = self.contract_slots.join(Contract).filter(
            Contract.status == ContractStatus.ACTIVE.value
        ).first()
        return cs.contract if cs else None

    @property
    def location_label(self):
        return f'Kệ {self.row_number}, Tầng {self.floor_number}'

    def __repr__(self):
        return f'<Slot {self.code} [{self.status}]>'


# ─────────────────────────────────────────
# MODULE 2: HỢP ĐỒNG & DỊCH VỤ
# ─────────────────────────────────────────

class Contract(db.Model):
    """Hợp đồng thuê kho"""
    __tablename__ = 'contracts'

    id            = db.Column(db.Integer, primary_key=True)
    code          = db.Column(db.String(30), unique=True)  # HD-2026-001
    customer_id   = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    start_date    = db.Column(db.Date, nullable=False)
    end_date      = db.Column(db.Date, nullable=False)
    monthly_rate  = db.Column(db.Float, nullable=False)   # Đơn giá/tháng (VNĐ)
    total_value   = db.Column(db.Float)                   # Tổng giá trị HĐ
    status        = db.Column(db.String(20), default=ContractStatus.ACTIVE.value)
    notes         = db.Column(db.Text)
    created_by    = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Quan hệ
    slots         = db.relationship('ContractSlot', backref='contract',
                                    lazy='dynamic', cascade='all, delete-orphan')
    services      = db.relationship('ContractService', backref='contract',
                                    lazy='dynamic', cascade='all, delete-orphan')
    invoices      = db.relationship('Invoice', backref='contract', lazy='dynamic')

    @property
    def days_until_expiry(self):
        delta = self.end_date - date.today()
        return delta.days

    @property
    def is_expiring_soon(self):
        return 0 <= self.days_until_expiry <= 30

    def update_status(self):
        today = date.today()
        if self.end_date < today:
            self.status = ContractStatus.EXPIRED.value
        elif self.days_until_expiry <= 30:
            self.status = ContractStatus.EXPIRING.value
        else:
            self.status = ContractStatus.ACTIVE.value

    def __repr__(self):
        return f'<Contract {self.code}>'


class ContractSlot(db.Model):
    """Bảng trung gian: Hợp đồng ↔ Vị trí kho"""
    __tablename__ = 'contract_slots'

    id          = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    slot_id     = db.Column(db.Integer, db.ForeignKey('slots.id'), nullable=False)
    goods_type  = db.Column(db.String(100))   # Loại hàng hóa
    quantity    = db.Column(db.Integer)


class Service(db.Model):
    """Danh mục dịch vụ giá trị gia tăng"""
    __tablename__ = 'services'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)  # Bốc xếp, Đóng gói...
    unit        = db.Column(db.String(30))                   # lần, kg, m3
    unit_price  = db.Column(db.Float, default=0)

    def __repr__(self):
        return f'<Service {self.name}>'


class ContractService(db.Model):
    """Dịch vụ đính kèm hợp đồng"""
    __tablename__ = 'contract_services'

    id          = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    service_id  = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    quantity    = db.Column(db.Float, default=1)
    unit_price  = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, default=0)
    service_date = db.Column(db.Date)
    notes       = db.Column(db.String(200))

    service = db.relationship('Service')


# ─────────────────────────────────────────
# MODULE 3: NHẬP / XUẤT HÀNG HÓA
# ─────────────────────────────────────────

class Order(db.Model):
    """Lệnh nhập / xuất hàng hóa"""
    __tablename__ = 'orders'

    id           = db.Column(db.Integer, primary_key=True)
    code         = db.Column(db.String(20), unique=True)   # IO-001
    order_type   = db.Column(db.String(10), nullable=False)  # inbound / outbound
    customer_id  = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    slot_id      = db.Column(db.Integer, db.ForeignKey('slots.id'))
    request_date = db.Column(db.Date, default=date.today)
    scheduled_date = db.Column(db.Date)
    status       = db.Column(db.String(20), default=OrderStatus.PENDING.value)
    driver_name  = db.Column(db.String(100))
    vehicle_plate = db.Column(db.String(20))
    notes        = db.Column(db.Text)
    created_by   = db.Column(db.Integer, db.ForeignKey('users.id'))
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Quan hệ
    items        = db.relationship('OrderItem', backref='order',
                                   lazy='dynamic', cascade='all, delete-orphan')
    slot         = db.relationship('Slot', foreign_keys=[slot_id])

    @property
    def type_label(self):
        return 'NHẬP' if self.order_type == OrderType.INBOUND.value else 'XUẤT'

    def __repr__(self):
        return f'<Order {self.code} [{self.order_type}]>'


class OrderItem(db.Model):
    """Chi tiết hàng hóa trong lệnh nhập/xuất"""
    __tablename__ = 'order_items'

    id          = db.Column(db.Integer, primary_key=True)
    order_id    = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    barcode     = db.Column(db.String(100))     # Mã vạch / QR
    goods_name  = db.Column(db.String(150))
    quantity    = db.Column(db.Integer, default=0)
    unit        = db.Column(db.String(20))       # thùng, pallet, kg
    weight_kg   = db.Column(db.Float, default=0)
    volume_m3   = db.Column(db.Float, default=0)
    notes       = db.Column(db.String(200))

    def __repr__(self):
        return f'<OrderItem {self.goods_name} x{self.quantity}>'


# ─────────────────────────────────────────
# MODULE 4: TÀI CHÍNH & THANH TOÁN
# ─────────────────────────────────────────

class Invoice(db.Model):
    """Hóa đơn thanh toán"""
    __tablename__ = 'invoices'

    id           = db.Column(db.Integer, primary_key=True)
    code         = db.Column(db.String(20), unique=True)  # INV-0001
    contract_id  = db.Column(db.Integer, db.ForeignKey('contracts.id'), nullable=False)
    period_start = db.Column(db.Date, nullable=False)     # Kỳ từ ngày
    period_end   = db.Column(db.Date, nullable=False)     # Kỳ đến ngày
    base_amount  = db.Column(db.Float, default=0)         # Tiền thuê kho
    service_amount = db.Column(db.Float, default=0)       # Tiền dịch vụ
    total_amount = db.Column(db.Float, default=0)         # Tổng tiền
    due_date     = db.Column(db.Date)                     # Hạn thanh toán
    paid_date    = db.Column(db.Date)
    status       = db.Column(db.String(20), default=InvoiceStatus.UNPAID.value)
    notes        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    payments     = db.relationship('Payment', backref='invoice', lazy='dynamic')

    def check_overdue(self):
        if self.status != InvoiceStatus.PAID.value:
            if self.due_date and self.due_date < date.today():
                self.status = InvoiceStatus.OVERDUE.value

    def __repr__(self):
        return f'<Invoice {self.code}: {self.total_amount:,.0f}đ>'


class Payment(db.Model):
    """Ghi nhận thanh toán"""
    __tablename__ = 'payments'

    id          = db.Column(db.Integer, primary_key=True)
    invoice_id  = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    amount      = db.Column(db.Float, nullable=False)
    method      = db.Column(db.String(50))          # Chuyển khoản, Tiền mặt
    reference   = db.Column(db.String(100))         # Số bút toán / mã giao dịch
    paid_at     = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<Payment {self.amount:,.0f}đ for Invoice {self.invoice_id}>'
