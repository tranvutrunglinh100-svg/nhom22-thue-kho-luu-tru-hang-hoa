from flask import Flask, render_template, jsonify, request
import json, os

app = Flask(__name__)

DATA_FILE = 'data/db.json'

def load_data():
    os.makedirs('data', exist_ok=True)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    default = {
        "contracts": [],
        "warehouse_cells": {}
    }
    save_data(default)
    return default

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/api/contracts', methods=['GET','POST'])
def api_contracts():
    if request.method == 'POST':
        contract = request.get_json()
        data['contracts'].append(contract)
        save_data(data)
        return jsonify({"success": True})
    return jsonify(data['contracts'])

if __name__ == '__main__':
    app.run(debug=True, port=5000)