# powerCaldera

> **v1.0 Beta**

TUI (Terminal User Interface) para interactuar con la API REST v2 de [MITRE Caldera](https://caldera.mitre.org/). Permite gestionar habilidades, adversarios, operaciones y desplegar plantillas de ataque desde la terminal.

## Requisitos

- Python >= 3.11 (probado con 3.13)
- [Conda](https://docs.conda.io/) (recomendado) o cualquier gestor de entornos
- Servidor MITRE Caldera 5.x corriendo y accesible (API v2)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/mik3m1r/powerCaldera
cd powerCaldera

# Crear entorno conda local (recomendado)
conda create -p .conda python=3.13
conda activate ./.conda

# Instalar en modo desarrollo
pip install -e .

# Con dependencias de test
pip install -e ".[test]"
```

> **Importante:** todas las dependencias (PyYAML, textual, httpx, etc.) viven en el entorno `.conda`.
> Siempre ejecutá el proyecto dentro del entorno activado o usando `conda run -p .conda`.

## Configuración

La configuración se puede definir de tres formas (en orden de prioridad):

### 1. Argumentos CLI (mayor prioridad)

```bash
python -m powercaldera --server http://caldera:8888 --key ADMIN123 --log-level DEBUG
```

### 2. Variables de entorno

```bash
export CALDERA_URL=http://caldera:8888
export CALDERA_API_KEY=ADMIN123
export CALDERA_LOG_LEVEL=DEBUG
```

### 3. Archivo YAML

Copiá el ejemplo y editalo:

```bash
mkdir -p ~/.powercaldera
cp config.example.yaml ~/.powercaldera/config.yaml
```

```yaml
server_url: http://localhost:8888
api_key: ADMIN123
log_level: INFO
refresh_interval: 30          # segundos entre auto-refresh del dashboard y operaciones
templates_dir: ~/mis-templates # directorio extra de plantillas JSON (opcional)
```

Se puede especificar otra ruta con `--config /ruta/config.yaml`.

Variables de entorno soportadas: `CALDERA_URL`, `CALDERA_API_KEY`, `CALDERA_LOG_LEVEL`

## Uso

```bash
# Forma recomendada (con conda)
conda run -p .conda python -m powercaldera --server http://127.0.0.1:8888 --key ADMIN123

# Con entorno activado
conda activate ./.conda
python -m powercaldera --server http://127.0.0.1:8888 --key ADMIN123 --log-level DEBUG

# Usando el entry point (con entorno activado)
powercaldera --server http://127.0.0.1:8888 --key ADMIN123
```

## Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `d` | Dashboard |
| `a` | Habilidades (abilities) |
| `v` | Adversarios |
| `t` | Plantillas |
| `o` | Operaciones |
| `r` | Refrescar pantalla actual |
| `c` | Crear (en pantallas que lo soporten) |
| `q` | Salir |

### Atajos en Operaciones

| Tecla | Acción |
|-------|--------|
| `p` | Pausar operación seleccionada |
| `f` | Finalizar operación seleccionada |

## Pantallas

- **Dashboard**: Resumen de agentes conectados y operaciones activas. Auto-refresh configurable.
- **Habilidades**: Buscar por nombre/táctica/técnica (debounce 300ms), ver detalle y crear habilidades.
- **Adversarios**: Buscar por nombre/ID/tag, ver cadena de ataque y crear adversarios seleccionando habilidades.
- **Plantillas**: Importar plantillas JSON o usar las predefinidas para desplegar adversarios completos.
- **Operaciones**: Crear, pausar, reanudar, finalizar operaciones y ver reportes con output decodificado.

## Plantillas

Las plantillas son archivos JSON que definen un adversario completo (habilidades + cadena de ataque). Se pueden:

- **Usar predefinidas**: 6 plantillas incluidas (ransomware, APT, exfiltración, etc.)
- **Importar JSON**: Pegar JSON o cargar desde archivo con preview de validación
- **Generar con IA**: Usar cualquier LLM para generar plantillas siguiendo el schema

Ver [TEMPLATE_SCHEMA.md](TEMPLATE_SCHEMA.md) para el formato completo y un prompt sugerido.

### Plantillas predefinidas

| Archivo | Descripción |
|---------|-------------|
| `discovery_recon.json` | Reconocimiento y descubrimiento |
| `credential_harvesting.json` | Recolección de credenciales |
| `apt_lateral_movement.json` | Movimiento lateral tipo APT |
| `initial_access_persistence.json` | Acceso inicial y persistencia |
| `data_exfiltration.json` | Exfiltración de datos |
| `ransomware_simulation.json` | Simulación de ransomware |

## Logging

Los logs se escriben en `~/.powercaldera/powercaldera.log` con rotación automática (5 MB, 3 backups).

```bash
# Seguir logs en tiempo real
tail -f ~/.powercaldera/powercaldera.log
```

| Nivel | Descripción |
|-------|-------------|
| `DEBUG` | Todo: llamadas API, cache hits, detalles internos |
| `INFO` | Operaciones importantes: conexión, creación, despliegue |
| `WARNING` | Problemas no críticos: sin conexión, templates inválidos |
| `ERROR` | Errores: fallos de API, excepciones con traceback |

## Tests

```bash
# Suite completa (83 tests)
conda run -p .conda python -m pytest tests/ -v

# Por módulo
pytest tests/test_client.py -v      # API client
pytest tests/test_templates.py -v   # Template loader + deploy + rollback
pytest tests/test_config.py -v      # Config loading + precedencia
pytest tests/test_models.py -v      # Pydantic models
```

## Estructura del proyecto

```
powerCaldera/
├── pyproject.toml
├── README.md
├── TEMPLATE_SCHEMA.md
├── AGENTS.md                    # Convenciones para agentes de IA
├── todo/
│   └── PRD-v1.0-beta.md         # Product Requirements Document
├── tests/
│   ├── conftest.py
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_models.py
│   └── test_templates.py
└── powercaldera/
    ├── __main__.py
    ├── app.py
    ├── app.tcss                 # Sistema de layout CSS global
    ├── config.py
    ├── api/
    │   ├── client.py
    │   └── models.py
    ├── screens/
    │   ├── base.py
    │   ├── dashboard.py
    │   ├── abilities.py
    │   ├── adversaries.py
    │   ├── operations.py
    │   └── templates_screen.py
    ├── templates/
    │   ├── loader.py
    │   ├── models.py
    │   └── builtin/             # 6 plantillas incluidas como package data
    └── widgets/
        ├── header_bar.py
        └── status_bar.py
```


## Requisitos

- Python >= 3.11
- Servidor MITRE Caldera corriendo y accesible (API v2)

## Instalacion

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd powerCaldera

# Instalar en modo desarrollo
pip install -e .

# Con dependencias de test
pip install -e ".[test]"
```

## Configuracion

La configuracion se puede definir de tres formas (en orden de prioridad):

### 1. Argumentos CLI (mayor prioridad)

```bash
powercaldera --server http://caldera:8888 --key ADMIN123 --log-level DEBUG
```

### 2. Variables de entorno

```bash
export CALDERA_URL=http://caldera:8888
export CALDERA_API_KEY=ADMIN123
export CALDERA_LOG_LEVEL=DEBUG
```

### 3. Archivo YAML

Por defecto busca en `~/.powercaldera/config.yaml`:

```yaml
server:
  url: http://localhost:8888
  api_key: ADMIN123

settings:
  refresh_interval: 30
  log_level: INFO
  templates_dir: /ruta/a/plantillas/extras
```

Se puede especificar otra ruta con `--config /ruta/config.yaml`.

Variables de entorno soportadas:

- `CALDERA_URL`
- `CALDERA_API_KEY`
- `CALDERA_LOG_LEVEL`

`refresh_interval` y `templates_dir` se cargan desde el YAML, pero en la versión actual todavía no están conectadas a un comportamiento visible de la UI.

## Uso

```bash
# Usando el entry point
powercaldera --server http://caldera:8888 --key ADMIN123

# O como modulo
python -m powercaldera --server http://caldera:8888 --key ADMIN123

# Con nivel de log detallado
powercaldera --server http://caldera:8888 --key ADMIN123 --log-level DEBUG
```

## Atajos de teclado

| Tecla | Accion |
|-------|--------|
| `d` | Dashboard |
| `a` | Habilidades (abilities) |
| `v` | Adversarios |
| `t` | Plantillas |
| `o` | Operaciones |
| `r` | Refrescar pantalla actual |
| `c` | Crear (en pantallas que lo soporten) |
| `q` | Salir |

### Atajos en Operaciones

| Tecla | Accion |
|-------|--------|
| `p` | Pausar operacion seleccionada |
| `f` | Finalizar operacion seleccionada |

## Pantallas

- **Dashboard**: Resumen de agentes conectados y operaciones activas.
- **Habilidades**: Buscar, ver detalle y crear habilidades. Busqueda con debounce y cache.
- **Adversarios**: Listar, ver cadena de ataque y crear adversarios seleccionando habilidades.
- **Plantillas**: Importar plantillas JSON o usar las predefinidas para desplegar adversarios completos con un clic.
- **Operaciones**: Crear, pausar, reanudar, finalizar operaciones y ver reportes.

## Plantillas

Las plantillas son archivos JSON que definen un adversario completo (habilidades + cadena de ataque). Se pueden:

- **Usar predefinidas**: 6 plantillas incluidas (ransomware, APT, exfiltracion, etc.)
- **Importar JSON**: Pegar JSON o cargar desde archivo
- **Generar con IA**: Usar cualquier LLM para generar plantillas siguiendo el schema

Ver [TEMPLATE_SCHEMA.md](TEMPLATE_SCHEMA.md) para el formato completo y un prompt sugerido para generar plantillas con IA.

### Plantillas predefinidas

| Archivo | Descripcion |
|---------|-------------|
| `discovery_recon.json` | Reconocimiento y descubrimiento |
| `credential_harvesting.json` | Recoleccion de credenciales |
| `apt_lateral_movement.json` | Movimiento lateral tipo APT |
| `initial_access_persistence.json` | Acceso inicial y persistencia |
| `data_exfiltration.json` | Exfiltracion de datos |
| `ransomware_simulation.json` | Simulacion de ransomware |

## Logging

Los logs se escriben en `~/.powercaldera/powercaldera.log` con rotacion automatica (5 MB, 3 backups).

### Niveles de log

| Nivel | Descripcion |
|-------|-------------|
| `DEBUG` | Todo: llamadas API, cache hits, detalles internos |
| `INFO` | Operaciones importantes: conexion, creacion, despliegue |
| `WARNING` | Problemas no criticos: sin conexion, templates invalidos |
| `ERROR` | Errores: fallos de API, excepciones |

### Configurar nivel

```bash
# Via CLI
powercaldera --log-level DEBUG

# Via variable de entorno
export CALDERA_LOG_LEVEL=DEBUG

# Via config.yaml
settings:
  log_level: DEBUG
```

### Ver logs

```bash
# Ultimo contenido
tail -f ~/.powercaldera/powercaldera.log

# En Windows
type %USERPROFILE%\.powercaldera\powercaldera.log
```

## Tests

```bash
# Instalar dependencias de test
pip install -e ".[test]"

# Ejecutar todos los tests
pytest tests/ -v

# Solo tests del cliente API
pytest tests/test_client.py -v

# Solo tests de modelos
pytest tests/test_models.py -v
```

## Estructura del proyecto

```
powerCaldera/
├── pyproject.toml
├── README.md
├── TEMPLATE_SCHEMA.md
├── tests/
│   ├── conftest.py
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_models.py
│   └── test_templates.py
└── powercaldera/
    ├── __init__.py
    ├── __main__.py
    ├── app.py
    ├── app.tcss
    ├── config.py
    ├── logging.py
    ├── api/
    │   ├── __init__.py
    │   ├── client.py
    │   └── models.py
    ├── screens/
    │   ├── __init__.py
    │   ├── dashboard.py
    │   ├── abilities.py
    │   ├── adversaries.py
    │   ├── operations.py
    │   └── templates_screen.py
    ├── templates/
    │   ├── __init__.py
    │   ├── loader.py
    │   ├── models.py
    │   └── builtin/
    │       ├── ransomware_simulation.json
    │       ├── apt_lateral_movement.json
    │       ├── initial_access_persistence.json
    │       ├── data_exfiltration.json
    │       ├── credential_harvesting.json
    │       └── discovery_recon.json
    └── widgets/
        ├── __init__.py
        ├── header_bar.py
        └── status_bar.py
```
