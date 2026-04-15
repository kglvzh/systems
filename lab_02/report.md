# Лабораторная работа №2

## Тема. Разработка REST API и настройка обратного прокси Nginx

**Группа:** ЦИБ-241  
**Вариант:** 3

---

## 1. Цель работы

Изучить принципы работы REST API и обратного прокси Nginx, реализовать API для управления списком покупок, настроить Nginx как обратный прокси и освоить парсинг XML-данных с сайта ЦБ РФ.

---

## 2. Краткие теоретические сведения

**REST API** — архитектурный стиль взаимодействия клиента и сервера через HTTP. Основные методы: GET, POST, PUT, DELETE.

**Nginx** — веб-сервер и обратный прокси, проксирует запросы к внутренним серверам (например, Flask-приложениям).

**HTTP** — протокол передачи гипертекста. Коды состояния: 200 OK, 201 CREATED, 404 Not Found.

---

## 3. Описание варианта задания

**Вариант 3**

1. Получение и анализ XML с курсами валют с cbr.ru
2. Реализовать REST API для управления "Списком покупок" (сущность: id, product_name, quantity)
3. Настройка Nginx как обратного прокси для Flask API

---

## Архитектура инструментов PEST API с Nginx

```mermaid
flowchart LR
    client["Client (curl / browser)"]
    nginx["Nginx (порт 8080)\nОбратный прокси"]
    api["Flask API (порт 5000)\napp.py"]
    storage["Storage (список покупок\nв памяти сервера)"]
    cbr["ЦБ РФ\n(cbr.ru)"]

    client -->|HTTP запрос| nginx
    nginx -->|proxy_pass /api/| api
    api -->|CRUD операции GET POST PUT DELETE| storage
    storage -->|JSON ответ| api
    api -->|запрос курсов| cbr
    cbr -->|XML с курсами валют| api
    api -->|JSON ответ| nginx
    nginx -->|HTTP ответ| client


---

## 4. Ход выполнения

### Часть 1. Реализация REST API на Flask

**Установка зависимостей:**
```bash
pip install flask requests
```


<img width="383" height="220" alt="image" src="https://github.com/user-attachments/assets/ba7a237f-f64d-431d-9819-8eee167cfbd6" />


**Листинг кода `app.py`:**

```python
from flask import Flask, request, jsonify, Response
import requests
import xml.etree.ElementTree as ET
import json

app = Flask(__name__)

# Список покупок
shopping_list = [
    {"id": 1, "product_name": "Молоко", "quantity": 2},
    {"id": 2, "product_name": "Хлеб", "quantity": 1}
]
next_id = 3

@app.route('/api/items', methods=['GET'])
def get_items():
    return Response(json.dumps(shopping_list, ensure_ascii=False, indent=4), 
                    mimetype='application/json; charset=utf-8'), 200

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = next((i for i in shopping_list if i["id"] == item_id), None)
    if item:
        return Response(json.dumps(item, ensure_ascii=False, indent=4), 
                        mimetype='application/json; charset=utf-8'), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/api/items', methods=['POST'])
def create_item():
    global next_id
    data = request.get_json()
    if not data or "product_name" not in data or "quantity" not in data:
        return jsonify({"error": "Missing fields"}), 400
    new_item = {"id": next_id, "product_name": data["product_name"], "quantity": data["quantity"]}
    shopping_list.append(new_item)
    next_id += 1
    return Response(json.dumps(new_item, ensure_ascii=False, indent=4), 
                    mimetype='application/json; charset=utf-8'), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = next((i for i in shopping_list if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json()
    if "product_name" in data:
        item["product_name"] = data["product_name"]
    if "quantity" in data:
        item["quantity"] = data["quantity"]
    return Response(json.dumps(item, ensure_ascii=False, indent=4), 
                    mimetype='application/json; charset=utf-8'), 200

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    global shopping_list
    item = next((i for i in shopping_list if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Not found"}), 404
    shopping_list = [i for i in shopping_list if i["id"] != item_id]
    return jsonify({"message": "Item deleted"}), 200

# Получение курсов валют с cbr.ru
@app.route('/api/currency', methods=['GET'])
def get_all_currency():
    url = "http://www.cbr.ru/scripts/XML_daily.asp"
    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)
        rates = []
        for valute in root.findall('Valute'):
            rates.append({
                'code': valute.find('CharCode').text,
                'name': valute.find('Name').text,
                'value': float(valute.find('Value').text.replace(',', '.')),
                'nominal': int(valute.find('Nominal').text)
            })
        return Response(json.dumps({'date': root.get('Date'), 'rates': rates}, ensure_ascii=False, indent=4), 
                        mimetype='application/json; charset=utf-8'), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/currency/<string:code>', methods=['GET'])
def get_currency_by_code(code):
    url = "http://www.cbr.ru/scripts/XML_daily.asp"
    try:
        response = requests.get(url)
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
        return jsonify({'error': 'Currency not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
```

**Описание эндпоинтов:**

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/items` | Получить все покупки |
| GET | `/api/items/{id}` | Получить покупку по ID |
| POST | `/api/items` | Добавить покупку |
| PUT | `/api/items/{id}` | Обновить покупку |
| DELETE | `/api/items/{id}` | Удалить покупку |
| GET | `/api/currency` | Все курсы валют |
| GET | `/api/currency/{code}` | Курс конкретной валюты |

---

### Часть 2. Настройка Nginx как обратного прокси

**Конфигурация Nginx (`D:\nginx-1.28.3\conf\nginx.conf`):**

```nginx
events {
    worker_connections 1024;
}

http {
    server {
        listen       8080;
        server_name  localhost;
        
        location /api/ {
            proxy_pass http://127.0.0.1:5000/api/;
            proxy_set_header Host $host;
        }
        
        location / {
            return 200 "Nginx works! API on /api/items";
            add_header Content-Type text/plain;
        }
    }
}
```

**Запуск:**
```bash
cd D:\nginx-1.28.3
.\nginx.exe
```

---

### Часть 3. Тестирование API

**GET /api/items** - получение всего списка продуктов.
```bash
curl.exe -s http://127.0.0.1:5000/api/items
```

*Результат:*


<img width="397" height="167" alt="image" src="https://github.com/user-attachments/assets/331e79d9-555b-40dc-9942-94dd69aee4a1" />

---

**POST /api/items** - добавление продукта.
```bash
curl.exe -X POST http://127.0.0.1:5000/api/items -H "Content-Type: application/json" -d '{\"product_name\": \"Пицца\", \"quantity\": 1}'
```

*Результат:* `201 CREATED`


<img width="407" height="103" alt="image" src="https://github.com/user-attachments/assets/a4fd8bbc-1bfc-48b3-bfd8-d0d7e140ad27" />

---

**PUT /api/items/1** - изменение уже существующего продукта.
```bash
curl.exe -X PUT http://127.0.0.1:5000/api/items/1 -H "Content-Type: application/json" -d '{\"quantity\": 10}'
```

*Результат:*


<img width="369" height="101" alt="image" src="https://github.com/user-attachments/assets/2e0dfe4c-92fb-42a0-b00f-b0c67bb883f1" />

---

**DELETE /api/items/3** - удаление продукта по id.
```bash
curl.exe -X DELETE http://127.0.0.1:5000/api/items/3
```

*Результат:*


<img width="408" height="63" alt="image" src="https://github.com/user-attachments/assets/320109a9-a457-4a0d-9a16-0937ef5934ba" />

---

**GET /api/currency/USD** - получение курса валют на текущую дату.
```bash
curl.exe -s http://127.0.0.1:5000/api/currency
```

*Результат:*


<img width="413" height="263" alt="image" src="https://github.com/user-attachments/assets/8a78c9d9-d3bc-4310-a23f-e48bcea0fdfb" />

---

**GET через Nginx:**
```bash
curl.exe -s http://localhost:8080/api/items
```

*Результат:* идентичен прямому запросу к Flask.

---

## 5. Заключение

В ходе выполнения лабораторной работы был реализован REST API для управления списком покупок на Flask с поддержкой методов GET, POST, PUT и DELETE, настроен обратный прокси Nginx для проксирования запросов к API, а также реализовано получение и парсинг XML-данных с сайта ЦБ РФ для отображения актуальных курсов валют. Все тесты успешно пройдены, API корректно работает как напрямую через Flask (порт 5000), так и через Nginx (порт 8080).
