# Script 4 (nuevo): Presentador SCC que solo pinta la clasificación ya calculada
import os
import time
from datetime import datetime
import pandas as pd
import streamlit as st

# ============================
# CONFIGURABLES (SCC + Drive)
# ============================
CSV_URL = os.environ.get(
    "CSV_URL",
    "https://drive.google.com/uc?export=download&id=1AjZI7oFmivBzs39fX7f_bWwyULA_P75T"
)
REFRESH_INTERVAL = 2  # segundos
HINT_DURATION = 3     # segundos que se ve la flecha ▲ / ▼
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
/* =========================
   1) Animaciones y transiciones
   ========================= */
.fade-cell { transition: background-color 0.8s ease, border 0.4s ease; }
.gray  { background-color: #ffffe0 !important; }
.green { background-color: #d4edda !important; border: 2px solid #28a745; }
.purple{ background-color: #ead3ff !important; border: 2px solid #7f3fbf; }

.flash { animation: flashGlow 1s ease-in-out; }
@keyframes flashGlow {
  0%   { box-shadow: 0 0 18px 8px rgba(255,235,59,0.95); }
  100% { box-shadow: none; }
}

.slide-in { animation: slideInAnim 0.8s ease-out; }
@keyframes slideInAnim {
  0%   { transform: translateX(-20px); opacity: 0.5; }
  100% { transform: translateX(0); opacity: 1; }
}

/* =========================
   2) Tabla base
   ========================= */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 13px;
  border: none;
  text-align: center;
}

tr {
  transition: all 0.8s ease-in-out;
  border: none !important;          /* elimina líneas entre filas */
}

td, th {
  padding: 3px !important;
  text-align: center;
  vertical-align: middle;
  border: none !important;          /* elimina líneas entre celdas */
}

/* Columna estrecha para flechas (sin encabezado) */
th.arrow-col,
td.arrow-col {
  width: 18px;
  padding-left: 0 !important;
  padding-right: 0 !important;
}

/* =========================
   3) Cabecera
   ========================= */
table th {
  background: #d9d9d9 !important;   /* gris claro */
  border: none !important;          /* sin líneas */
  color: #000;
  text-align: center;
}

/* =========================
   4) Zebra striping
   ========================= */
table tr:nth-child(even) { background-color: #ffffff; }
table tr:nth-child(odd)  { background-color: #f7f7f7; }
table tr:first-child     { background-color: #d9d9d9 !important; } /* cabecera */

/* =========================
   5) Badge amarillo en la primera columna
   ========================= */
table td:first-child {
  text-align: center;
}

table td:first-child span.pos-badge {
  display: inline-block;
  background-color: #fff8b3;   /* fondo amarillo suave */
  border: 2px solid #ffd60a;   /* borde amarillo fuerte */
  border-radius: 6px;
  padding: 2px 8px;
  font-weight: bold;
  color: #333;
  min-width: 28px;
}

/* =========================
   6) Indicador de cambio de posición (flechas)
   ========================= */
.pos-change {
  display: inline-block;
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  opacity: 1;
  animation: fadeOut 2s 1s forwards;  /* visible un poco y luego desaparece */
}
.pos-up   { color: #1aaa55; }  /* verde subida */
.pos-down { color: #d33;    }  /* rojo bajada */

@keyframes fadeOut {
  0%   { opacity: 1; }
  100% { opacity: 0; }
}

/* =========================
   7) Ocultar interfaz Streamlit
   ========================= */
#MainMenu,
header,
footer,
div[data-testid="stFooter"],
div[data-testid="stToolbar"],
div.viewerBadge_container__1QSob,
div.viewerBadge_link__1S137,
div.stDeployButton,
a[href*="streamlit.app/profile"],
a[href*="streamlit.io"] {
  display: none !important;
}
section.main > div.block-container + div {
  display: none !important;
}
</style>

""", unsafe_allow_html=True)

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
    # Cabecera: Pos | (columna vacía para flecha) | Kart | Mejor | Última | Vueltas
    html += (
        "<tr>"
        "<th>Pos</th>"
        "<th class='arrow-col'></th>"
        "<th>Kart</th>"
        "<th>Mejor</th>"
        "<th>Última</th>"
        "<th>Vueltas</th>"
        "</tr>"
    )

    now_ts = time.time()
    for i, row in display_df.iterrows():
        color_class = row_color.get(i, "")
        row_class = f"fade-cell {color_class}" if color_class else "fade-cell"

        # Asumimos columnas: ["Pos", "Kart", "Mejor", "Última", "Vueltas"]
        pos_val  = row.iloc[0]
        kart_val = str(row.iloc[1]) if len(row) > 1 else ""
        mejor    = row.iloc[2] if len(row) > 2 else ""
        ultima   = row.iloc[3] if len(row) > 3 else ""
        vueltas  = row.iloc[4] if len(row) > 4 else ""

        # Flecha según movimiento almacenado en move_hint
        hint = st.session_state.move_hint.get(kart_val, None)
        arrow_html = ""
        if hint and now_ts < hint.get("until", 0):
            if hint.get("dir") == "up":
                arrow_html = "<span class='pos-change pos-up'>▲</span>"
            elif hint.get("dir") == "down":
                arrow_html = "<span class='pos-change pos-down'>▼</span>"

        cells = []
        # Columna 1: Pos con badge
        cells.append(f"<td><span class='pos-badge'>{pos_val}</span></td>")
        # Columna 2: flecha (puede estar vacía)
        cells.append(f"<td class='arrow-col'>{arrow_html}</td>")
        # Resto de columnas
        cells.append(f"<td>{kart_val}</td>")
        cells.append(f"<td>{mejor}</td>")
        cells.append(f"<td>{ultima}</td>")
        cells.append(f"<td>{vueltas}</td>")

        html += f"<tr class='{row_class}'>" + "".join(cells) + "</tr>"

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
# Nuevo: hints de movimiento (▲ / ▼)
if "move_hint" not in st.session_state:
    st.session_state.move_hint = {}

placeholder = st.empty()

try:
    while True:
        now = datetime.now()
        now_ts = time.time()

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
        for col in ["position", "kart_number", "best_time_ms", "last_time_ms", "laps"]:
            if col not in df.columns:
                df[col] = pd.NA

        # Orden por posición (la clasificación ya viene ordenada)
        summary_sorted = df.sort_values("position").reset_index(drop=True)

        # Display con columna Pos. a la izquierda, sin Estado
        # Normalizamos nombres a: ["Pos", "Kart", "Mejor", "Última", "Vueltas"]
        if "best_time_str" in df.columns and "last_time_str" in df.columns:
            display = summary_sorted[["position", "kart_number",
                                      "best_time_str", "last_time_str", "laps"]].copy()
            display.columns = ["Pos", "Kart", "Mejor", "Última", "Vueltas"]
        else:
            display = summary_sorted.copy()
            display["Mejor"] = display["best_time_ms"].apply(ms_to_timestr)
            display["Última"] = display["last_time_ms"].apply(ms_to_timestr)
            display["Vueltas"] = display["laps"].astype("Int64")
            display = display[["position", "kart_number", "Mejor", "Última", "Vueltas"]]
            display.columns = ["Pos", "Kart", "Mejor", "Última", "Vueltas"]

        # --- Lógica de transiciones (igual que antes, usando datos ya agregados) ---
        prev_global_best = st.session_state.global_best
        prev_best_map = st.session_state.prev_best
        prev_lap_map = st.session_state.last_lap_count
        prev_positions = st.session_state.prev_positions

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
            if prev_pos is not None:
                # Subida de posición
                if i < prev_pos:
                    color = (color + " " if color else "") + "flash slide-in"
                    st.session_state.move_hint[k] = {
                        "dir": "up",
                        "until": now_ts + HINT_DURATION
                    }
                # Bajada de posición
                elif i > prev_pos:
                    st.session_state.move_hint[k] = {
                        "dir": "down",
                        "until": now_ts + HINT_DURATION
                    }

            row_color[i] = color

        with placeholder.container():
            render_table_with_fade(display, row_color)
            st.caption(f"Última actualización: {now.strftime('%H:%M:%S')}")

        # Actualizar estado
        new_prev_best = {}
        new_last_lap = {}
        new_positions = {}
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

        # Limpiar hints expirados para no acumular
        now_ts2 = time.time()
        st.session_state.move_hint = {
            k: v for k, v in st.session_state.move_hint.items()
            if now_ts2 < v.get("until", 0)
        }

        time.sleep(REFRESH_INTERVAL)

except KeyboardInterrupt:
    pass
