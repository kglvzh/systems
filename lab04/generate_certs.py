from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime

def gen_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )

def save_key(key, filename):
    with open(filename, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    print(f"Created: {filename}")

def save_cert(cert, filename):
    with open(filename, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"Created: {filename}")

# 1. CA
print("1. Creating CA...")
ca_key = gen_key()
ca_subj = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"RU"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"LabCA"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"MyCA"),
])
ca_cert = x509.CertificateBuilder().subject_name(ca_subj).issuer_name(ca_subj).public_key(ca_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)).add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True).sign(ca_key, hashes.SHA256(), default_backend())
save_key(ca_key, "ca_key.pem")
save_cert(ca_cert, "ca_cert.pem")

# 2. Server
print("2. Creating Server certificate...")
server_key = gen_key()
server_subj = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"RU"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"LabCA"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
])
san = x509.SubjectAlternativeName([x509.DNSName(u"localhost"), x509.DNSName(u"127.0.0.1")])
server_cert = x509.CertificateBuilder().subject_name(server_subj).issuer_name(ca_cert.subject).public_key(server_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)).add_extension(san, critical=False).add_extension(x509.ExtendedKeyUsage([x509.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False).sign(ca_key, hashes.SHA256(), default_backend())
save_key(server_key, "server_key.pem")
save_cert(server_cert, "server_cert.pem")

# 3. Client
print("3. Creating Client certificate...")
client_key = gen_key()
client_subj = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"RU"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"LabCA"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"client"),
])
client_cert = x509.CertificateBuilder().subject_name(client_subj).issuer_name(ca_cert.subject).public_key(client_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)).add_extension(x509.ExtendedKeyUsage([x509.ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False).sign(ca_key, hashes.SHA256(), default_backend())
save_key(client_key, "client_key.pem")
save_cert(client_cert, "client_cert.pem")

print("Done. All certificates created.")