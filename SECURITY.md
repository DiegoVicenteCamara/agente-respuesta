# Política de seguridad

## Reportar una vulnerabilidad o un secreto filtrado

**No abras un issue público** con los detalles. Contacta en privado al
mantenedor (`@DiegoVicenteCamara` desde el tracker del repo o el canal privado
que indique el README) incluyendo:

- Descripción del problema y su impacto potencial.
- Pasos para reproducirlo (sin incluir secretos reales).
- Si es un secreto filtrado: qué clave, dónde la viste (commit/rama/log de CI)
  y si ya la has rotado.

Recibirás acuse de recibo en 48h y una estimación de corrección. Los secretos
filtrados se tratan como incidentes: rotar primero, limpiar después.

## Alcance

- Código de `backend/` y `web/`, workflows de `.github/workflows/` y
  configuración de ejemplo (`.env.example`).
- Quedan fuera: servicios de terceros (LiveKit Cloud, OpenAI, Tavily, Redis
  Cloud) — repórtalos a su proveedor además de avisarnos si les afecta.

## Higiene de secretos del proyecto

- `.env`, `logs/`, `*.pem`, `*.key` y credenciales están en `.gitignore` y no
  deben commitearse jamás.
- Las claves solo se configuran por entorno o secretos de GitHub Actions
  (`${{ secrets.* }}`); ningún workflow debe imprimir valores de secretos en
  logs (`echo ${{ secrets.* }}`, `print(os.environ[...])` y equivalentes están
  prohibidos en CI).
- `.env.example` solo contiene placeholders (`TU_...`, valores vacíos): es la
  referencia pública de qué variables existen, nunca valores reales.
- Antes de hacer público el repo se audita `git log -p` en busca de secretos
  históricos; si aparece alguno se rota la clave y se reescribe el historial
  con `git filter-repo` (documentado en el ADR de go-public).

## Versiones soportadas

Se da soporte de seguridad a `main` (rama en desarrollo continuo). Las ramas
efímeras `opencode/issue<N>-<ts>` heredan la política de `main`.
