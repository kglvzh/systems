from cryptography.fernet import Fernet

def generate_encryption_key():
    key = Fernet.generate_key()
    with open('encryption_key.txt', 'wb') as f:
        f.write(key)
    print("Key generated and saved to encryption_key.txt")
    return key

if __name__ == '__main__':
    generate_encryption_key()