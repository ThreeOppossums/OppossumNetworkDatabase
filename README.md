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
docker-compose up -d --build
#used --build to rebuild the docker Image cause I changed some python packages
```