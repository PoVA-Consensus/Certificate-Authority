import sys
import re
from OpenSSL import crypto
import argparse

def verify_certificate_chain(cert_path, trusted_path):
    '''
    This function verifies if a given certificate traces to the root certificate in the chain of trust.
    Args:
        cert_path: Path to the certificate to be verified
        trusted_path: Path to the CA PEM bundle
    Return: bool based on verification
    '''
    cert_file = open(cert_path, 'r')
    cert_data = cert_file.read()
    certificate = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)

    trust_file = open(trusted_path, 'r')
    trust_data = trust_file.read()

    # To extract all the certificates in the chain of trust via the regex
    list_trust = re.findall("(-----BEGIN CERTIFICATE-----(.|\n)+?(?=-----END CERTIFICATE-----)+)", trust_data)

    #Creating a certificate store and adding all the trusted certificates from the chain
    
    try:
        store = crypto.X509Store()

        for _cert in list_trust:
            # appending the footer to the certificate as that was not captured via the regex
            cert = _cert[0] + "-----END CERTIFICATE-----"
            client_certificate = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
            store.add_cert(client_certificate)
        
        # Create a certificate context using the store and the loaded certificate
        store_ctx = crypto.X509StoreContext(store, certificate)
        
        # To verify the certificate
        # Returns None if the certificate can be validated
        store_ctx.verify_certificate()
        return True

    except Exception as e:
        print(e)
        return False
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", required = True, type = str, help = "Enter the path to the PEM encoded certificate to be verified")
    parser.add_argument("-v", required = True, type = str, help = "Path to the trusted chain")
    args = parser.parse_args()
    cert_path = args.c
    trusted_path = args.v

    if not verify_certificate_chain(cert_path, trusted_path):
        print("Invalid certificate")
        sys.exit(1)

    print("Valid certificate")
    sys.exit(0)