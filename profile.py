import hashlib
import json
import argparse

def generate_device_id (MAC_addr, manufacturer_name, device_name):
    '''
    This function returns the SHA256 hashed value of the attributes passed as args.
    Args:
        MAC_addr (str): The MAC address of the device
        manufacturer_name (str): The device manufacturer name
        device_name (str): The device name
    Return:
        The SHA256 hashed result of the attributes concatenated
    '''
    attributes_concatenate = str(MAC_addr).lower() + str(manufacturer_name).lower() + str(device_name).lower()
    device_id = hashlib.sha256(attributes_concatenate.encode()).hexdigest()
    return device_id

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
    device_id = generate_device_id(MAC_addr, manufacturer_name, device_name)[0:20]
    print(device_id[0:8].upper() + "-" + device_id[8:12].upper() + "-" + device_id[12:16].upper() + "-" + device_id[16:].upper())
    #print(generate_device_id(MAC_addr, manufacturer_name, device_name)[0:20])