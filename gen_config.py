import configparser

config_file = configparser.ConfigParser()

config_file.add_section("mountPoints")
config_file.set("mountPoints", "ISSUE_URL", "http://127.0.0.1:8200/v1/pki/ca")
config_file.set("mountPoints", "CRL_DIST", "http://127.0.0.1:8200/v1/pki/crl")
config_file.set("mountPoints", "X_TOKEN", "hvs.LIHlZAB59EnMWTJFIPaOo6qy")
config_file.set("mountPoints", "ISSUE_CERT", "http://127.0.0.1:8200/v1/pki/issue/")
config_file.set("mountPoints", "ROLE", "Certificates")
config_file.set("mountPoints", "CA", "e48BC-B809")

with open(r"config.ini", 'w') as configfileObj:
    config_file.write(configfileObj)
    configfileObj.flush()
    configfileObj.close()

print("Config file 'config.ini' created")

read_file = open("config.ini", "r")
content = read_file.read()
print("Content of the config file are:")
print(content)
read_file.flush()
read_file.close()