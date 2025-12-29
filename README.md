# 🏠 Real Estate LLM - Web App

App completa con React + Node.js + OpenAI streaming para generar respuestas de bienes raíces.

## 🚀 Quick Start (Local)

```bash
npm install
node server.js
```

Abre `http://localhost:3001` en tu navegador.

## 📦 Deploy a Producción

Lee **[DEPLOY.md](./DEPLOY.md)** para instrucciones completas de:
- Railway (recomendado)
- Render
- Vercel
- Fly.io

## 🔑 Variables de Entorno

Crea `.env` en este directorio:
```bash
OPENAI_API_KEY=sk-proj-tu-key-aqui
PORT=3001
```

## 📁 Archivos

- `index.html` - Frontend React (single-page app)
- `server.js` - Backend Express + OpenAI con streaming
- `package.json` - Dependencias Node.js
- `docs/` - System prompt y documentación
- `vercel.json` / `render.yaml` / `railway.json` - Configs de deployment

## ✨ Features

- ✅ Streaming en tiempo real (SSE)
- ✅ 21 escenarios pre-cargados
- ✅ Interfaz moderna con React
- ✅ Backend Express con CORS
- ✅ Listo para deployment

## 🆘 Troubleshooting

**Error: Cannot find module 'docs/system_prompt.md'**
```bash
cp -r ../docs ./docs
```

**Error: OPENAI_API_KEY not found**
Crea archivo `.env` con tu API key.

**Quiero deployarlo:**
Lee [DEPLOY.md](./DEPLOY.md) - setup en 5 minutos con Railway.
