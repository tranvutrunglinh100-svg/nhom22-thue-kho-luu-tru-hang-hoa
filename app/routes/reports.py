# ============================================================
# MODULE 8: BÁO CÁO & THỐNG KÊ (Reports & Dashboards)
# File: app/routes/reports.py
# ============================================================

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date, timedelta
import io
from app import db
from app.models import (Zone, Slot, SlotStatus, Contract, ContractStatus,
                        ContractSlot, Customer, Invoice, InvoiceStatus,
                        Order, OrderType, OrderStatus)

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


# ─── Helper tính doanh thu hợp lệ (lọc dữ liệu bẩn > 10 tỷ/HĐ) ─────────────
MAX_VALID_INVOICE = 10_000_000_000   # 10 tỷ — ngưỡng lọc dữ liệu test bẩn

def _revenue_query(first_day, last_day):
    """Tổng doanh thu hóa đơn đã thanh toán trong kỳ, bỏ qua dữ liệu bẩn."""
    return db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.status     == InvoiceStatus.PAID.value,
        Invoice.paid_date.between(first_day, last_day),
        Invoice.total_amount <= MAX_VALID_INVOICE,        # ← lọc dữ liệu test
    ).scalar() or 0


def _occupancy_on_date(zone, target_date):
    """
    Tỷ lệ lấp đầy của zone vào một ngày cụ thể.
    Đếm số ContractSlot có Contract bao phủ ngày đó (start_date <= target <= end_date).
    """
    total = zone.total_slots
    if total == 0:
        return 0.0

    rented = db.session.query(func.count(ContractSlot.id)).join(Contract).filter(
        ContractSlot.slot_id.in_(
            db.session.query(Slot.id).filter(Slot.zone_id == zone.id)
        ),
        Contract.start_date <= target_date,
        Contract.end_date   >= target_date,
        Contract.status.in_([ContractStatus.ACTIVE.value,
                              ContractStatus.EXPIRING.value,
                              ContractStatus.EXPIRED.value]),  # kể cả đã hết hạn (lịch sử)
    ).scalar() or 0

    return round(min(rented, total) / total * 100, 1)


# ─── Trang báo cáo chính ─────────────────────────────────

@reports_bp.route('/')
@login_required
def index():
    if not current_user.can_access_reports():
        flash('Bạn không có quyền xem báo cáo.', 'danger')
        return redirect(url_for('dashboard.index'))

    today     = date.today()
    year      = request.args.get('year',  today.year,  type=int)
    month     = request.args.get('month', today.month, type=int)
    first_day = date(year, month, 1)
    last_day  = (date(year, month + 1, 1) - timedelta(days=1)
                 if month < 12 else date(year + 1, 1, 1) - timedelta(days=1))

    zones = Zone.query.all()

    # ─ Tỷ lệ lấp đầy hiện tại theo khu vực ─
    occupancy_data = [{
        'zone':   z.name,
        'code':   z.code,
        'total':  z.total_slots,
        'rented': z.rented_slots,
        'empty':  z.empty_slots,
        'rate':   z.occupancy_rate,
    } for z in zones]

    # ─ Doanh thu 12 tháng gần nhất (triệu đồng) ─
    monthly_revenue = []
    for i in range(11, -1, -1):
        d  = today
        m  = (d.month - i - 1) % 12 + 1
        y  = d.year - ((d.month - i - 1) // 12)
        fd = date(y, m, 1)
        ld = (date(y, m + 1, 1) - timedelta(days=1)
              if m < 12 else date(y + 1, 1, 1) - timedelta(days=1))
        rev = _revenue_query(fd, ld)
        monthly_revenue.append({
            'month':   f'T{m}/{y}',
            'revenue': round(rev / 1_000_000, 1),
        })

    # ─ Doanh thu theo khách hàng trong tháng ─
    revenue_by_customer = db.session.query(
        Customer.name,
        func.sum(Invoice.total_amount).label('total')
    ).join(Contract, Contract.customer_id == Customer.id
    ).join(Invoice, Invoice.contract_id == Contract.id
    ).filter(
        Invoice.status == InvoiceStatus.PAID.value,
        Invoice.paid_date.between(first_day, last_day),
        Invoice.total_amount <= MAX_VALID_INVOICE,
    ).group_by(Customer.id
    ).order_by(db.text('total DESC')
    ).limit(10).all()

    # ─ Tổng hợp tháng ─
    total_revenue = _revenue_query(first_day, last_day)

    summary = {
        'total_revenue': total_revenue,
        'total_inbound': Order.query.filter(
            Order.order_type == OrderType.INBOUND.value,
            Order.status     == OrderStatus.DONE.value,
            db.func.date(Order.completed_at).between(first_day, last_day)
        ).count(),
        'total_outbound': Order.query.filter(
            Order.order_type == OrderType.OUTBOUND.value,
            Order.status     == OrderStatus.DONE.value,
            db.func.date(Order.completed_at).between(first_day, last_day)
        ).count(),
        'new_contracts': Contract.query.filter(
            Contract.start_date.between(first_day, last_day)
        ).count(),
        'overall_occupancy': round(
            Slot.query.filter_by(status=SlotStatus.RENTED.value).count() /
            max(Slot.query.count(), 1) * 100, 1
        ),
    }

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(50).all()

    return render_template('reports/index.html',
                           occupancy_data=occupancy_data,
                           monthly_revenue=monthly_revenue,
                           revenue_by_customer=revenue_by_customer,
                           recent_orders=recent_orders,
                           summary=summary,
                           year=year,
                           month=month)


# ─── API biểu đồ ─────────────────────────────────────────

@reports_bp.route('/api/monthly-revenue')
@login_required
def api_monthly_revenue():
    today = date.today()
    data  = []
    for i in range(11, -1, -1):
        m  = (today.month - i - 1) % 12 + 1
        y  = today.year - ((today.month - i - 1) // 12)
        fd = date(y, m, 1)
        ld = (date(y, m + 1, 1) - timedelta(days=1)
              if m < 12 else date(y + 1, 1, 1) - timedelta(days=1))
        rev = _revenue_query(fd, ld)
        data.append({'month': f'T{m}/{y}', 'revenue': round(rev / 1_000_000, 1)})
    return jsonify(data)


@reports_bp.route('/api/occupancy')
@login_required
def api_occupancy():
    zones = Zone.query.all()
    return jsonify([{
        'zone':   z.name,
        'rented': z.rented_slots,
        'empty':  z.empty_slots,
        'rate':   z.occupancy_rate,
    } for z in zones])


@reports_bp.route('/api/occupancy-by-year')
@login_required
def api_occupancy_by_year():
    """Tỷ lệ lấp đầy theo từng tháng trong năm, phân theo khu vực."""
    today = date.today()
    year  = request.args.get('year', today.year, type=int)
    zones = Zone.query.all()

    result = []
    for m in range(1, 13):
        # Dùng ngày cuối tháng làm snapshot, không vượt hôm nay
        if m < 12:
            snapshot = date(year, m + 1, 1) - timedelta(days=1)
        else:
            snapshot = date(year + 1, 1, 1) - timedelta(days=1)
        snapshot = min(snapshot, today)

        zone_rates = {z.name: _occupancy_on_date(z, snapshot) for z in zones}
        result.append({'label': f'T{m}', 'zones': zone_rates})

    return jsonify(result)


@reports_bp.route('/api/occupancy-by-day')
@login_required
def api_occupancy_by_day():
    """Tỷ lệ lấp đầy theo từng ngày trong tháng, phân theo khu vực."""
    today = date.today()
    year  = request.args.get('year',  today.year,  type=int)
    month = request.args.get('month', today.month, type=int)
    zones = Zone.query.all()

    fd = date(year, month, 1)
    ld = (date(year, month + 1, 1) - timedelta(days=1)
          if month < 12 else date(year + 1, 1, 1) - timedelta(days=1))
    ld = min(ld, today)

    result  = []
    current = fd
    while current <= ld:
        zone_rates = {z.name: _occupancy_on_date(z, current) for z in zones}
        result.append({'label': current.strftime('%d/%m'), 'zones': zone_rates})
        current += timedelta(days=1)

    return jsonify(result)
