from flask import Flask, request, jsonify
import requests
import urllib3
import ssl

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

SERVER_URLS = ['https://127.0.0.1:5001', 'https://127.0.0.1:5002']

# SSL контекст для координатора
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