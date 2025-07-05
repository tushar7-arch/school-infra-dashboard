import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="📊 School Infrastructure Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Data Loading & Derived Fields ────────────────────────────────────────────
@st.cache_data
def load_data(path="sample_school_data.csv"):
    df = pd.read_csv(path)

    # Composite Infra Score (0–4)
    df["infra_score"] = (
        df[["electricity_availability", "internet", "library_availability", "playground_available"]]
        .replace({2: 0, 3: 0})  # map “No” or “Not functional” → 0
        .sum(axis=1)
    )

    # Toilet Functionality Ratio
    df["toilet_functionality_ratio"] = (
        (df["total_boys_func_toilet"] + df["total_girls_func_toilet"]) /
        (df["total_boys_toilet"] + df["total_girls_toilet"]).replace(0, np.nan)
    )

    # CWSN-ready flag
    df["cwsn_ready"] = (
        (df["availability_ramps"] == 1) &
        ((df["func_boys_cwsn_friendly"] > 0) | (df["func_girls_cwsn_friendly"] > 0))
    )

    return df

df = load_data()

# ─── Sidebar Filters & Applying Them ────────────────────────────────────────
st.sidebar.header("🔍 Filters")
f = df.copy()

def apply_multiselect(col, label=None, default_all=True):
    """Helper: show a multiselect only if col exists; returns selected values or None."""
    if col not in df.columns:
        return None
    opts = df[col].dropna().unique()
    default = list(opts) if default_all else []
    sel = st.sidebar.multiselect(label or col, opts, default=default)
    return sel

def apply_selectbox(col, mapping, label=None):
    """Helper: show a selectbox only if col exists; returns the mapped code or None."""
    if col not in df.columns:
        return None
    choice = st.sidebar.selectbox(label or col, ["All"] + list(mapping.keys()))
    return mapping.get(choice, None)

# 1) Geography
states   = apply_multiselect("state",    "State")
districts= apply_multiselect("district","District")
blocks   = apply_multiselect("block",    "Block")
ru_map   = {"Rural":1, "Urban":2}
rural_urban = apply_selectbox("rural_urban", ru_map, "Location Type")

# 2) School attributes
school_cat = apply_multiselect("school_category","School Category")
school_type= apply_multiselect("school_type",    "School Type")
management = apply_multiselect("managment",      "Management")
resi_map   = {"Yes":1, "Partial":2, "No":3}
resi       = apply_selectbox("resi_school", resi_map, "Residential School?")
minority   = apply_selectbox("minority_school", {"Yes":1,"No":2}, "Minority-managed?")

# 3) Grade range
if "lowclass" in df.columns and "highclass" in df.columns:
    low, high = int(df["lowclass"].min()), int(df["highclass"].max())
    grade_range = st.sidebar.slider("Grades Offered", low, high, (low, high))
else:
    grade_range = None

# 4) Infrastructure toggles
elec_map      = {"Yes":1, "No/Not functional":2}
elec          = apply_selectbox("electricity_availability", elec_map, "Electricity")
internet      = apply_selectbox("internet", {"Yes":1,"No":2})
library       = apply_selectbox("library_availability", {"Yes":1,"No":2})
playground    = apply_selectbox("playground_available", {"Yes":1,"No":2})
rainwater     = apply_selectbox("rain_water_harvesting", {"Yes":1,"No":2})
boundary_sel  = apply_multiselect("boundary_wall","Boundary Wall")
ramps         = apply_selectbox("availability_ramps", {"Yes":1,"No":2}, "Ramps")
handrails     = apply_selectbox("availability_of_handrails", {"Yes":1,"No":2}, "Handrails")
spl_edu       = apply_selectbox("spl_educator_yn", {"Dedicated":1,"Cluster":2,"None":3}, "Special Educator")

# Apply each filter only if its widget returned something
if states:    f = f[f["state"].isin(states)]
if districts: f = f[f["district"].isin(districts)]
if blocks:    f = f[f["block"].isin(blocks)]
if rural_urban: f = f[f["rural_urban"] == rural_urban]
if school_cat: f = f[f["school_category"].isin(school_cat)]
if school_type: f = f[f["school_type"].isin(school_type)]
if management: f = f[f["managment"].isin(management)]
if resi:        f = f[f["resi_school"] == resi]
if minority:    f = f[f["minority_school"] == minority]
if grade_range:
    f = f[(f["lowclass"] >= grade_range[0]) & (f["highclass"] <= grade_range[1])]

for col, val in [
    ("electricity_availability", elec),
    ("internet", internet),
    ("library_availability", library),
    ("playground_available", playground),
    ("rain_water_harvesting", rainwater),
    ("availability_ramps", ramps),
    ("availability_of_handrails", handrails),
    ("spl_educator_yn", spl_edu),
]:
    if val is not None:
        f = f[f[col] == val]

if boundary_sel:
    f = f[f["boundary_wall"].isin(boundary_sel)]

# ─── KPI CARDS ────────────────────────────────────────────────────────────────
st.title("📊 School Infrastructure Dashboard")
st.markdown("### National Infra Snapshot")
c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
c1.metric("🏫 Total Schools", f"{len(f):,}")
c2.metric("💡 Electricity (%)", f"{(f['electricity_availability'] == 1).mean() * 100:0.1f}%")
c3.metric("🌐 Internet (%)", f"{(f['internet'] == 1).mean() * 100:0.1f}%")
c4.metric("📚 Library (%)", f"{(f['library_availability'] == 1).mean() * 100:0.1f}%")
c5.metric("⚽ Playground (%)", f"{(f['playground_available'] == 1).mean() * 100:0.1f}%")
c6.metric("💧 Rainwater Harvest (%)", f"{(f['rain_water_harvesting'] == 1).mean() * 100:0.1f}%")
c7.metric("🚻 Toilet Functionality", f"{f['toilet_functionality_ratio'].mean() * 100:0.1f}%")
c8.metric("♿ CWSN Ready (%)", f"{f['cwsn_ready'].mean() * 100:0.1f}%")
st.markdown("---")

# ─── INTERACTIVE CHARTS ──────────────────────────────────────────────────────

# 1. Top 10 Districts by Avg Infra Score
st.markdown("#### 🔝 Top 10 Districts by Avg. Infra Score")
infra_by_dist = (
    f.groupby("district")["infra_score"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
fig1 = px.bar(infra_by_dist, x="infra_score", y="district", orientation="h",
              title="Infra Score by District", labels={"infra_score": "Avg Score"})
st.plotly_chart(fig1, use_container_width=True)

# 2. Electricity vs Internet vs Library (stacked bar)
st.markdown("#### ⚡📶📚 Electricity · Internet · Library")
stack = (
    f.assign(
        Electricity=(f["electricity_availability"] == 1).astype(int),
        Internet=(f["internet"] == 1).astype(int),
        Library=(f["library_availability"] == 1).astype(int),
    )
    .melt(id_vars="district", value_vars=["Electricity", "Internet", "Library"],
          var_name="Infra", value_name="Has")
    .groupby(["district", "Infra"])["Has"].mean()
    .mul(100)
    .reset_index()
)
fig2 = px.bar(stack, x="district", y="Has", color="Infra", barmode="group",
              title="Infra Access % by District", labels={"Has": "% Schools"})
st.plotly_chart(fig2, use_container_width=True)

# 3. Building Status Pie
st.markdown("#### 🏗️ Building Status Distribution")
bs = f["building_status"].value_counts().reset_index()
fig3 = px.pie(bs, values="building_status", names="index", title="Building Status")
st.plotly_chart(fig3, use_container_width=True)

# 4. Heatmap: CWSN-ready vs Ramps
st.markdown("#### ♿ CWSN-ready vs Ramps")
heat = f.groupby(["availability_ramps", "cwsn_ready"]).size().unstack(fill_value=0)
fig4 = px.imshow(heat, text_auto=True, labels=dict(x="CWSN Ready", y="Ramps", color="Count"))
st.plotly_chart(fig4, use_container_width=True)

# 5. Smart Tech by School Type (avg projectors)
st.markdown("#### 📽️ Avg. Projectors by School Type")
proj = f.groupby("school_type")["projector"].mean().reset_index()
fig5 = px.bar(proj, x="school_type", y="projector", title="Avg. # Projectors",
              labels={"projector": "Avg Count"})
st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

# ─── DATA TABLE & DOWNLOAD ────────────────────────────────────────────────────
st.markdown("### 📋 Filtered School Data (first 200 rows)")
st.dataframe(f.head(200), use_container_width=True)

@st.cache_data
def to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

csv_data = to_csv(f)
st.download_button("📥 Download Filtered Data as CSV", csv_data, "filtered_schools.csv", "text/csv")

