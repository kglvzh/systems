from flask import Flask, request, jsonify, Response
import requests
import xml.etree.ElementTree as ET
import json

app = Flask(__name__)

# Список покупок (хранилище)
shopping_list = [
    {"id": 1, "product_name": "Молоко", "quantity": 2},
    {"id": 2, "product_name": "Хлеб", "quantity": 1}
]
next_id = 3

# GET /api/items - получить все покупки
@app.route('/api/items', methods=['GET'])
def get_items():
    return Response(json.dumps(shopping_list, ensure_ascii=False, indent=4), mimetype='application/json; charset=utf-8'), 200

# GET /api/items/<id> - получить покупку по id
@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = next((i for i in shopping_list if i["id"] == item_id), None)
    if item:
        return Response(json.dumps(item, ensure_ascii=False, indent=4), mimetype='application/json; charset=utf-8'), 200
    return jsonify({"error": "Item not found"}), 404

# POST /api/items - создать новую покупку
@app.route('/api/items', methods=['POST'])
def create_item():
    global next_id
    data = request.get_json()
    
    if not data or "product_name" not in data or "quantity" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    new_item = {
        "id": next_id,
        "product_name": data["product_name"],
        "quantity": data["quantity"]
    }
    shopping_list.append(new_item)
    next_id += 1
    
    return Response(json.dumps(new_item, ensure_ascii=False, indent=4), mimetype='application/json; charset=utf-8'), 201

# PUT /api/items/<id> - обновить покупку
@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = next((i for i in shopping_list if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    data = request.get_json()
    if "product_name" in data:
        item["product_name"] = data["product_name"]
    if "quantity" in data:
        item["quantity"] = data["quantity"]
    
    return Response(json.dumps(item, ensure_ascii=False, indent=4), mimetype='application/json; charset=utf-8'), 200

# DELETE /api/items/<id> - удалить покупку
@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    global shopping_list
    item = next((i for i in shopping_list if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    shopping_list = [i for i in shopping_list if i["id"] != item_id]
    return jsonify({"message": "Item deleted"}), 200

# GET /api/currency - получить курсы валют с cbr.ru
@app.route('/api/currency', methods=['GET'])
def get_currency():
    url = "http://www.cbr.ru/scripts/XML_daily.asp"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        rates = []
        
        for valute in root.findall('Valute'):
            rates.append({
                'code': valute.find('CharCode').text,
                'name': valute.find('Name').text,
                'value': float(valute.find('Value').text.replace(',', '.')),
                'nominal': int(valute.find('Nominal').text)
            })
        
        return Response(json.dumps({
            'date': root.get('Date'),
            'rates': rates
        }, ensure_ascii=False, indent=4), mimetype='application/json; charset=utf-8'), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET /api/currency/<code> - получить курс конкретной валюты
@app.route('/api/currency/<string:code>', methods=['GET'])
def get_currency_by_code(code):
    url = "http://www.cbr.ru/scripts/XML_daily.asp"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        for valute in root.findall('Valute'):
            if valute.find('CharCode').text == code.upper():
                return Response(json.dumps({
                    'date': root.get('Date'),
                    'currency': {
                        'code': code.upper(),
                        'name': valute.find('Name').text,
                        'value': float(valute.find('Value').text.replace(',', '.')),
                        'nominal': int(valute.find('Nominal').text)
                    }
                }, ensure_ascii=False, indent=4), mimetype='application/json; charset=utf-8'), 200
        
        return jsonify({'error': f'Currency {code} not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Сервер запущен!")
    print("="*50)
    print("\nСписок покупок API:")
    print("  GET    http://localhost:5000/api/items")
    print("  GET    http://localhost:5000/api/items/1")
    print("  POST   http://localhost:5000/api/items")
    print("  PUT    http://localhost:5000/api/items/1")
    print("  DELETE http://localhost:5000/api/items/1")
    print("\nКурсы валют API:")
    print("  GET    http://localhost:5000/api/currency")
    print("  GET    http://localhost:5000/api/currency/USD")
    print("\n" + "="*50)
    print("Для остановки сервера нажмите Ctrl+C\n")
    
    app.run(host='127.0.0.1', port=5000, debug=True)