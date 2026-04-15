import grpc
import message_service_pb2
import message_service_pb2_grpc

def test_password():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = message_service_pb2_grpc.MessageServiceStub(channel)
        
        # Тест пароля
        response = stub.CheckPassword(message_service_pb2.PasswordRequest(password="qwerty123!"))
        print(f"Пароль 'qwerty123!': {response.strength}")
        
        # Тест транслитерации
        response = stub.Transliterate(message_service_pb2.TextRequest(text="привет мир"))
        print(f"Транслитерация 'привет мир': {response.result}")
        
        # Тест email
        response = stub.ExtractEmails(message_service_pb2.TextRequest(text="Мои почты: test@mail.ru, hello@gmail.com"))
        print(f"Email'ы: {response.emails}")

if __name__ == '__main__':
    test_password()