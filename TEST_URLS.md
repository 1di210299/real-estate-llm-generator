# URLs de Prueba - Multi-Content-Type System

## 🏠 Real Estate (Propiedades)

### Brevitas
```
https://www.brevitas.com/costa-rica/properties/casa-en-escazu-con-vista
https://www.brevitas.com/costa-rica/properties/apartamento-en-san-jose
```

### Coldwell Banker
```
https://www.coldwellbankercostarica.com/property/oceanview-villa-jaco
https://www.coldwellbankercostarica.com/property/modern-home-escazu
```

### Encuentra24
```
https://www.encuentra24.com/costa-rica-es/bienes-raices-venta-casas/casa-en-santa-ana/12345678
https://www.encuentra24.com/costa-rica-es/bienes-raices-venta-apartamentos
```

---

## 🗺️ Tours (Actividades)

### CostaRica.org (Operador Local Costarricense)
```
https://costarica.org/tours/
https://costarica.org/tours/arenal/
https://costarica.org/tours/monteverde/
https://costarica.org/tours/manuel-antonio/
https://costarica.org/tours/guanacaste/
```

### Desafío Adventure Company (Operador Costarricense)
```
https://www.desafiocostarica.com/
https://www.desafiocostarica.com/tour-detail/rafting-balsa-river-costa-rica-2-3
https://www.desafiocostarica.com/tour-detail/lost-canyon-canyoning-costa-rica
https://www.desafiocostarica.com/tour-detail/costa-rica-rafting-sarapiqui-river
https://www.desafiocostarica.com/tour-detail/gravity-falls-waterfall-canyoning
```

### Sky Adventures (Empresa Familiar Costarricense)
```
https://skyadventures.travel/
https://skyadventures.travel/tickets/
```

### Anywhere Costa Rica
```
https://www.anywhere.com/costa-rica/tours
https://www.anywhere.com/costa-rica/tours/canopy-tour
https://www.anywhere.com/costa-rica/tours/rafting
https://www.anywhere.com/costa-rica/tours/hot-springs
```

### Viator (Internacional)
```
https://www.viator.com/tours/Costa-Rica/Arenal-Volcano-and-Hot-Springs-Day-Trip/d742-3876SANJOSE
https://www.viator.com/tours/Costa-Rica/Monteverde-Cloud-Forest-and-Hanging-Bridges/d742-12345
https://www.viator.com/tours/Jaco/Zipline-Canopy-Tour/d5161-6789
```

### GetYourGuide
```
https://www.getyourguide.com/costa-rica-l123/from-san-jose-arenal-volcano-tour-t123456/
https://www.getyourguide.com/manuel-antonio-l567/zipline-adventure-t789012/
```

### TripAdvisor (Tours)
```
https://www.tripadvisor.com/AttractionProductReview-g309293-d11452345-Arenal_Volcano_Tour
https://www.tripadvisor.com/AttractionProductReview-g309293-d12345678-Manuel_Antonio_National_Park_Tour
```

---

## 🍴 Restaurants (Restaurantes)

### TripAdvisor (Restaurants)
```
https://www.tripadvisor.com/Restaurant_Review-g309293-d1234567-La_Esquina_de_Buenos_Aires
https://www.tripadvisor.com/Restaurant_Review-g309293-d7654321-Park_Cafe_Restaurant
```

### Yelp
```
https://www.yelp.com/biz/restaurante-grano-de-oro-san-jose
https://www.yelp.com/biz/olive-garden-escazu-san-jose
```

### OpenTable
```
https://www.opentable.com/r/restaurante-silvestre-san-jose
https://www.opentable.com/r/tin-jo-asian-restaurant-san-jose
```

---

## 💡 Local Tips / Travel Advice

### WikiVoyage
```
https://en.wikivoyage.org/wiki/Costa_Rica
https://en.wikivoyage.org/wiki/San_Jos%C3%A9_(Costa_Rica)
```

### Lonely Planet
```
https://www.lonelyplanet.com/costa-rica/travel-tips-and-articles
https://www.lonelyplanet.com/costa-rica/san-jose/practical-information
```

---

## 🚗 Transportation

### Rome2Rio
```
https://www.rome2rio.com/map/San-Jose-Costa-Rica/Jaco
https://www.rome2rio.com/map/San-Jose-Airport-SJO/Arenal-Volcano-National-Park
https://www.rome2rio.com/map/San-Jose-Costa-Rica/Manuel-Antonio-National-Park
```

---

## 🧪 Pasos para Probar

### 1. **Test Real Estate (ya funcionaba antes)**
```bash
URL: https://www.coldwellbankercostarica.com/property/oceanview-villa-jaco
Content Type: 🏠 Real Estate (default)
Expected: Precio, bedrooms, bathrooms, ubicación
```

### 2. **Test Tour (NUEVO)**
```bash
URL: https://www.viator.com/tours/Costa-Rica/Arenal-Volcano-and-Hot-Springs-Day-Trip/d742-3876SANJOSE
Content Type: 🗺️ Tour / Actividad
Expected: Duración, precio, dificultad, qué incluye
```

### 3. **Test Restaurant (NUEVO)**
```bash
URL: https://www.tripadvisor.com/Restaurant_Review-g309293-d1234567-La_Esquina_de_Buenos_Aires
Content Type: 🍴 Restaurante
Expected: Tipo de cocina, rango de precio, horarios
```

### 4. **Test Auto-Detection**
```bash
URL: https://www.viator.com/tours/...
Content Type: Dejar en "Real Estate"
Expected: Backend debería detectar "tour" automáticamente
```

---

## ⚠️ Notas Importantes

### Para URLs reales de Coldwell Banker:
```bash
# Ir al sitio y copiar una URL real
https://www.coldwellbankercostarica.com/properties/
# Ejemplo de una propiedad real que existe ahora:
https://www.coldwellbankercostarica.com/en/property/listing-21317-four-bedroom-home-in-the-village-inside-the-eco-residential-hacienda-pinilla/
```

### Para URLs de Viator:
```bash
# Buscar tours en Costa Rica:
https://www.viator.com/Costa-Rica/d742-ttd
# Copiar URL de cualquier tour
```

### Para Testing Rápido (URLs que sabemos existen):
1. **Coldwell Banker** (Real Estate): 
   - Ir a https://www.coldwellbankercostarica.com/properties/
   - Click en cualquier propiedad
   - Copiar URL

2. **Viator** (Tours):
   - Ir a https://www.viator.com/Costa-Rica/d742-ttd
   - Click en cualquier tour
   - Copiar URL

3. **TripAdvisor** (Restaurants):
   - Buscar "restaurants san jose costa rica" en Google
   - Click en resultado de TripAdvisor
   - Copiar URL

---

## 🎯 Verificaciones

### ✅ Checklist de Testing

#### Backend:
- [ ] Endpoint `/api/ingest/content-types/` retorna 5 tipos
- [ ] POST con `content_type: "tour"` usa prompt de tour
- [ ] POST con `content_type: "restaurant"` usa prompt de restaurant
- [ ] Detección automática funciona (sin especificar content_type)

#### Frontend:
- [ ] Dropdown muestra 5 opciones con icons
- [ ] Al cambiar dropdown, descripción cambia
- [ ] Al extraer, se envía el `content_type` seleccionado
- [ ] Resultados muestran badge del tipo

#### Extracción:
- [ ] Real Estate extrae: precio, bedrooms, bathrooms
- [ ] Tour extrae: duración, precio, dificultad
- [ ] Restaurant extrae: cocina, precio, horarios

---

## 🐛 Troubleshooting

### Si falla la extracción:
1. Verificar que URL es accesible (no requiere login)
2. Revisar logs del backend para ver qué prompt se usó
3. Verificar que el content_type se está enviando correctamente

### Si no se muestra el dropdown:
1. Verificar que `/api/ingest/content-types/` funciona
2. Abrir DevTools → Network → verificar llamada
3. Verificar console.log de loadContentTypes()

### Si no detecta automáticamente:
1. Es normal, la detección automática es smart pero no perfecta
2. Usuario puede cambiar manualmente en el dropdown
3. Fase 2 mejorará esto con auto-suggest visual
