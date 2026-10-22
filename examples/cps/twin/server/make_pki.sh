#!/bin/sh
# Creates a small private PKI for the twin server:
#   ca.key/ca.crt          our own certificate authority (10 years)
#   server.key/server.crt  the server certificate, signed by the CA
# The device trusts only ca.crt (compiled into the firmware), so it accepts
# this one server and no other, even one with a certificate from a public CA.
#
# Usage: make_pki.sh <dir> <ip> [dns-name]
# Run it again to renew the server certificate (825 days); the CA stays.
# Keep <dir> outside the repository: the .key files are secrets.
set -e
dir=$1 ip=$2 dns=${3:-localhost}
mkdir -p "$dir" && cd "$dir"
umask 077
if [ ! -f ca.key ]; then            # keep an existing CA: the firmware trusts it
  openssl ecparam -name prime256v1 -genkey -noout -out ca.key
  openssl req -x509 -new -key ca.key -sha256 -days 3650 -out ca.crt \
    -subj "/O=Embedded Computing lecture/CN=Twin demo CA" \
    -addext "basicConstraints=critical,CA:TRUE,pathlen:0" \
    -addext "keyUsage=critical,keyCertSign,cRLSign"
fi
openssl ecparam -name prime256v1 -genkey -noout -out server.key
openssl req -new -key server.key -out server.csr -subj "/CN=$ip"
cat > ext.cnf <<END
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature
extendedKeyUsage=serverAuth
subjectAltName=IP:$ip,DNS:$dns
authorityKeyIdentifier=keyid
END
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days 825 -sha256 -extfile ext.cnf -out server.crt
rm server.csr ext.cnf
chmod 644 ca.crt server.crt
openssl verify -CAfile ca.crt server.crt
