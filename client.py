import hvac
import datetime
import logging
import configparser
import requests
import json
import argparse
import sys

# Set the logging level to debug
class ColourLogs(logging.Formatter):
    grey = '\x1b[38;21m'
    green = '\033[92m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'
    blue = '\033[34m'

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.blue + self.fmt + self.reset,
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
file_handler = logging.FileHandler('logs/client_{}.log'.format(today.strftime('%Y_%m_%d')))
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(fmt))

# Add both handlers to the logger
logger.addHandler(stdout_handler)
logger.addHandler(file_handler)

def init_server(config):
    '''
    This function initialises the HVAC client for Vault.
    Args:
        config: a configparser object
    Return:
        client: HVAC Client object
    '''
    client = hvac.Client(url = config['mountPoints']['INIT_URL'])
    try:
        logger.info("The Vault Client has been authenticated")
        return client
    except:
        logger.error("The client is not authenticated. Check if Vault server is running.")

def read_config():
    '''
    This function reads the configuration file and returns the configparser object.
    Return:
        config: a configparser object
    '''
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        logger.debug("Successfully read config file")
        return config
    except Exception as e:
        logger.error("Cannot read config file")
        logger.error(e)

def setMountPoints(config, client):
    '''
    This function mounts the certificate issuing URL and CRL distribution point.
    Args:
        config: a configparser object
        client: an initialised instance of Vault via HVAC
    '''
    try:
        set_urls_response = client.secrets.pki.set_urls(
            {
            'issuing_certificates': config['mountPoints']['ISSUE_URL'],
            'crl_distribution_points': config['mountPoints']['CRL_DIST']
            }
            )
    except Exception as e:
        logger.error("Cannot set Mount Points for Issue URL and CRL Distribution")
        logger.error(e)
    
def generateRootCA(config, client, commonName):
    '''
    This function generates the root CA.
    Args:
        config: a configparser object
        client: an initialised instance of Vault via HVAC
        commonName: common name of the device which is the unique device ID
    '''
    setMountPoints(config, client)
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

def generate_intermediate_CA(client, commonName):
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

def read_roles(client):
    '''
    This function reads all the PKI roles that have been defined.
    Args:
        client: an initialised instance of Vault via HVAC
    '''
    list_roles = client.secrets.pki.list_roles()
    #print('List of available roles: {}'.format(list_roles))

def readPKIURL(client):
    '''
    This function reads all the PKI roles tha have been defined.
    Args:
        client: an initialised instance of Vault via HVAC
    '''
    response = client.secrets.pki.read_urls()
    #print('PKI urls: {}'.format(response))

def create_role(client, role_name, allowed, allow = 'false', ttl = '8794h'):
    '''
    This function creates a role.
    Args:
        client: an initialised instance of Vault via HVAC
        role_name: Name of the PKI role to be created
        allowed: domain that is allowed by the role
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
                'allowed_domains': [allowed]
            }
        )
        logger.info('Created role: %s', role_name)  
        logger.info(response)

    except Exception as e:
        logger.error(e)

def read_role(client, role_name):
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

def list_roles(client):
    '''
    This function reads a given role.
    Args:
        client: an initialised instance of Vault via HVAC
    '''
    list_roles_response = client.secrets.pki.list_roles()
    print('List of available roles: {}'.format(list_roles_response))

def generate_certificate(config, role_name, issue_url, payload_path):
    '''
    This function generates the certificate for a given payload and role.
    Args:
        config: a configparser object
        role_name: The Vault role under which the certificate is generated
        issue_url: The Vault API issue point
        payload_path: Path to payload to fetch details for certifcate generation
    '''
    try:
        
        headers = {
            'X-Vault-Token': config['mountPoints']['X_TOKEN'],
            'Content-Type': 'application/x-www-form-urlencoded',
            }

        try:
            with open(payload_path) as f:
                data = f.read().replace('\n', '')
        except Exception as e:
            logger.error(e)
            logger.error("Aborted Device certificate generation")
            sys.exit()
        
        data_json = json.loads(data)
        #print(data_json['common_name'])

        response = requests.post(issue_url + role_name, headers=headers, data=data)
        #print(response.content)
        response_dict = json.loads(str(response.content, 'UTF-8'))

        #print(response_dict['data']['certificate'])
        f = open(data_json['common_name'] + ".pem", "w")
        f.write(response_dict['data']['certificate'])
        f.close()

        logger.info(f"Certificate written to {data_json['common_name']}.pem")

        f = open(data_json['common_name'] + ".key", "w")
        f.write(response_dict['data']['private_key'])
        f.close()

        logger.info(f"Private Key written to {data_json['common_name']}.key")

    except Exception as e:
        logger.error(e)


if __name__ == '__main__':

    config = read_config()
    
    try:
        client = init_server(config)
        delete_root_response = client.secrets.pki.delete_root()
    except Exception as e:
        logger.error(e)
        sys.exit()

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", required = True, type = str, help = "Enter the path to the file containing details for generating the device certificate")
    args = parser.parse_args()
    payload_path = args.s

    role = config['mountPoints']['ROLE']
    root_issuer = config['mountPoints']['CA']
    cert_issue = config['mountPoints']['ISSUE_CERT']
    generateRootCA(config, client, root_issuer)
    generate_intermediate_CA(client, root_issuer)
    create_role(client, role, root_issuer)
    #read_role(client, role)
    #list_roles(client)
    generate_certificate(config, role, cert_issue, payload_path)
