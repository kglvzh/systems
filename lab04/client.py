from cryptography.fernet import Fernet
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    with open('encryption_key.txt', 'rb') as f:
        cipher = Fernet(f.read())
    print("Ключ Fernet загружен")
except Exception as e:
    print(f"Ошибка загрузки ключа: {e}")
    exit(1)

message = input("Введите сообщение для отправки: ")

try:
    encrypted = cipher.encrypt(message.encode())
    print(f"Зашифрованное сообщение: {encrypted}")
    
    # Теперь координатор на HTTPS
    resp = requests.post(
        'https://localhost:8000/api/data',
        json={'data': encrypted.decode()},
        verify='ca_cert.pem',
        cert=('client_cert.pem', 'client_key.pem'),
        timeout=10
    )
    
    print(f"Код ответа: {resp.status_code}")
    print(f"Ответ сервера: {resp.json()}")
    
except requests.exceptions.ConnectionError:
    print("Ошибка: Не удалось подключиться к координатору. Убедитесь, что координатор запущен на порту 8000")
except requests.exceptions.Timeout:
    print("Ошибка: Превышено время ожидания ответа")
except Exception as e:
    print(f"Ошибка: {e}")