# Contribuir a agente-respuesta

¡Gracias por querer contribuir! Este proyecto combina desarrollo humano y
autónomo: los issues marcados con la label **`agent-ready`** los implementa un
agente opencode en CI y los devuelve como Pull Request listo para revisión.

## Flujo `agent-ready` (implementación autónoma)

1. **Crear el issue** con la plantilla de *feature* (ver
   `.github/ISSUE_TEMPLATE/`): secciones `Contexto`, `Feature`, `Diseño corto`
   (clasificación `brainstorming`: spike / bounded / architectural) y
   `Criterios de éxito`. Si es architectural, el issue debe indicar que se
   requiere un ADR en `docs/decisions/` antes de implementar.
2. **Etiquetar**: las features (`enhancement`) que estén listas para el
   pipeline llevan además `agent-ready` y entran solas en la cola. Seguridad
   (`security`), UX/UI (`ux-ui`), documentación (`documentation`) y workflows
   (`workflows`) quedan en triaje humano (sin `agent-ready`).
3. **El agente implementa**: el workflow `opencode-label` (al poner la label)
   o `opencode-schedule` (cada 6h, el `agent-ready` más antiguo sin PR) crea la
   rama `opencode/issue<N>-<ts>` y abre la PR con `Closes #N`.
4. **Revisión y merge automático** (`opencode-review`): un agente revisor
   verifica la Definición de Hecho (`docs/definition-of-done.md`), trae `main`
   sobre la rama, espera el check `test` en verde y mergea solo si la DoD se
   cumple. Si algo falla, comenta en la PR qué falla y qué soluciones propone.

Labels de estado: `agent-ready` → `agent-in-progress` mientras el agente
trabaja; si falla, vuelve a `agent-ready` con un comentario explicativo.

## Desarrollo local

```bash
cp .env.example .env   # rellena tus claves; NUNCA commitees .env ni secretos
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python -m pytest -q   # la suite debe quedar verde antes de abrir PR
```

- Sigue `AGENTS.md` y sus skills (`brainstorming` antes de cualquier trabajo
  creativo; decisiones con trade-offs → ADR en `docs/decisions/`).
- No toques `backend/` ni `web/` si tu cambio es solo de metadatos/docs.
- Añade o actualiza tests del comportamiento nuevo/cambiado.
- La suite usa fakes (`fakeredis` + `monkeypatch`): corre sin Redis, sin API
  keys y sin red.

## Higiene de secretos (obligatorio antes de publicar)

- Nunca commitees `.env`, `logs/`, `*.pem`, `*.key` ni ficheros de
  credenciales (ver `.gitignore`).
- Las claves solo viajan por variables de entorno o secretos de GitHub
  Actions (`${{ secrets.* }}`); los workflows de CI nunca deben imprimir
  secretos en logs.
- Si sospechas que una clave llegó a git (actual o histórico), abre un issue
  `security:` y rota la clave de inmediato; el historial se limpia con
  `git filter-repo`, nunca con un commit encima.

## Código de conducta y seguridad

- Toda interacción sigue el [Código de Conducta](CODE_OF_CONDUCT.md).
- Para reportar vulnerabilidades o secretos filtrados usa
  [SECURITY.md](SECURITY.md) (no abras un issue público con el secreto).

## Licencia

Al contribuir aceptas que tu aportación se distribuya bajo la licencia
[MIT](LICENSE).
