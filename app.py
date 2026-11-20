"""
DASHBOARD GENERAL
Panorama académico y participación estudiantil (TFI - Business Intelligence & Analytics).
Conceptos: st.sidebar.multiselect(), st.metric(), st.columns() y gráficos Plotly.

Ejecutar con:  streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from datos import COLORES_ACTIVIDAD, ORDEN_ESTADOS, cargar_datos, mostrar_grafico, mostrar_tabla

st.set_page_config(page_title="Dashboard General", page_icon="📊", layout="wide")

# 1. Cargar datos
maestra, kpis = cargar_datos()

st.title("📊 Dashboard General")
st.caption("Panorama académico y participación estudiantil. Matrícula vigente (sin bajas).")

# 2. Filtro en Sidebar
asignaturas_opt = sorted(maestra["asignatura"].unique())
asignaturas_sel = st.sidebar.multiselect("Filtrar asignaturas:", asignaturas_opt, default=asignaturas_opt)

# Filtrado con Pandas usando .isin() (solo matrícula vigente, sin bajas)
df = maestra[(maestra["asignatura"].isin(asignaturas_sel)) & (maestra["vigente"])]

if df.empty:
    st.warning("Seleccioná al menos una asignatura.")
    st.stop()

evaluados = df[df["estado"] != "Sin Evaluar"]

# 3. KPIs principales (2 filas de 4 tarjetas)
total = len(df)
activos = int(df["activo"].sum())
aprobados = df["estado"].isin(["Promociona", "Regular"]).sum()
en_riesgo = ((~df["activo"]) & (df["estado"].isin(["Libre", "Sin Evaluar"]))).sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Matriculados vigentes", f"{total:,}")
c2.metric("Cobertura de participación", f"{activos / total * 100:.1f}%")
c3.metric("Promedio de notas", f"{evaluados['puntaje_final'].mean():.1f}")
c4.metric("Aprobación de cursada", f"{aprobados / total * 100:.1f}%")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Interacciones promedio", f"{df['interacciones'].mean():.0f}")
c6.metric("Tiempo promedio de uso", f"{df['tiempo_uso_h'].mean():.1f} h")
c7.metric("Avance promedio", f"{df['avance'].mean():.1f}%")
c8.metric("Alumnos en riesgo", f"{en_riesgo:,}")

st.caption(
    "Cobertura: activos / matriculados. Aprobación: (promocionados + regulares) / matriculados. "
    "En riesgo: inactivos que están libres o sin evaluar."
)

st.divider()

# 4. Resumen consolidado por asignatura (se arma con los KPIs calculados en el notebook)
st.subheader("Resumen consolidado por asignatura")


def semaforo(cobertura):
    # Alerta según la cobertura de participación
    if cobertura >= 70:
        return "🟢"
    elif cobertura >= 50:
        return "🟡"
    return "🔴"


resumen = df.groupby("asignatura").size().rename("Matriculados").reset_index()

cobertura = kpis["kpi_porcentaje_participacion"][["asignatura", "cobertura_participacion_pct"]]
notas = kpis["kpi_prom_calificaciones"][["asignatura", "promedio_calificaciones"]]
inter = kpis["kpi_promedio_interacciones"][["asignatura", "promedio_interacciones"]]
tiempo = kpis["kpi_tiempo_promedio_uso"][["asignatura", "tiempo_promedio_uso"]]

# % de promocionados, regulares y libres: una columna por estado
estados = (
    kpis["kpi_porc_aprobacion"]
    .pivot_table(index="asignatura", columns="estado", values="porcentaje_total", fill_value=0)
    .reindex(columns=ORDEN_ESTADOS, fill_value=0)
    .reset_index()
)

for kpi in [cobertura, notas, estados, inter, tiempo]:
    resumen = resumen.merge(kpi, on="asignatura", how="left")

resumen["tiempo_promedio_uso"] = resumen["tiempo_promedio_uso"] / 60   # el KPI está en minutos
resumen["Alerta"] = resumen["cobertura_participacion_pct"].map(semaforo)

resumen = resumen.rename(columns={
    "asignatura": "Asignatura",
    "cobertura_participacion_pct": "Cobertura (%)",
    "promedio_calificaciones": "Promedio de notas",
    "Promociona": "% Promociona",
    "Regular": "% Regular",
    "Libre": "% Libre",
    "Sin Evaluar": "% Sin evaluar",
    "promedio_interacciones": "Interacciones prom.",
    "tiempo_promedio_uso": "Tiempo prom. (h)",
})

columnas = [
    "Asignatura", "Alerta", "Matriculados", "Cobertura (%)", "Promedio de notas",
    "% Promociona", "% Regular", "% Libre", "% Sin evaluar", "Interacciones prom.", "Tiempo prom. (h)",
]
mostrar_tabla(
    resumen[columnas],
    hide_index=True,
    column_config={
        "Cobertura (%)": st.column_config.NumberColumn(format="%.1f"),
        "Promedio de notas": st.column_config.NumberColumn(format="%.1f"),
        "% Promociona": st.column_config.NumberColumn(format="%.1f"),
        "% Regular": st.column_config.NumberColumn(format="%.1f"),
        "% Libre": st.column_config.NumberColumn(format="%.1f"),
        "% Sin evaluar": st.column_config.NumberColumn(format="%.1f"),
        "Interacciones prom.": st.column_config.NumberColumn(format="%.0f"),
        "Tiempo prom. (h)": st.column_config.NumberColumn(format="%.1f"),
    },
)
st.caption("Alerta de cobertura: 🟢 70% o más · 🟡 entre 50% y 70% · 🔴 menos de 50%.")

st.divider()

# 5. Activos vs. inactivos: 2 gráficos en paralelo
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Activos vs. inactivos")
    datos_dona = pd.DataFrame({"Estado": ["Activos", "Inactivos"], "Cantidad": [activos, total - activos]})
    fig1 = px.pie(
        datos_dona, names="Estado", values="Cantidad", hole=0.5,
        color="Estado", color_discrete_map=COLORES_ACTIVIDAD,
    )
    fig1.update_traces(textinfo="percent+value")
    mostrar_grafico(fig1)

with col_g2:
    st.subheader("Participación por asignatura")
    por_materia = df.groupby("asignatura")["activo"].agg(Activos="sum", Total="count").reset_index()
    por_materia["Inactivos"] = por_materia["Total"] - por_materia["Activos"]
    largo = por_materia.melt(
        id_vars="asignatura", value_vars=["Activos", "Inactivos"],
        var_name="Estado", value_name="Cantidad",
    )
    fig2 = px.bar(
        largo, x="Cantidad", y="asignatura", color="Estado", orientation="h", text="Cantidad",
        color_discrete_map=COLORES_ACTIVIDAD,
    )
    fig2.update_layout(barnorm="percent", xaxis_title="% de alumnos", yaxis_title="")
    mostrar_grafico(fig2)

st.divider()

# 6. Rendimiento y tendencias: 2 gráficos en paralelo
col_g3, col_g4 = st.columns(2)

with col_g3:
    st.subheader("Distribución de calificaciones")
    fig3 = px.histogram(evaluados, x="puntaje_final", color="asignatura", barmode="stack")
    fig3.update_traces(xbins=dict(start=0, end=100, size=10))
    fig3.update_layout(xaxis_title="Puntaje final", yaxis_title="Cantidad de alumnos", bargap=0.05)
    fig3.update_xaxes(range=[0, 100])
    mostrar_grafico(fig3)

with col_g4:
    st.subheader("Tendencia de participación por mes")
    frec = kpis["kpi_frecuencia_ingreso"]
    frec = frec[frec["asignatura"].isin(asignaturas_sel)].copy()
    frec["mes_txt"] = pd.to_datetime(dict(year=frec["anio"], month=frec["mes"], day=1)).dt.strftime("%Y-%m")
    fig4 = px.line(
        frec.sort_values("mes_txt"), x="mes_txt", y="total_actividades", color="asignatura", markers=True,
        labels={"mes_txt": "Mes", "total_actividades": "Total de actividades"},
    )
    mostrar_grafico(fig4)
    st.caption("El último mes puede estar incompleto (los datos llegan hasta la fecha de corte).")