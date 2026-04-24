# ============================================================
# MODULE 8: BÁO CÁO & THỐNG KÊ (Reports & Dashboards)
# File: app/routes/reports.py
# ============================================================

from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import date, timedelta
import io
from app import db
from app.models import (Zone, Slot, SlotStatus, Contract, ContractStatus,
                        Customer, Invoice, InvoiceStatus, Order, OrderType,
                        OrderStatus)

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    if not current_user.is_admin():
        from flask import flash, redirect, url_for
        flash('Chỉ Admin mới có quyền xem báo cáo.', 'danger')
        return redirect(url_for('dashboard.index'))

    # Kỳ báo cáo (mặc định tháng này)
    today     = date.today()
    year      = request.args.get('year', today.year, type=int)
    month     = request.args.get('month', today.month, type=int)
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # ─ Tỷ lệ lấp đầy theo khu vực ─
    zones = Zone.query.all()
    occupancy_data = []
    for z in zones:
        occupancy_data.append({
            'zone':    z.name,
            'code':    z.code,
            'total':   z.total_slots,
            'rented':  z.rented_slots,
            'empty':   z.empty_slots,
            'rate':    z.occupancy_rate,
        })

    # ─ Doanh thu theo khu vực ─
    revenue_by_zone = []
    for z in zones:
        # Tổng invoice của các slot thuộc zone này
        slot_ids = [s.id for s in z.slots]
        rev = db.session.query(func.sum(Invoice.total_amount)).join(
            Contract
        ).filter(
            Invoice.status == InvoiceStatus.PAID.value,
            Invoice.paid_date.between(first_day, last_day)
        ).scalar() or 0
        revenue_by_zone.append({'zone': z.name, 'revenue': rev})

    # ─ Doanh thu theo khách hàng ─
    revenue_by_customer = db.session.query(
        Customer.name,
        func.sum(Invoice.total_amount).label('total')
    ).join(Contract, Contract.customer_id == Customer.id
    ).join(Invoice, Invoice.contract_id == Contract.id
    ).filter(
        Invoice.status == InvoiceStatus.PAID.value,
        Invoice.paid_date.between(first_day, last_day)
    ).group_by(Customer.id
    ).order_by(db.text('total DESC')
    ).limit(10).all()

    # ─ Doanh thu 12 tháng gần nhất ─
    monthly_revenue = []
    for i in range(11, -1, -1):
        d   = date.today()
        m   = (d.month - i - 1) % 12 + 1
        y   = d.year - ((d.month - i - 1) // 12)
        fd  = date(y, m, 1)
        ld  = date(y, m + 1, 1) - timedelta(days=1) if m < 12 else date(y + 1, 1, 1) - timedelta(days=1)
        rev = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.status == InvoiceStatus.PAID.value,
            Invoice.paid_date.between(fd, ld)
        ).scalar() or 0
        monthly_revenue.append({
            'month':   f'T{m}/{y}',
            'revenue': round(rev / 1_000_000, 1)
        })

    # ─ Lịch sử nhập/xuất (Audit Log) ─
    recent_orders = Order.query.order_by(
        Order.created_at.desc()
    ).limit(50).all()

    # ─ Tổng hợp tháng ─
    summary = {
        'total_revenue': db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.status == InvoiceStatus.PAID.value,
            Invoice.paid_date.between(first_day, last_day)
        ).scalar() or 0,
        'total_inbound': Order.query.filter(
            Order.order_type == OrderType.INBOUND.value,
            Order.status == OrderStatus.DONE.value,
            db.func.date(Order.completed_at).between(first_day, last_day)
        ).count(),
        'total_outbound': Order.query.filter(
            Order.order_type == OrderType.OUTBOUND.value,
            Order.status == OrderStatus.DONE.value,
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

    return render_template('reports/index.html',
                           occupancy_data=occupancy_data,
                           revenue_by_zone=revenue_by_zone,
                           revenue_by_customer=revenue_by_customer,
                           monthly_revenue=monthly_revenue,
                           recent_orders=recent_orders,
                           summary=summary,
                           year=year,
                           month=month)


# ─── API cho biểu đồ Chart.js ─────────────────────────────

@reports_bp.route('/api/monthly-revenue')
@login_required
def api_monthly_revenue():
    data = []
    for i in range(5, -1, -1):
        d  = date.today()
        m  = (d.month - i - 1) % 12 + 1
        y  = d.year - ((d.month - i - 1) // 12)
        fd = date(y, m, 1)
        ld = date(y, m + 1, 1) - timedelta(days=1) if m < 12 else date(y + 1, 1, 1) - timedelta(days=1)
        rev = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.status == InvoiceStatus.PAID.value,
            Invoice.paid_date.between(fd, ld)
        ).scalar() or 0
        data.append({'month': f'T{m}', 'revenue': round(rev / 1_000_000, 1)})
    return jsonify(data)


@reports_bp.route('/api/occupancy')
@login_required
def api_occupancy():
    zones = Zone.query.all()
    return jsonify([{
        'zone':   z.name,
        'rented': z.rented_slots,
        'empty':  z.empty_slots,
        'rate':   z.occupancy_rate
    } for z in zones])
