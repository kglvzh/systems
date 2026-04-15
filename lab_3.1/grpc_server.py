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