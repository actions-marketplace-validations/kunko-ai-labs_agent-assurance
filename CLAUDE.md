# agent-assurance — reglas del proyecto

## Qué es (y qué no)

Linter de **lo que el repo dice que un agente de IA puede hacer**: lee un manifiesto (`agent-assurance.yaml`, y desde v0.2 la configuración real del repo), calcula un riesgo transparente y lo enseña en el PR (markdown, JSON, SARIF) con exit code que bloquea.

No es: un motor en runtime, un interceptor de tool calls, un ledger, un sistema de aprobaciones. Eso es otro producto (carril empresa de Kunko AI Labs); aquí no entra código de eso.

## Contratos que no se rompen sin avisar

- **Exit codes**: `0` pass/review · `1` gate · `2` uso/manifiesto inválido. Están en `tests/test_cli_contract.py` y en `.github/workflows/ci.yml`. La Action depende de ellos.
- **Riesgo reproducible a mano**: cada punto sale de `risk.py` con su motivo. Nunca un LLM en el veredicto.
- **SARIF**: apunta al fichero real, con región; PASS sale como `kind: pass` (sin alerta).
- **Estándares**: mapeo a OWASP ASI; lo que viene de APTS se etiqueta `(adapted)`. No se reclama conformidad que no existe.
- **Lo no soportado es `UNKNOWN`**, nunca inferido.

## Cómo se trabaja

- Entorno: `.venv` con `pip install -e ".[dev]"`. Antes de commitear: `ruff check src tests && pytest -q`.
- El CI de dogfood (`assurance.yml`) es una **alarma**: cada job afirma que la Action pasa lo que debe y bloquea lo que debe. No añadir `continue-on-error` sin un paso que afirme el resultado esperado.
- Una unidad shippable por semana con demo de 30 s. Si una feature no cabe en una demo, está mal cortada.
- Ejemplos en `examples/` cubren las cuatro bandas (safe=LOW, medium=MEDIUM, high=HIGH, dangerous=CRITICAL); un check nuevo añade su ejemplo.
- Commits en inglés, imperativo, prefijo `feat:|fix:|ci:|docs:|test:`.

## Roadmap vigente

Está en el README (§Roadmap). Las decisiones de programa viven en el repo privado `vmbb13/ideas-ia-plan-personal` (doc 12). Si algo aquí contradice a ese doc, manda el doc y se abre issue.
