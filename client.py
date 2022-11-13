import hvac
import logging
# Set the logging level to debug
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    )

def init_server():
    '''
    This function initialises the HVAC client for Vault.
    Return:
        client: HVAC Client object
    '''
    client = hvac.Client(url = "http://127.0.0.1:8200")
    try:
        logging.info(client.is_authenticated())
        return client
    except:
        logging.error("The client is not authenticated. Check if Vault server is running.")

def generateRootCA(client):
    '''
    This function generates the root CA.
    '''
    response = client.secrets.pki.generate_root(
        type='exported',
        common_name='IoT CA'
    )
    print('Root CA certificate: {}'.format(response['data']['certificate']))

client = init_server()
generateRootCA(client)
