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