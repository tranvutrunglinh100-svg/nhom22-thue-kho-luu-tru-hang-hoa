"""
run.py — Điểm khởi chạy ứng dụng WareFlow
Chạy: python run.py
"""

from app import create_app, db
from app.models import User, Zone, Slot, Contract, Customer, Invoice, Order

app = create_app('development')


@app.shell_context_processor
def make_shell_context():
    """Tiện ích cho Flask shell: flask shell"""
    return {
        'db': db,
        'User': User,
        'Zone': Zone,
        'Slot': Slot,
        'Contract': Contract,
        'Customer': Customer,
        'Invoice': Invoice,
        'Order': Order,
    }


@app.context_processor
def inject_globals():
    """Inject biến toàn cục vào tất cả templates"""
    from datetime import datetime
    return {'now': datetime.now()}


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
