#!usr/bin/env bash

head -3 "keys.txt"|

while read -r line; do
    vault operator unseal "$line"
done <$file

vault login $(tail -n 1 "keys.txt")
#vault secrets enable pki
vault secrets tune -max-lease-ttl=8760h pki