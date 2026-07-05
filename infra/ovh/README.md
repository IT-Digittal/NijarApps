# Despliegue en producción — VPS OVHcloud

Guía de instalación de la Plataforma DTI Níjar completa (API, PostgreSQL/PostGIS,
Redis, MQTT, workers y chatbot Rasa) en un único VPS de OVH.

**Servidor de referencia**: OVH VPS-4 (8 vCores, 24 GB RAM, 200 GB NVMe),
Ubuntu 24.04/26.04 LTS, con las opciones *Snapshot* y *Backup automático* activadas.

## Contenido de este directorio

| Fichero | Descripción |
|---|---|
| `docker-compose.prod.yml` | Stack completo de producción (solo Caddy expone puertos) |
| `Caddyfile` | Reverse proxy con TLS automático de Let's Encrypt |
| `mosquitto.prod.conf` | Broker MQTT con autenticación obligatoria |
| `.env.production.example` | Plantilla de variables de entorno de producción |

## 1. DNS

Antes de nada, crear un registro `A` del dominio (p. ej. `dti.nijar.es`)
apuntando a la IP pública del VPS. Caddy lo necesita para emitir el certificado
TLS en el primer arranque.

## 2. Acceso y endurecimiento básico del VPS

Conectar con el usuario inicial que envía OVH por email y asegurar el acceso:

```bash
# Crear usuario de trabajo con sudo
adduser deploy && usermod -aG sudo deploy

# Copiar tu clave pública SSH
mkdir -p /home/deploy/.ssh
nano /home/deploy/.ssh/authorized_keys   # pegar la clave pública
chown -R deploy:deploy /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys

# Deshabilitar acceso root y contraseñas por SSH
sudo nano /etc/ssh/sshd_config
#   PermitRootLogin no
#   PasswordAuthentication no
sudo systemctl restart ssh

# Actualizaciones automáticas de seguridad
sudo apt update && sudo apt upgrade -y
sudo apt install -y unattended-upgrades fail2ban
```

## 3. Firewall

Solo deben quedar abiertos SSH y HTTP/HTTPS:

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirección a HTTPS + reto ACME)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

> PostgreSQL (5432), Redis (6379), MQTT (1883) y Rasa (5005) **no** se abren:
> solo existen dentro de la red interna de Docker. Si en el futuro los sensores
> IoT publican desde Internet, abrir únicamente `8883/tcp` (MQTT sobre TLS) y
> activar el listener correspondiente en `mosquitto.prod.conf`.

Activar también el **firewall de red de OVH** (panel → IP → Firewall) con las
mismas reglas, como segunda capa.

## 4. Instalar Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy   # cerrar sesión y volver a entrar
```

## 5. Swap (colchón para el entrenamiento de Rasa)

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 6. Clonar el repositorio y configurar

```bash
git clone https://github.com/IT-Digittal/NijarApps.git
cd NijarApps/infra/ovh

# Variables de entorno
cp .env.production.example .env
nano .env    # rellenar todos los CAMBIAR (SECRET_KEY, contraseñas, dominio…)

# Credenciales del broker MQTT (usar la misma contraseña en MQTT_PASSWORD del .env)
docker run --rm -v "$PWD:/work" eclipse-mosquitto:2 \
  mosquitto_passwd -c -b /work/mosquitto_passwd nijar-platform '<CONTRASEÑA_MQTT>'
```

Generadores de secretos:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # SECRET_KEY
openssl rand -base64 24                                          # contraseñas
```

## 7. Arrancar la plataforma

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps        # todo "running/healthy"
docker compose -f docker-compose.prod.yml logs -f api
```

Las migraciones de Alembic se aplican automáticamente al arrancar la API.
Cargar los datos iniciales (idempotente):

```bash
docker compose -f docker-compose.prod.yml exec api python -m nijar_dti.data.seed_loader
```

Verificación:

- `https://<DOMINIO>/api/v1/health` → `{"status": "ok"}`
- `https://<DOMINIO>/dashboard` y `https://<DOMINIO>/totem` cargan
- `https://<DOMINIO>/metrics` → 403 (bloqueado desde el exterior, correcto)

## 8. Entrenar y activar el chatbot Rasa

El entrenamiento consume 2–4 GB de RAM adicionales durante varios minutos;
en el VPS-4 (24 GB) puede hacerse en caliente sin problema:

```bash
# Regenerar ficheros de entrenamiento desde el seed de FAQs (si cambió)
docker compose -f docker-compose.prod.yml exec api python -m nijar_dti.workers.rasa_generator

# Entrenar y recargar
docker compose -f docker-compose.prod.yml --profile rasa-train run --rm rasa-trainer
docker compose -f docker-compose.prod.yml restart rasa
```

Mientras Rasa no tenga modelo entrenado, la API usa el fallback léxico
automáticamente (`RASA_FALLBACK_TO_LEXICAL=true`) — el chatbot nunca deja de
responder.

## 9. Copias de seguridad

Tres capas:

1. **Backup automático de OVH** (contratado con el VPS): imagen diaria del
   servidor completo, restauración de 7 días.
2. **Snapshot de OVH**: hacer uno manualmente antes de cada actualización.
3. **Volcado lógico diario de PostgreSQL** (recomendado, restauración granular):

```bash
sudo mkdir -p /var/backups/nijar-dti && sudo chown deploy: /var/backups/nijar-dti
crontab -e
# Añadir (volcado a las 04:00, conserva 14 días):
# 0 4 * * * docker exec nijar-dti-db pg_dump -U nijar -Fc nijar_dti > /var/backups/nijar-dti/nijar_dti_$(date +\%F).dump && find /var/backups/nijar-dti -name '*.dump' -mtime +14 -delete
```

Restauración de un volcado:

```bash
docker exec -i nijar-dti-db pg_restore -U nijar -d nijar_dti --clean < nijar_dti_YYYY-MM-DD.dump
```

## 10. Actualizaciones de la plataforma

```bash
cd ~/NijarApps
git pull
cd infra/ovh
docker compose -f docker-compose.prod.yml up -d --build   # reconstruye y reinicia solo lo que cambió
```

## Consumo previsto (VPS-4: 8 vCores / 24 GB)

| Servicio | Límite RAM |
|---|---|
| API (4 workers uvicorn) | 2 GB |
| PostgreSQL + PostGIS | 4 GB |
| Redis | 768 MB |
| Mosquitto | 256 MB |
| Workers (MQTT + Social) | 1 GB |
| Rasa | 3 GB |
| Caddy | 256 MB |
| **Total límites** | **~11,3 GB** |

Quedan ~12 GB libres para el sistema, el entrenamiento de Rasa y, si se desea,
el stack de observabilidad de `infra/observability/` (Prometheus + Grafana +
Loki, ~2 GB adicionales).
