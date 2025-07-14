import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Isotherm Shifter", page_icon="💧")

st.title("Isotherm Shifter")

st.write(
    """
    **Purpose**  
    Upload an equilibrium isotherm (RH vs water loading in g water per g salt) and interactively re‑reference it
    to a chosen starting humidity. The adjusted curve shows incremental water uptake per gram of the *initial total
    mass* (salt + dead water) so that the value is zero at the selected starting point.
    """
)

# -----------------------------------------------------------------------------
# 1 – File upload
# -----------------------------------------------------------------------------
uploaded_file = st.file_uploader("CSV file", type=["csv"])
if uploaded_file is None:
    st.info("Upload a CSV to get started. Expected columns: Relative Humidity (%) and water loading (g/g).")
    st.stop()

# -----------------------------------------------------------------------------
# 2 – Read and display raw data
# -----------------------------------------------------------------------------
df_raw = pd.read_csv(uploaded_file)
st.subheader("Raw Data")
st.dataframe(df_raw)

# -----------------------------------------------------------------------------
# 3 – Let the user choose which columns contain RH and loading values
# -----------------------------------------------------------------------------
if df_raw.empty or len(df_raw.columns) < 2:
    st.error("CSV must contain at least two numeric columns (RH and loading).")
    st.stop()

rh_col = st.selectbox("Column containing RH (%)", options=df_raw.columns.tolist(), index=0)
q_col = st.selectbox("Column containing loading (g water / g salt)", options=df_raw.columns.tolist(), index=1)

# Clean selected columns
iso = (
    df_raw[[rh_col, q_col]]
    .dropna()
    .apply(pd.to_numeric, errors="coerce")
    .dropna()
    .sort_values(rh_col)
    .reset_index(drop=True)
)

if iso.empty:
    st.error("Selected columns could not be converted to numeric values.")
    st.stop()

# -----------------------------------------------------------------------------
# 4 – Starting RH slider
# -----------------------------------------------------------------------------
rh_min, rh_max = iso[rh_col].min(), iso[rh_col].max()
start_rh = st.slider("Starting RH (%)", float(rh_min), float(rh_max), float(rh_min), step=1.0)

# -----------------------------------------------------------------------------
# 5 – Compute adjusted isotherm
# -----------------------------------------------------------------------------
# Interpolate baseline loading at the chosen starting RH (linear interpolation)
baseline_q = np.interp(start_rh, iso[rh_col], iso[q_col])
initial_total_mass = 1.0 + baseline_q  # 1 g salt + dead‑water at start

# Incremental uptake per g initial total mass
iso["Adjusted uptake (g/g initial mass)"] = (1.0 + iso[q_col] - initial_total_mass) / initial_total_mass

# -----------------------------------------------------------------------------
# 6 – Plot adjusted isotherm
# -----------------------------------------------------------------------------
fig = px.line(
    iso,
    x=rh_col,
    y="Adjusted uptake (g/g initial mass)",
    title=f"Adjusted Isotherm (start = {start_rh:.0f}% RH)",
    labels={rh_col: "Relative Humidity (%)", "Adjusted uptake (g/g initial mass)": "Uptake (g / g initial total mass)"},
)
fig.update_layout(margin=dict(l=40, r=40, t=60, b=40))
st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 7 – Download adjusted data
# -----------------------------------------------------------------------------
st.download_button(
    label="Download adjusted isotherm as CSV",
    data=iso.to_csv(index=False).encode("utf-8"),
    file_name="adjusted_isotherm.csv",
    mime="text/csv",
)
