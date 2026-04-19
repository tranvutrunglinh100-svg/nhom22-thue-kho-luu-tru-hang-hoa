from flask import Blueprint, jsonify, request
from models import Database

warehouse_bp = Blueprint('warehouse', __name__, url_prefix='/api')

@warehouse_bp.route('/warehouse')
def get_warehouse():
    db = Database.load()
    return jsonify(db.get('warehouse_cells', {}))

@warehouse_bp.route('/warehouse/update', methods=['POST'])
def update_cell():
    data = request.get_json()
    db = Database.load()
    cell_id = data.get('cell_id')
    if cell_id in db['warehouse_cells']:
        db['warehouse_cells'][cell_id] = data.get('info', {})
        Database.save(db)
        return jsonify({"success": True})
    return jsonify({"success": False}), 400