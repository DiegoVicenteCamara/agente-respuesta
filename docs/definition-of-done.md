# Definición de Hecho (DoD)

La Definición de Hecho (Definition of Done) es el conjunto de criterios que una
tarea (issue) debe cumplir para considerarse **Done**. Se aplica a cualquier
trabajo sobre este repositorio: tanto a las tareas implementadas de forma
autónoma por agentes opencode como a las implementadas por humanos.

La revisión automática de PRs (`opencode-review`) usa esta DoD como gate antes
de mergear. Un PR cuyo trabajo **no** cumpla todos los puntos **no** se mergea:
desde `docs/decisions/ADR-004-revision-y-merge-automatico-de-prs-con-agente-opencode.md`
la norma es *merge 100% automático solo cuando la DoD se cumple*.

## Criterios

Una tarea se considera **Done** únicamente cuando cumple **todos** los puntos:

1. **Implementación completada según alcance de la issue.**
   El código resuelve la issue tal y como estaba definida; no hay TODOs ni
   funciones a medio hacer dentro del alcance.

2. **Código integrado en la rama de trabajo acordada sin conflictos pendientes.**
   El trabajo está integrado en la rama acordada (por defecto `main`, vía PR) y
   GitHub reporta la PR como *mergeable* sin conflictos.

3. **Verificación técnica ejecutada para el alcance afectado.**
   La suite de tests (`python -m pytest -q`) pasa en verde sobre el estado
   final del PR y cubre el comportamiento nuevo/cambiado. Si el cambio lo
   requiere, se ejecutan las validaciones específicas del alcance afectado.

4. **Evidencias registradas en la issue.**
   La issue vinculada (`Closes #N`) contiene un comentario con el checklist de
   evidencias (formato en la siguiente sección): qué se hizo, enlaces a
   commits/PR y el resultado de validación.

5. **Documentación asociada actualizada.**
   La documentación que el cambio afecta (README, `docs/`, ADRs, AGENTS.md)
   queda actualizada o se declara explícitamente que no aplica.

## Evidencia estructurada (punto 4)

Para que un agente (o un humano) pueda verificar el punto 4 de forma objetiva,
la issue debe contener un comentario con **este checklist** tras la
implementación:

```markdown
## Evidencias DoD
- [x] Implementación: implementada según alcance de la issue — <resumen> — commits: <sha1>, <sha2>
- [x] Integración: PR #<N> sobre main, mergeable sin conflictos (merge de main aplicado)
- [x] Verificación técnica: `python -m pytest -q` en verde — <N> passed — <enlace al run de CI / salida>
- [x] Documentación: <archivos> actualizados — <enlace a commit(s)> (o "no aplica")
```

Reglas de verificación:

- Un punto **desmarcado** o **sin enlaces/resultados** > la DoD no se cumple.
- La verificación técnica se contrasta con el estado real del CI (check `test`
  en verde sobre el head final del PR); una casilla marcada no sustituye a un CI
  rojo.
- La integración se contrasta con el estado *mergeable* de GitHub real.

## Cómo funciona la revisión automática (resumen)

1. El workflow `opencode-review` se dispara en cada evento de una PR
   (abierta, actualizada, reabierta, lista para review).
2. El agente revisor lee esta DoD y la evidence de la issue vinculada.
3. Trae `main` sobre la rama (`git merge origin/main`) y resuelve los
   conflictos **integrando ambas partes**, sin descartar trabajo de otras
   issues.
4. Espera a que el check `test` quede verde sobre el head final.
5. Si todos los puntos cumplen → **merge** (merge commit) y borra la rama.
6. Si algo falla → comenta en la PR **qué falla y qué soluciones** y **no**
   mergea (deja la PR abierta para que la implementación se corrija y vuelva a
   revisarse en el siguiente push).

Siempre hay, además, retroalimentación humana: los issues y PRs son auditables y
cualquiera puede pedir cambios; el merge automático aplica solo cuando la DoD se
cumple de forma objetiva.

## Referencias

- ADR-003: Automatización de issues con agente opencode (superseded por ADR-004).
- ADR-004: Revisión y merge automático de PRs con agente opencode.
- README → sección *Implementación autónoma de issues (opencode en CI)*.