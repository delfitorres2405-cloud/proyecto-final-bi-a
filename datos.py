"""
datos.py
Carga y preparación de datos compartida por TODOS los dashboards del TFI.
Cada dashboard hace `from datos import ...` y no vuelve a leer ni limpiar nada.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# Configuración general
# ----------------------------------------------------------------------------
DATA = Path(__file__).parent / "data"

# En el notebook las asignaturas quedaron en minúscula (limpiar_tabla).
# Acá se pasan a un nombre prolijo para mostrar en los gráficos.
NOMBRES_ASIGNATURA = {
    "algebra": "Álgebra",
    "álgebra": "Álgebra",
    "algoritmos y estructuras de datos": "Algoritmos y Estructuras de Datos",
    "probabilidad y estadistica": "Probabilidad y Estadística",
    "probabilidad y estadística": "Probabilidad y Estadística",
}

ORDEN_ESTADOS = ["Promociona", "Regular", "Libre", "Sin Evaluar"]
COLORES_ESTADO = {
    "Promociona": "#2ecc71",   # verde
    "Regular": "#f1c40f",      # amarillo
    "Libre": "#e74c3c",        # rojo
    "Sin Evaluar": "#95a5a6",  # gris
}
COLORES_ACTIVIDAD = {"Activos": "#2ecc71", "Inactivos": "#e74c3c"}


def nombre_asignatura(valor):
    """'algoritmos y estructuras de datos' -> 'Algoritmos y Estructuras de Datos'."""
    texto = str(valor).strip()
    return NOMBRES_ASIGNATURA.get(texto.lower(), texto.capitalize())


# ----------------------------------------------------------------------------
# Carga (se ejecuta una sola vez gracias a la caché)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos():
    """Devuelve (tabla_maestra, dict_de_kpis) ya preparados."""
    # Los parquet viajan en el repositorio (carpeta data/)
    if not (DATA / "tabla_maestra.parquet").exists():
        raise FileNotFoundError("Falta data/tabla_maestra.parquet: copiá los parquet a la carpeta data/.")

    # --- KPIs: se leen todos los kpi_*.parquet que haya en /data ---
    kpis = {}
    for ruta in sorted(DATA.glob("kpi_*.parquet")):
        kpi = pd.read_parquet(ruta)
        if "asignatura" in kpi.columns:
            kpi["asignatura"] = kpi["asignatura"].map(nombre_asignatura)
        kpis[ruta.stem] = kpi

    # --- Tabla maestra (una fila por alumno y asignatura) ---
    maestra = pd.read_parquet(DATA / "tabla_maestra.parquet")
    maestra["asignatura"] = maestra["asignatura"].map(nombre_asignatura)

    # Columnas opcionales: si el parquet no las trae, se reconstruyen o quedan vacías
    if "ultima_actividad" not in maestra:
        maestra["ultima_actividad"] = (
            maestra["ultima_interaccion"] if "ultima_interaccion" in maestra else pd.NaT
        )
    if "fecha_corte" not in maestra:
        maestra["fecha_corte"] = pd.to_datetime(maestra["ultima_actividad"]).max()
    if "dias_sin_actividad" not in maestra:
        maestra["dias_sin_actividad"] = (
            pd.to_datetime(maestra["fecha_corte"]) - pd.to_datetime(maestra["ultima_actividad"])
        ).dt.days
    if "avance" not in maestra:
        maestra["avance"] = float("nan")

    # Inscripciones dadas de baja: no cuentan como matrícula vigente
    maestra["vigente"] = maestra["estado_inscripcion"].astype(str).str.lower().ne("baja")

    # Seguro anti-duplicados: si un alumno aparece dos veces en la misma materia
    # se conserva la fila vigente (las bajas quedan al final del orden).
    maestra = (
        maestra.sort_values("vigente", ascending=False)
        .drop_duplicates(["usuario", "asignatura"])
        .reset_index(drop=True)
    )

    # tiempo_uso_min viene como timedelta -> se pasa a horas (número)
    maestra["tiempo_uso_h"] = pd.to_timedelta(maestra["tiempo_uso_min"]).dt.total_seconds() / 3600

    maestra["activo"] = maestra["activo"].fillna(False).astype(bool)
    maestra["estado"] = maestra["estado"].fillna("Sin Evaluar")

    return maestra, kpis


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def pct(parte, total):
    """Porcentaje seguro (devuelve 0 si el total es 0)."""
    return float(parte) / float(total) * 100 if total else 0.0


def fmt(valor, formato="{:.1f}", sufijo=""):
    """Formatea un número; si es nulo devuelve un guion."""
    if valor is None or pd.isna(valor):
        return "–"
    return formato.format(valor) + sufijo


def _version_nueva():
    """True si la versión de Streamlit soporta width='stretch'."""
    try:
        mayor, menor = (int(p) for p in st.__version__.split(".")[:2])
        return (mayor, menor) >= (1, 50)
    except Exception:
        return False


def mostrar_grafico(fig, **kwargs):
    """st.plotly_chart a todo el ancho, compatible con versiones viejas y nuevas."""
    if _version_nueva():
        try:
            return st.plotly_chart(fig, width="stretch", **kwargs)
        except Exception:
            pass
    return st.plotly_chart(fig, use_container_width=True, **kwargs)


def mostrar_tabla(df, **kwargs):
    """st.dataframe a todo el ancho, compatible con versiones viejas y nuevas."""
    if _version_nueva():
        try:
            return st.dataframe(df, width="stretch", **kwargs)
        except Exception:
            pass
    return st.dataframe(df, use_container_width=True, **kwargs)