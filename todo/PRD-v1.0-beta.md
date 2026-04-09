# powerCaldera — PRD v1.0 Beta

**Versión:** 1.0 Beta  
**Fecha:** 2026-04-09  
**Estado:** En desarrollo activo  
**Repositorio:** https://github.com/mik3m1r/powerCaldera

---

## 1. Visión del Producto

powerCaldera es una TUI (Terminal User Interface) en Python para operar [MITRE Caldera v5](https://github.com/mitre/caldera) desde la línea de comandos. El objetivo es reemplazar la interfaz web de Caldera con una experiencia de teclado-first, optimizada para red teamers que ya viven en la terminal.

**Propuesta de valor:**  
> Crear, desplegar y monitorear operaciones ofensivas en Caldera sin salir de la terminal, con soporte para templates generados por IA.

---

## 2. Usuarios Target

- Red teamers internos que usan Caldera 5.x
- Operadores que prefieren flujos CLI/TUI
- Automatización de ejercicios a partir de templates JSON generados por LLMs

---

## 3. Alcance v1.0 Beta

### 3.1 Funcionalidades Incluidas

| # | Funcionalidad | Estado |
|---|--------------|--------|
| F1 | Conexión a Caldera con API key (CLI / env / YAML) | ✅ Completo |
| F2 | Dashboard: ver agentes y operaciones activas | ✅ Completo |
| F3 | Pantalla de Habilidades con búsqueda + detalle | ✅ Completo |
| F4 | Pantalla de Adversarios con búsqueda + detalle | ✅ Completo (búsqueda agregada en beta) |
| F5 | Pantalla de Operaciones: crear, pausar, reanudar, finalizar | ✅ Completo |
| F6 | Ver links ejecutados y reporte de operación | ✅ Completo |
| F7 | Pantalla de Templates: builtin + importar JSON | ✅ Completo |
| F8 | Deploy de template: crea habilidades + adversario con rollback | ✅ Completo |
| F9 | Crear habilidades manualmente | ✅ Completo |
| F10 | Crear adversarios manualmente con selección de habilidades | ✅ Completo |
| F11 | Layout responsive según tamaño de terminal | ✅ Completo (fijado en beta) |
| F12 | Logging a archivo con rotación (DEBUG / INFO) | ✅ Completo |

### 3.2 Fuera de Alcance v1.0

- Multi-servidor (conectar a múltiples instancias de Caldera)
- Gestión de agentes (deploy, kill)
- Editor de abilities inline
- Exportar reportes a archivo
- Autenticación OAuth / LDAP

---

## 4. Arquitectura

```
powercaldera/
├── __main__.py         # Entrypoint, CLI args, config override
├── app.py              # PowerCalderaApp — mode switching, abilities cache
├── config.py           # Config (CLI > env > YAML)
├── utils.py            # truncate(), helpers
│
├── api/
│   ├── client.py       # AsyncClient httpx — todos los endpoints Caldera
│   └── models.py       # Pydantic models (Ability, Adversary, Operation, ...)
│
├── templates/
│   ├── models.py       # TemplateModel (schema JSON de templates)
│   ├── loader.py       # list_builtin(), load_from_string(), deploy()
│   └── builtin/*.json  # Templates incluidos como package data
│
├── screens/
│   ├── base.py         # BaseScreen — load_data(), _check_connection()
│   ├── dashboard.py    # Agentes + Operaciones (auto-refresh)
│   ├── abilities.py    # Lista + búsqueda + detalle + crear modal
│   ├── adversaries.py  # Lista + búsqueda + detalle + crear modal
│   ├── operations.py   # Lista + controles + links + reporte
│   └── templates_screen.py  # Builtin tab + Import JSON tab
│
├── widgets/
│   ├── header_bar.py   # Dock top — título + shortcuts
│   └── status_bar.py   # Dock bottom — conexión + agentes
│
└── app.tcss            # CSS global — layout system con 1fr
```

### Layout System

Todas las pantallas comparten el mismo sistema de clases CSS:

```
Screen (height: 100%, layout: vertical)
├── HeaderBar           [dock: top, height: 3]
├── .section-title      [height: 1]
├── Input búsqueda      [height: 3]  — solo en abilities / adversaries
├── #result-count       [height: 1]  — solo en abilities / adversaries
├── .content-area       [height: 1fr, layout: horizontal]
│   ├── .pane-left      [width: 60%, height: 100%]
│   │   └── DataTable   [height: 1fr]
│   └── .pane-right     [width: 40%, height: 100%, overflow-y: auto]
├── StatusBar           [dock: bottom, height: 1]
└── Footer              [dock: bottom]
```

---

## 5. Template Schema

Los templates JSON siguen el esquema definido en `TEMPLATE_SCHEMA.md`. Son el puente entre LLMs y Caldera:

1. El usuario pide a un LLM: *"generame un template de reconocimiento para Windows"*
2. El LLM devuelve un JSON válido según el schema
3. El usuario lo pega en la pestaña "Importar JSON" de powerCaldera
4. powerCaldera valida, muestra preview, y despliega en Caldera con un botón

---

## 6. Configuración

**Precedencia:** CLI flags > variables de entorno > `~/.powercaldera/config.yaml`

```yaml
server_url: http://127.0.0.1:8888
api_key: ADMIN123
log_level: INFO
refresh_interval: 30
templates_dir: ~/mis-templates
```

**Variables de entorno:** `CALDERA_URL`, `CALDERA_API_KEY`, `CALDERA_LOG_LEVEL`

---

## 7. Instalación y Uso

```bash
# Clonar y crear entorno
git clone https://github.com/mik3m1r/powerCaldera
cd powerCaldera
conda create -p .conda python=3.13
conda activate ./.conda
pip install -e ".[test]"

# Ejecutar
conda run -p .conda python -m powercaldera \
  --server http://127.0.0.1:8888 \
  --key ADMIN123 \
  --log-level DEBUG

# Tests
pytest tests/ -v
```

---

## 8. Bugs Conocidos (Beta)

| ID | Descripción | Impacto | Estado |
|----|-------------|---------|--------|
| B1 | `Executor.command` puede ser `null` en Caldera → falla Pydantic | CRÍTICO | ✅ Fijado |
| B2 | `TemplatesScreen` sin `compose()` → crash al navegar | CRÍTICO | ✅ Fijado |
| B3 | `IndentationError` en `operations.py` → app no inicia | CRÍTICO | ✅ Fijado |
| B4 | Layout colapsa a 1 fila visible en todas las pantallas | MAYOR | ✅ Fijado |
| B5 | `TemplatesScreen` no cargaba contenido — `on_mount` corre antes de que `TabbedContent` monte sus hijos | MAYOR | ✅ Fijado |
| B6 | `ModuleNotFoundError: yaml` cuando se corre fuera del env conda | MENOR | Documentado |

---

## 9. Backlog v2.0

> Estos ítems están fuera del alcance de v1.0 beta.

### Alta Prioridad
- [ ] **Gestión de Agentes** — ver detalle, agrupar, kill beacon
- [ ] **Editor inline de Abilities** — editar nombre, descripción, comando desde la TUI
- [ ] **Exportar reporte a archivo** — markdown / JSON desde la pantalla de operaciones
- [ ] **Filtro por táctica en Habilidades** — dropdown lateral con las 14 tácticas MITRE

### Media Prioridad
- [ ] **Multi-servidor** — conectar y switchear entre múltiples instancias de Caldera
- [ ] **Catálogo de abilities al generar templates** — pasar la lista disponible al LLM para que use ability_ids reales
- [ ] **Preview de comando del executor** — expandir detalle de ability con el comando completo scrollable
- [ ] **Templates: búsqueda en builtin** — input de búsqueda en la pestaña Predefinidas
- [ ] **Confirmación antes de crear operación** — modal de resumen antes de ejecutar

### Baja Prioridad
- [ ] **Tema claro / oscuro** — toggle via binding
- [ ] **Shortcuts customizables** — via config YAML
- [ ] **Historial de operaciones** — cache local de operaciones anteriores
- [ ] **Notificaciones sonoras** — beep cuando una operación termina

---

## 10. Testing

```bash
# Suite completa (83 tests)
pytest tests/ -v

# Por módulo
pytest tests/test_client.py -v      # API client + httpx mocks
pytest tests/test_templates.py -v   # Template loader + deploy + rollback
pytest tests/test_config.py -v      # Config loading + precedence
pytest tests/test_models.py -v      # Pydantic models + edge cases
```

**Cobertura actual:** API client, templates, config, modelos Pydantic.  
**Sin cobertura:** Pantallas TUI (requieren teatest o similar).

---

## 11. Decisiones Técnicas

| Decisión | Alternativa Descartada | Razón |
|----------|----------------------|-------|
| Textual para TUI | urwid, curses directo | Componentes modernos, CSS-like layout, async-native |
| httpx async | requests | Compatibilidad nativa con asyncio de Textual |
| Pydantic v2 | dataclasses | Validación automática, `model_validate`, `extra="ignore"` |
| `field_validator` para coercionar `null → ""` | `Optional[str]` | Caldera devuelve `null` en `command`, Pydantic v2 no coerciona por defecto |
| conda env local `.conda` | venv | Aislamiento completo, reproducibilidad |

---

*Última actualización: 2026-04-09*
