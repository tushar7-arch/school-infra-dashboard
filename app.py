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

# ─── Sidebar Filters ──────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

# Geography
states = st.sidebar.multiselect("State", df["state"].unique(), default=df["state"].unique())
districts = st.sidebar.multiselect(
    "District",
    df.query("state in @states")["district"].unique(),
    default=df["district"].unique()
)
blocks = st.sidebar.multiselect(
    "Block",
    df.query("district in @districts")["block"].unique(),
    default=df["block"].unique()
)
rural_urban = st.sidebar.selectbox("Location Type", ["All", "Rural (1)", "Urban (2)"])

# School attributes
school_cat = st.sidebar.multiselect("School Category", df["school_category"].unique(),
                                    default=df["school_category"].unique())
school_type = st.sidebar.multiselect("School Type", df["school_type"].unique(),
                                     default=df["school_type"].unique())
management = st.sidebar.multiselect("Management", df["managment"].unique(),
                                    default=df["managment"].unique())
resi = st.sidebar.selectbox("Residential School?", ["All", "Yes (1)", "Partial (2)", "No (3)"])
minority = st.sidebar.selectbox("Minority-managed?", ["All", "Yes (1)", "No (2)"])

# Grade range
low, high = int(df["lowclass"].min()), int(df["highclass"].max())
grade_range = st.sidebar.slider("Grades Offered (min→max)", low, high, (low, high))

# Infrastructure toggles
elec = st.sidebar.selectbox("Electricity", ["All", "Yes (1)", "No/Not functional (2/3)"])
internet = st.sidebar.selectbox("Internet", ["All", "Yes (1)", "No (2)"])
library = st.sidebar.selectbox("Library", ["All", "Yes (1)", "No (2)"])
playground = st.sidebar.selectbox("Playground", ["All", "Yes (1)", "No (2)"])
rainwater = st.sidebar.selectbox("Rainwater Harvesting", ["All", "Yes (1)", "No (2)"])
boundary = st.sidebar.multiselect("Boundary Wall (types)", df["boundary_wall"].unique(),
                                  default=df["boundary_wall"].unique())
ramps = st.sidebar.selectbox("Ramps Available", ["All", "Yes (1)", "No (2)"])
handrails = st.sidebar.selectbox("Handrails", ["All", "Yes (1)", "No (2)"])
spl_edu = st.sidebar.selectbox("Special Educator", ["All", "Dedicated (1)", "Cluster (2)", "None (3)"])

# Apply filters
f = df.copy()
f = f[f["state"].isin(states)]
f = f[f["district"].isin(districts)]
f = f[f["block"].isin(blocks)]
if rural_urban != "All":
    code = int(rural_urban.split("(")[1].strip(")"))
    f = f[f["rural_urban"] == code]
f = f[f["school_category"].isin(school_cat)]
f = f[f["school_type"].isin(school_type)]
f = f[f["managment"].isin(management)]
if resi != "All":
    f = f[f["resi_school"] == int(resi.split("(")[1].strip(")"))]
if minority != "All":
    f = f[f["minority_school"] == int(minority.split("(")[1].strip(")"))]
f = f[(f["lowclass"] >= grade_range[0]) & (f["highclass"] <= grade_range[1])]
for name, choice in [
    ("electricity_availability", elec),
    ("internet", internet),
    ("library_availability", library),
    ("playground_available", playground),
    ("rain_water_harvesting", rainwater),
    ("availability_ramps", ramps),
    ("availability_of_handrails", handrails),
    ("spl_educator_yn", spl_edu),
]:
    if choice != "All":
        code = int(choice.split("(")[1].strip(")"))
        f = f[f[name] == code]
f = f[f["boundary_wall"].isin(boundary)]

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

