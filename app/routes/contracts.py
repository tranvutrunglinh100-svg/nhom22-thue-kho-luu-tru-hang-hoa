# ============================================================
# MODULE 5: QUẢN LÝ HỢP ĐỒNG & DỊCH VỤ (Contract Management)
# File: app/routes/contracts.py
# ============================================================

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify)
from flask_login import login_required, current_user
from datetime import date, timedelta
from app import db
from app.models import (Contract, ContractSlot, ContractService, ContractStatus,
                        Customer, Slot, SlotStatus, Service)

contracts_bp = Blueprint('contracts', __name__, url_prefix='/contracts')


def _generate_contract_code():
    """Tạo mã hợp đồng tự động: HD-2026-001"""
    year = date.today().year
    last = Contract.query.filter(
        Contract.code.like(f'HD-{year}-%')
    ).order_by(Contract.id.desc()).first()
    if last and last.code:
        seq = int(last.code.split('-')[-1]) + 1
    else:
        seq = 1
    return f'HD-{year}-{seq:03d}'


# ─── Danh sách & chi tiết ────────────────────────────────

@contracts_bp.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    search        = request.args.get('search', '').strip()

    query = Contract.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if search:
        query = query.join(Customer).filter(
            Customer.name.ilike(f'%{search}%') |
            Contract.code.ilike(f'%{search}%')
        )

    # Cập nhật trạng thái hợp đồng trước khi hiển thị
    contracts = query.order_by(Contract.end_date).all()
    for c in contracts:
        c.update_status()
    db.session.commit()

    # Thống kê nhanh
    stats = {
        'active':   Contract.query.filter_by(status=ContractStatus.ACTIVE.value).count(),
        'expiring': Contract.query.filter_by(status=ContractStatus.EXPIRING.value).count(),
        'expired':  Contract.query.filter_by(status=ContractStatus.EXPIRED.value).count(),
    }

    return render_template('contracts/index.html',
                           contracts=contracts,
                           status_filter=status_filter,
                           search=search,
                           stats=stats,
                           statuses=ContractStatus)


@contracts_bp.route('/<int:contract_id>')
@login_required
def detail(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    contract.update_status()
    db.session.commit()
    return render_template('contracts/detail.html', contract=contract)


# ─── Tạo hợp đồng ────────────────────────────────────────

@contracts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_admin():
        flash('Chỉ Admin mới có quyền tạo hợp đồng.', 'danger')
        return redirect(url_for('contracts.index'))

    customers     = Customer.query.order_by(Customer.name).all()
    available_slots = Slot.query.filter_by(status=SlotStatus.EMPTY.value).all()
    services      = Service.query.all()

    if request.method == 'POST':
        customer_id   = int(request.form.get('customer_id'))
        start_date    = date.fromisoformat(request.form.get('start_date'))
        end_date      = date.fromisoformat(request.form.get('end_date'))
        monthly_rate  = float(request.form.get('monthly_rate', 0))
        notes         = request.form.get('notes', '').strip()

        # Tính tổng giá trị hợp đồng
        months = (end_date.year - start_date.year) * 12 + \
                 (end_date.month - start_date.month) + 1
        total_value = monthly_rate * months

        contract = Contract(
            code         = _generate_contract_code(),
            customer_id  = customer_id,
            start_date   = start_date,
            end_date     = end_date,
            monthly_rate = monthly_rate,
            total_value  = total_value,
            notes        = notes,
            created_by   = current_user.id
        )
        contract.update_status()
        db.session.add(contract)
        db.session.flush()  # Lấy contract.id trước khi commit

        # Gắn vị trí kho vào hợp đồng
        slot_ids   = request.form.getlist('slot_ids')
        goods_types = request.form.getlist('goods_types')
        for i, slot_id in enumerate(slot_ids):
            if slot_id:
                slot = Slot.query.get(int(slot_id))
                if slot:
                    cs = ContractSlot(
                        contract_id = contract.id,
                        slot_id     = int(slot_id),
                        goods_type  = goods_types[i] if i < len(goods_types) else ''
                    )
                    db.session.add(cs)
                    slot.status = SlotStatus.RENTED.value  # Đánh dấu đang thuê

        db.session.commit()
        flash(f'Tạo hợp đồng {contract.code} thành công!', 'success')
        return redirect(url_for('contracts.detail', contract_id=contract.id))

    return render_template('contracts/form.html',
                           contract=None,
                           customers=customers,
                           available_slots=available_slots,
                           services=services)


# ─── Chỉnh sửa hợp đồng ─────────────────────────────────

@contracts_bp.route('/<int:contract_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(contract_id):
    if not current_user.is_admin():
        flash('Chỉ Admin mới có quyền chỉnh sửa.', 'danger')
        return redirect(url_for('contracts.index'))

    contract      = Contract.query.get_or_404(contract_id)
    customers     = Customer.query.order_by(Customer.name).all()
    available_slots = Slot.query.filter(
        (Slot.status == SlotStatus.EMPTY.value) |
        (Slot.id.in_([cs.slot_id for cs in contract.slots]))
    ).all()

    if request.method == 'POST':
        contract.end_date     = date.fromisoformat(request.form.get('end_date'))
        contract.monthly_rate = float(request.form.get('monthly_rate', 0))
        contract.notes        = request.form.get('notes', '').strip()
        contract.update_status()
        db.session.commit()
        flash('Cập nhật hợp đồng thành công!', 'success')
        return redirect(url_for('contracts.detail', contract_id=contract_id))

    return render_template('contracts/form.html',
                           contract=contract,
                           customers=customers,
                           available_slots=available_slots)


# ─── Kết thúc hợp đồng ──────────────────────────────────

@contracts_bp.route('/<int:contract_id>/terminate', methods=['POST'])
@login_required
def terminate(contract_id):
    if not current_user.is_admin():
        return jsonify({'error': 'Không có quyền'}), 403

    contract = Contract.query.get_or_404(contract_id)
    contract.status   = ContractStatus.EXPIRED.value
    contract.end_date = date.today()

    # Trả lại trạng thái Trống cho các vị trí
    for cs in contract.slots:
        cs.slot.status = SlotStatus.EMPTY.value

    db.session.commit()
    flash(f'Đã kết thúc hợp đồng {contract.code}.', 'info')
    return redirect(url_for('contracts.index'))


# ─── Khách hàng (Customer) ───────────────────────────────

@contracts_bp.route('/customers')
@login_required
def customer_list():
    search    = request.args.get('search', '').strip()
    customers = Customer.query
    if search:
        customers = customers.filter(
            Customer.name.ilike(f'%{search}%') |
            Customer.code.ilike(f'%{search}%')
        )
    customers = customers.order_by(Customer.name).all()
    return render_template('contracts/customers.html',
                           customers=customers, search=search)


@contracts_bp.route('/customers/create', methods=['GET', 'POST'])
@login_required
def customer_create():
    if request.method == 'POST':
        # Tạo mã khách hàng tự động
        count = Customer.query.count() + 1
        code  = f'KH-{count:03d}'

        customer = Customer(
            code         = code,
            name         = request.form.get('name', '').strip(),
            tax_code     = request.form.get('tax_code', '').strip(),
            address      = request.form.get('address', '').strip(),
            contact_name = request.form.get('contact_name', '').strip(),
            phone        = request.form.get('phone', '').strip(),
            email        = request.form.get('email', '').strip(),
        )
        db.session.add(customer)
        db.session.commit()
        flash(f'Thêm khách hàng {customer.name} thành công!', 'success')
        return redirect(url_for('contracts.customer_list'))

    return render_template('contracts/customer_form.html', customer=None)


@contracts_bp.route('/customers/<int:cid>/edit', methods=['GET', 'POST'])
@login_required
def customer_edit(cid):
    customer = Customer.query.get_or_404(cid)

    if request.method == 'POST':
        customer.name         = request.form.get('name', '').strip()
        customer.tax_code     = request.form.get('tax_code', '').strip()
        customer.address      = request.form.get('address', '').strip()
        customer.contact_name = request.form.get('contact_name', '').strip()
        customer.phone        = request.form.get('phone', '').strip()
        customer.email        = request.form.get('email', '').strip()
        db.session.commit()
        flash('Cập nhật thông tin khách hàng thành công!', 'success')
        return redirect(url_for('contracts.customer_list'))

    return render_template('contracts/customer_form.html', customer=customer)


# ─── Dịch vụ giá trị gia tăng ───────────────────────────

@contracts_bp.route('/services')
@login_required
def service_list():
    services = Service.query.all()
    return render_template('contracts/services.html', services=services)


@contracts_bp.route('/services/create', methods=['GET', 'POST'])
@login_required
def service_create():
    if not current_user.is_admin():
        flash('Chỉ Admin mới có quyền tạo dịch vụ.', 'danger')
        return redirect(url_for('contracts.service_list'))

    if request.method == 'POST':
        service = Service(
            name       = request.form.get('name', '').strip(),
            unit       = request.form.get('unit', '').strip(),
            unit_price = float(request.form.get('unit_price', 0) or 0)
        )
        db.session.add(service)
        db.session.commit()
        flash('Tạo dịch vụ thành công!', 'success')
        return redirect(url_for('contracts.service_list'))

    return render_template('contracts/service_form.html', service=None)
