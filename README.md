# 🏛️ LegisTrack — Predictor de Votaciones en la Cámara de Diputados de Argentina

**Proyecto Final — Ciencia de Datos aplicada a Política Legislativa**

**Equipo:** Estefanía Zangaro · Martina Pusso · Milagros Cosentino · Juan Manuel Maiorano

---

## ¿Qué hace este proyecto?

LegisTrack es un sistema de predicción que, dado el texto de un proyecto de ley hipotético y quién sería el autor de dicho proyecto, estima cómo votaría cada uno de los diputados activos de la Cámara de Diputados de la Nación Argentina.

El usuario ingresa el título o descripción de una ley imaginaria y el sistema devuelve una predicción por diputado (AFIRMATIVO, NEGATIVO o ABSTENCIÓN), junto con una estimación de si el proyecto lograría o no la mayoría simple necesaria para su aprobación.

---

## ¿Cómo lo estamos haciendo?

### Datos

- **Dataset de votaciones**: ~578.500 registros históricos de votaciones nominales en la Cámara de Diputados, con columnas de diputado, bloque, provincia, voto y título del proyecto.
- **Dataset de proyectos parlamentarios**: ~111.000 proyectos con autor, tipo, expediente y cámara de origen.

### Pipeline

```
Datos crudos
    │
    ├── STG 1 — Scraping
    │
    ├── STG 2 — Transformación y limpieza
    │       ├── Eliminación de ruido procedimental
    │       ├── Extracción de título base (colapso de votaciones por artículo)
    │       └── Consolidación por moda de voto (una postura por diputado por ley)
    │
    ├── STG 3 — Ingeniería de Features (en curso)
    │       ├── Vectorización TF-IDF de títulos
    │       ├── Encoding de bloque y provincia
    │       ├── Flag es_oficialismo (según año de votación)
    │       └── Features temporales (ciclo electoral, año)
    │
    ├── STG 4 — Modelado (pendiente)
    │       └── Clasificación multinomial (Random Forest / XGBoost / LightGBM)
    │
    └── STG 5 — Aplicación web (pendiente)
            └── Streamlit app con predicción interactiva
```

### Stack tecnológico

| Capa | Herramientas |
|---|---|
| Procesamiento | Python, Pandas, NumPy |
| NLP | Scikit-learn (TF-IDF), regex |
| Modelado | Scikit-learn, XGBoost / LightGBM |
| Aplicación | Streamlit |
| Infraestructura | GitHub + Streamlit Community Cloud |

---

## Estado actual del proyecto

| Etapa | Estado |
|---|---|
| Recolección de datos | ✅ Completo |
| Limpieza y transformación | ✅ Completo |
| Ingeniería de features | 🔄 En curso |
| Entrenamiento del modelo | ⏳ Pendiente |
| Aplicación web | ⏳ Pendiente |

---

## Estructura del repositorio

```
votos-diputados/
├── data/
│   └── proyectos_parlamentarios2.1.csv
├── notebooks/
│   ├── STG_1_carga.ipynb
│   └── STG_2_transformacion.ipynb
├── models/              # (pendiente)
├── app/                 # (pendiente — Streamlit)
└── README.md
```

---

> Proyecto desarrollado en el marco de la carrera de **Ciencia de Datos** — 2025
