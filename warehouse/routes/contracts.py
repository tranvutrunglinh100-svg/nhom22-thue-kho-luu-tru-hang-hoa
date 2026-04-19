from flask import Blueprint, jsonify, request
from models import Database

contracts_bp = Blueprint('contracts', __name__, url_prefix='/api')

@contracts_bp.route('/contracts', methods=['GET', 'POST'])
def contracts():
    db = Database.load()
    if request.method == 'POST':
        new_contract = request.get_json()
        db['contracts'].append(new_contract)
        Database.save(db)
        return jsonify({"success": True, "message": "Thêm hợp đồng thành công"})
    return jsonify(db.get('contracts', []))

@contracts_bp.route('/contracts/<string:contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    db = Database.load()
    db['contracts'] = [c for c in db['contracts'] if c.get('id') != contract_id]
    Database.save(db)
    return jsonify({"success": True})