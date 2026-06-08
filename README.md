# LegisTrack — Predictor de Votaciones en la Cámara de Diputados

**Proyecto Final — Ciencia de Datos aplicada a Política Legislativa**

**Equipo:** Estefanía Zangaro · Martina Pusso · Milagros Cosentino · Juan Manuel Maiorano

---

## Qué hace este proyecto

LegisTrack es un sistema en construcción que busca predecir cómo votaría cada diputado activo de la Cámara de Diputados de la Nación Argentina ante un proyecto de ley hipotético. El usuario ingresa el título o descripción de una ley y el sistema devuelve una predicción por diputado (AFIRMATIVO, NEGATIVO o ABSTENCIÓN), junto con una estimación de si el proyecto lograría la mayoría simple necesaria para ser aprobado.

El modelo se entrena sobre el historial de votaciones nominales de la cámara desde 2020.

---

## Estado actual

| Etapa | Descripción | Estado |
|---|---|---|
| Scraping | Descarga del historial de votaciones desde la API de la HCDN | Completo |
| STG 1 — Filtrado | Reducción al padrón actual de 257 diputados | Completo |
| STG 2 — Transformación | Limpieza, normalización de títulos y consolidación de votos por proyecto | Completo |
| STG 3 — Filtro de títulos | Eliminación de registros sin valor temático (mociones, habilitaciones, etc.) | Completo |
| STG 4 — Features semánticas | Embeddings y clustering temático de los títulos de ley | Completo |
| App web v1 | Historial de votaciones por diputado, publicada en Streamlit Cloud | Completo |
| Modelado | Entrenamiento del clasificador de voto | Pendiente |
| Predicción en la app | Integración del modelo en la app para predicción interactiva | Pendiente |

La app ya está publicada y permite consultar el historial de votaciones de cualquier diputado activo. La funcionalidad de predicción se integrará cuando el modelo esté entrenado.

**App:** [votos-diputados-gxuaqsn2fp3jdntelqxfgy.streamlit.app](https://votos-diputados-gxuaqsn2fp3jdntelqxfgy.streamlit.app/)

---

## Estructura del repositorio

```
legistrack-predictor/
├── notebooks/
│   ├── Scraping.ipynb              # Descarga datos de la HCDN
│   ├── STG_1_Filtrado.ipynb        # Filtra al padrón actual de diputados
│   ├── STG_2_transformacion.ipynb  # Limpieza y consolidación de votos
│   ├── STG_3_filtro_titulos.ipynb  # Elimina registros sin valor temático
│   └── STG_4_features_titulo.ipynb # Embeddings y clustering de temas
├── data/
│   ├── hcdn_votaciones_historico.csv  # Dataset crudo (no se modifica)
│   ├── df_consolidado.csv             # Output de STG 2
│   ├── df_modelado.csv                # Output de STG 3 (base para el modelo)
│   └── df_features_titulo.csv         # Output de STG 4 (embeddings por título)
├── app/
│   └── app.py                      # Aplicación Streamlit
├── specs/                          # Documentación técnica de cada feature
├── memoria/
│   └── DECISIONES.md               # Bitácora de decisiones del proyecto
├── CLAUDE.md                       # Instrucciones para el asistente IA
├── CONSTITUCION.md                 # Principios no negociables del proyecto
└── requirements.txt                # Dependencias del proyecto
```

---

## Cómo correr el proyecto localmente

### Requisitos previos

- Python 3.10 o superior
- pip

### Instalación

```bash
git clone https://github.com/juanmanuelmaiorano92/legistrack-predictor.git
cd legistrack-predictor
pip install -r requirements.txt
```

### Ejecutar los notebooks

Los notebooks se corren en orden. Cada uno lee el archivo de la etapa anterior y genera uno nuevo en `data/`. Abrirlos con Jupyter Notebook o JupyterLab:

```bash
jupyter notebook
```

Orden de ejecución:
1. `Scraping.ipynb` → genera `hcdn_votaciones_historico.csv`
2. `STG_1_Filtrado.ipynb` → genera `votaciones_filtrado.csv`
3. `STG_2_transformacion.ipynb` → genera `df_consolidado.csv`
4. `STG_3_filtro_titulos.ipynb` → genera `df_modelado.csv`
5. `STG_4_features_titulo.ipynb` → genera `df_features_titulo.csv`

> Los archivos CSV ya procesados están incluidos en el repositorio, así que no es necesario re-correr los notebooks para usar la app.

### Levantar la app localmente

```bash
streamlit run app/app.py
```

La app se abre automáticamente en el navegador en `http://localhost:8501`.

---

## Stack tecnológico

| Capa | Herramientas |
|---|---|
| Procesamiento de datos | Python, Pandas, NumPy |
| NLP y features semánticas | sentence-transformers, scikit-learn |
| Modelado (pendiente) | scikit-learn, XGBoost / LightGBM |
| Aplicación web | Streamlit |
| Deploy | Streamlit Community Cloud + GitHub |

---

