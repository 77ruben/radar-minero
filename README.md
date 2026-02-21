# radar-minero
# 🔍 Radar Minero V6 PRO

Búsqueda automática de empleos en minería chilena, con notificaciones por Telegram cada 6 horas.

## Fuentes que monitorea

| Fuente | Tipo |
|--------|------|
| trabajoenmineria.cl | Portal especializado |
| trabajando.cl | Portal general |
| laborum.cl | Portal general |
| computrabajo.cl | Portal general |
| indeed.cl | Portal global |
| linkedin.com | Red profesional |
| codelco.com | Minera directa |
| bhp.com | Minera directa |
| collahuasi.cl | Minera directa |
| angloamerican.com | Minera directa |
| aminerals.cl | Minera directa |
| bne.cl | Gobierno Chile |

## ⚙️ Configuración inicial

### 1. Secrets en GitHub

Ve a tu repositorio → **Settings → Secrets and variables → Actions → New repository secret**

Agrega estos dos secrets:

| Secret | Valor |
|--------|-------|
| `TOKEN` | Token de tu bot de Telegram |
| `CHAT_ID` | Tu chat ID de Telegram |

> **¿Cómo obtener el TOKEN?** Habla con [@BotFather](https://t.me/BotFather) en Telegram → `/newbot`  
> **¿Cómo obtener tu CHAT_ID?** Habla con [@userinfobot](https://t.me/userinfobot) en Telegram

### 2. Crear archivo inicial de deduplicación

Crea un archivo vacío `seen_jobs.json` en la raíz del repositorio con este contenido:

```json
[]
```

### 3. Habilitar permisos de escritura en Actions

Ve a **Settings → Actions → General → Workflow permissions**  
Selecciona: ✅ **Read and write permissions**

### 4. Estructura del repositorio

```
tu-repo/
├── radar_minero.py           ← Script principal
├── seen_jobs.json            ← Avisos ya enviados (auto-actualizado)
├── .github/
│   └── workflows/
│       └── radar.yml         ← Automatización
└── README.md
```

## 🕐 Horario de ejecución

El bot corre a las **00:00, 06:00, 12:00 y 18:00 hora Chile** (aprox.).  
También puedes correrlo manualmente desde la pestaña **Actions** → **Run workflow**.

## 📨 Formato de notificación en Telegram

```
🔔 NUEVO EMPLEO - Laborum.cl
📋 Supervisor de Mantenimiento Planta
🏭 Compass Group S.A.
📍 Calama
⏰ Turno: 14X14
🔗 https://...
```

## 🔧 Personalización

Edita `radar_minero.py`:

- **`PERFIL`** → palabras clave del cargo que buscas
- **`EXCLUIR`** → cargos que NO quieres ver
- **`UBICACIONES_KEYWORDS`** → zonas de interés

## 🐛 Solución de problemas

- **No llegan mensajes:** Verifica que los secrets TOKEN y CHAT_ID estén bien configurados
- **Error de permisos al hacer push:** Activa "Read and write permissions" en Settings → Actions
- **Demasiados avisos irrelevantes:** Ajusta la lista `PERFIL` haciéndola más específica
