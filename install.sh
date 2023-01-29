#!/bin/bash

while getopts ":a:p::h" opt; do
	case $opt in
		h) echo "usage $0 -p -h"
		echo -e "-h \tDisplay the help menu"
		echo -e "-p \tPath to mount Vault"
		exit 1
		;;
		p) VAULT_MOUNT_PATH="$OPTARG"
		;;
		\?) echo "Invalid option -$OPTARG" >&2
		exit 1
		;;
	esac

	case $OPTARG in
		-*) echo "Option $opt needs a valid argument"
		exit 1
		;;
	esac
done

#echo "Installing GPG"
#sudo apt update && sudo apt install gpg
#echo "Installing GPG key of HashiCorp"
#wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
#echo "Installing HashiCorp Linux Repository"
#echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
#echo "Installing Vault"
#sudo apt update && sudo apt install vault

# vault --version
# if [[ $? -ne 0 ]]
# then
#     echo "Vault has not been installed."
# fi

if [ -z "$VAULT_MOUNT_PATH" ]
then
	echo "Path to mount Vault is empty"
	exit 1

fi

if [ -d "$VAULT_MOUNT_PATH" ] 
then
    echo "$VAULT_MOUNT_PATH exists." 
else
    echo "Error: "$VAULT_MOUNT_PATH" does not exist."
    exit 1
fi

PORT=8200

nc -z localhost $PORT
RESULT=$?

if [ $RESULT -eq 0 ]; then
	echo "Error: Port $PORT is listening and not free"
fi

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
