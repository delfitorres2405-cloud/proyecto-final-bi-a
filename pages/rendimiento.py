"""
DASHBOARD DE RENDIMIENTO ACADÉMICO
Notas, situación académica y su relación con la actividad en el aula virtual.
Conceptos: st.sidebar.multiselect(), st.metric(), st.columns() y gráficos de dispersión.

Ubicación: pages/3_Rendimiento.py (junto a app.py y datos.py)
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from datos import COLORES_ESTADO, ORDEN_ESTADOS, cargar_datos, mostrar_grafico

st.set_page_config(page_title="Rendimiento académico", page_icon="🎓", layout="wide")

# 1. Cargar datos
maestra, kpis = cargar_datos()

# kpi_cruces_analiticos: interacciones, tiempo de uso y puntaje final por alumno
cruces = kpis["kpi_cruces_analiticos"].copy()
cruces["tiempo_uso_h"] = pd.to_timedelta(cruces["tiempo_uso_min"]).dt.total_seconds() / 3600
cruces = cruces.merge(maestra[["usuario", "asignatura", "estado"]], on=["usuario", "asignatura"], how="left")

st.title("🎓 Dashboard de Rendimiento Académico")

# 2. Filtros en Sidebar: asignaturas y estados
asignaturas_opt = sorted(maestra["asignatura"].unique())
asignaturas_sel = st.sidebar.multiselect("Filtrar asignaturas:", asignaturas_opt, default=asignaturas_opt)

estados_sel = st.sidebar.multiselect("Filtrar estados:", ORDEN_ESTADOS, default=ORDEN_ESTADOS)

# Filtrado con Pandas usando .isin() (solo matrícula vigente, sin bajas)
df = maestra[
    (maestra["asignatura"].isin(asignaturas_sel))
    & (maestra["estado"].isin(estados_sel))
    & (maestra["vigente"])
]

# Para relacionar notas con actividad se usan solo los alumnos evaluados
evaluados = df[df["estado"] != "Sin Evaluar"]
cruces_f = cruces[
    (cruces["asignatura"].isin(asignaturas_sel))
    & (cruces["estado"].isin(estados_sel))
    & (cruces["estado"] != "Sin Evaluar")
]

if evaluados.empty:
    st.warning("No hay alumnos evaluados para los filtros seleccionados.")
    st.stop()


def correlacion(x, y):
    r = x.corr(y)
    return "–" if pd.isna(r) else f"{r:.2f}"


# 3. KPIs principales
c1, c2, c3, c4 = st.columns(4)
c1.metric("Alumnos evaluados", f"{len(evaluados):,}")
c2.metric("Promedio de notas", f"{evaluados['puntaje_final'].mean():.1f}")
c3.metric("Correlación interacciones - nota", correlacion(cruces_f["interacciones"], cruces_f["puntaje_final"]))
c4.metric("Correlación tiempo de uso - nota", correlacion(cruces_f["tiempo_uso_h"], cruces_f["puntaje_final"]))

st.caption("Correlación de Pearson: cerca de 0 indica que no hay relación; cerca de 1, que a más actividad mayor nota.")

st.divider()

# 4. Relación entre actividad y rendimiento: 2 gráficos de dispersión en paralelo
st.subheader("Relación entre actividad y rendimiento")
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig1 = px.scatter(
        cruces_f, x="interacciones", y="puntaje_final", color="asignatura",
        hover_data=["usuario"], title="Interacciones vs. puntaje final",
        labels={"interacciones": "Interacciones", "puntaje_final": "Puntaje final"},
    )
    mostrar_grafico(fig1)

with col_g2:
    fig2 = px.scatter(
        cruces_f, x="tiempo_uso_h", y="puntaje_final", color="asignatura",
        hover_data=["usuario"], title="Tiempo de uso vs. puntaje final",
        labels={"tiempo_uso_h": "Tiempo de uso (horas)", "puntaje_final": "Puntaje final"},
    )
    mostrar_grafico(fig2)

st.divider()

# 5. Distribución de notas y estados: 2 gráficos en paralelo
st.subheader("Distribución de notas y situación académica")
col_g3, col_g4 = st.columns(2)

with col_g3:
    fig3 = px.histogram(
        evaluados, x="puntaje_final", color="asignatura", barmode="stack",
        title="Distribución de calificaciones",
    )
    fig3.update_traces(xbins=dict(start=0, end=100, size=10))
    fig3.update_layout(xaxis_title="Puntaje final", yaxis_title="Cantidad de alumnos", bargap=0.05)
    fig3.update_xaxes(range=[0, 100])
    mostrar_grafico(fig3)

with col_g4:
    estados = df.groupby(["asignatura", "estado"]).size().reset_index(name="alumnos")
    fig4 = px.bar(
        estados, x="alumnos", y="asignatura", color="estado", orientation="h", text="alumnos",
        color_discrete_map=COLORES_ESTADO, category_orders={"estado": ORDEN_ESTADOS},
        title="Situación académica por asignatura (%)",
    )
    fig4.update_layout(barnorm="percent", xaxis_title="% de alumnos", yaxis_title="")
    mostrar_grafico(fig4)

st.divider()

# 6. Comparación de calificaciones entre instrumentos
st.subheader("Comparación entre instrumentos de evaluación")

if "kpi_notas_instrumento" in kpis:
    instrumentos = kpis["kpi_notas_instrumento"]
    instrumentos = instrumentos[instrumentos["asignatura"].isin(asignaturas_sel)]
    fig5 = px.bar(
        instrumentos, x="evaluacion", y="promedio_pct", color="asignatura", barmode="group",
        labels={"evaluacion": "Instrumento", "promedio_pct": "Nota promedio (% del puntaje máximo)"},
    )
    mostrar_grafico(fig5)
else:
    st.info("Falta el KPI kpi_notas_instrumento: calculalo en el notebook y subilo a Drive.")
