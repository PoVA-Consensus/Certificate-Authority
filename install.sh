#!/bin/bash

# Usage menu for ./install.sh
show_usage() 
{
	echo "Usage: $0 [options]"
	echo "Options:"
	echo -e "-p, --path\tRequired path argument for Vault mount"
	echo -e "-h, --help\tShow this help message"
	exit 1

}

# Function to unseal vault using the seal token and login with root token
unseal_vault(){

	KEYS_FILE="vault_keys.txt"
	head -3 $KEYS_FILE|

	while read -r line; do
		vault operator unseal "$line"
	done 

	vault login $(tail -n 1 $KEYS_FILE)

}

# Function to extract the 5 tokens and root token
extract_keys(){

	INIT_FILE="vault_init.txt"
	KEYS_FILE="vault_keys.txt"
	rm $KEYS_FILE
	touch $KEYS_FILE
	while read -r line
	do
	if [[ $line == *":"* ]]; then
		string="${line##*:}"
		echo "$string" | xargs >> "$KEYS_FILE"
	fi
	done < "$INIT_FILE"
}

#Installing all the necessary dependencies for Vault
install(){
echo "Installing GPG"
sudo apt update && sudo apt install gpg
echo "Installing GPG key of HashiCorp"
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
echo "Installing HashiCorp Linux Repository"
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
echo "Installing Vault"
sudo apt update && sudo apt install vault
}

while [[ $# -gt 0 ]]; do
	key="$1"
	case $key in
			-p|--path)
			VAULT_MOUNT_PATH="$2"
			shift
			shift
			;;
			-h|--help)
			show_usage
			;;
			*)
			echo "Error: Unknown option $key"
			show_usage
			;;
	esac
done

# Checking if mount Path for Vault has been parsed as named parameter
if [ -z "$VAULT_MOUNT_PATH" ]; then
  echo "Error: Path to mount Vault is empty"
  show_usage
fi

vault --version
if [[ $? -ne 0 ]]
then
    echo "Vault has not been installed."
	install
fi

# Checking if the path is valid
if [ -d "$VAULT_MOUNT_PATH" ] 
then
    echo "$VAULT_MOUNT_PATH exists." 
else
    echo "Error: "$VAULT_MOUNT_PATH" does not exist."
    exit 1
fi

PORT=8200
# Checking if the port is available
nc -z localhost $PORT
RESULT=$?

if [ $RESULT -eq 0 ]; then
	echo "Error: Port $PORT is listening and not free"
	# Remove the next two lines in production. This is just for development process.
	# Un-comment exit 1
	# KILL_PORT=$(sudo lsof -ti:8200)
	# kill $KILL_PORT
	exit 1
fi

# Config file generation to initialise vault
BASE="127.0.0.1:"
ADDRESS="$BASE""$PORT"
API_ADDR="http://""$BASE""$PORT"

rm config.hcl
touch config.hcl
cat << EOF >> config.hcl
backend "file" {
path = "$VAULT_MOUNT_PATH"
}
listener "tcp" {
address = "$ADDRESS"
tls_disable = 1
}
api_addr = "$API_ADDR"
EOF

echo "Start Vault server with configurations"
#vault server -config=config.hcl >/dev/null 2>&1 &
vault server -config=config.hcl &
export VAULT_ADDR=$API_ADDR
sleep 1

echo "Initialising Vault"
INIT_FILE="vault_init.txt"
# 2>&1 redirects STDERR to STDOUT, so both streams are combined into one. 
# The output is then piped to the sed command, which removes all color codes (using a regular expression) from the output.
vault operator init 2>&1 | sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g" > $INIT_FILE
INIT_STATUS_BASH="${PIPESTATUS[0]}" 
INIT_STATUS_ZSH="${pipestatus[1]}" 
#echo $INIT_STATUS_BASH $INIT_STATUS_ZSH 
if [ $INIT_STATUS_BASH -eq 2 ] || [ $INIT_STATUS_ZSH -eq 2 ]; then
	echo "Vault already initialised"
	unseal_vault
else
	extract_keys
	unseal_vault
fi

vault secrets enable pki
vault secrets tune -max-lease-ttl=87600h pki
export VAULT_ADDR='http://127.0.0.1:8200'
