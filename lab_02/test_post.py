import requests

data = {"product_name": "Кофе", "quantity": 1}
response = requests.post("http://127.0.0.1:5000/api/items", json=data)
print(f"Статус: {response.status_code}")
print(f"Ответ: {response.json()}")