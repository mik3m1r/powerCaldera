# powerCaldera — Backlog & Próximos Pasos

> Estado al: 2026-04-09
> v1.0 implementada y testeada (83/83 tests pasan).

---

## ✅ v1.0 — Completado

| # | Tarea | Archivo(s) |
|---|-------|-----------|
| T1.1 | Regex `technique_id` relajado (`^T\d+(\.\d+)?$`) | `templates/models.py` |
| T1.2 | 24/24 tests de templates pasan | `tests/test_templates.py` |
| T1.3-T1.4 | Escape markup en abilities y operations | `screens/abilities.py`, `screens/operations.py` |
| T1.5 | `TemplatesScreen` hereda `BaseScreen` | `screens/templates_screen.py` |
| T1.6 | `DEFAULT_SERVER_URL` como constante de módulo | `config.py` |
| T1.7 | `sorted(set(...))` en lista de platforms | `screens/abilities.py` |
| T2.1-T2.4 | `health_check()` retorna `"connected" \| "auth_error" \| "offline"` | `api/client.py`, `screens/base.py`, `screens/dashboard.py`, `app.py` |
| T2.3 | `StatusBar` muestra estado `auth_error` en naranja | `widgets/status_bar.py` |
| T2.5 | Tests para 401/403 en health_check | `tests/test_client.py` |
| T3.1 | `on_progress` callback en `TemplateLoader.deploy()` | `templates/loader.py` |
| T3.2 | `Config.templates_dir` wired en `TemplatesScreen` | `screens/templates_screen.py` |
| T3.3-T3.4 | Progress y rollback visibles en UI de templates | `screens/templates_screen.py` |
| T4.1 | `ConfirmFinishModal` antes de finalizar operación | `screens/operations.py` |
| T4.2-T4.3 | Auto-refresh timers wired a `Config.refresh_interval` | `screens/dashboard.py`, `screens/operations.py` |
| T4.4 | `AbilitiesCache._ttl` desde `Config.refresh_interval` | `app.py` |
| T4.5 | Versión desde `importlib.metadata` | `__main__.py` |

---

## 🔜 v1.1 — Próximos pasos inmediatos

### Calidad y estabilidad

- [ ] **Prueba con Caldera 5.3.0 real** — validar endpoints, auth, flujo completo
- [ ] **`sdd-verify`** — ejecutar la fase de verificación contra los specs definidos en engram (`sdd/powercaldera-v1/spec`)
- [ ] **`sdd-archive`** — archivar el cambio `powercaldera-v1` y sincronizar delta specs
- [ ] **Tests de integración mínimos** — al menos un test end-to-end con servidor mock que cubra el flujo completo: load template → validate → deploy → check adversary exists

### UX / Usability

- [ ] **Indicador visual de "cargando"** en todas las pantallas durante `load_data()` — actualmente no hay feedback de que está fetching
- [ ] **Pantalla de configuración inline** — permitir editar `server_url` y `api_key` desde la TUI sin restartar (sin tocar el YAML)
- [ ] **Filtro de operaciones por estado** — poder ver solo `running`, `finished`, etc.
- [ ] **Paginación o virtualización** para abilities cuando hay >200 (actualmente se truncan a MAX_ROWS=200)
- [ ] **Mensaje de bienvenida** cuando no hay agentes conectados — guiar al usuario a conectar un agente

### Bugs conocidos / edge cases

- [ ] **Triple health check al arrancar** — `on_mount()` en `app.py` + `_check_connection()` en cada screen al montarse. Reducir a una sola llamada con estado compartido en `app.py`
- [ ] **`TemplatesScreen._load_builtin()` corre en el hilo principal** — si hay muchos templates en `templates_dir` podría bloquear la UI. Mover a worker async
- [ ] **`ConfirmFinishModal` no deshabilita el botón** durante la acción — doble click puede enviar dos requests

---

## 🚀 v2.0 — Backlog futuro (NO implementar en v1.x)

> Estos ítems requieren decisiones de diseño y/o dependen de feedback real de uso.

### Integración con LLM

- [ ] **Catálogo de abilities exportable** — endpoint o comando para exportar abilities existentes de Caldera a JSON, para pasarle contexto a la IA
- [ ] **Integración LLM directa** — generar templates desde la TUI (requiere API key de OpenAI/Anthropic/etc.)
- [ ] **Sugerencias de abilities existentes** — al crear un template, mostrar abilities del catálogo que matchean el technique_id

### Multi-instancia

- [ ] **Perfiles de servidor** — múltiples configs (dev/staging/prod) seleccionables desde la TUI
- [ ] **Conexión simultánea** a múltiples instancias de Caldera

### Operaciones avanzadas

- [ ] **Live tail de links** — auto-refresh del log de links de una operación en curso (polling cada N segundos)
- [ ] **Exportar reporte** a archivo (TXT/JSON) desde la TUI
- [ ] **Crear operación desde template** — atajo directo: seleccionar template → deploy → crear operación en un flujo

### Adversarios

- [ ] **Editar adversario existente** — agregar/quitar abilities del atomic_ordering desde la TUI
- [ ] **Clonar adversario** — base para crear variantes

---

## 📝 Notas técnicas

- **Caldera 5.3.0** usa API v2 bajo `/api/v2/*`. El endpoint `/api/v2/health` requiere auth (401 si la API key es incorrecta).
- **`refresh_interval`** controla tanto el TTL del cache de abilities como los timers de auto-refresh de Dashboard y Operations.
- **`templates_dir`** en config apunta a un directorio con templates JSON adicionales (además de los builtins de `powercaldera/templates/builtin/`).
- **SDD artifacts** guardados en engram con topic_keys `sdd/powercaldera-v1/*` (proposal, spec, design, tasks).
