"""
seed.py — Khởi tạo dữ liệu mẫu cho WareFlow
Chạy: python seed.py
"""

from app import create_app, db
from app.models import (User, UserRole, Customer, Zone, Slot, SlotStatus,
                        Contract, ContractStatus, ContractSlot,
                        Service, Order, OrderType, OrderStatus,
                        OrderItem, Invoice, InvoiceStatus)
from datetime import date, timedelta, datetime


def seed():
    app = create_app('development')
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✓ Tạo bảng CSDL xong")

        # ── Tài khoản người dùng ──────────────────────────────
        admin = User(username='admin', email='admin@wareflow.vn',
                     full_name='Nguyễn Văn Admin', phone='0901234567',
                     role=UserRole.ADMIN.value)
        admin.set_password('admin123')

        staff = User(username='nhanvien', email='staff@wareflow.vn',
                     full_name='Trần Thị Nhân Viên', phone='0912345678',
                     role=UserRole.STAFF.value)
        staff.set_password('staff123')

        db.session.add_all([admin, staff])
        db.session.flush()
        print("✓ Tạo tài khoản xong")

        # ── Khách hàng ────────────────────────────────────────
        customers = [
            Customer(code='KH-001', name='Công ty TNHH ABC',
                     tax_code='0101234567', contact_name='Lê Văn A',
                     phone='0938111222', email='contact@abc.vn',
                     address='123 Nguyễn Văn Linh, Q.7, TP.HCM'),
            Customer(code='KH-002', name='Cửa hàng XYZ',
                     tax_code='0109876543', contact_name='Phạm Thị B',
                     phone='0909333444', email='xyz@gmail.com',
                     address='456 Lê Đại Hành, Q.11, TP.HCM'),
            Customer(code='KH-003', name='Công ty Minh Nhật',
                     tax_code='0102468135', contact_name='Nguyễn Văn C',
                     phone='0977555666', email='minhnhat@vn',
                     address='789 Cộng Hòa, Q.Tân Bình, TP.HCM'),
            Customer(code='KH-004', name='Công ty Thiên Phú',
                     tax_code='0108765432', contact_name='Hoàng Thị D',
                     phone='0933777888', email='thienphu@vn',
                     address='101 Đinh Tiên Hoàng, Q.Bình Thạnh, TP.HCM'),
        ]
        db.session.add_all(customers)
        db.session.flush()
        print("✓ Tạo khách hàng xong")

        # ── Khu vực kho ──────────────────────────────────────
        zone_a = Zone(code='A', name='Khu vực A', description='Hàng khô',
                      max_area_m2=500, max_weight_kg=50000)
        zone_b = Zone(code='B', name='Khu vực B', description='Hàng lạnh',
                      max_area_m2=300, max_weight_kg=30000)
        db.session.add_all([zone_a, zone_b])
        db.session.flush()
        print("✓ Tạo khu vực xong")

        # ── Vị trí lưu trữ ──────────────────────────────────
        slots_data = [
            # Zone A
            ('A01', zone_a.id, 1, 2, 15, 10, 5000, SlotStatus.RENTED.value),
            ('A02', zone_a.id, 1, 2, 15, 10, 5000, SlotStatus.RENTED.value),
            ('A03', zone_a.id, 1, 3, 15, 12, 5000, SlotStatus.EMPTY.value),
            ('A04', zone_a.id, 2, 1, 15, 10, 5000, SlotStatus.MAINTENANCE.value),
            ('A05', zone_a.id, 2, 2, 15, 15, 5000, SlotStatus.RENTED.value),
            ('A06', zone_a.id, 2, 3, 15, 10, 5000, SlotStatus.EMPTY.value),
            ('A07', zone_a.id, 3, 1, 15, 10, 5000, SlotStatus.EMPTY.value),
            ('A08', zone_a.id, 3, 2, 15, 12, 5000, SlotStatus.EMPTY.value),
            # Zone B
            ('B01', zone_b.id, 1, 1, 20, 20, 8000, SlotStatus.RENTED.value),
            ('B02', zone_b.id, 1, 2, 20, 20, 8000, SlotStatus.CLEANING.value),
            ('B03', zone_b.id, 2, 1, 20, 18, 8000, SlotStatus.EMPTY.value),
            ('B04', zone_b.id, 2, 2, 20, 16, 8000, SlotStatus.RENTED.value),
        ]
        slot_objs = {}
        for (code, zone_id, row, floor, area, vol, wt, status) in slots_data:
            s = Slot(code=code, zone_id=zone_id, row_number=row,
                     floor_number=floor, area_m2=area, volume_m3=vol,
                     max_weight_kg=wt, status=status)
            db.session.add(s)
            slot_objs[code] = s
        db.session.flush()
        print("✓ Tạo vị trí kho xong")

        # ── Dịch vụ giá trị gia tăng ─────────────────────────
        services = [
            Service(name='Bốc xếp hàng hóa', unit='lần', unit_price=500000),
            Service(name='Đóng gói bảo quản', unit='thùng', unit_price=15000),
            Service(name='Bảo hiểm hàng hóa', unit='lô', unit_price=200000),
            Service(name='Phun khử trùng', unit='lần', unit_price=1000000),
            Service(name='Kiểm đếm hàng', unit='lần', unit_price=300000),
        ]
        db.session.add_all(services)
        print("✓ Tạo dịch vụ xong")

        # ── Hợp đồng ─────────────────────────────────────────
        today = date.today()

        c1 = Contract(code='HD-2026-011', customer_id=customers[0].id,
                      start_date=date(2026, 1, 1), end_date=date(2026, 6, 30),
                      monthly_rate=18000000, total_value=108000000,
                      status=ContractStatus.ACTIVE.value, created_by=admin.id)

        c2 = Contract(code='HD-2026-008', customer_id=customers[2].id,
                      start_date=date(2025, 10, 1), end_date=today + timedelta(days=15),
                      monthly_rate=12500000, total_value=87500000,
                      status=ContractStatus.EXPIRING.value, created_by=admin.id)

        c3 = Contract(code='HD-2026-015', customer_id=customers[3].id,
                      start_date=date(2026, 3, 15), end_date=date(2026, 9, 14),
                      monthly_rate=22000000, total_value=132000000,
                      status=ContractStatus.ACTIVE.value, created_by=admin.id)

        c4 = Contract(code='HD-2026-003', customer_id=customers[1].id,
                      start_date=date(2026, 2, 1), end_date=date(2026, 7, 31),
                      monthly_rate=8500000, total_value=51000000,
                      status=ContractStatus.ACTIVE.value, created_by=admin.id)

        db.session.add_all([c1, c2, c3, c4])
        db.session.flush()

        # Gắn vị trí vào hợp đồng
        cs_data = [
            (c1.id, 'A01', 'Đồ điện tử'),
            (c1.id, 'A02', 'Đồ điện tử'),
            (c2.id, 'A05', 'Hàng thực phẩm'),
            (c3.id, 'B01', 'Thực phẩm đông lạnh'),
            (c4.id, 'B04', 'Hải sản'),
        ]
        for (cid, slot_code, goods) in cs_data:
            cs = ContractSlot(contract_id=cid,
                              slot_id=slot_objs[slot_code].id,
                              goods_type=goods)
            db.session.add(cs)
        print("✓ Tạo hợp đồng xong")

        # ── Lệnh nhập/xuất ───────────────────────────────────
        orders_data = [
            ('IO-001', OrderType.INBOUND.value,  customers[0].id, 'A01',
             OrderStatus.PENDING.value, 'Nguyễn Tài Xế', '51A-11111'),
            ('IO-002', OrderType.OUTBOUND.value, customers[1].id, 'B04',
             OrderStatus.DONE.value,    'Trần Tài Xế', '51B-22222'),
            ('IO-003', OrderType.INBOUND.value,  customers[3].id, 'B01',
             OrderStatus.PROCESSING.value, 'Lê Giao Nhận', '51C-33333'),
            ('IO-004', OrderType.OUTBOUND.value, customers[2].id, 'A05',
             OrderStatus.DONE.value,    'Phạm Tài Xế', '51D-44444'),
            ('IO-005', OrderType.INBOUND.value,  customers[0].id, 'A02',
             OrderStatus.PENDING.value, None, None),
        ]
        order_objs = []
        for i, (code, otype, cid, slot_code, status, driver, plate) in enumerate(orders_data):
            o = Order(code=code, order_type=otype, customer_id=cid,
                      slot_id=slot_objs[slot_code].id,
                      request_date=today - timedelta(days=i),
                      status=status, driver_name=driver, vehicle_plate=plate,
                      created_by=staff.id,
                      completed_at=datetime.utcnow() - timedelta(hours=i)
                      if status == OrderStatus.DONE.value else None)
            db.session.add(o)
            order_objs.append(o)
        db.session.flush()

        # Chi tiết hàng hóa cho lệnh đầu tiên
        items = [
            OrderItem(order_id=order_objs[0].id, barcode='8935024100001',
                      goods_name='Điện thoại Samsung', quantity=20,
                      unit='hộp', weight_kg=40, volume_m3=0.2),
            OrderItem(order_id=order_objs[0].id, barcode='8935024100002',
                      goods_name='Máy tính bảng iPad', quantity=10,
                      unit='hộp', weight_kg=25, volume_m3=0.15),
        ]
        db.session.add_all(items)
        print("✓ Tạo lệnh nhập/xuất xong")

        # ── Hóa đơn ──────────────────────────────────────────
        first_month = date(today.year, today.month, 1)

        invoices = [
            Invoice(code='INV-0041', contract_id=c1.id,
                    period_start=first_month,
                    period_end=date(today.year, today.month, 30),
                    base_amount=18000000, service_amount=0,
                    total_amount=18000000,
                    due_date=first_month + timedelta(days=15),
                    paid_date=today - timedelta(days=3),
                    status=InvoiceStatus.PAID.value),

            Invoice(code='INV-0040', contract_id=c2.id,
                    period_start=first_month,
                    period_end=date(today.year, today.month, 30),
                    base_amount=12500000, service_amount=0,
                    total_amount=12500000,
                    due_date=today - timedelta(days=5),
                    status=InvoiceStatus.OVERDUE.value),

            Invoice(code='INV-0039', contract_id=c3.id,
                    period_start=first_month,
                    period_end=date(today.year, today.month, 30),
                    base_amount=22000000, service_amount=500000,
                    total_amount=22500000,
                    due_date=first_month + timedelta(days=20),
                    status=InvoiceStatus.UNPAID.value),

            Invoice(code='INV-0038', contract_id=c4.id,
                    period_start=first_month,
                    period_end=date(today.year, today.month, 30),
                    base_amount=8500000, service_amount=0,
                    total_amount=8500000,
                    due_date=today - timedelta(days=10),
                    status=InvoiceStatus.OVERDUE.value),
        ]
        db.session.add_all(invoices)
        db.session.commit()
        print("✓ Tạo hóa đơn xong")

        print("\n" + "="*50)
        print("  SEED HOÀN TẤT!")
        print("="*50)
        print(f"  URL:      http://127.0.0.1:5000")
        print(f"  Admin:    admin / admin123")
        print(f"  Nhân viên: nhanvien / staff123")
        print("="*50)


if __name__ == '__main__':
    seed()
