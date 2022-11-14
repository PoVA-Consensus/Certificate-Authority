import hvac
import datetime
import logging
import configparser

# Set the logging level to debug
class ColourLogs(logging.Formatter):
    grey = '\x1b[38;21m'
    green = '\033[92m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.green + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define format for logs
fmt = '%(asctime)s | %(levelname)8s | %(message)s'

# Create stdout handler for logging to the console (logs all five levels)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(ColourLogs(fmt))

# Create file handler for logging to a file (logs all five levels)
today = datetime.date.today()
file_handler = logging.FileHandler('client_{}.log'.format(today.strftime('%Y_%m_%d')))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(fmt))

# Add both handlers to the logger
logger.addHandler(stdout_handler)
logger.addHandler(file_handler)

def init_server():
    '''
    This function initialises the HVAC client for Vault.
    Return:
        client: HVAC Client object
    '''
    client = hvac.Client(url = "http://127.0.0.1:8200")
    try:
        logger.info("The Vault Client has been authenticated")
        return client
    except:
        logger.error("The client is not authenticated. Check if Vault server is running.")

def setMountPoints(client):
    '''
    This function mounts the certificate issuing URL and CRL distribution point.
    Args:
        client: an initialised instance of Vault via HVAC
    '''
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        logger.debug("Read configuration for mount points")
        set_urls_response = client.secrets.pki.set_urls(
            {
            'issuing_certificates': [config['mountPoints']['issue_url']],
            'crl_distribution_points': [config['mountPoints']['crl_dist']]
            }
            )
    except Exception as e:
        logger.error(e)
    
def generateRootCA(client,commonName):
    '''
    This function generates the root CA.
    Args:
        client: an initialised instance of Vault via HVAC
        commonName: common name of the device which is the unique device ID
    '''
    setMountPoints(client)
    logger.debug("Successfully set mount points")
    try:
        
        crl_config_response = client.secrets.pki.set_crl_configuration(
        expiry='86500h',
        disable=False
        )
        
        response = client.secrets.pki.generate_root(
            type='exported',
            common_name=commonName
        )
        #print('Root CA certificate: {}'.format(response['data']['certificate']))
        f = open("rootCA.pem", "w")
        f.write(response['data']['certificate'])
        f.close()

        logger.info("Root CA certificate written to rootCA.pem")

    except Exception as e:
        logger.error(e)

def generateIntermediateCA(client,commonName):
    '''
    This function generates the intermediate Certificate Authority.
    Args:
        client: an initialised instance of Vault via HVAC
        commonName: common name of the device which is the unique device ID    
    '''
    
    response = client.secrets.pki.generate_intermediate(
    type='exported',
    common_name=commonName
    )
    logger.info("Generated CSR for Intermediate CA Certificate")
    #print('Intermediate certificate CSR: {}'.format(response['data']['csr']))
    sign_intermediate_response = client.secrets.pki.sign_intermediate(
    csr=response['data']['csr'],
    common_name=commonName
    )
    logger.info("Successfully signed Intermediate CA Certificate")
    if sign_intermediate_response['warnings'] != None:
        for warn in sign_intermediate_response['warnings']:
            logger.warning(warn)

    f = open("intermediateCA.pem", "w")
    f.write(sign_intermediate_response['data']['certificate'])
    f.close()

def readRoles(client):
    '''
    This function reads all the PKI roles that have been defined.
    Args:
        client: an initialised instance of Vault via HVAC
    '''
    list_roles = client.secrets.pki.list_roles()
    print('List of available roles: {}'.format(list_roles))

def readPKIURL(client):
    '''
    This function reads all the PKI roles tha have been defined.
    Args:
        client: an initialised instance of Vault via HVAC
    '''
    response = client.secrets.pki.read_urls()
    print('PKI urls: {}'.format(response))


def createRole(client, role_name, allow = 'false', ttl = '8794h'):
    '''
    This function creates a role.
    Args:
        client: an initialised instance of Vault via HVAC
        role_name: Name of the PKI role to be created
        allow: flag to set local host permissions with default set as false
        ttl: Time to live with default set as 8794h ~1 year
    '''
    try:
        response = client.secrets.pki.create_or_update_role(
            role_name,
            {
                'ttl': ttl,
                'allow_localhost': 'true',
                'allow_subdomains': 'true',
                'allowed_domains': ["e48BC-B809"]
            }
        )
        logger.info('Created role: %s', role_name)  
        logger.info(response)

    except Exception as e:
        logger.error(e)

def readRole(client, role_name):
    '''
    This function reads a given role.
    Args:
        client: an initialised instance of Vault via HVAC
        role_name: Name of the PKI role to be read
    '''
    try:
        read_role_response = client.secrets.pki.read_role(role_name)
        print('Role definition: {}'.format(read_role_response))
    except Exception as e:
        logger.error("Could not read role: %s", role_name)
        logger.error(e)

def listRoles(client):
    '''
    This function reads a given role.
    Args:
        client: an initialised instance of Vault via HVAC
    '''
    list_roles_response = client.secrets.pki.list_roles()
    print('List of available roles: {}'.format(list_roles_response))

def generateCertificate(client, role_name, deviceID):
    try:
        response = client.secrets.pki.generate_certificate(
            name = role_name,
            common_name = "EA7553CD-A667-48BC-B809.e48BC-B809"
            )
        print('Certificate: {}'.format(response))
    except Exception as e:
        logger.error(e)
if __name__ == '__main__':
    client = init_server()
    delete_root_response = client.secrets.pki.delete_root()

    generateRootCA(client,"e48BC-B809")
    generateIntermediateCA(client,"e48BC-B809")
    createRole(client, "Certificates")
    readRole(client, "Certificates")
    listRoles(client)
    generateCertificate(client, "Certificates", "EA7553CD-A667-48BC-B809")


