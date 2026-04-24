# ============================================================
# MODULE 4: QUẢN LÝ KHÔNG GIAN KHO (Warehouse Layout)
# File: app/routes/warehouse.py
# ============================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Zone, Slot, SlotStatus, ContractSlot, Contract, ContractStatus

warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/warehouse')

STATUS_LABELS = {
    SlotStatus.EMPTY.value:       ('Trống',       'success'),
    SlotStatus.RENTED.value:      ('Đang thuê',   'info'),
    SlotStatus.MAINTENANCE.value: ('Bảo trì',     'warning'),
    SlotStatus.CLEANING.value:    ('Cần vệ sinh', 'pink'),
}


# ─── Khu vực (Zone) ────────────────────────────────────────

@warehouse_bp.route('/')
@login_required
def index():
    """Sơ đồ kho tổng thể"""
    zones = Zone.query.all()
    selected_zone = request.args.get('zone', 'all')

    if selected_zone != 'all':
        zone_obj = Zone.query.filter_by(code=selected_zone).first()
        slots = zone_obj.slots.all() if zone_obj else []
    else:
        slots = Slot.query.all()

    # Tổng hợp thống kê
    stats = {
        'total':    Slot.query.count(),
        'empty':    Slot.query.filter_by(status=SlotStatus.EMPTY.value).count(),
        'rented':   Slot.query.filter_by(status=SlotStatus.RENTED.value).count(),
        'maintain': Slot.query.filter_by(status=SlotStatus.MAINTENANCE.value).count(),
        'cleaning': Slot.query.filter_by(status=SlotStatus.CLEANING.value).count(),
    }

    return render_template('warehouse/index.html',
                           zones=zones,
                           slots=slots,
                           selected_zone=selected_zone,
                           stats=stats,
                           status_labels=STATUS_LABELS)


@warehouse_bp.route('/zones')
@login_required
def zone_list():
    zones = Zone.query.all()
    return render_template('warehouse/zone_list.html', zones=zones)


@warehouse_bp.route('/zones/create', methods=['GET', 'POST'])
@login_required
def zone_create():
    if not current_user.is_admin():
        flash('Chỉ Admin mới có quyền tạo khu vực.', 'danger')
        return redirect(url_for('warehouse.zone_list'))

    if request.method == 'POST':
        code         = request.form.get('code', '').strip().upper()
        name         = request.form.get('name', '').strip()
        description  = request.form.get('description', '').strip()
        max_area_m2  = float(request.form.get('max_area_m2', 0) or 0)
        max_weight_kg = float(request.form.get('max_weight_kg', 0) or 0)

        if Zone.query.filter_by(code=code).first():
            flash(f'Mã khu vực "{code}" đã tồn tại.', 'danger')
            return render_template('warehouse/zone_form.html', zone=None)

        zone = Zone(code=code, name=name, description=description,
                    max_area_m2=max_area_m2, max_weight_kg=max_weight_kg)
        db.session.add(zone)
        db.session.commit()
        flash(f'Tạo khu vực {name} thành công!', 'success')
        return redirect(url_for('warehouse.zone_list'))

    return render_template('warehouse/zone_form.html', zone=None)


@warehouse_bp.route('/zones/<int:zone_id>/edit', methods=['GET', 'POST'])
@login_required
def zone_edit(zone_id):
    if not current_user.is_admin():
        flash('Chỉ Admin mới có quyền chỉnh sửa.', 'danger')
        return redirect(url_for('warehouse.zone_list'))

    zone = Zone.query.get_or_404(zone_id)

    if request.method == 'POST':
        zone.name         = request.form.get('name', '').strip()
        zone.description  = request.form.get('description', '').strip()
        zone.max_area_m2  = float(request.form.get('max_area_m2', 0) or 0)
        zone.max_weight_kg = float(request.form.get('max_weight_kg', 0) or 0)
        db.session.commit()
        flash('Cập nhật khu vực thành công!', 'success')
        return redirect(url_for('warehouse.zone_list'))

    return render_template('warehouse/zone_form.html', zone=zone)


# ─── Vị trí lưu trữ (Slot) ────────────────────────────────

@warehouse_bp.route('/slots')
@login_required
def slot_list():
    zone_id = request.args.get('zone_id', type=int)
    status  = request.args.get('status', '')
    search  = request.args.get('search', '').strip()

    query = Slot.query
    if zone_id:
        query = query.filter_by(zone_id=zone_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Slot.code.ilike(f'%{search}%'))

    slots = query.order_by(Slot.code).all()
    zones = Zone.query.all()

    return render_template('warehouse/slot_list.html',
                           slots=slots, zones=zones,
                           status_labels=STATUS_LABELS,
                           statuses=SlotStatus)


@warehouse_bp.route('/slots/create', methods=['GET', 'POST'])
@login_required
def slot_create():
    if not current_user.is_admin():
        flash('Chỉ Admin mới có quyền tạo vị trí.', 'danger')
        return redirect(url_for('warehouse.slot_list'))

    zones = Zone.query.all()

    if request.method == 'POST':
        code         = request.form.get('code', '').strip().upper()
        zone_id      = int(request.form.get('zone_id'))
        row_number   = int(request.form.get('row_number', 1) or 1)
        floor_number = int(request.form.get('floor_number', 1) or 1)
        area_m2      = float(request.form.get('area_m2', 0) or 0)
        volume_m3    = float(request.form.get('volume_m3', 0) or 0)
        max_weight_kg = float(request.form.get('max_weight_kg', 0) or 0)
        notes        = request.form.get('notes', '').strip()

        if Slot.query.filter_by(code=code).first():
            flash(f'Mã vị trí "{code}" đã tồn tại.', 'danger')
            return render_template('warehouse/slot_form.html', slot=None, zones=zones)

        slot = Slot(code=code, zone_id=zone_id, row_number=row_number,
                    floor_number=floor_number, area_m2=area_m2,
                    volume_m3=volume_m3, max_weight_kg=max_weight_kg, notes=notes)
        db.session.add(slot)
        db.session.commit()
        flash(f'Tạo vị trí {code} thành công!', 'success')
        return redirect(url_for('warehouse.slot_list'))

    return render_template('warehouse/slot_form.html', slot=None, zones=zones)


@warehouse_bp.route('/slots/<int:slot_id>/edit', methods=['GET', 'POST'])
@login_required
def slot_edit(slot_id):
    slot  = Slot.query.get_or_404(slot_id)
    zones = Zone.query.all()

    if request.method == 'POST':
        slot.zone_id      = int(request.form.get('zone_id'))
        slot.row_number   = int(request.form.get('row_number', 1) or 1)
        slot.floor_number = int(request.form.get('floor_number', 1) or 1)
        slot.area_m2      = float(request.form.get('area_m2', 0) or 0)
        slot.volume_m3    = float(request.form.get('volume_m3', 0) or 0)
        slot.max_weight_kg = float(request.form.get('max_weight_kg', 0) or 0)
        slot.notes        = request.form.get('notes', '').strip()

        # Chỉ cho phép đổi trạng thái nếu không vi phạm hợp đồng
        new_status = request.form.get('status')
        if new_status:
            if (new_status != SlotStatus.RENTED.value and
                    slot.status == SlotStatus.RENTED.value):
                # Kiểm tra có hợp đồng active không
                active_cs = slot.contract_slots.join(Contract).filter(
                    Contract.status.in_([ContractStatus.ACTIVE.value,
                                         ContractStatus.EXPIRING.value])
                ).first()
                if active_cs:
                    flash('Không thể đổi trạng thái: Vị trí đang có hợp đồng hiệu lực.', 'danger')
                    return redirect(url_for('warehouse.slot_edit', slot_id=slot_id))
            slot.status = new_status

        db.session.commit()
        flash(f'Cập nhật vị trí {slot.code} thành công!', 'success')
        return redirect(url_for('warehouse.slot_list'))

    return render_template('warehouse/slot_form.html',
                           slot=slot, zones=zones,
                           statuses=SlotStatus,
                           status_labels=STATUS_LABELS)


@warehouse_bp.route('/slots/<int:slot_id>/update-status', methods=['POST'])
@login_required
def slot_update_status(slot_id):
    """API nhanh: Cập nhật trạng thái ô kho (AJAX)"""
    slot   = Slot.query.get_or_404(slot_id)
    status = request.json.get('status')

    if status not in [s.value for s in SlotStatus]:
        return jsonify({'error': 'Trạng thái không hợp lệ'}), 400

    slot.status = status
    db.session.commit()
    label, color = STATUS_LABELS.get(status, (status, 'secondary'))
    return jsonify({'success': True, 'status': status,
                    'label': label, 'color': color})


@warehouse_bp.route('/api/slot/<int:slot_id>')
@login_required
def api_slot_detail(slot_id):
    """API trả JSON chi tiết ô kho (dùng cho popup)"""
    slot = Slot.query.get_or_404(slot_id)
    label, color = STATUS_LABELS.get(slot.status, (slot.status, 'secondary'))
    contract = slot.current_contract

    return jsonify({
        'code':        slot.code,
        'zone':        slot.zone.name,
        'location':    slot.location_label,
        'area_m2':     slot.area_m2,
        'volume_m3':   slot.volume_m3,
        'status':      slot.status,
        'status_label': label,
        'tenant':      contract.customer.name if contract else None,
        'goods_type':  slot.contract_slots.first().goods_type
                       if slot.contract_slots.count() else None,
    })
