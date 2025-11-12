# Script 4 (nuevo): Presentador SCC que solo pinta la clasificación ya calculada
import os
import time
from datetime import datetime
import pandas as pd
import streamlit as st

# ============================
# CONFIGURABLES (SCC + Drive)
# ============================
CSV_URL = os.environ.get("CSV_URL", "https://drive.google.com/uc?export=download&id=1AjZI7oFmivBzs39fX7f_bWwyULA_P75T")
REFRESH_INTERVAL = 2  # segundos
# ============================

st.set_page_config(page_title="K4TCS Leaderboard", layout="centered")
st.image("kartingsallent.png")
st.markdown("""
    <div style="background-color: black; padding: 2px 5px; align-items: center;">
        <h3 style="color: white; text-align: center; margin: 0;">Livetiming</h3>
    </div>
    <div style="height: 2px;"></div>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.fade-cell { transition: background-color 0.8s ease, border 0.4s ease; }
.gray  { background-color: #f0f0f0; }
.green { background-color: #d4edda; border: 2px solid #28a745; }
.purple{ background-color: #ead3ff; border: 2px solid #7f3fbf; }
.flash { animation: flashGlow 1s ease-in-out; }
@keyframes flashGlow { 0% { box-shadow: 0 0 18px 8px rgba(255,235,59,0.95); } 100% { box-shadow: none; } }
.slide-in { animation: slideInAnim 0.8s ease-out; }
@keyframes slideInAnim { 0% { transform: translateX(-20px); opacity: 0.5; } 100% { transform: translateX(0); opacity: 1; } }
th { background: #d9d9d9; border-bottom: 2px solid #ccc; }
td, th { padding: 6px; text-align: center; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; font-family: Arial, Helvetica, sans-serif; }
tr { transition: all 0.8s ease-in-out; }
/* Ocultar UI Streamlit extra */
#MainMenu, header, footer, div[data-testid="stFooter"], div[data-testid="stToolbar"],
div.viewerBadge_container__1QSob, div.viewerBadge_link__1S137, div.stDeployButton,
a[href*="streamlit.app/profile"], a[href*="streamlit.io"] { display: none !important; }
section.main > div.block-container + div { display: none !important; }
</style>
""", unsafe_allow_html=True)

def ms_to_timestr(ms):
    if pd.isna(ms): return "-"
    try: ms = int(ms)
    except Exception: return "-"
    mm = ms // 60000; ss = (ms % 60000) // 1000; mmm = ms % 1000
    return f"{mm:02d}:{ss:02d}:{mmm:03d}"

def render_table_with_fade(display_df, row_color):
    html = "<table>"
    html += "<tr>" + "".join(f"<th>{c}</th>" for c in display_df.columns) + "</tr>"
    for i, row in display_df.iterrows():
        color_class = row_color.get(i, "")
        row_class = f"fade-cell {color_class}" if color_class else "fade-cell"
        html += f"<tr class='{row_class}'>" + "".join(f"<td>{val}</td>" for val in row) + "</tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=2)
def load_classification(url: str):
    return pd.read_csv(f"{url}&v={int(time.time())}")

# Estado persistente para transiciones
if "prev_best" not in st.session_state:
    st.session_state.prev_best = {}
if "global_best" not in st.session_state:
    st.session_state.global_best = None
if "last_lap_count" not in st.session_state:
    st.session_state.last_lap_count = {}
if "prev_positions" not in st.session_state:
    st.session_state.prev_positions = {}

placeholder = st.empty()

try:
    while True:
        now = datetime.now()
        try:
            df = load_classification(CSV_URL)
        except Exception:
            placeholder.info("⏳ Esperando clasificación (CSV en Drive) ...")
            time.sleep(REFRESH_INTERVAL)
            continue

        if df.empty:
            placeholder.info("⏳ Sin datos de clasificación todavía.")
            time.sleep(REFRESH_INTERVAL)
            continue

        # Asegurar columnas esperadas del CSV de clasificación
        # (position, kart_number, best_time_ms, best_time_str, last_time_ms, last_time_str, laps, estado, updated_at_utc)
        for col in ["position","kart_number","best_time_ms","last_time_ms","laps"]:
            if col not in df.columns: df[col] = pd.NA

        # Orden por posición (la clasificación ya viene ordenada)
        summary_sorted = df.sort_values("position").reset_index(drop=True)

        # === CAMBIO 1: Añadir columna "Pos." a la izquierda (desde 'position')
        # === CAMBIO 2: Eliminar "Estado" del display
        if "best_time_str" in df.columns and "last_time_str" in df.columns:
            display = summary_sorted[["position","kart_number","best_time_str","last_time_str","laps"]].copy()
            display.columns = ["Pos.","Kart","Mejor vuelta","Última vuelta","Vueltas"]
        else:
            display = summary_sorted.copy()
            display["Mejor vuelta"] = display["best_time_ms"].apply(ms_to_timestr)
            display["Última vuelta"] = display["last_time_ms"].apply(ms_to_timestr)
            display["Vueltas"] = display["laps"].astype("Int64")
            display = display[["position","kart_number","Mejor vuelta","Última vuelta","Vueltas"]]
            display.columns = ["Pos.","Kart","Mejor vuelta","Última vuelta","Vueltas"]

        # --- Lógica de transiciones (igual que antes, usando datos ya agregados) ---
        prev_global_best = st.session_state.global_best
        prev_best_map    = st.session_state.prev_best
        prev_lap_map     = st.session_state.last_lap_count
        prev_positions   = st.session_state.prev_positions

        bests_nonnull = summary_sorted["best_time_ms"].dropna()
        current_global_best = int(bests_nonnull.min()) if not bests_nonnull.empty else None

        row_color = {}
        for i, row in summary_sorted.iterrows():
            k = str(row["kart_number"])
            laps = int(row["laps"]) if not pd.isna(row["laps"]) else 0
            last = row["last_time_ms"]
            best = row["best_time_ms"]

            prev_laps = prev_lap_map.get(k, 0)
            new_event = laps > prev_laps

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

                    color = "green" if improved else "gray"

            prev_pos = prev_positions.get(k)
            if prev_pos is not None and i < prev_pos:
                color = (color + " " if color else "") + "flash slide-in"

            row_color[i] = color

        with placeholder.container():
            render_table_with_fade(display, row_color)
            st.caption(f"Última actualización: {now.strftime('%H:%M:%S')}")

        new_prev_best   = {}
        new_last_lap    = {}
        new_positions   = {}
        for i, r in summary_sorted.iterrows():
            k = str(r["kart_number"])
            b = r["best_time_ms"]
            laps = int(r["laps"]) if not pd.isna(r["laps"]) else 0
            new_last_lap[k] = laps
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
        st.session_state.last_lap_count = new_last_lap
        st.session_state.prev_positions = new_positions

        time.sleep(REFRESH_INTERVAL)

except KeyboardInterrupt:
    pass
