# Лабораторная работа № 3-1
## Тема. Организация асинхронного взаимодействия микросервисов с помощью брокера сообщений RabbitMQ

**Группа:** ЦИБ-241  
**Дата:** 15.04.2026  
**Вариант:** 3

---

## 1. Цель работы
Изучить и реализовать два ключевых подхода к взаимодействию между сервисами:
1. Синхронное прямое взаимодействие с использованием gRPC.
2. Асинхронное взаимодействие через брокер сообщений RabbitMQ.
3. Освоить развертывание инфраструктурных компонентов с помощью Docker.

# Инструменты и технологический стек:
- операционная система: Windows 11;
- язык программирования: Python 3.13.

# Библиотеки:
- grpcio, grpcio-tools (для gRPC);
- pika (клиент для RabbitMQ).

# Инфраструктура:
- Docker и Docker Compose (для запуска RabbitMQ);
- RabbitMQ (брокер сообщений).

---

## 2. Краткие теоретические сведения

**gRPC** — высокопроизводительный фреймворк для удалённого вызова процедур (RPC), использующий Protocol Buffers для определения контракта сервиса.

**RabbitMQ** — брокер сообщений, реализующий паттерн очереди. Компоненты:
- **Producer** — отправляет сообщения в очередь.
- **Queue** — буфер, хранящий сообщения.
- **Consumer** — забирает сообщения из очереди и обрабатывает их.

**Асинхронное взаимодействие** — Producer и Consumer не зависят друг от друга. Consumer может быть недоступен — сообщения накопятся в очереди и обработаются позже.

---

## Часть 3. Синхронное взаимодействие (gRPC)
На этом этапе создаются два сервиса, общающихся напрямую в режиме "запрос-ответ".

# Ход работы

**Установка зависимостей:**

```protobaf
pip install grpcio grpcio-tools
```

**Создание контракта (message_service.proto):**

```protobaf
syntax = "proto3";

package message;

service MessageService {
  rpc CheckPassword (PasswordRequest) returns (PasswordResponse);
  rpc Transliterate (TextRequest) returns (TextResponse);
  rpc ExtractEmails (TextRequest) returns (EmailListResponse);
}

message PasswordRequest {
  string password = 1;
}

message PasswordResponse {
  string strength = 1;
}

message TextRequest {
  string text = 1;
}

message TextResponse {
  string result = 1;
}

message EmailListResponse {
  repeated string emails = 1;
}
```
**Генерация кода:**

python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. message_service.proto

**Реализация сервера (grpc_server.py):**

```python
import grpc
from concurrent import futures
import re
import message_service_pb2
import message_service_pb2_grpc

class MessageService(message_service_pb2_grpc.MessageServiceServicer):
    
    def CheckPassword(self, request, context):
        password = request.password
        if len(password) >= 8 and any(c.isdigit() for c in password) and any(c in "!@#$%^&*" for c in password):
            strength = "STRONG"
        else:
            strength = "WEAK"
        return message_service_pb2.PasswordResponse(strength=strength)
    
    def Transliterate(self, request, context):
        rus_to_lat = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
            'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        result = ''.join(rus_to_lat.get(c, c) for c in request.text.lower())
        return message_service_pb2.TextResponse(result=result)
    
    def ExtractEmails(self, request, context):
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', request.text)
        return message_service_pb2.EmailListResponse(emails=emails)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    message_service_pb2_grpc.add_MessageServiceServicer_to_server(MessageService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC сервер запущен на порту 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
```
    
**Реализация клиента (grpc_client.py):**

```python
import grpc
import message_service_pb2
import message_service_pb2_grpc

def test_password():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = message_service_pb2_grpc.MessageServiceStub(channel)
        
        # Проверка STRONG пароля
        response = stub.CheckPassword(message_service_pb2.PasswordRequest(password="Qwerty123!"))
        print(f"Пароль 'Qwerty123!': {response.strength}")
        
        # Проверка WEAK пароля
        response = stub.CheckPassword(message_service_pb2.PasswordRequest(password="weak"))
        print(f"Пароль 'weak': {response.strength}")

def test_transliterate():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = message_service_pb2_grpc.MessageServiceStub(channel)
        
        response = stub.Transliterate(message_service_pb2.TextRequest(text="привет мир"))
        print(f"Транслитерация 'привет мир': {response.result}")

def test_emails():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = message_service_pb2_grpc.MessageServiceStub(channel)
        
        response = stub.ExtractEmails(message_service_pb2.TextRequest(text="Мои почты: test@mail.ru, hello@gmail.com"))
        print(f"Найденные email: {', '.join(response.emails)}")

if __name__ == '__main__':
    print("=== Тестирование gRPC сервера ===\n")
    test_password()
    print()
    test_transliterate()
    print()
    test_emails()
```

---

## Часть 4. Асинхронное взаимодействие (RabbitMQ)
В этой части добавляется брокер сообщений для развязывания сервисов. Цепочка взаимодействия: Producer -> RabbitMQ -> Consumer -> gRPC Server.

# Ход работы
RabbitMQ запускается в Docker-контейнере на локальной машине.

**Запуск контейнера:**

```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.8-management
```

**Создание Producer (producer.py): отправляет задачи в очередь task_queue.**

```python
import pika
import sys

credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

message = ' '.join(sys.argv[1:]) or "password:qwerty123"
channel.basic_publish(exchange='', routing_key='task_queue', body=message)
print(f" [x] Отправлено: '{message}'")
connection.close()
```

**Создание Consumer (consumer.py): Слушает очередь и вызывает gRPC-сервис.**

```python
import pika
import grpc
import message_service_pb2
import message_service_pb2_grpc

def process_message(text):
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = message_service_pb2_grpc.MessageServiceStub(channel)
        
        if text.startswith('password:'):
            pwd = text.split(':', 1)[1]
            response = stub.CheckPassword(message_service_pb2.PasswordRequest(password=pwd))
            return f"Результат: {response.strength}"
        
        elif text.startswith('translit:'):
            txt = text.split(':', 1)[1]
            response = stub.Transliterate(message_service_pb2.TextRequest(text=txt))
            return f"Результат: {response.result}"
        
        elif text.startswith('email:'):
            txt = text.split(':', 1)[1]
            response = stub.ExtractEmails(message_service_pb2.TextRequest(text=txt))
            return f"Результат: {', '.join(response.emails)}"
        
        else:
            return "Ошибка: неизвестный тип"

def main():
    credentials = pika.PlainCredentials('guest', 'guest')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    def callback(ch, method, properties, body):
        text = body.decode()
        print(f" [x] Получено: {text}")
        result = process_message(text)
        print(f" [✓] {result}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='task_queue', on_message_callback=callback)
    print(' [*] Ожидание сообщений...')
    channel.start_consuming()

if __name__ == '__main__':
    main()
```

---

📄 Требования к отчету
Отчет оформляется в файле readme.md в корне репозитория:

Постановка задачи. Описание решаемой проблемы.
Вариант. Номер и текст задания.
Архитектура:
Схема и описание Части 1 (gRPC).
Схема и описание Части 2 (RabbitMQ + gRPC).
Код docker-compose.yml.
Стек технологий. Перечень инструментов.
Скриншоты. Демонстрация работы (Server, Consumer, Producer, логи).

💡 Пример реализации (Вариант 30)
Задача:

gRPC-сервис с методами: AssignAB (A/B тестирование), Factorial (факториал), MostFrequentLetter (частая буква).
RabbitMQ Producer отправляет сообщения с префиксами: user_id, fact:N, freq:TEXT.
Структура проекта:

├── grpc_sync/
│   ├── message_service.proto   # Контракт с 3 методами
│   ├── grpc_server.py          # Реализация логики методов
│   └── grpc_client.py          # Тестовый клиент
├── rabbitmq_async/
│   ├── docker-compose.yml      # RabbitMQ
│   ├── producer.py             # Парсит аргументы и шлёт в очередь
│   └── consumer.py             # Читает очередь, парсит префикс, вызывает нужный метод gRPC
Алгоритм запуска:

Терминал 1: cd grpc_sync && python grpc_server.py (Запуск gRPC сервера).
Терминал 2: cd rabbitmq_async && python consumer.py (Запуск слушателя).
Терминал 3: cd rabbitmq_async && python producer.py fact:5 (Отправка задачи).
Результат в Терминале 3: [✓] Результат: 120.
