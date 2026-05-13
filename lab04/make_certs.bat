@echo off
echo Generating CA...
openssl req -x509 -newkey rsa:4096 -nodes -keyout ca_key.pem -out ca_cert.pem -config ca.conf -extensions ca_ext -days 365

echo Generating Server CSR...
openssl req -newkey rsa:4096 -nodes -keyout server_key.pem -out server.csr -config server.conf

echo Signing Server Cert...
openssl x509 -req -in server.csr -CA ca_cert.pem -CAkey ca_key.pem -CAcreateserial -out server_cert.pem -extfile server.conf -extensions server_ext -days 365

echo Generating Client CSR...
openssl req -newkey rsa:4096 -nodes -keyout client_key.pem -out client.csr -subj "/CN=client"

echo Signing Client Cert...
openssl x509 -req -in client.csr -CA ca_cert.pem -CAkey ca_key.pem -CAcreateserial -out client_cert.pem -days 365

del server.csr client.csr ca_cert.srl
echo Done.