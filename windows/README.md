# Carpeta `windows/` — Scripts de despliegue local

Esta carpeta contiene los scripts para desplegar la Plataforma DTI Níjar
en Windows con Docker Desktop.

## Uso rápido (doble clic)

1. **Primera vez:** doble clic en `setup.bat`
2. **Arrancar:** doble clic en `start.bat`
3. **Parar:** doble clic en `stop.bat`

## Uso desde PowerShell (recomendado para perfiles avanzados)

```powershell
# Setup inicial (solo la primera vez)
.\windows\setup.ps1

# Arrancar (perfil mínimo)
.\windows\start.ps1

# Arrancar con workers
.\windows\start.ps1 -Workers

# Arrancar con todo (workers + Rasa)
.\windows\start.ps1 -Workers -Rasa

# Estado
.\windows\status.ps1

# Logs (servicio por defecto: api)
.\windows\logs.ps1
.\windows\logs.ps1 -Service db
.\windows\logs.ps1 -Service all

# Parar
.\windows\stop.ps1

# Reset completo (borra datos)
.\windows\reset.ps1
```

## Documentación completa

Ver `..\README-Windows.md` en la raíz del proyecto.
