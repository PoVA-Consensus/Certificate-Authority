import hashlib
import json
import argparse
from Crypto.Hash import keccak

def keccak_hash(MAC_addr, manufacturer_name, device_name):
    """
    Computes the Keccak hash of a string using the sha3 module in the Crypto package.
    Args:
        MAC_addr (str): The MAC address of the device
        manufacturer_name (str): The device manufacturer name
        device_name (str): The device name
    Return:
        The Keccak hashed result of the attributes concatenated
    """
    attributes_concatenate = str(MAC_addr).lower() + str(manufacturer_name).lower() + str(device_name).lower()
    hash_object = keccak.new(digest_bits=256)
    hash_object.update(attributes_concatenate.encode('utf-8'))
    hex_digest = hash_object.hexdigest()
    return hex_digest

def read_details(file_path):
    '''
    This function takes the path containing the JSON file with details of the device 
    Args:
        file_path (str): The path to the file
    Return:
        The extracted attributes from JSON
    '''
    file = open(file_path)
    details = json.loads(file.read())
    #print(details['MAC_address'])
    return details["MAC_address"], details["Manufacturer_name"], details["Device_name"] 


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", required = True, type = str, help = "Path to JSON file containing details of device")
    args = parser.parse_args()
    payload_path = args.f
    MAC_addr, manufacturer_name, device_name = read_details(payload_path)
    device_id = keccak_hash(MAC_addr, manufacturer_name, device_name)
    print(device_id)
    #print(generate_device_id(MAC_addr, manufacturer_name, device_name)[0:20])