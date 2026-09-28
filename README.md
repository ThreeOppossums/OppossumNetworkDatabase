# OppossumNetworkDatabase
> Database of the Network (currently contains: Accounts)

---

## Overview

- Python
- DockerCompose
- MySql

## Documentations
*commands and code in order of usage*

> 20/08/2026
> Setting up Firewall, allow ssh and create whitelist

updated the Stystem

```bash
sudo apt install ufw
ufw disable

sudo ufw default deny incoming

sudo ufw default allow outgoing

sudo ufw allow 22/tcp
```

> 20/08/2026
> install and enable docker

```bash
sudo apt update && sudo apt install -y docker.io docker-compose

systemctl enable --now docker
```

> 20/08/2026
> setting up MySql in docker for accounts

Wrote the [/accounts/docker-compose.yml](/accounts/docker-compose.yml) and put important data into the .env
created folder for thy python api for later

```bash
docker-compose up -d
```

> 21/08/2026
> created test api

directory: [/test_api](/test_api)

```bash
docker-compose up -d --build
#used --build to rebuild the docker Image cause I changed some python packages
```

> 23/08/2026
> created register api

directory: [/accounts/API](/accounts/API)

```bash
#navigate into "accounts" folder
docker-compose up -d --build --build API
#use 'API' to restart just the python-api.
```

> 31/08/2026
> added docker network and https for safe communication

```bash
docker network create server-internal-communication
```

Updated all docker-compose files to use the internal network. 
Removed listening to external Ports(bc it uses apache as a reverse-proxy)

created certificate:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt -subj "/CN=IPADRESS"

chmod 600 server.key
chmod 644 server.crt
```

added bash-script "update-certificate.sh" to renew certificate for https (not visible cause of safety reasons)
added bash-script to chmod:

```bash
chmod +x /root/OppossumNetworkDatabase/bash-scripts/update_certificate/update_certificate.sh

crontab -e
#installed cronjob because for some reason it wasnt on the server:
sudo apt update && sudo apt install -y cron nano

#opened it again and chose nano
crontab -e
1
```

added the following:

0 1 1,7,14,21,28 * * /root/OppossumNetworkDatabase/bash-scripts/update_certificate/update_certificate.sh 2>> /root/OppossumNetworkDatabase/bash-scripts/update_certificate/logs/error.log 1>> /root/OppossumNetworkDatabase/bash-scripts/update_certificate/logs/execute.log

```bash
crontab -l
#everything looks fine goodnight
```

restarted all containers
