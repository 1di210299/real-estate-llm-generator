# 🚀 Guía de Deployment

## Opciones de Hosting

### 1. **Railway** (Recomendado - Más Simple)

**Ventajas:**
- ✅ FREE tier generoso (500 hrs/mes)
- ✅ Setup automático desde GitHub
- ✅ Variables de entorno fáciles
- ✅ Streaming SSE compatible

**Pasos:**

1. **Push a GitHub:**
```bash
cd /Users/1di/kp-real-estate-llm-prototype/web
git init
git add .
git commit -m "Initial commit"
gh repo create real-estate-llm --public --source=. --remote=origin --push
```

2. **Deploy en Railway:**
   - Ve a [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Selecciona "Deploy from GitHub repo"
   - Selecciona tu repo `real-estate-llm`
   - Railway detectará Node.js automáticamente

3. **Agregar Variables de Entorno:**
   - En el dashboard de Railway → Variables
   - Agrega: `OPENAI_API_KEY` = tu-key-aqui
   - Railway reiniciará automáticamente

4. **Obtener URL:**
   - Railway te da una URL pública: `https://your-app.railway.app`
   - Actualiza el fetch en `index.html` (línea ~320):
   ```javascript
   const res = await fetch('https://your-app.railway.app/generate', {
   ```

---

### 2. **Render**

**Ventajas:**
- ✅ FREE tier permanente
- ✅ SSL automático
- ⚠️ Se duerme después de 15 min de inactividad (FREE tier)

**Pasos:**

1. **Push a GitHub** (mismo paso 1 de arriba)

2. **Deploy en Render:**
   - Ve a [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Conecta tu repo de GitHub
   - Configuración:
     - **Name:** real-estate-llm
     - **Environment:** Node
     - **Build Command:** `npm install`
     - **Start Command:** `node server.js`
   
3. **Variables de Entorno:**
   - En "Environment" tab
   - Agrega: `OPENAI_API_KEY` = tu-key-aqui

4. **Actualizar URL en `index.html`:**
   ```javascript
   const res = await fetch('https://real-estate-llm.onrender.com/generate', {
   ```

---

### 3. **Vercel** (Alternativa Serverless)

**Ventajas:**
- ✅ Deploy instantáneo
- ✅ FREE tier generoso
- ⚠️ Requiere configuración especial para streaming

**Pasos:**

1. **Instalar Vercel CLI:**
```bash
npm install -g vercel
```

2. **Deploy:**
```bash
cd /Users/1di/kp-real-estate-llm-prototype/web
vercel
```

3. **Configurar Variables:**
```bash
vercel env add OPENAI_API_KEY
```

4. **Deploy a producción:**
```bash
vercel --prod
```

---

### 4. **Fly.io** (Para más control)

**Ventajas:**
- ✅ FREE tier (3 apps)
- ✅ Mejor para streaming
- ✅ Más control sobre la infra

**Pasos:**

1. **Instalar Fly CLI:**
```bash
brew install flyctl
```

2. **Login:**
```bash
fly auth login
```

3. **Inicializar app:**
```bash
cd /Users/1di/kp-real-estate-llm-prototype/web
fly launch --name real-estate-llm
```

4. **Configurar secrets:**
```bash
fly secrets set OPENAI_API_KEY=tu-key-aqui
```

5. **Deploy:**
```bash
fly deploy
```

---

## 📝 Checklist Pre-Deploy

- [ ] Copiar `docs/` y `scenarios/` al directorio `/web` o ajustar rutas
- [ ] Actualizar URL del backend en `index.html` (línea ~320)
- [ ] Configurar variable `OPENAI_API_KEY` en el hosting
- [ ] Probar que el streaming funciona en producción
- [ ] Configurar `.gitignore` (ya incluido)
- [ ] Agregar `.env.example` para otros developers

---

## 🔧 Ajustes Post-Deploy

### Actualizar URL del Backend

En `index.html`, busca (~línea 320):
```javascript
const res = await fetch('http://localhost:3001/generate', {
```

Reemplaza con:
```javascript
// Para Railway:
const res = await fetch('https://your-app.railway.app/generate', {

// Para Render:
const res = await fetch('https://real-estate-llm.onrender.com/generate', {

// Para Vercel:
const res = await fetch('https://your-app.vercel.app/generate', {

// Para Fly:
const res = await fetch('https://real-estate-llm.fly.dev/generate', {
```

### Copiar Archivos Necesarios

Si los paths relativos no funcionan en producción:
```bash
cd /Users/1di/kp-real-estate-llm-prototype/web
cp -r ../docs ./docs
cp -r ../scenarios ./scenarios
```

Luego actualiza `server.js`:
```javascript
// Cambiar de:
const systemPrompt = fs.readFileSync(path.join(__dirname, '../docs/system_prompt.md'), 'utf-8');

// A:
const systemPrompt = fs.readFileSync(path.join(__dirname, 'docs/system_prompt.md'), 'utf-8');
```

---

## 🎯 Recomendación Final

**Para testing rápido:** Usa **Railway** → Deploy en 2 minutos, free tier generoso, streaming funciona perfecto.

**Para producción seria:** Usa **Render** o **Fly.io** → Más estable, mejor uptime, configuración profesional.

**Para serverless:** Usa **Vercel** → Deploy instantáneo pero requiere ajustes para streaming.

---

## 🆘 Troubleshooting

### Error: "Cannot find module '../docs/system_prompt.md'"
```bash
cd /Users/1di/kp-real-estate-llm-prototype/web
cp -r ../docs ./docs
```

### Error: "OPENAI_API_KEY not found"
Verifica que configuraste la variable en el dashboard del hosting.

### Error: "Streaming no funciona"
Algunos hostings (como Vercel) tienen timeouts de 10s en el FREE tier. Usa Railway o Render.

### Error: "CORS blocked"
El backend ya tiene `app.use(cors())` configurado. Si persiste, agrega el dominio específico:
```javascript
app.use(cors({ origin: 'https://tu-dominio.com' }));
```

---

## 📞 Siguiente Paso

1. Elige un hosting (recomiendo Railway)
2. Sigue los pasos de arriba
3. Actualiza la URL en `index.html`
4. Comparte el link y prueba! 🎉
