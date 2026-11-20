"""
DASHBOARD DE PARTICIPACIÓN
Actividad por asignatura y estudiante, y evolución de accesos en el tiempo.
Conceptos: st.sidebar.multiselect(), st.sidebar.select_slider(), st.metric() y st.columns().

Ubicación: pages/1_Participacion.py (junto a app.py y datos.py)
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from datos import cargar_datos, mostrar_grafico

st.set_page_config(page_title="Participación", page_icon="👥", layout="wide")

# 1. Cargar datos
maestra, kpis = cargar_datos()

frec = kpis["kpi_frecuencia_ingreso"].copy()
frec["mes_txt"] = pd.to_datetime(dict(year=frec["anio"], month=frec["mes"], day=1)).dt.strftime("%Y-%m")

st.title("👥 Dashboard de Participación")

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
]

if df.empty:
    st.warning("Seleccioná al menos una asignatura.")
    st.stop()

# 3. KPIs principales
activos = int(df["activo"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Alumnos activos", f"{activos:,}")
c2.metric("Cobertura de participación", f"{activos / len(df) * 100:.1f}%")
c3.metric("Interacciones promedio", f"{df['interacciones'].mean():.0f}")
c4.metric("Tiempo promedio de uso", f"{df['tiempo_uso_h'].mean():.1f} h")

st.caption("Los indicadores y los gráficos por alumno abarcan toda la cursada. El rango de meses filtra los gráficos de evolución.")

st.divider()

# 4. Evolución de accesos: 2 gráficos en paralelo
st.subheader("Evolución de accesos por mes")
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig1 = px.line(
        frec_f.sort_values("mes_txt"), x="mes_txt", y="total_actividades",
        color="asignatura", markers=True,
        title="Total de actividades", labels={"mes_txt": "Mes", "total_actividades": "Actividades"},
    )
    mostrar_grafico(fig1)

with col_g2:
    fig2 = px.line(
        frec_f.sort_values("mes_txt"), x="mes_txt", y="alumnos_unicos_activos",
        color="asignatura", markers=True,
        title="Alumnos únicos activos", labels={"mes_txt": "Mes", "alumnos_unicos_activos": "Alumnos"},
    )
    mostrar_grafico(fig2)

st.divider()

# 5. Participación por asignatura: 2 gráficos en paralelo
st.subheader("Participación por asignatura")
col_g3, col_g4 = st.columns(2)

with col_g3:
    inter = kpis["kpi_promedio_interacciones"]
    inter = inter[inter["asignatura"].isin(asignaturas_sel)]
    fig3 = px.bar(
        inter, x="promedio_interacciones", y="asignatura", orientation="h",
        color="asignatura", title="Interacciones promedio",
        labels={"promedio_interacciones": "Interacciones", "asignatura": ""},
    )
    fig3.update_layout(showlegend=False)
    mostrar_grafico(fig3)

with col_g4:
    tiempo = kpis["kpi_tiempo_promedio_uso"]
    tiempo = tiempo[tiempo["asignatura"].isin(asignaturas_sel)].copy()
    tiempo["horas"] = tiempo["tiempo_promedio_uso"] / 60   # el KPI está en minutos
    fig4 = px.bar(
        tiempo, x="horas", y="asignatura", orientation="h",
        color="asignatura", title="Tiempo promedio de uso (horas)",
        labels={"horas": "Horas", "asignatura": ""},
    )
    fig4.update_layout(showlegend=False)
    mostrar_grafico(fig4)

st.divider()

# 6. Participación por estudiante: 2 gráficos en paralelo
st.subheader("Participación por estudiante")
col_g5, col_g6 = st.columns(2)

with col_g5:
    top = df.nlargest(10, "interacciones").sort_values("interacciones")
    fig5 = px.bar(
        top, x="interacciones", y="usuario", orientation="h", color="asignatura",
        title="Top 10 alumnos con más interacciones",
        labels={"interacciones": "Interacciones", "usuario": "Alumno"},
    )
    mostrar_grafico(fig5)

with col_g6:
    fig6 = px.histogram(
        df, x="dias_sin_actividad", nbins=15,
        title="Días sin actividad hasta la fecha de corte",
        labels={"dias_sin_actividad": "Días sin actividad"},
    )
    fig6.update_layout(yaxis_title="Cantidad de alumnos")
    mostrar_grafico(fig6)
