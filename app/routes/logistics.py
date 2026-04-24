# ============================================================
# MODULE 6: NHẬP / XUẤT HÀNG HÓA (Logistics)
# File: app/routes/logistics.py
# ============================================================

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify)
from flask_login import login_required, current_user
from datetime import date, datetime
from app import db
from app.models import (Order, OrderItem, OrderType, OrderStatus,
                        Customer, Slot, SlotStatus)

logistics_bp = Blueprint('logistics', __name__, url_prefix='/logistics')

STATUS_LABELS = {
    OrderStatus.PENDING.value:    ('Chờ xử lý',   'warning'),
    OrderStatus.PROCESSING.value: ('Đang bốc xếp', 'info'),
    OrderStatus.DONE.value:       ('Hoàn thành',   'success'),
    OrderStatus.CANCELLED.value:  ('Đã huỷ',       'secondary'),
}


def _generate_order_code():
    """Tạo mã lệnh: IO-001"""
    last = Order.query.order_by(Order.id.desc()).first()
    seq  = (last.id + 1) if last else 1
    return f'IO-{seq:03d}'


# ─── Danh sách lệnh nhập/xuất ────────────────────────────

@logistics_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    type_filter   = request.args.get('type', 'all')
    search        = request.args.get('search', '').strip()
    page          = request.args.get('page', 1, type=int)

    query = Order.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if type_filter != 'all':
        query = query.filter_by(order_type=type_filter)

    if search:
        query = query.join(Customer).filter(
            Customer.name.ilike(f'%{search}%') |
            Order.code.ilike(f'%{search}%')
        )

    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    stats = {
        'pending':    Order.query.filter_by(status=OrderStatus.PENDING.value).count(),
        'processing': Order.query.filter_by(status=OrderStatus.PROCESSING.value).count(),
        'done_today': Order.query.filter(
            Order.status == OrderStatus.DONE.value,
            db.func.date(Order.completed_at) == date.today()
        ).count(),
    }

    return render_template('logistics/index.html',
                           orders=orders,
                           status_filter=status_filter,
                           type_filter=type_filter,
                           search=search,
                           stats=stats,
                           STATUS_LABELS=STATUS_LABELS,
                           OrderStatus=OrderStatus,
                           OrderType=OrderType)


# ─── Chi tiết lệnh ────────────────────────────────────────

@logistics_bp.route('/<int:order_id>')
@login_required
def detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('logistics/detail.html',
                           order=order,
                           STATUS_LABELS=STATUS_LABELS)


# ─── Tạo lệnh nhập/xuất ──────────────────────────────────

@logistics_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    customers = Customer.query.order_by(Customer.name).all()
    slots     = Slot.query.filter(
        Slot.status.in_([SlotStatus.RENTED.value, SlotStatus.EMPTY.value])
    ).order_by(Slot.code).all()

    if request.method == 'POST':
        order_type     = request.form.get('order_type')
        customer_id    = int(request.form.get('customer_id'))
        slot_id        = request.form.get('slot_id') or None
        scheduled_date = request.form.get('scheduled_date')
        driver_name    = request.form.get('driver_name', '').strip()
        vehicle_plate  = request.form.get('vehicle_plate', '').strip()
        notes          = request.form.get('notes', '').strip()

        order = Order(
            code           = _generate_order_code(),
            order_type     = order_type,
            customer_id    = customer_id,
            slot_id        = int(slot_id) if slot_id else None,
            scheduled_date = date.fromisoformat(scheduled_date) if scheduled_date else None,
            driver_name    = driver_name,
            vehicle_plate  = vehicle_plate,
            notes          = notes,
            created_by     = current_user.id
        )
        db.session.add(order)
        db.session.flush()

        # Thêm chi tiết hàng hóa
        barcodes     = request.form.getlist('barcodes')
        goods_names  = request.form.getlist('goods_names')
        quantities   = request.form.getlist('quantities')
        units        = request.form.getlist('units')
        weights      = request.form.getlist('weights')
        volumes      = request.form.getlist('volumes')

        for i in range(len(goods_names)):
            if goods_names[i].strip():
                item = OrderItem(
                    order_id   = order.id,
                    barcode    = barcodes[i] if i < len(barcodes) else '',
                    goods_name = goods_names[i].strip(),
                    quantity   = int(quantities[i]) if quantities[i] else 0,
                    unit       = units[i] if i < len(units) else 'thùng',
                    weight_kg  = float(weights[i]) if weights[i] else 0,
                    volume_m3  = float(volumes[i]) if volumes[i] else 0,
                )
                db.session.add(item)

        db.session.commit()
        flash(f'Tạo lệnh {order.code} thành công!', 'success')
        return redirect(url_for('logistics.detail', order_id=order.id))

    return render_template('logistics/form.html',
                           order=None,
                           customers=customers,
                           slots=slots,
                           OrderType=OrderType)


# ─── Cập nhật trạng thái ──────────────────────────────────

@logistics_bp.route('/<int:order_id>/approve', methods=['POST'])
@login_required
def approve(order_id):
    """Duyệt lệnh: Chờ xử lý → Đang bốc xếp"""
    order = Order.query.get_or_404(order_id)
    if order.status != OrderStatus.PENDING.value:
        flash('Lệnh không ở trạng thái Chờ xử lý.', 'warning')
        return redirect(url_for('logistics.detail', order_id=order_id))

    order.status       = OrderStatus.PROCESSING.value
    order.processed_by = current_user.id
    db.session.commit()
    flash(f'Đã duyệt lệnh {order.code}. Bắt đầu bốc xếp hàng.', 'success')
    return redirect(url_for('logistics.detail', order_id=order_id))


@logistics_bp.route('/<int:order_id>/complete', methods=['POST'])
@login_required
def complete(order_id):
    """Hoàn thành lệnh: Đang bốc xếp → Hoàn thành"""
    order = Order.query.get_or_404(order_id)
    if order.status != OrderStatus.PROCESSING.value:
        flash('Lệnh chưa được duyệt hoặc đã hoàn thành.', 'warning')
        return redirect(url_for('logistics.detail', order_id=order_id))

    order.status       = OrderStatus.DONE.value
    order.completed_at = datetime.utcnow()
    db.session.commit()
    flash(f'Lệnh {order.code} đã hoàn thành!', 'success')
    return redirect(url_for('logistics.detail', order_id=order_id))


@logistics_bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status == OrderStatus.DONE.value:
        flash('Không thể huỷ lệnh đã hoàn thành.', 'danger')
        return redirect(url_for('logistics.detail', order_id=order_id))

    order.status = OrderStatus.CANCELLED.value
    db.session.commit()
    flash(f'Đã huỷ lệnh {order.code}.', 'info')
    return redirect(url_for('logistics.index'))


# ─── In biên bản bàn giao ─────────────────────────────────

@logistics_bp.route('/<int:order_id>/print')
@login_required
def print_handover(order_id):
    """Biên bản bàn giao điện tử"""
    order = Order.query.get_or_404(order_id)
    return render_template('logistics/print_handover.html', order=order)


# ─── Quét mã vạch (API) ──────────────────────────────────

@logistics_bp.route('/api/scan-barcode', methods=['POST'])
@login_required
def scan_barcode():
    """API xác nhận mã vạch / QR Code"""
    barcode  = request.json.get('barcode', '').strip()
    order_id = request.json.get('order_id')

    if not barcode:
        return jsonify({'error': 'Mã vạch không hợp lệ'}), 400

    # Tìm item theo barcode trong order
    item = OrderItem.query.filter_by(
        barcode=barcode, order_id=order_id
    ).first()

    if item:
        return jsonify({
            'found':      True,
            'goods_name': item.goods_name,
            'quantity':   item.quantity,
            'unit':       item.unit,
        })
    else:
        return jsonify({'found': False, 'barcode': barcode})
