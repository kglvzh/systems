import pika
import grpc
import message_service_pb2
import message_service_pb2_grpc

def process_message(text):
    try:
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
                return "Ошибка: неизвестный тип (используй password:, translit:, email:)"
    except grpc.RpcError as e:
        return f"Ошибка gRPC: {e.details()}"

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