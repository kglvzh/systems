import pika
import sys

credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=credentials))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

if len(sys.argv) < 2:
    message = "password:qwerty123!"
else:
    message = ' '.join(sys.argv[1:])

channel.basic_publish(exchange='', routing_key='task_queue', body=message)
print(f" [x] Отправлено: '{message}'")
connection.close()