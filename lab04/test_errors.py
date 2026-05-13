import requests
import urllib3
from cryptography.fernet import Fernet

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ca_cert = 'ca_cert.pem'
client_cert = ('client_cert.pem', 'client_key.pem')

# Тест 1: Неверный Content-Type
print("\n ТЕСТ 1: Неверный Content-Type")
try:
    resp = requests.post(
        'https://localhost:8000/api/data',
        data="просто текст",
        headers={'Content-Type': 'text/plain'},
        verify=ca_cert,
        cert=client_cert
    )
    print(f"Код: {resp.status_code}")
    print(f"Ответ: {resp.json()}")
except Exception as e:
    print(f"Ошибка: {e}")

# Тест 2: Отсутствует поле data
print("\n ТЕСТ 2: Отсутствует поле data")
try:
    resp = requests.post(
        'https://localhost:8000/api/data',
        json={'wrong_field': 'значение'},
        verify=ca_cert,
        cert=client_cert
    )
    print(f"Код: {resp.status_code}")
    print(f"Ответ: {resp.json()}")
except Exception as e:
    print(f"Ошибка: {e}")

# Тест 3: Пустое поле data
print("\n ТЕСТ 3: Пустое поле data")
try:
    resp = requests.post(
        'https://localhost:8000/api/data',
        json={'data': ''},
        verify=ca_cert,
        cert=client_cert
    )
    print(f"Код: {resp.status_code}")
    print(f"Ответ: {resp.json()}")
except Exception as e:
    print(f"Ошибка: {e}")

# Тест 4: Неверный ключ (ошибка расшифровки)
print("\n ТЕСТ 4: Ошибка расшифровки (неверный ключ)")
try:
    fake_key = Fernet.generate_key()
    fake_cipher = Fernet(fake_key)
    fake_encrypted = fake_cipher.encrypt("тест".encode()).decode()
    
    resp = requests.post(
        'https://localhost:8000/api/data',
        json={'data': fake_encrypted},
        verify=ca_cert,
        cert=client_cert
    )
    print(f"Код: {resp.status_code}")
    print(f"Ответ: {resp.json()}")
except Exception as e:
    print(f"Ошибка: {e}")

# Тест 5: Успешный запрос
print("\n ТЕСТ 5: Успешный запрос")
try:
    with open('encryption_key.txt', 'rb') as f:
        cipher = Fernet(f.read())
    
    encrypted = cipher.encrypt("Привет, мир!".encode()).decode()
    
    resp = requests.post(
        'https://localhost:8000/api/data',
        json={'data': encrypted},
        verify=ca_cert,
        cert=client_cert
    )
    print(f"Код: {resp.status_code}")
    print(f"Ответ: {resp.json()}")
except Exception as e:
    print(f"Ошибка: {e}")