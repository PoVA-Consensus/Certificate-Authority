# Certificate-Authority
Install GPG which is a free implementation of OpenPGP. This permits us to sign and encrypt data. GPG offers a versatile key management.
```console
pavithra@client:~/Desktop/Cert-Auth$ sudo apt update && sudo apt install gpg
```

Add the GPG key of HashiCorp
```console
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg >/dev/null
```

Verify the fingerprint of this key
```console
pavithra@client:~/Desktop/Cert-Auth$ gpg --no-default-keyring --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg --fingerprint
```
```console
/usr/share/keyrings/hashicorp-archive-keyring.gpg
-------------------------------------------------
pub   rsa4096 2020-05-07 [SC]
      E8A0 32E0 94D8 EB4E A189  D270 DA41 8C88 A321 9F7B
uid           [ unknown] HashiCorp Security (HashiCorp Package Signing) <security+packaging@hashicorp.com>
sub   rsa4096 2020-05-07 [E]
```
The fingerprint must match E8A0 32E0 94D8 EB4E A189 D270 DA41 8C88 A321 9F7B

Add the offical HashiCorp Linux repository

```console
pavithra@client:~/Desktop/Cert-Auth$ echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
```

Install Vault
```console
pavithra@client:~/Desktop/Cert-Auth$ sudo apt update && sudo apt install vault
```

In order to check if you have installed Vault, run Vault. All the common commands should be visible via the help menu.

```console
pavithra@client:~/Desktop/Cert-Auth$ vault
```

Vault can be run in a pre-configured dev mode. Here, Vault will run entirely in-memory and can be unsealed with a single unseal key which is not recommended for a production environment owing to security reasons.

A Vault server can be set using a config file. The storage and listener parameters will be specified here along with the API address. The storage parameter helps us specify where the storage backend should be in order to store Vault data. Listener parameter enables us to  specify the host and port.

```console
pavithra@client:~/Desktop/Cert-Auth$ cat config.hcl 
backend "file" {
path = "/home/pavithra/Desktop/Cert-Auth"
}
listener "tcp" {
address = "127.0.0.1:8200"
tls_disable = 1
}
api_addr = "http://127.0.0.1:8200"
```

Start the Vault server with the aforementioned configurations.
```console
pavithra@client:~/Desktop/Cert-Auth$ vault server -config=config.hcl
```
The vault server will start and all log data will be streamed. In case of error in initializing a TCP listener due to bind address already being in use, proceed to kill the process.

```console
pavithra@client:~/Desktop/Cert-Auth$ sudo lsof -ti:8200
pavithra@client:~/Desktop/Cert-Auth$ kill <pid>
```

In another terminal, initialise Vault.
```console
pavithra@client:~/Desktop/Cert-Auth$ export VAULT_ADDR='http://127.0.0.1:8200'
pavithra@client:~/Desktop/Cert-Auth$ vault operator init
```

You will be given 5 unseal keys and a root token. In order to unseal Vault, you will have to provide at least 3/5 unseal keys as 3 is set as the threshold by default.
Store the above in another file for later use. 
**Note** : If you lose these keys, your Vault storage will prove to be useless.

**Sealed state:** Here, Vault knows the location of where the encrypted data is stored and how to access it but cannot decrypt it.

Vault utilises `Shamir's Secret Sharing` algorithm. The actual key is split into N parts and K of them would be required to re-generate the key back. The N key parts are known as Unseal key.

When the server is initialised with the init command, the master key is split into 5 parts, and 3 of them will be used via the `unseal` command to unseal. Proceed to do this 3 times, to unseal the Vault server.

Log in to Vault via the root token.
```console
pavithra@client:~/Desktop/Cert-Auth$ vault login <root-token>
```
```console
Success! You are now authenticated. The token information displayed below
is already stored in the token helper. You do NOT need to run "vault login"
again. Future Vault requests will automatically use this token.
```
Enable the PKI secrets engine of Vault.
```console
pavithra@client:~/Desktop/Cert-Auth$ vault secrets enable pki
Success! Enabled the pki secrets engine at: pki/
pavithra@client:~/Desktop/Cert-Auth$ vault secrets tune -max-lease-ttl=8760h pki
Success! Tuned the secrets engine at: pki/
```







