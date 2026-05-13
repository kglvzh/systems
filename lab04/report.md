# Лабораторная работа №4

## Выполнила

* ФИО: Гловели Джемма Камрановна
* Группа: ЦИБ-241
* Вариант: 3

---

# Тема работы

Разработка распределённой защищённой системы с использованием:

* HTTPS
* mTLS
* PKI
* симметричного шифрования Fernet
* механизма отказоустойчивости (Failover)
* обработки ошибок на сервере и клиенте

---

# Цель работы

Реализовать защищённое взаимодействие между клиентом и сервером с использованием HTTPS и сертификатов X.509, обеспечить шифрование данных алгоритмом Fernet, реализовать механизм автоматического переключения на резервный сервер при отказе основного, а также добавить расширенную обработку ошибок на стороне сервера и клиента.

---

# Индивидуальное задание

## Вариант 3 — Обработка ошибок

Реализована расширенная обработка ошибок:

| Тип ошибки | Действие сервера | Код ответа |
|------------|------------------|-------------|
| Неверный Content-Type | Возврат ошибки с пояснением | 400 |
| Отсутствие поля data | Возврат ошибки с пояснением | 400 |
| Пустые данные | Возврат ошибки с пояснением | 400 |
| Ошибка расшифровки (неверный ключ) | Возврат ошибки с пояснением | 422 |
| Внутренняя ошибка сервера | Возврат ошибки с кодом 500 | 500 |
| Недоступность всех серверов | Координатор возвращает ошибку 503 | 503 |

Клиент обрабатывает следующие ошибки:
- Ошибка подключения к координатору
- Таймаут ожидания ответа
- Ошибки сервера с расшифровкой сообщения

---

# Используемые технологии

* Python 3.8+
* Flask
* requests
* cryptography
* OpenSSL

---

# Архитектура системы

```
Клиент (client.py) ---> Координатор (coordinator.py) ---> Сервер 1 (5001)
                                      |
                                      +---> Сервер 2 (5002)
```

* Клиент общается с координатором по HTTPS + mTLS
* Координатор общается с серверами по HTTPS + mTLS
* При отказе сервера 1 координатор переключается на сервер 2

---

# Структура проекта

```
lab_04/
│
├── ca_cert.pem
├── ca_key.pem
├── server_cert.pem
├── server_key.pem
├── client_cert.pem
├── client_key.pem
├── server.py
├── client.py
├── coordinator.py
├── generate_key.py
├── make_certs.bat (или generate_certs.py)
├── encryption_key.txt
├── requirements.txt
└── README.md
```

---

# Настройка окружения

## 1. Создание виртуального окружения (Windows)

```powershell
py -m venv venv
venv\Scripts\activate
```

## 2. Установка зависимостей

```powershell
pip install flask cryptography requests
```

---

# requirements.txt

```
flask
cryptography
requests
```

---

# Генерация сертификатов (PKI)

## Создание сертификатов через OpenSSL

```batch
make_certs.bat
```

Будут созданы:

* ca_cert.pem — сертификат центра сертификации (CA)
* ca_key.pem — ключ CA
* server_cert.pem — сертификат сервера
* server_key.pem — ключ сервера
* client_cert.pem — сертификат клиента
* client_key.pem — ключ клиента

---

# Генерация ключа Fernet

```powershell
py generate_key.py
```

Будет создан файл:

```
encryption_key.txt
```

---

# Исходные коды

## Сервер (server.py)

```python
import ssl
import sys
import logging
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001

try:
    with open('encryption_key.txt', 'rb') as f:
        cipher = Fernet(f.read())
    logger.info("Ключ Fernet загружен")
except Exception as e:
    logger.error(f"Ошибка загрузки ключа Fernet: {e}")
    sys.exit(1)

try:
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain('server_cert.pem', 'server_key.pem')
    ssl_context.load_verify_locations('ca_cert.pem')
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    logger.info("SSL контекст настроен")
except Exception as e:
    logger.error(f"Ошибка загрузки сертификатов: {e}")
    sys.exit(1)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'port': port}), 200

@app.route('/api/data', methods=['POST'])
def process_data():
    try:
        if not request.is_json:
            logger.error("Запрос не в формате JSON")
            return jsonify({'error': 'Неверный формат запроса', 'code': 'INVALID_CONTENT_TYPE', 'message': 'Content-Type должен быть application/json'}), 400
        
        data = request.get_json()
        
        if data is None or 'data' not in data:
            logger.error("Отсутствует поле 'data'")
            return jsonify({'error': 'Неверный запрос', 'code': 'MISSING_FIELD', 'message': 'Отсутствует обязательное поле data'}), 400
        
        encrypted_data = data['data']
        
        if not encrypted_data:
            logger.error("Пустые зашифрованные данные")
            return jsonify({'error': 'Неверный запрос', 'code': 'EMPTY_DATA', 'message': 'Поле data не может быть пустым'}), 400
        
        try:
            decrypted_bytes = cipher.decrypt(encrypted_data.encode())
            decrypted_text = decrypted_bytes.decode()
            logger.info(f"Данные успешно расшифрованы")
        except Exception as e:
            logger.error(f"Ошибка расшифровки: {e}")
            return jsonify({'error': 'Ошибка расшифровки', 'code': 'DECRYPTION_FAILED', 'message': f'Не удалось расшифровать данные: {str(e)}'}), 422
        
        result = {
            'status': 'success',
            'decrypted_message': decrypted_text,
            'server_port': port,
            'message': 'Данные успешно обработаны'
        }
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера', 'code': 'INTERNAL_ERROR', 'message': str(e)}), 500

if __name__ == '__main__':
    print(f"Сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port, ssl_context=ssl_context, debug=False)
```

## Координатор (coordinator.py)

```python
from flask import Flask, request, jsonify
import requests
import urllib3
import ssl

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

SERVER_URLS = ['https://127.0.0.1:5001', 'https://127.0.0.1:5002']

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('server_cert.pem', 'server_key.pem')
ssl_context.load_verify_locations('ca_cert.pem')
ssl_context.verify_mode = ssl.CERT_REQUIRED

@app.route('/api/data', methods=['POST'])
def handle_request():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Пустой запрос', 'code': 'EMPTY_REQUEST'}), 400
    
    for url in SERVER_URLS:
        try:
            response = requests.post(
                f"{url}/api/data",
                json=data,
                verify='ca_cert.pem',
                cert=('client_cert.pem', 'client_key.pem'),
                timeout=5
            )
            
            if response.status_code == 200:
                return jsonify(response.json()), 200
            else:
                print(f"Сервер {url} вернул ошибку: {response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"Ошибка подключения к {url}: {e}")
            continue
        except requests.exceptions.Timeout:
            print(f"Таймаут при подключении к {url}")
            continue
        except Exception as e:
            print(f"Неизвестная ошибка при подключении к {url}: {e}")
            continue
    
    return jsonify({'error': 'Все серверы недоступны', 'code': 'ALL_SERVERS_DOWN'}), 503

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running', 'message': 'Координатор работает'}), 200

if __name__ == '__main__':
    print("Координатор запущен на порту 8000 (HTTPS)")
    app.run(host='0.0.0.0', port=8000, ssl_context=ssl_context, debug=False)
```

## Клиент (client.py)

```python
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
```

---

# Запуск системы

## Терминал 1 — Сервер 1

```powershell
py server.py 5001
```

## Терминал 2 — Сервер 2

```powershell
py server.py 5002
```

## Терминал 3 — Координатор

```powershell
py coordinator.py
```

## Терминал 4 — Клиент

```powershell
py client.py
```

---

# Реализованный функционал

## HTTPS

Передача данных между компонентами выполняется по HTTPS. Координатор и серверы запускаются с SSL контекстом.

## mTLS

Используются клиентские и серверные сертификаты X.509. Сервер проверяет клиентский сертификат, клиент проверяет серверный.

## Fernet-шифрование

Полезная нагрузка дополнительно шифруется алгоритмом Fernet.

## Failover

Координатор автоматически перенаправляет запросы на резервный сервер при отказе основного. При недоступности сервера 5001 запрос уходит на сервер 5002.

## Обработка ошибок (Вариант 3)

Реализована расширенная обработка ошибок на сервере и клиенте с возвратом понятных кодов и сообщений на русском языке.

---

# Демонстрация работы

## 1. Успешный запрос

<img width="767" height="362" alt="image" src="https://github.com/user-attachments/assets/6c760b2a-31d7-44b7-9a8b-75d459720e1b" />


На скриншоте виден успешный ответ от сервера с кодом 200 и расшифрованным сообщением.

## 2. Демонстрация отказоустойчивости (Failover)

<img width="761" height="397" alt="image" src="https://github.com/user-attachments/assets/b85d022d-f5af-422d-9169-aaef4dad79b7" />


На скриншоте видно:
- Остановка сервера 5001 (Ctrl+C)
- Ошибка подключения к серверу 5001 в логах координатора
- Успешный ответ от сервера 5002

## 3. Демонстрация обработки ошибок

Для тестирования обработки ошибок разработан отдельный скрипт [test_errors.py](lab04/test_errors.py).

<img width="767" height="496" alt="image" src="https://github.com/user-attachments/assets/de64e450-f8c6-4a43-a20e-35ba4d42226f" />


На скриншоте виден пример ошибки с соответствующим кодом ответа и сообщением на русском языке.

---

# Принцип работы системы

1. Клиент вводит сообщение.
2. Сообщение шифруется алгоритмом Fernet.
3. Клиент отправляет зашифрованные данные на координатор по HTTPS + mTLS.
4. Координатор принимает запрос.
5. Координатор пересылает запрос на основной сервер (5001) по HTTPS + mTLS.
6. Сервер проверяет корректность запроса (Content-Type, наличие поля data).
7. Сервер расшифровывает сообщение.
8. Сервер формирует ответ.
9. Ответ возвращается клиенту.
10. При недоступности основного сервера координатор автоматически переключается на резервный сервер (5002).

---

# Вывод

В ходе лабораторной работы была разработана распределённая защищённая система, поддерживающая полную инфраструктуру открытых ключей (PKI) с использованием сертификатов X.509, обеспечивающую защищённое соединение по протоколу HTTPS с взаимной аутентификацией (mTLS) между всеми компонентами, а также дополнительное симметричное шифрование передаваемых данных алгоритмом Fernet. В систему встроен механизм отказоустойчивости Failover, позволяющий координатору автоматически перенаправлять запросы на резервный сервер при недоступности основного. Кроме того, в соответствии с вариантом 3 реализована расширенная обработка ошибок на стороне сервера и клиента с возвратом подробных сообщений на русском языке и соответствующих HTTP-кодов.

Система успешно обеспечивает защищённую передачу данных, автоматическое переключение на резервный сервер при отказе основного, а также корректную обработку ошибок с понятными сообщениями для пользователя.
