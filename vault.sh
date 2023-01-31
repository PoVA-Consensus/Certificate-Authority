#!usr/bin/ bash

head -3 "keys.txt"|

# export VAULT_ADDR='http://127.0.0.1:8200' is an issue

while read -r line; do
    vault operator unseal "$line"
done 

vault login $(tail -n 1 "keys.txt")
#vault secrets enable pki
vault secrets tune -max-lease-ttl=87600h pki