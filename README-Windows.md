# Guía de despliegue local en Windows — Plataforma DTI Níjar

Esta guía explica cómo desplegar la Plataforma DTI Níjar en una máquina Windows 10/11 usando Docker Desktop. No requiere conocimientos previos de Docker ni de PowerShell: hay scripts de doble clic preparados.

---

## Contenido

1. [Requisitos previos](#1-requisitos-previos)
2. [Instalación paso a paso](#2-instalación-paso-a-paso)
3. [Uso diario](#3-uso-diario)
4. [Endpoints disponibles](#4-endpoints-disponibles)
5. [Credenciales por defecto](#5-credenciales-por-defecto)
6. [Recursos del sistema](#6-recursos-del-sistema)
7. [Solución de problemas](#7-solución-de-problemas)
8. [Cómo modificar la configuración](#8-cómo-modificar-la-configuración)
9. [Cómo limpiar todo](#9-cómo-limpiar-todo)

---

## 1. Requisitos previos

### Hardware mínimo recomendado

| Componente | Mínimo | Recomendado |
|---|---|---|
| RAM | 8 GB | 16 GB |
| CPU | 4 núcleos | 8 núcleos |
| Disco libre | 10 GB | 20 GB SSD |
| Sistema | Windows 10 21H2+ o Windows 11 | Windows 11 |

Con 8 GB de RAM total solo se puede arrancar el perfil mínimo (sin Rasa). Para todos los servicios incluyendo Rasa, se recomienda tener al menos 16 GB.

### Software requerido

**1. Docker Desktop para Windows** (obligatorio)

- Descargar de https://www.docker.com/products/docker-desktop
- Durante la instalación, dejar marcada la opción "Use WSL 2 instead of Hyper-V" (recomendada)
- Tras instalar, arrancar Docker Desktop y esperar a que el icono de la ballena en la bandeja del sistema se ponga estático y verde
- Comprobar versión 4.x o superior

**2. WSL2** (si Docker Desktop no lo activó automáticamente)

Abrir PowerShell como administrador y ejecutar:

```powershell
wsl --install
```

Reiniciar el equipo si lo pide.

**3. Git para Windows** (opcional, pero recomendado)

- Descargar de https://git-scm.com/download/win
- Solo es necesario si vas a clonar el repositorio. Si recibiste el proyecto como ZIP, no hace falta.

### Cosas que NO necesitas

- Python instalado en Windows
- Node.js instalado en Windows
- Laragon, XAMPP, WAMP o similares
- Cualquier servidor de bases de datos (Postgres, MySQL, etc.)
- Cualquier servidor web (Apache, Nginx, IIS)
- Cuenta AWS

Todo se ejecuta dentro de contenedores Docker.

---

## 2. Instalación paso a paso

### 2.1. Extraer el proyecto

Coloca el ZIP del proyecto en una ruta **sin espacios ni acentos**. Recomendado:

```
C:\dev\nijar-dti\
```

**Evita** rutas como `C:\Users\Tu Nombre\Escritorio\proyecto`. Los espacios y caracteres especiales causan problemas con Docker en algunos casos.

Tras extraer, la estructura debe verse así:

```
C:\dev\nijar-dti\
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── README.md
├── README-Windows.md          (este archivo)
├── docker-compose.override.windows.yml
├── alembic\
├── docs\
├── frontend\
├── infra\
├── rasa\
├── scripts\
├── src\
├── tests\
└── windows\                   ← carpeta con scripts de despliegue
    ├── setup.bat
    ├── setup.ps1
    ├── start.bat
    ├── start.ps1
    ├── stop.bat
    ├── stop.ps1
    ├── status.bat
    ├── status.ps1
    ├── reset.bat
    ├── reset.ps1
    ├── logs.bat
    └── logs.ps1
```

### 2.2. Comprobar que Docker Desktop está arrancado

Mira la bandeja del sistema (junto al reloj). Debe estar el icono de la ballena de Docker en color (no animado, no en gris).

Si está animada o en gris, espera 30-60 segundos a que termine de arrancar. Si no arranca, ábrelo desde el menú Inicio.

### 2.3. Ejecutar el setup inicial

Doble clic en `windows\setup.bat`.

Se abrirá una ventana negra de PowerShell que hará 6 comprobaciones:

1. Docker Desktop arrancado
2. WSL2 disponible
3. Puertos libres (8000, 5432, 6379, 1883, 9001, 5005)
4. Crear el archivo `.env` desde `.env.example` con un `SECRET_KEY` aleatorio
5. Comprobar RAM disponible
6. Pre-descargar imágenes Docker base (puede tardar 5-10 min la primera vez)

Si alguna comprobación falla, te dirá qué hacer. Cuando todo está OK, verás:

```
============================================================
 Setup completado correctamente
============================================================
```

### 2.4. Arrancar la plataforma

Doble clic en `windows\start.bat`.

Esto arranca el perfil **mínimo**: API + PostgreSQL + Redis + MQTT broker. La primera vez tarda 1-2 minutos en aplicar migraciones y cargar datos seed.

Cuando termina, se abre automáticamente el navegador en http://localhost:8000/docs (Swagger UI).

### 2.5. Arrancar con perfiles adicionales

Si quieres arrancar también los workers (MQTT subscriber + Social Listening) o Rasa, abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
# Solo workers (sin Rasa)
.\windows\start.ps1 -Workers

# Workers + Rasa (recomendado solo con 16 GB de RAM o más)
.\windows\start.ps1 -Workers -Rasa
```

> El primer arranque con `-Rasa` tardará 3-5 minutos adicionales mientras se entrena el modelo.

---

## 3. Uso diario

| Acción | Doble clic | PowerShell |
|---|---|---|
| Arrancar plataforma | `windows\start.bat` | `.\windows\start.ps1` |
| Arrancar con workers | — | `.\windows\start.ps1 -Workers` |
| Arrancar todo | — | `.\windows\start.ps1 -Workers -Rasa` |
| Ver estado | `windows\status.bat` | `.\windows\status.ps1` |
| Ver logs (API) | `windows\logs.bat` | `.\windows\logs.ps1` |
| Ver logs de otro servicio | — | `.\windows\logs.ps1 -Service db` |
| Ver logs de todos | — | `.\windows\logs.ps1 -Service all` |
| Parar plataforma | `windows\stop.bat` | `.\windows\stop.ps1` |
| Reset completo (borra datos) | `windows\reset.bat` | `.\windows\reset.ps1` |

### Apagar el ordenador

Si vas a apagar el equipo, ejecuta primero `stop.bat`. Si no lo haces no pasa nada grave (Docker se cierra y los contenedores quedan parados), pero al volver a arrancar tendrás que hacer `start.bat` de nuevo.

---

## 4. Endpoints disponibles

Una vez arrancada la plataforma:

| Recurso | URL |
|---|---|
| Swagger UI (probar la API) | http://localhost:8000/docs |
| ReDoc (documentación API) | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Health check | http://localhost:8000/api/v1/health |
| Dashboard SPA | http://localhost:8000/dashboard |
| Plantilla del tótem | http://localhost:8000/totem |
| Rasa server (si `-Rasa`) | http://localhost:5005 |

---

## 5. Credenciales por defecto

Tras el primer arranque, hay un usuario administrador creado automáticamente:

```
email: admin@nijar.es
pass:  CambiarEnPrimerArranque#2026
```

Para cambiar las credenciales por defecto, edita el `.env` antes del primer arranque y modifica:

```
INITIAL_ADMIN_EMAIL=tu@correo.com
INITIAL_ADMIN_PASSWORD=TuContraseñaSegura#2026
```

Y haz un reset (`reset.bat`) para que se apliquen.

### Datos cargados automáticamente

- 1 usuario administrador con 2FA obligatorio
- 14 recursos turísticos con coordenadas GPS reales y descripciones en 4 idiomas
- 9 sensores del Smart Office y los 2 tótems
- 22 FAQs base del chatbot en ES/EN/DE/FR

---

## 6. Recursos del sistema

### Consumo aproximado de RAM por perfil

| Perfil | Servicios | RAM aprox. |
|---|---|---|
| Mínimo | api + db + redis + mqtt | 1.5 GB |
| Workers | + mqtt-subscriber + social-worker | 2.5 GB |
| Completo | + rasa | 5 GB |

A esto súmale ~2 GB que consume Docker Desktop + WSL2 por sí mismos.

### Limitar recursos en máquinas modestas

Si tu máquina tiene 8 GB y quieres asegurarte de no quedarte sin RAM:

1. Renombra `docker-compose.override.windows.yml` a `docker-compose.override.yml`
2. Ejecuta `start.bat` de nuevo

El override aplica límites por contenedor que evitan que Docker se coma toda la RAM.

### Configurar WSL2

Si Docker Desktop usa demasiada RAM, crea el archivo `C:\Users\<TuUsuario>\.wslconfig`:

```ini
[wsl2]
memory=8GB
processors=4
swap=4GB
localhostForwarding=true
```

Cierra Docker Desktop, ejecuta `wsl --shutdown` en PowerShell, y vuelve a abrir Docker Desktop.

---

## 7. Solución de problemas

### "Docker Desktop no esta arrancado"

Abre Docker Desktop desde el menú Inicio. Espera 30-60 segundos. Si sigue sin arrancar:

1. Abre PowerShell como administrador
2. Ejecuta: `wsl --shutdown`
3. Cierra Docker Desktop completamente (Tray > Quit Docker Desktop)
4. Vuelve a abrirlo

### "Puerto 5432 ocupado" (o cualquier otro)

Tienes otro servicio usando ese puerto. Opciones:

**Opción A** — Detener el servicio que lo ocupa. Para PostgreSQL local:

```powershell
# Ver qué proceso lo usa
Get-Process -Id (Get-NetTCPConnection -LocalPort 5432).OwningProcess

# Si es Postgres local, parar el servicio
Stop-Service postgresql-x64-XX
```

**Opción B** — Cambiar el puerto en el compose. Edita `docker-compose.yml` y cambia:

```yaml
ports:
  - "5432:5432"   # cambia el primer 5432 a 15432, por ejemplo
```

### "API no responde tras 60s"

Mira los logs:

```powershell
.\windows\logs.ps1 -Service api -Tail 200
```

Causas frecuentes:

- **Migraciones de Alembic fallaron** → reset y reintentar
- **No se pudieron cargar datos seed** → suele ser inocuo, la API arranca igual
- **Falta de RAM** → Docker mata el contenedor, mira `docker stats`

### Docker Desktop consume mucha RAM

Crea `C:\Users\<TuUsuario>\.wslconfig` con los límites del apartado 6.

### "Acceso denegado" al ejecutar .ps1 directamente

Los `.bat` tienen `-ExecutionPolicy Bypass` y no requieren cambiar nada. Si quieres ejecutar `.ps1` directamente:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

(solo para tu usuario, sin permisos de administrador).

### Los datos parecen corruptos o el sistema no arranca bien

Reset completo:

```
windows\reset.bat
```

Confirma con SI y vuelve a arrancar con `start.bat`. Esto regenera la BBDD desde cero con los datos seed.

### Docker Desktop "WSL integration failed"

1. PowerShell como administrador:
   ```powershell
   wsl --update
   wsl --set-default-version 2
   ```
2. Reiniciar Docker Desktop

### El antivirus ralentiza mucho los volúmenes

Windows Defender escanea los volúmenes de Docker y ralentiza notablemente las operaciones de I/O. Añade exclusiones:

1. Configuración → Privacidad y seguridad → Seguridad de Windows
2. Protección antivirus y antiamenazas → Administrar configuración
3. Exclusiones → Agregar:
   - Carpeta del proyecto: `C:\dev\nijar-dti`
   - Carpeta de Docker: `C:\ProgramData\Docker`
   - Carpeta WSL: `\\wsl$`

### Quiero ver lo que la API devuelve sin Swagger

```powershell
# Health check
curl http://localhost:8000/api/v1/health

# Login (admin)
curl -X POST http://localhost:8000/api/v1/auth/login `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=admin@nijar.es&password=CambiarEnPrimerArranque#2026"
```

### Bind mount muy lento (compilación, cargas de archivos)

Esto es esperable si el proyecto está en `C:\...`. Para desarrollo activo y mucho I/O, mover el proyecto al sistema de archivos de WSL2:

```powershell
# Abrir WSL Ubuntu
wsl

# Dentro de WSL
cd ~
mkdir dev && cd dev
# Copia o mueve el proyecto aquí
```

Luego abre la carpeta desde Docker Desktop o desde VS Code con la extensión "WSL".

---

## 8. Cómo modificar la configuración

### Cambiar el puerto de la API

Editar `docker-compose.yml`:

```yaml
api:
  ports:
    - "9000:8000"   # ahora la API se sirve en localhost:9000
```

### Activar Social Listening real (sin dry-run)

Editar `.env`:

```
SOCIAL_DRY_RUN=false
SOCIAL_LISTENING_ENABLED=true
TWITTER_BEARER_TOKEN=AAAA...
FACEBOOK_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
```

Y reiniciar (`stop.bat` + `start.bat -Workers`).

### Usar Rasa en vez del motor lexical

Editar `.env`:

```
CHATBOT_ENGINE=rasa
RASA_URL=http://rasa:5005
RASA_FALLBACK_TO_LEXICAL=true
```

Y arrancar con `-Rasa`:

```powershell
.\windows\start.ps1 -Workers -Rasa
```

### Cambiar la contraseña del admin tras primer arranque

Mejor hazlo desde Swagger UI (http://localhost:8000/docs), endpoint `POST /api/v1/auth/change-password` después de hacer login.

---

## 9. Cómo limpiar todo

### Borrar solo los datos (mantener imágenes)

```
windows\reset.bat
```

### Borrar todo (imágenes incluidas)

```powershell
# Para los servicios y borra volúmenes
docker compose --profile workers --profile rasa down -v

# Borra imágenes de la plataforma
docker images "*nijar*" -q | ForEach-Object { docker rmi $_ }

# Borra imágenes de Rasa (pesan ~3 GB)
docker images "rasa/rasa*" -q | ForEach-Object { docker rmi $_ }
```

### Desinstalar completamente

1. `windows\reset.bat` para borrar volúmenes
2. Borrar la carpeta del proyecto (`C:\dev\nijar-dti`)
3. Si no lo necesitas para otros proyectos, desinstalar Docker Desktop desde Configuración → Aplicaciones

---

## ¿Algo no encaja?

Para problemas con el código de la plataforma (bugs, comportamientos raros del API o del chatbot), abre un ticket o contacta con el equipo del proyecto.

Para problemas con el despliegue local específico de Windows que no estén cubiertos en esta guía, revisa primero los logs (`logs.bat`) y el estado (`status.bat`). Si persisten, comparte la salida con el equipo.
