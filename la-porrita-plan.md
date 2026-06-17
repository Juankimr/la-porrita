# La Porrita - Plan del Proyecto

## Goal
Crear una aplicación web completa para gestionar una porra del Mundial 2026 con Django, HTMX, SQLite y Pandas, que importe predicciones desde Excel, sincronice resultados con football-data.org y muestre rankings/estadísticas.

## Análisis del Excel

### Hojas Principales
| Hoja | Dimensiones | Propósito |
|------|-------------|-----------|
| WORLDCUP | 170x124 | Partidos, predicciones por jugador, clasificaciones por grupo |
| ADMIN | 267x33 | Reglas de puntuación, predicciones por fase, puntos |
| CLAS | 14x19 | Clasificación general con puntos totales y por fase |
| DailyPrediction | 35x38 | Predicciones diarias por jugador |
| DailyClas | 8x39 | Clasificación diaria |
| Stats | 55x42 | Estadísticas, pichichi, MVP |
| Fixture | 51x67 | Fixture completo del mundial |
| Equipos | 63x20 | Lista de equipos con grupos |

### Mapeo a Modelos Django
```
Excel Hoja → Modelo Django
─────────────────────────────
Equipos → Team (nombre, grupo, bandera)
WORLDCUP → Match (fecha, hora, local, visitante, goles, fase)
WORLDCUP → Prediction (jugador, partido, goles local, goles visitante)
ADMIN → ScoringConfig (reglas de puntuación)
CLAS → StandingSnapshot (clasificación en momento dado)
Stats → ScorerStat (pichichi, MVP)
Credits → Participant (nombre del jugador)
```

### Sistema de Puntuación (configurable)
- Signo 1X2: X puntos
- Diferencia de goles (con 1X2): Y puntos
- Resultado exacto: Z puntos
- Posición exacta grupo: A puntos
- Equipos por ronda: B puntos
- Campeón: C puntos
- Subcampeón: D puntos
- Pichichi: E puntos
- MVP: F puntos

## Tasks

### Fase 1: Configuración del Proyecto
- [ ] 1.1 Crear estructura Django con `uv` y configurar settings
  - Crear proyecto `porrita` y app `pool`
  - Configurar SQLite, templates, static files
  - Agregar dependencias: django, pandas, openpyxl, django-htmx, tailwind
  - Verificar: `uv run python manage.py runserver` funciona

- [ ] 1.2 Diseñar modelos Django
  - Participant, Team, Match, Prediction, SpecialPrediction
  - StandingSnapshot, ScorerStat, ScoringConfig
  - ImportLog, ApiSyncLog
  - Verificar: `uv run python manage.py makemigrations` genera migraciones

- [ ] 1.3 Crear management commands básicos
  - `seed_demo_data` para poblar datos de prueba
  - Verificar: `uv run python manage.py seed_demo_data` funciona

### Fase 2: Importación Excel
- [ ] 2.1 Crear script exploratorio mejorado
  - Analizar hoja WORLDCUP para extraer partidos y predicciones
  - Analizar hoja ADMIN para extraer configuración de puntuación
  - Analizar hoja CLAS para extraer clasificación
  - Verificar: Script imprime estructura correcta

- [ ] 2.2 Implementar servicio de importación Excel
  - `import_pool_excel` management command
  - Parsear hoja WORLDCUP: partidos (columnas 22-30) y predicciones por jugador
  - Parsear hoja ADMIN: configuración de puntuación
  - Parsear hoja Equipos: lista de selecciones
  - Verificar: Command importa datos correctamente en SQLite

- [ ] 2.3 Crear vista admin para importación
  - Formulario HTMX para subir Excel
  - Preview de datos importados
  - Log de importaciones
  - Verificar: Se puede subir Excel desde el navegador

### Fase 3: Integración API
- [ ] 3.1 Crear cliente API football-data.org
  - `FootballDataClient` con autenticación X-Auth-Token
  - Endpoints: competitions, matches, standings, scorers
  - Manejo de errores 400, 403, 404, 429
  - Caché con TTL configurable
  - Verificar: `sync_football_data` obtiene datos de la API

- [ ] 3.2 Implementar sincronización de resultados
  - `sync_football_data` management command
  - Actualizar goles reales en Match
  - Calcular automáticamente ganador/empate
  - Log de sincronizaciones en ApiSyncLog
  - Verificar: Después de sync, partidos tienen resultados reales

### Fase 4: Lógica de Puntuación
- [ ] 4.1 Implementar cálculo de puntos
  - `calculate_prediction_score(prediction, match)`
  - Soporte para signo, diferencia goles, resultado exacto
  - Bonificaciones por fase (grupos, octavos, etc.)
  - Verificar: Predicción exacta da puntos correctos

- [ ] 4.2 Crear command de recálculo
  - `recalculate_scores` que recalcula todos los puntos
  - Actualizar StandingSnapshot después del cálculo
  - Verificar: Después de recalcular, clasificación está actualizada

### Fase 5: Vistas Web con HTMX
- [ ] 5.1 Dashboard principal
  - Resumen: partidos jugados, predicciones, líder
  - HTMX: actualización en tiempo real
  - Tailwind: diseño responsive
  - Verificar: Dashboard muestra datos correctos

- [ ] 5.2 Clasificación general
  - Tabla ordenable con posiciones
  - Filtros por fase
  - Badges: acertado, parcial, fallado, pendiente
  - Verificar: Clasificación se actualiza con HTMX

- [ ] 5.3 Vista de partidos
  - Lista de partidos con resultado real y predicciones
  - Filtro por partido: qué predijo cada jugador
  - Filtro por jugador: sus predicciones
  - Verificar: Filtros funcionan sin recarga

- [ ] 5.4 Estadísticas
  - Ranking diario
  - Estadísticas de pichichi
  - Vista de MVP (o carga manual)
  - Verificar: Estadísticas muestran datos correctos

### Fase 6: Búsqueda y UX
- [ ] 6.1 Implementar buscador
  - Búsqueda por participante, equipo, partido
  - Resultados con HTMX (sin recarga)
  - Verificar: Búsqueda retorna resultados correctos

- [ ] 6.2 Tablas ordenables
  - Ordenar por columna en clasificación y partidos
  - HTMX para ordenación dinámica
  - Verificar: Click en columna ordena la tabla

### Fase 7: Tests y Documentación
- [ ] 7.1 Crear tests básicos
  - Tests de modelos
  - Tests de servicios de importación
  - Tests de lógica de puntuación
  - Verificar: `uv run python manage.py test` pasa

- [ ] 7.2 Documentación README
  - Instalación con uv
  - Variables de entorno (FOOTBALL_DATA_TOKEN)
  - Comandos de gestión
  - Verificar: README explica todo correctamente

## Done When
- [ ] Se puede importar Excel y ver predicciones en la web
- [ ] Se puede sincronizar resultados con football-data.org
- [ ] Clasificación se calcula automáticamente
- [ ] Dashboard muestra datos en tiempo real con HTMX
- [ ] Tests pasan correctamente
- [ ] Documentación completa

## Tech Stack
- Django 5.x + HTMX
- SQLite
- Pandas + openpyxl
- Tailwind CSS (via CDN o django-tailwind)
- uv para gestión de dependencias

## API Configuration
```env
FOOTBALL_DATA_TOKEN=your_token_here
FOOTBALL_DATA_BASE_URL=https://api.football-data.org/v4
WORLD_CUP_COMPETITION_ID=WC  # Código de competición
```

## File Structure
```
la-porrita/
├── manage.py
├── pyproject.toml
├── .env.example
├── README.md
├── porrita/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── pool/
│   ├── models.py
│   ├── services/
│   │   ├── excel_importer.py
│   │   ├── football_api.py
│   │   └── scoring.py
│   ├── management/
│   │   └── commands/
│   │       ├── import_pool_excel.py
│   │       ├── sync_football_data.py
│   │       ├── recalculate_scores.py
│   │       └── seed_demo_data.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── classification.html
│       ├── matches.html
│       └── stats.html
└── tests/
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```
