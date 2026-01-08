# Reporte de Debugging - Deployment DigitalOcean App Platform

**Fecha:** 8 de enero de 2026  
**App:** kp-realestate (ID: a3f4fb2d-82c0-431e-ab43-16c433aecdab)  
**URL:** https://goldfish-app-3hc23.ondigitalocean.app

## Resumen Ejecutivo

Sesión de debugging para resolver errores 404 en el chatbot RAG desplegado en DigitalOcean App Platform. El problema principal fue que las requests del frontend al backend no llegaban correctamente debido a múltiples problemas de configuración de ingress y conflictos de puertos.

---

## Problema Inicial

**Síntoma:** Frontend y Backend desplegados correctamente, pero al intentar usar el chatbot, todas las requests a `/chat/` retornaban **404 Not Found**.

**Error en consola:**
```
POST https://goldfish-app-3hc23.ondigitalocean.app/chat/ 404 (Not Found)
❌ Error response: 
<!doctype html>
<html lang="en">
<head>
  <title>Not Found</title>
</head>
<body>
  <h1>Not Found</h1><p>The requested resource was not found on this server.</p>
</body>
</html>
```

**Observación clave:** El HTML de error era genérico, NO venía de Django, lo que indicaba que las requests nunca llegaban al backend.

---

## Proceso de Debugging

### 1. Análisis de Logs (Commit: 4d892be)

**Acción:** Agregamos extensive logging en backend y frontend para ver qué estaba pasando.

**Backend logs agregados:**
- `backend/config/urls.py`: Print de todos los URL patterns al startup
- `backend/apps/chat/urls.py`: Confirmación de que chat URLs se cargaron
- `backend/apps/chat/views.py`: Log de cada POST request con path, headers, data

**Frontend logs agregados:**
- `frontend/src/components/Chatbot.tsx`: 
  - Log de configuración de API_URL
  - Log de cada fetch request con URL y payload
  - Log de response status y errores

**Resultado:** Los logs del backend **NO mostraban ningún POST a `/chat/`**, confirmando que las requests no llegaban al backend.

---

### 2. Verificación de Headers (Curl Tests)

**Test realizado:**
```bash
curl -v https://goldfish-app-3hc23.ondigitalocean.app/health/
```

**Headers reveladores:**
```
< HTTP/2 404
< x-do-app-origin: 3df5d58d-13e3-4936-a2f1-84a0e03f2e8a
< x-do-orig-status: 404
```

**Conclusión:** El `x-do-app-origin` correspondía al ID del **frontend**, NO del backend. Las requests estaban siendo enrutadas al frontend en lugar del backend.

---

### 3. Primer Intento: Agregar Trailing Slashes (Commit: 644b8e8)

**Hipótesis:** Las reglas de ingress tenían `/chat` sin trailing slash, pero Django usa `/chat/` con trailing slash.

**Cambio realizado:**
```yaml
# Antes
prefix: /chat

# Después  
prefix: /chat/
```

**Resultado:** ❌ **FALLÓ** - DigitalOcean normaliza automáticamente las rutas y **QUITA las trailing slashes**. El spec activo seguía teniendo `/chat` sin slash.

---

### 4. Segundo Intento: Quitar Trailing Slashes del Frontend (Commit: 7948b79)

**Hipótesis:** Ya que DO normaliza sin trailing slash, el frontend debe llamar sin trailing slash.

**Cambios realizados:**
- `frontend/src/components/Chatbot.tsx`: `/chat/` → `/chat`
- `frontend/src/components/PropertyList.tsx`: `/properties/` → `/properties`

**Resultado:** ❌ **FALLÓ** - Seguía 404, el problema era más profundo.

---

### 5. Tercer Intento: Corregir Orden de Campos en Ingress (Commit: 4fd4167)

**Descubrimiento:** Al revisar la documentación oficial de DO, encontramos que el orden de los campos en las reglas de ingress era **INCORRECTO**.

**Documentación de DO muestra:**
```yaml
ingress:
  rules:
    - match:          # PRIMERO match
        path:
          prefix: /api
      component:      # DESPUÉS component
        name: web-service
```

**Nuestro spec tenía:**
```yaml
ingress:
  rules:
    - component:      # ❌ INVERTIDO
        name: web
      match:
        path:
          prefix: /chat
```

**Cambio realizado:** Reordenamos para poner `match:` antes de `component:` en todas las reglas.

**Resultado:** ❌ **FALLÓ** - Curiosamente, DO re-ordena automáticamente al guardar el spec, así que esto NO era el problema real.

---

### 6. Solución Final: Conflicto de Puertos (Commit: 017452a)

**Descubrimiento CRÍTICO:** Tanto frontend como backend estaban configurados en el **mismo puerto 8080**:

```yaml
services:
- name: web          # Backend
  http_port: 8080
  
- name: frontend     # Frontend
  http_port: 8080    # ❌ CONFLICTO
```

**Problema:** DigitalOcean probablemente no sabía a cuál servicio enrutar las requests cuando ambos compartían el mismo puerto.

**Solución aplicada:**
```yaml
services:
- name: web          # Backend
  http_port: 8080    # ✅ Puerto 8080
  
- name: frontend     # Frontend  
  http_port: 3000    # ✅ Puerto 3000
  envs:
  - key: PORT
    scope: RUN_TIME
    value: "3000"
```

**Estado actual:** ⏳ **EN DEPLOYMENT** - Esperando que termine para validar.

---

## Problemas Identificados

### 1. **Conflicto de Puertos**
- **Severidad:** ALTA
- **Causa raíz:** Frontend y backend en el mismo puerto (8080)
- **Impacto:** Ingress no podía distinguir a qué servicio enrutar
- **Solución:** Frontend movido a puerto 3000

### 2. **Trailing Slashes**
- **Severidad:** MEDIA
- **Causa raíz:** DigitalOcean normaliza URLs quitando trailing slashes
- **Impacto:** Mismatch entre URLs del frontend y reglas de ingress
- **Solución:** Frontend llama sin trailing slash, Django maneja con APPEND_SLASH

### 3. **Falta de Visibility**
- **Severidad:** MEDIA
- **Causa raíz:** Sin logs suficientes para debugging
- **Impacto:** Difícil diagnosticar dónde fallaba el routing
- **Solución:** Extensive logging agregado (conservar para futuro)

---

## Configuración Final

### Ingress Rules (.do/app.yaml)
```yaml
ingress:
  rules:
  - match:
      path:
        prefix: /chat
    component:
      name: web
  - match:
      path:
        prefix: /properties
    component:
      name: web
  - match:
      path:
        prefix: /conversations
    component:
      name: web
  - match:
      path:
        prefix: /documents
    component:
      name: web
  - match:
      path:
        prefix: /ingest
    component:
      name: web
  - match:
      path:
        prefix: /health
    component:
      name: web
  - match:
      path:
        prefix: /admin
    component:
      name: web
  - match:
      path:
        prefix: /static
    component:
      name: web
  - match:
      path:
        prefix: /
    component:
      name: frontend
```

### Services Configuration
```yaml
services:
- name: web           # Backend Django
  dockerfile_path: ./backend/Dockerfile
  source_dir: ./backend
  http_port: 8080
  health_check:
    http_path: /health/

- name: frontend      # Frontend React + Express
  source_dir: ./frontend
  http_port: 3000     # ✅ Puerto diferente
  environment_slug: node-js
  run_command: npm start
  health_check:
    http_path: /health
  envs:
  - key: VITE_API_URL
    scope: BUILD_TIME
    value: ${APP_URL}
  - key: PORT
    scope: RUN_TIME
    value: "3000"
```

### Frontend API URLs
```typescript
// Chatbot.tsx
const API_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/chat`      // Sin trailing slash
  : 'http://localhost:8000/chat/';              // Local con trailing slash

// PropertyList.tsx
const API_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/properties` // Sin trailing slash
  : 'http://localhost:8000/properties/';         // Local con trailing slash
```

---

## Lecciones Aprendidas

1. **Puertos únicos por servicio:** Nunca usar el mismo puerto para múltiples servicios en App Platform
2. **DigitalOcean normaliza URLs:** Las trailing slashes se eliminan automáticamente del spec
3. **Logging es crucial:** Sin logs detallados, debugging de routing es casi imposible
4. **Verificar headers:** `x-do-app-origin` revela qué servicio realmente está respondiendo
5. **Documentación oficial:** Siempre consultar docs de DO antes de asumir comportamiento

---

## Próximos Pasos

1. ✅ Esperar que deployment actual (commit 017452a) termine
2. ⏳ Probar endpoint `/chat` con curl
3. ⏳ Verificar en browser que chatbot funciona
4. ⏳ Revisar logs del backend para confirmar requests llegan
5. ⏳ Si funciona, limpiar logs de debug (opcional)
6. ⏳ Documentar configuración final en README

---

## Commits Relevantes

1. **4d892be** - "debug: add extensive logging to backend and frontend"
2. **644b8e8** - "fix: add trailing slashes to ingress rules to match Django URLs" (REVERTIDO)
3. **7948b79** - "fix: remove trailing slashes from frontend API URLs"
4. **4fd4167** - "fix: correct ingress rules syntax - match before component"
5. **017452a** - "fix: change frontend port to 3000 to avoid conflict with backend" (ACTUAL)

---

## Recursos Consultados

- [DigitalOcean App Platform - App Spec Reference](https://docs.digitalocean.com/products/app-platform/reference/app-spec/)
- [DigitalOcean - Manage Internal Routing](https://docs.digitalocean.com/products/app-platform/how-to/manage-internal-routing/)
- [DigitalOcean - Manage Networking](https://docs.digitalocean.com/products/app-platform/how-to/manage-networking/)

---

**Estado Final:** ⏳ Deployment en progreso con solución de conflicto de puertos
