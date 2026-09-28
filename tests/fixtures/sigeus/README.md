# Fixtures de siGEUS (Distromel · RSU y limpieza viaria)

Todavía **no se han podido capturar** respuestas reales.

- Motivo: Login bloqueado por segundo factor (OTP): La cuenta de siGEUS exige segundo factor (OTP); solicitar usuario técnico sin 2FA

El usuario técnico facilitado por Distromel tiene el segundo factor
(OTP) activado, y `POST api/session/login` responde HTTP 200 con
`{"token": null, "twoFactorAuthentication": true}`, sin emitir token.
El login automatizado no es posible en ese caso.

Siguiente paso: solicitar a Distromel un usuario técnico **sin 2FA**
(solo lectura) y volver a ejecutar `python -m scripts.capturar_fixtures_sigeus`.
