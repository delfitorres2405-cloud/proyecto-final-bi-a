"""
DASHBOARD DE TRAZABILIDAD
Interacciones de los alumnos en el aula virtual: qué hacen y con qué intensidad.
Conceptos: st.sidebar.multiselect(), st.sidebar.select_slider(), st.metric() y st.columns().

Ubicación: pages/2_Trazabilidad.py (junto a app.py y datos.py)
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from datos import cargar_datos, mostrar_grafico

st.set_page_config(page_title="Trazabilidad", page_icon="🧭", layout="wide")

# 1. Cargar datos
maestra, kpis = cargar_datos()

frec = kpis["kpi_frecuencia_ingreso"].copy()
frec["mes_txt"] = pd.to_datetime(dict(year=frec["anio"], month=frec["mes"], day=1)).dt.strftime("%Y-%m")

acciones = kpis["kpi_tipos_evento"]

st.title("🧭 Dashboard de Trazabilidad")

# 2. Filtros en Sidebar: asignaturas y rango de meses
asignaturas_opt = sorted(maestra["asignatura"].unique())
asignaturas_sel = st.sidebar.multiselect("Filtrar asignaturas:", asignaturas_opt, default=asignaturas_opt)

meses_opt = sorted(frec["mes_txt"].unique())
mes_desde, mes_hasta = st.sidebar.select_slider(
    "Rango de meses:", options=meses_opt, value=(meses_opt[0], meses_opt[-1])
)

# Filtrado con Pandas usando .isin() (solo matrícula vigente, sin bajas)
df = maestra[(maestra["asignatura"].isin(asignaturas_sel)) & (maestra["vigente"])]

frec_f = frec[
    (frec["asignatura"].isin(asignaturas_sel))
    & (frec["mes_txt"] >= mes_desde)
    & (frec["mes_txt"] <= mes_hasta)
].copy()

if df.empty:
    st.warning("Seleccioná al menos una asignatura.")
    st.stop()

# 3. KPIs principales
total_inter = df["interacciones"].sum()
total_dias = df["dias_activos"].sum()
inter_por_dia = total_inter / total_dias if total_dias > 0 else 0
accion_top = acciones.nlargest(1, "total_interacciones")["accion"].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Interacciones totales", f"{total_inter:,.0f}")
c2.metric("Interacciones por día activo", f"{inter_por_dia:.1f}")
c3.metric("Días activos promedio", f"{df['dias_activos'].mean():.1f}")
c4.metric("Acción más frecuente", accion_top)

st.divider()

# 4. Tipos de acción y evolución en el tiempo
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Interacciones por tipo de acción")
    top_acc = acciones.nlargest(10, "total_interacciones").sort_values("total_interacciones")
    fig1 = px.bar(
        top_acc, x="total_interacciones", y="accion", orientation="h", color="total_interacciones",
        labels={"total_interacciones": "Interacciones", "accion": ""},
    )
    fig1.update_layout(coloraxis_showscale=False)
    mostrar_grafico(fig1)
    st.caption("Top 10 de acciones. Este KPI incluye todas las asignaturas.")

with col_g2:
    st.subheader("Actividades por alumno activo, por mes")
    frec_f["actividades_por_alumno"] = frec_f["total_actividades"] / frec_f["alumnos_unicos_activos"]
    fig2 = px.line(
        frec_f.sort_values("mes_txt"), x="mes_txt", y="actividades_por_alumno",
        color="asignatura", markers=True,
        labels={"mes_txt": "Mes", "actividades_por_alumno": "Actividades por alumno"},
    )
    mostrar_grafico(fig2)

st.divider()

# 5. Intensidad de uso por alumno
col_g3, col_g4 = st.columns(2)

with col_g3:
    st.subheader("Distribución de interacciones por alumno")
    fig3 = px.histogram(
        df, x="interacciones", nbins=20, color="asignatura",
        labels={"interacciones": "Interacciones"},
    )
    fig3.update_layout(yaxis_title="Cantidad de alumnos")
    mostrar_grafico(fig3)

with col_g4:
    st.subheader("Días activos vs. interacciones")
    fig4 = px.scatter(
        df, x="dias_activos", y="interacciones", color="asignatura",
        hover_data=["usuario"],
        labels={"dias_activos": "Días activos", "interacciones": "Interacciones"},
    )
    mostrar_grafico(fig4)
