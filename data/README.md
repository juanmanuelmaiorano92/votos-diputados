# Archivos de datos — LegisTrack

Esta carpeta contiene todos los archivos de datos del pipeline.
Los archivos `.csv` están almacenados con **Git LFS** (Large File Storage).

## Requisito antes de clonar

Tener Git LFS instalado. Una sola vez por máquina:

```bash
# Windows (con winget)
winget install Git.LFS

# O descargar desde: https://git-lfs.com

# Luego, dentro del repo clonado:
git lfs install
git lfs pull
```

---

## Tabla de archivos

| Archivo | Tamaño | Origen | Descripción |
|---|---|---|---|
| `diputados_actuales.csv` | 22 KB | Manual / externo | Nómina de los 257 diputados actuales. Entrada de STG_1. |
| `hcdn_votaciones_historico.csv` | 140 MB | `notebooks/Scraping.ipynb` | Histórico completo de votaciones descargado de la HCDN. Entrada de STG_1. Almacenado en Git LFS. |
| `proyectos_parlamentarios2.1.csv` | 33 MB | Manual / externo | Dataset de proyectos parlamentarios con expedientes y autores. Usado en STG_3. |
| `votaciones_filtrado.csv` | 17.6 MB | `notebooks/STG_1_Filtrado.ipynb` | Votos filtrados a la nómina actual de diputados. |
| `df_consolidado.csv` | 7 MB | `notebooks/STG_2_transformacion.ipynb` | Votos consolidados por diputado-proyecto (un voto por fila). Base del modelo. |
| `df_modelado.csv` | 6 MB | `notebooks/STG_3_filtro_titulos.ipynb` | `df_consolidado` con títulos filtrados semánticamente y columnas de autor. |
| `df_features_titulo.csv` | 4.7 MB | `notebooks/STG_4_features_titulo.ipynb` | Features semánticas por título: embeddings (384 dims) y tema (K-Means, K=20). |
| `titulos_autor.xlsx` | 90 KB | `notebooks/STG_3_filtro_titulos.ipynb` | Planilla de auditoría: 1022 títulos únicos con autor asignado (30.5% de cobertura). |

---

## Cadena del pipeline

```
Scraping.ipynb
    → hcdn_votaciones_historico.csv
        → STG_1_Filtrado.ipynb
            → votaciones_filtrado.csv
                → STG_2_transformacion.ipynb
                    → df_consolidado.csv
                        → STG_3_filtro_titulos.ipynb
                            → df_modelado.csv
                            → titulos_autor.xlsx
                                → STG_4_features_titulo.ipynb
                                    → df_features_titulo.csv
```
