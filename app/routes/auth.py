# ============================================================
# MODULE 2: XÁC THỰC NGƯỜI DÙNG (Authentication)
# File: app/routes/auth.py
# ============================================================

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, UserRole

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=bool(remember))
            next_page = request.args.get('next')
            flash(f'Chào mừng {user.full_name or user.username}!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/users')
@login_required
def user_list():
    if not current_user.is_admin():
        flash('Bạn không có quyền truy cập trang này.', 'danger')
        return redirect(url_for('dashboard.index'))
    users = User.query.all()
    return render_template('auth/users.html', users=users)


@auth_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def user_create():
    if not current_user.is_admin():
        flash('Bạn không có quyền thực hiện thao tác này.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        email     = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone     = request.form.get('phone', '').strip()
        role      = request.form.get('role', UserRole.STAFF.value)
        password  = request.form.get('password', '')

        # Kiểm tra trùng lặp
        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại.', 'danger')
            return render_template('auth/user_form.html', roles=UserRole)

        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng.', 'danger')
            return render_template('auth/user_form.html', roles=UserRole)

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role=role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'Tạo tài khoản {username} thành công!', 'success')
        return redirect(url_for('auth.user_list'))

    return render_template('auth/user_form.html', roles=UserRole, user=None)


@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    if not current_user.is_admin():
        flash('Bạn không có quyền thực hiện thao tác này.', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        user.phone     = request.form.get('phone', '').strip()
        user.role      = request.form.get('role', UserRole.STAFF.value)
        user.is_active = 'is_active' in request.form

        new_password = request.form.get('new_password', '')
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        flash('Cập nhật tài khoản thành công!', 'success')
        return redirect(url_for('auth.user_list'))

    return render_template('auth/user_form.html', roles=UserRole, user=user)
