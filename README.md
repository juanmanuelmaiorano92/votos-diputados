# LegisTrack — Predictor de Votaciones en la Cámara de Diputados

**Proyecto Final — Ciencia de Datos aplicada a Política Legislativa**

**Equipo:** Estefanía Zangaro · Martina Pusso · Milagros Cosentino · Juan Manuel Maiorano

---

## Qué hace este proyecto

LegisTrack predice cómo votaría cada uno de los 257 diputados activos de la Cámara de Diputados de la Nación Argentina ante un proyecto de ley hipotético. El usuario ingresa el título de una ley y quién la firma (un diputado actual o el Poder Ejecutivo Nacional), inicia sesión, y el sistema devuelve una predicción por diputado (AFIRMATIVO, NEGATIVO o ABSTENCIÓN) junto con la distribución total de votos.

El modelo se entrena con datos de votaciones desde 2019 en adelante; sus features históricas (afinidad de cada diputado, de su bloque, etc.) se calculan sobre el historial completo de la cámara, que se remonta a la década de 1990.

---

## Estado actual

| Etapa | Descripción | Estado |
|---|---|---|
| Scraping | Descarga del historial de votaciones desde la API de la HCDN | Completo |
| STG 1 — Filtrado | Reducción al padrón actual de diputados | Completo |
| STG 2 — Transformación | Limpieza, normalización de títulos y consolidación de votos por proyecto | Completo |
| STG 3 — Filtro de títulos | Eliminación de registros sin valor temático (mociones, habilitaciones, etc.) | Completo |
| STG 4 — Features semánticas | Embeddings y clustering temático de los títulos de ley | Completo |
| Features de autoría | Bloque del autor del proyecto, si es del Poder Ejecutivo, si coincide con el bloque del votante | Completo |
| Modelado | Comparación de 6 modelos con validación temporal — ganador: LightGBM, F1-macro 0.581 | Completo |
| API (FastAPI) | Backend que sirve el historial de diputados y las predicciones | Completo |
| Base de datos y autenticación | Usuarios, login (JWT) e historial de predicciones por usuario (Supabase) | Completo |
| App web multisección | Consultar diputado, predecir una votación, ver mis predicciones — requiere login | Completo |
| Deploy en la nube | Evaluado a fondo (Render, Hugging Face Spaces, Google Cloud Run) | No requerido — la cátedra autorizó demo local |

El proyecto se corre localmente (API + app en la propia máquina): ver [Cómo correr el proyecto localmente](#cómo-correr-el-proyecto-localmente). No hay un link público — el deploy se evaluó en detalle (ver `specs/017-deploy-nube/`) pero no fue necesario.

---

## Estructura del repositorio

```
legistrack-predictor/
├── notebooks/
│   ├── Scraping.ipynb                    # Descarga datos de la HCDN
│   ├── STG_1_Filtrado.ipynb              # Filtra al padrón actual de diputados
│   ├── STG_2_transformacion.ipynb        # Limpieza y consolidación de votos
│   ├── STG_3_filtro_titulos.ipynb        # Elimina registros sin valor temático
│   ├── STG_4_features_titulo.ipynb       # Embeddings y clustering de temas
│   ├── STG_5_features_diputado.ipynb     # Rama sin autoría (histórica)
│   ├── STG_6_modelado.ipynb              #   comparación de modelos
│   ├── STG_7_tuning.ipynb                #   afinado de hiperparámetros
│   ├── STG_8_serializar_artefactos.ipynb #   artefactos para la API
│   ├── STG_5.2_features_autor.ipynb          # Rama con autoría (vigente)
│   ├── STG_5.3_dataset_entrenamiento_autor.ipynb
│   ├── STG_6.2_modelado_autor.ipynb          #   ganador: LightGBM, F1-macro 0.581
│   ├── STG_6.3_experimento_factorial_negativos.ipynb  # experimento (no reemplazó al modelo vigente)
│   ├── STG_7.2_tuning_autor.ipynb
│   └── STG_8.2_serializar_artefactos_autor.ipynb  # artefactos vigentes de la API
├── data/                            # datasets y artefactos entrenados (CSVs vía Git LFS; .sav y .env no se versionan)
├── api/                             # backend FastAPI
│   ├── main.py                      # arma la app y precarga el modelo al iniciar
│   ├── modelo.py                    # carga los artefactos y arma cada predicción
│   ├── database.py                  # lee los CSV de historial/snapshots
│   ├── db.py                        # conexión a la base de datos (Supabase)
│   ├── tablas.py                    # tablas de usuarios y predicciones
│   ├── seguridad.py                 # hash de contraseñas y JWT
│   ├── schemas.py                   # esquemas de entrada/salida
│   └── routers/                     # endpoints: diputados, predecir, auth, historial
├── app/                             # aplicación Streamlit
│   ├── app.py                       # punto de entrada, arma el menú de navegación
│   ├── comun.py                     # login, sesión y llamadas a la API
│   └── paginas/                     # Consultar, Predecir, Mis predicciones
├── specs/                           # documentación técnica de cada feature
├── memoria/
│   └── DECISIONES.md                # bitácora de decisiones del proyecto
├── CLAUDE.md                        # instrucciones para el asistente IA
├── CONSTITUCION.md                  # principios no negociables del proyecto
└── requirements.txt                 # dependencias del proyecto
```

---

## Cómo correr el proyecto localmente

### Requisitos previos

- Python 3.10 o superior
- pip
- Una base de datos PostgreSQL (el proyecto usa [Supabase](https://supabase.com), nivel gratuito) para usuarios y login

### Instalación

```bash
git clone https://github.com/juanmanuelmaiorano92/legistrack-predictor.git
cd legistrack-predictor
pip install -r requirements.txt
```

### Configurar variables de entorno

La API necesita un archivo `.env` (no se versiona) con la conexión a la base y la clave de firma de los tokens de login. Copiar `.env.example` a `.env` y completar:

- `DATABASE_URL` — cadena de conexión a la base PostgreSQL (Supabase)
- `JWT_SECRET_KEY` — clave para firmar los tokens de sesión
- `USUARIO_PRUEBA` / `CLAVE_PRUEBA` — credenciales de un usuario de prueba que la API crea sola al arrancar (si no existe todavía)

### Levantar la API

```bash
uvicorn api.main:app --reload
```

La primera vez tarda unos segundos en arrancar porque precarga el modelo entrenado. Queda disponible en `http://127.0.0.1:8000`.

### Levantar la app (en otra terminal)

```bash
streamlit run app/app.py
```

La app se abre en `http://localhost:8501` y pide iniciar sesión (o registrarse) antes de mostrar cualquier pantalla — usa el usuario de prueba de `.env`, o uno nuevo desde "Registrarse".

### Ejecutar los notebooks (opcional)

No hace falta para usar la app: los datasets y artefactos ya entrenados están incluidos en `data/`. Los notebooks sirven para reproducir el pipeline completo desde cero, en orden de dependencias: `Scraping` → `STG_1` → `STG_2` → `STG_3` → `STG_4`, y desde ahí dos ramas independientes — `STG_5`→`STG_8` (histórica, sin autoría) y `STG_5.2`→`STG_8.2` (vigente, con autoría, la que usa la API hoy). Abrirlos con Jupyter Notebook o JupyterLab:

```bash
jupyter notebook
```

---

## Stack tecnológico

| Capa | Herramientas |
|---|---|
| Procesamiento de datos | Python, Pandas, NumPy |
| NLP y features semánticas | sentence-transformers, scikit-learn |
| Modelado | scikit-learn, LightGBM (modelo ganador), XGBoost (comparado y descartado) |
| Backend / API | FastAPI, Uvicorn, Pydantic |
| Base de datos y autenticación | PostgreSQL (Supabase), SQLAlchemy, JWT (python-jose), bcrypt/passlib |
| Aplicación web | Streamlit |
| Deploy | Evaluado a fondo (Render, Hugging Face Spaces, Google Cloud Run) — no requerido; el proyecto corre en local |

---

