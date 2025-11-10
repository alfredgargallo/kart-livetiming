# K4TCS_Leaderboard_v9.py  (CORREGIDO: combina color + flash/slide-in y flash usa box-shadow)
import streamlit as st
import pandas as pd
import os
import time
from pathlib import Path
from datetime import datetime

# ============================
# CONFIGURABLES
# ============================
CSV_URL = os.environ.get("CSV_URL", "https://drive.google.com/uc?export=download&id=1AjZI7oFmivBzs39fX7f_bWwyULA_P75T")
@st.cache_data(ttl=3)
def load_data():
    # cache-buster para evitar caché intermedia en Drive
    url = f"{CSV_URL}&v={int(time.time())}"
    return pd.read_csv(url)

REFRESH_INTERVAL = 3
# ============================

st.set_page_config(page_title="K4TCS Leaderboard", layout="centered")
st.image("kartingsallent.png")

st.markdown("""
    <div style="background-color: black; padding: 10px 30px; align-items: center;">
        <h1 style="color: white; ; text-align: center; margin: 0;">Livetiming</h1>
    </div>
    <br>
""", unsafe_allow_html=True)  
#st.title("🏁 K4TCS Leaderboard")
#st.caption("🏁 Tabla de tiempos")

# ============================
# CSS para estilos y animaciones
# ============================
st.markdown("""
<style>
/* transición para cambio de fondo (fade-in al colorear) */
.fade-cell {
    transition: background-color 0.8s ease, border 0.4s ease;
}

/* colores base para eventos (no serán sobrescritos por flash) */
.gray { background-color: #f0f0f0; }
.green { background-color: #d4edda; border: 2px solid #28a745; }
.purple { background-color: #ead3ff; border: 2px solid #7f3fbf; }

/* flash amarillo: efecto de resplandor (box-shadow) para NO sobrescribir el background */
.flash {
    animation: flashGlow 1s ease-in-out;
}
@keyframes flashGlow {
    0%   { box-shadow: 0 0 18px 8px rgba(255,235,59,0.95); }
    100% { box-shadow: none; }
}

/* slide-in lateral cuando sube de posición */
.slide-in {
    animation: slideInAnim 0.8s ease-out;
}
@keyframes slideInAnim {
    0%   { transform: translateX(-20px); opacity: 0.5; }
    100% { transform: translateX(0); opacity: 1; }
}

/* estilos de tabla */
th {
    background: #f8f9fa;
    border-bottom: 2px solid #ccc;
}
td, th {
    padding: 6px;
    text-align: center;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    font-family: Arial, Helvetica, sans-serif;
}

/* transición global para reordenación de filas */
tr {
    transition: all 0.8s ease-in-out;
}
</style>
""", unsafe_allow_html=True)

# === Bloque extra: ocultar menú/footers/enlaces de Streamlit ===
st.markdown("""
<style>
#MainMenu {visibility: hidden;}   /* Oculta el menú (tres puntos) */
footer {visibility: hidden;}      /* Oculta el pie "Made with Streamlit" y enlaces */
header {visibility: hidden;}      /* Oculta la cabecera superior */
</style>
""", unsafe_allow_html=True)

# ============================
# util
# ============================
def ms_to_timestr(ms):
    if pd.isna(ms):
        return "-"
    try:
        ms = int(ms)
    except Exception:
        return "-"
    mm = ms // 60000
    ss = (ms % 60000) // 1000
    mmm = ms % 1000
    return f"{mm:02d}:{ss:02d}:{mmm:03d}"

def render_table_with_fade(display_df, row_color):
    html = "<table>"
    # encabezados
    html += "<tr>"
    for col in display_df.columns:
        html += f"<th>{col}</th>"
    html += "</tr>"

    # filas
    for i, row in display_df.iterrows():
        color_class = row_color.get(i, "")
        # color_class puede contener varias clases separadas por espacios, p.e. "green flash slide-in"
        row_class = f"fade-cell {color_class}" if color_class else "fade-cell"
        html += f"<tr class='{row_class}'>"
        for val in row:
            html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# ============================
# Estado persistente
# ============================
if "prev_best" not in st.session_state:
    st.session_state.prev_best = {}
if "global_best" not in st.session_state:
    st.session_state.global_best = None
if "last_lap_count" not in st.session_state:
    st.session_state.last_lap_count = {}
if "prev_positions" not in st.session_state:
    st.session_state.prev_positions = {}

placeholder = st.empty()

# ============================
# Bucle principal
# ============================
try:
    while True:
        now = datetime.now()

        try:
            df = load_data()
        except Exception:
            placeholder.info("⏳ Esperando datos (archivo no legible todavía)...")
            time.sleep(REFRESH_INTERVAL)
            continue

        if df.empty:
            placeholder.info("⏳ No hay karts encontrados todavía.")
            time.sleep(REFRESH_INTERVAL)
            continue

        # asegurar tipos
        df["kart_number"] = df["kart_number"].astype(str)
        df["lap_time_ms"] = pd.to_numeric(df.get("lap_time_ms", pd.Series(dtype=float)), errors="coerce")
        df["lap_index"] = pd.to_numeric(df.get("lap_index", pd.Series(dtype=float)), errors="coerce")

        # resumen por kart (ignorando lap_index==1 para best_time_ms)
        summary_rows = []
        for kart, g in df.groupby("kart_number"):
            g_sorted = g.sort_values("lap_index")
            laps_total = int(g_sorted["lap_index"].max()) if not g_sorted["lap_index"].isna().all() else 0
            estado = "vuelta inicial" if laps_total <= 1 else ""
            valid_laps = g_sorted[g_sorted["lap_index"] > 1]
            best_time_ms = valid_laps["lap_time_ms"].min() if not valid_laps.empty else pd.NA
            last_time_ms = g_sorted["lap_time_ms"].iloc[-1] if not g_sorted["lap_time_ms"].isna().all() else pd.NA
            summary_rows.append({
                "kart_number": kart,
                "best_time_ms": best_time_ms,
                "last_time_ms": last_time_ms,
                "laps": laps_total,
                "estado": estado
            })
        summary = pd.DataFrame(summary_rows)

        if summary.empty:
            placeholder.info("⏳ No hay karts encontrados todavía.")
            time.sleep(REFRESH_INTERVAL)
            continue

        # calcular global best actual
        bests_nonnull = summary["best_time_ms"].dropna()
        current_global_best = int(bests_nonnull.min()) if not bests_nonnull.empty else None

        prev_global_best = st.session_state.global_best
        prev_best_map = st.session_state.prev_best
        prev_lap_map = st.session_state.last_lap_count
        prev_positions = st.session_state.prev_positions

        # ordenar por best_time_ms
        summary_sorted = summary.sort_values("best_time_ms", na_position="last").reset_index(drop=True)

        display = summary_sorted.copy()
        display["Mejor vuelta"] = display["best_time_ms"].apply(ms_to_timestr)
        display["Última vuelta"] = display["last_time_ms"].apply(ms_to_timestr)
        display["Vueltas"] = display["laps"].astype(int)
        display["Estado"] = display["estado"]
        display = display[["kart_number", "Mejor vuelta", "Última vuelta", "Vueltas", "Estado"]]
        display.columns = ["Kart", "Mejor vuelta", "Última vuelta", "Vueltas", "Estado"]

        # decidir colores y efectos por fila
        row_color = {}
        for i, row in summary_sorted.iterrows():
            k = str(row["kart_number"])
            laps = int(row["laps"]) if not pd.isna(row["laps"]) else 0
            last = row["last_time_ms"]
            best = row["best_time_ms"]

            prev_laps = prev_lap_map.get(k, 0)
            new_event = laps > prev_laps

            # color base según evento (purple > green > gray). Por defecto ""
            color = ""
            if new_event and (not pd.isna(last)) and laps >= 2:
                purple = False
                try:
                    if prev_global_best is None:
                        if current_global_best is not None and int(last) == int(current_global_best):
                            purple = True
                    else:
                        if int(last) < int(prev_global_best):
                            purple = True
                except Exception:
                    purple = False

                if purple:
                    color = "purple"
                else:
                    prev_best = prev_best_map.get(k, None)
                    improved = False
                    if prev_best is None or pd.isna(prev_best):
                        if not pd.isna(best) and int(best) == int(last):
                            improved = True
                    else:
                        try:
                            if int(last) < int(prev_best):
                                improved = True
                        except Exception:
                            improved = False

                    if improved:
                        color = "green"
                    else:
                        color = "gray"

            # si sube de posición, añadimos flash + slide-in SIN eliminar la clase de color
            prev_pos = prev_positions.get(k)
            if prev_pos is not None and i < prev_pos:
                if color:
                    color = f"{color} flash slide-in"
                else:
                    color = "flash slide-in"

            row_color[i] = color

        # render
        with placeholder.container():
            render_table_with_fade(display, row_color)
            st.caption(f"Última actualización: {now.strftime('%H:%M:%S')}")

        # actualizar estados en session_state
        new_prev_best = {}
        new_last_lap_count = {}
        new_positions = {}
        for i, r in summary_sorted.iterrows():
            k = str(r["kart_number"])
            b = r["best_time_ms"]
            laps = int(r["laps"]) if not pd.isna(r["laps"]) else 0
            new_last_lap_count[k] = laps
            new_positions[k] = i
            if pd.isna(b):
                if k in prev_best_map:
                    new_prev_best[k] = prev_best_map[k]
            else:
                try:
                    new_prev_best[k] = int(b)
                except Exception:
                    new_prev_best[k] = prev_best_map.get(k)

        st.session_state.prev_best = new_prev_best
        st.session_state.global_best = int(current_global_best) if current_global_best is not None else prev_global_best
        st.session_state.last_lap_count = new_last_lap_count
        st.session_state.prev_positions = new_positions

        time.sleep(REFRESH_INTERVAL)

except KeyboardInterrupt:
    pass
