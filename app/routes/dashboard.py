# ============================================================
# MODULE 3: BẢNG ĐIỀU KHIỂN TỔNG QUAN (Dashboard)
# File: app/routes/dashboard.py
# ============================================================

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date, timedelta
from app import db
from app.models import (Zone, Slot, SlotStatus, Contract, ContractStatus,
                        Order, OrderStatus, Invoice, InvoiceStatus, Customer)

dashboard_bp = Blueprint('dashboard', __name__)


def get_dashboard_stats():
    """Tính toán tất cả số liệu cho dashboard"""

    # --- Kho ---
    total_slots   = Slot.query.count()
    empty_slots   = Slot.query.filter_by(status=SlotStatus.EMPTY.value).count()
    rented_slots  = Slot.query.filter_by(status=SlotStatus.RENTED.value).count()
    maintain_slots = Slot.query.filter_by(status=SlotStatus.MAINTENANCE.value).count()
    occupancy_rate = round(rented_slots / total_slots * 100, 1) if total_slots else 0

    total_area_m2 = db.session.query(func.sum(Slot.area_m2)).scalar() or 0
    empty_area_m2 = db.session.query(func.sum(Slot.area_m2)).filter(
        Slot.status == SlotStatus.EMPTY.value
    ).scalar() or 0

    # --- Hợp đồng ---
    active_contracts  = Contract.query.filter_by(status=ContractStatus.ACTIVE.value).count()
    expiring_contracts = Contract.query.filter_by(status=ContractStatus.EXPIRING.value).count()

    # --- Đơn hàng ---
    pending_orders = Order.query.filter_by(status=OrderStatus.PENDING.value).count()
    today_orders   = Order.query.filter(
        func.date(Order.created_at) == date.today()
    ).count()

    # --- Tài chính tháng này ---
    first_day = date.today().replace(day=1)
    monthly_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.status == InvoiceStatus.PAID.value,
        Invoice.paid_date >= first_day
    ).scalar() or 0

    overdue_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.status == InvoiceStatus.OVERDUE.value
    ).scalar() or 0

    return {
        'total_slots':       total_slots,
        'empty_slots':       empty_slots,
        'rented_slots':      rented_slots,
        'maintain_slots':    maintain_slots,
        'occupancy_rate':    occupancy_rate,
        'total_area_m2':     round(total_area_m2, 1),
        'empty_area_m2':     round(empty_area_m2, 1),
        'active_contracts':  active_contracts,
        'expiring_contracts': expiring_contracts,
        'pending_orders':    pending_orders,
        'today_orders':      today_orders,
        'monthly_revenue':   monthly_revenue,
        'overdue_amount':    overdue_amount,
    }


def get_recent_activity(limit=10):
    """Lấy hoạt động gần đây"""
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(limit).all()
    activities = []
    for o in recent_orders:
        activities.append({
            'time':  o.created_at.strftime('%H:%M %d/%m'),
            'type':  o.type_label,
            'text':  f'{o.type_label} hàng — {o.customer.name}',
            'color': 'success' if o.order_type == 'inbound' else 'warning'
        })
    return activities


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    stats      = get_dashboard_stats()
    activities = get_recent_activity()

    # Hợp đồng sắp hết hạn
    expiring = Contract.query.filter(
        Contract.status.in_([ContractStatus.ACTIVE.value,
                              ContractStatus.EXPIRING.value]),
        Contract.end_date <= date.today() + timedelta(days=30)
    ).order_by(Contract.end_date).limit(5).all()

    # Đơn hàng chờ xử lý
    pending_orders = Order.query.filter_by(
        status=OrderStatus.PENDING.value
    ).order_by(Order.created_at.desc()).limit(5).all()

    return render_template('dashboard/index.html',
                           stats=stats,
                           activities=activities,
                           expiring_contracts=expiring,
                           pending_orders=pending_orders)


@dashboard_bp.route('/api/chart/occupancy')
@login_required
def api_occupancy():
    """API trả JSON cho biểu đồ tỷ lệ lấp đầy"""
    zones = Zone.query.all()
    data = [{
        'zone':  z.name,
        'rented':  z.rented_slots,
        'empty':   z.empty_slots,
        'total':   z.total_slots,
        'rate':    z.occupancy_rate
    } for z in zones]
    return jsonify(data)


@dashboard_bp.route('/api/chart/revenue')
@login_required
def api_revenue():
    """API trả JSON cho biểu đồ doanh thu 6 tháng"""
    results = []
    for i in range(5, -1, -1):
        d = date.today()
        month = (d.month - i - 1) % 12 + 1
        year  = d.year - ((d.month - i - 1) // 12)
        first = date(year, month, 1)
        if month == 12:
            last = date(year + 1, 1, 1)
        else:
            last = date(year, month + 1, 1)

        revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.status == InvoiceStatus.PAID.value,
            Invoice.paid_date >= first,
            Invoice.paid_date < last
        ).scalar() or 0

        results.append({
            'month':   f'T{month}/{year}',
            'revenue': round(revenue / 1_000_000, 1)  # Triệu đồng
        })

    return jsonify(results)
