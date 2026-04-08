# Esquema de Plantillas JSON para powerCaldera

Este documento describe el formato JSON que powerCaldera acepta para crear adversarios y abilities en MITRE Caldera.

**Usa este documento como prompt para cualquier IA** (ChatGPT, Claude, Gemini, etc.) para generar plantillas compatibles.

---

## Prompt Sugerido para IA

Copia y pega esto en tu IA preferida:

```
Genera una plantilla JSON de adversario para MITRE Caldera con el siguiente formato.
El adversario debe simular [DESCRIBE TU ESCENARIO AQUÍ].

Formato requerido:
{
  "name": "Nombre del Adversario",
  "description": "Descripción del escenario de ataque",
  "tags": ["tag1", "tag2"],
  "abilities": [
    {
      "name": "Nombre de la ability",
      "tactic": "táctica MITRE ATT&CK",
      "technique_id": "TXXXX",
      "technique_name": "Nombre de la técnica",
      "description": "Qué hace esta ability",
      "platforms": {
        "windows": {
          "psh": "comando PowerShell"
        },
        "linux": {
          "sh": "comando shell"
        }
      }
    }
  ]
}

Tácticas válidas: reconnaissance, resource-development, initial-access, execution,
persistence, privilege-escalation, defense-evasion, credential-access, discovery,
lateral-movement, collection, command-and-control, exfiltration, impact.

Ejecutores válidos: psh (PowerShell), cmd (Windows CMD), sh (shell), bash, pwsh (PowerShell Core).
Plataformas válidas: windows, linux, darwin.

Reglas:
- Si querés desplegar la ability en Caldera, definí al menos una plataforma con un comando
- technique_id debe empezar con T (ej: T1082, T1003.001)
- Los comandos deben ser seguros para simulación (no destructivos)
- Incluye 1 ability como mínimo; 3 o más es recomendable para una secuencia útil
- Ordena las abilities en orden lógico de ejecución
```

---

## Esquema JSON Completo

```json
{
  "name": "string (obligatorio) — Nombre del adversario",
  "description": "string (opcional) — Descripción del escenario",
  "tags": ["string"] ,
  "abilities": [
    {
      "name": "string (obligatorio) — Nombre de la ability",
      "tactic": "string (obligatorio) — Táctica MITRE ATT&CK",
      "technique_id": "string (obligatorio) — ID de técnica (ej: T1082)",
      "technique_name": "string (obligatorio) — Nombre de la técnica",
      "description": "string (opcional) — Descripción",
      "platforms": {
        "windows": {
          "psh": "comando PowerShell",
          "cmd": "comando CMD"
        },
        "linux": {
          "sh": "comando shell",
          "bash": "comando bash"
        },
        "darwin": {
          "sh": "comando shell"
        }
      }
    }
  ]
}
```

### Campos Obligatorios

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | string | Nombre del adversario |
| `abilities` | array | Lista de abilities (mínimo 1) |
| `abilities[].name` | string | Nombre de la ability |
| `abilities[].tactic` | string | Táctica MITRE ATT&CK |
| `abilities[].technique_id` | string | ID de técnica (empieza con T) |
| `abilities[].technique_name` | string | Nombre de la técnica |
| `abilities[].platforms` | object | Plataformas y comandos por ejecutor |

### Campos Opcionales

| Campo | Tipo | Default |
|-------|------|---------|
| `description` | string | "" |
| `tags` | array de strings | [] |
| `abilities[].description` | string | "" |

---

## Tácticas Válidas MITRE ATT&CK

| Táctica | Descripción |
|---------|-------------|
| `reconnaissance` | Reconocimiento previo al ataque |
| `resource-development` | Desarrollo de recursos |
| `initial-access` | Acceso inicial al sistema |
| `execution` | Ejecución de código |
| `persistence` | Establecer persistencia |
| `privilege-escalation` | Escalación de privilegios |
| `defense-evasion` | Evasión de defensas |
| `credential-access` | Acceso a credenciales |
| `discovery` | Descubrimiento de información |
| `lateral-movement` | Movimiento lateral |
| `collection` | Recolección de datos |
| `command-and-control` | Comando y control |
| `exfiltration` | Exfiltración de datos |
| `impact` | Impacto en el sistema |

---

## Plataformas y Ejecutores

| Plataforma | Ejecutores Disponibles |
|------------|----------------------|
| `windows` | `psh` (PowerShell), `cmd` (CMD), `pwsh` (PowerShell Core) |
| `linux` | `sh` (shell), `bash` |
| `darwin` | `sh` (shell), `bash` |

---

## Ejemplo Completo

```json
{
  "name": "Simulación de Ransomware",
  "description": "Simula la cadena de ataque de un ransomware típico",
  "tags": ["ransomware", "simulation"],
  "abilities": [
    {
      "name": "Descubrimiento del Sistema",
      "tactic": "discovery",
      "technique_id": "T1082",
      "technique_name": "System Information Discovery",
      "description": "Recopila información del sistema",
      "platforms": {
        "windows": {
          "psh": "systeminfo; Get-ComputerInfo | Select-Object OsName, OsVersion"
        },
        "linux": {
          "sh": "uname -a; cat /etc/os-release"
        }
      }
    },
    {
      "name": "Descubrimiento de Recursos de Red",
      "tactic": "discovery",
      "technique_id": "T1135",
      "technique_name": "Network Share Discovery",
      "description": "Enumera recursos compartidos",
      "platforms": {
        "windows": {
          "psh": "Get-SmbShare | Select-Object Name, Path"
        }
      }
    },
    {
      "name": "Detección de Software de Seguridad",
      "tactic": "defense-evasion",
      "technique_id": "T1518.001",
      "technique_name": "Software Discovery: Security Software",
      "description": "Identifica antivirus y EDR instalados",
      "platforms": {
        "windows": {
          "psh": "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object displayName"
        },
        "linux": {
          "sh": "ps aux | grep -iE 'falcon|sentinel|ossec' | grep -v grep"
        }
      }
    }
  ]
}
```

---

## Validación

powerCaldera valida automáticamente cada plantilla al importar:
- JSON sintácticamente correcto
- Campos obligatorios presentes
- Tácticas en la lista válida
- technique_id empieza con "T"
- Ejecutores en la lista válida
- Las plataformas son opcionales; si una ability no define ninguna, la plantilla sigue siendo válida pero no generará executors al desplegarse

Los errores de validación se muestran con la ubicación exacta del error.
