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

# ─── Load & Merge Data ───────────────────────────────────────────────────────
@st.cache_data
def load_data():
    prof = pd.read_csv("100_prof1.csv")       # profile data (state, district, etc.)
    fac  = pd.read_csv("100_fac_trim.csv")    # facility data
    df   = prof.merge(fac, on="pseudocode", how="inner")
    # Derived fields
    df["infra_score"] = (
        df[["electricity_availability","internet","library_availability","playground_available"]]
        .replace({2: 0, 3: 0})  # map “No” or “Not functional” → 0
        .sum(axis=1)
    )
    df["toilet_functionality_ratio"] = (
        (df["total_boys_func_toilet"] + df["total_girls_func_toilet"]) /
        (df["total_boys_toilet"] + df["total_girls_toilet"]).replace(0, np.nan)
    )
    df["cwsn_ready"] = (
        (df["availability_ramps"] == 1) &
        ((df["func_boys_cwsn_friendly"] > 0) | (df["func_girls_cwsn_friendly"] > 0))
    )
    return df

df = load_data()

# ─── Sidebar Filters ──────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")
f = df.copy()

def ms(col, label=None):
    if col not in df: return None
    opts = df[col].dropna().unique()
    return st.sidebar.multiselect(label or col, opts, default=list(opts))

def sb(col, mapping, label=None):
    if col not in df: return None
    choice = st.sidebar.selectbox(label or col, ["All"] + list(mapping.keys()))
    return mapping.get(choice, None)

# Geography
states       = ms("state",    "State")
districts    = ms("district", "District")
blocks       = ms("block",    "Block")
rural_map    = {"Rural":1, "Urban":2}
rural_urban  = sb("rural_urban", rural_map, "Location")

# School profile
school_cat   = ms("school_category","Category")
school_type  = ms("school_type",    "Type")
management   = ms("managment",       "Mgmt")
resi_map     = {"Yes":1,"Partial":2,"No":3}
resi         = sb("resi_school",     resi_map, "Residential?")
minority     = sb("minority_school", {"Yes":1,"No":2}, "Minority?")

# Grades offered
if "lowclass" in df and "highclass" in df:
    low, high = int(df.lowclass.min()), int(df.highclass.max())
    grade_range = st.sidebar.slider("Grades (min→max)", low, high, (low, high))
else:
    grade_range = None

# Infrastructure toggles
elec       = sb("electricity_availability", {"Yes":1,"No/Not functional":2}, "Electricity")
internet   = sb("internet", {"Yes":1,"No":2}, "Internet")
library    = sb("library_availability", {"Yes":1,"No":2}, "Library")
playg      = sb("playground_available", {"Yes":1,"No":2}, "Playground")
rain       = sb("rain_water_harvesting", {"Yes":1,"No":2}, "Rainwater Harvest")
boundary   = ms("boundary_wall", "Boundary Wall")
ramps      = sb("availability_ramps", {"Yes":1,"No":2}, "Ramps")
handrails  = sb("availability_of_handrails", {"Yes":1,"No":2}, "Handrails")
spl_edu    = sb("spl_educator_yn", {"Dedicated":1,"Cluster":2,"None":3}, "Special Educator")

# Apply filters if set
if states:       f = f[f.state.isin(states)]
if districts:    f = f[f.district.isin(districts)]
if blocks:       f = f[f.block.isin(blocks)]
if rural_urban:  f = f[f.rural_urban==rural_urban]
if school_cat:   f = f[f.school_category.isin(school_cat)]
if school_type:  f = f[f.school_type.isin(school_type)]
if management:   f = f[f.managment.isin(management)]
if resi:         f = f[f.resi_school==resi]
if minority:     f = f[f.minority_school==minority]
if grade_range:
    f = f[(f.lowclass>=grade_range[0]) & (f.highclass<=grade_range[1])]
for col,val in [
    ("electricity_availability",elec),
    ("internet",internet),
    ("library_availability",library),
    ("playground_available",playg),
    ("rain_water_harvesting",rain),
    ("availability_ramps",ramps),
    ("availability_of_handrails",handrails),
    ("spl_educator_yn",spl_edu),
]:
    if val is not None:
        f = f[f[col]==val]
if boundary:    f = f[f.boundary_wall.isin(boundary)]

# ─── KPI CARDS ────────────────────────────────────────────────────────────────
st.title("📊 School Infrastructure Dashboard")
c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8)
c1.metric("🏫 Total Schools",   f"{len(f):,}")
c2.metric("💡 Electricity (%)", f"{(f.electricity_availability==1).mean()*100:0.1f}%")
c3.metric("🌐 Internet (%)",     f"{(f.internet==1).mean()*100:0.1f}%")
c4.metric("📚 Library (%)",      f"{(f.library_availability==1).mean()*100:0.1f}%")
c5.metric("⚽ Playground (%)",   f"{(f.playground_available==1).mean()*100:0.1f}%")
c6.metric("💧 Rainwater (%)",    f"{(f.rain_water_harvesting==1).mean()*100:0.1f}%")
c7.metric("🚻 Toilet Func (%)",  f"{f.toilet_functionality_ratio.mean()*100:0.1f}%")
c8.metric("♿ CWSN Ready (%)",    f"{f.cwsn_ready.mean()*100:0.1f}%")
st.markdown("---")

# ─── Charts (5) ───────────────────────────────────────────────────────────────
# 1. Top 10 Districts by Infra Score
st.markdown("#### 🔝 Top 10 Districts by Avg Infra Score")
infra_by_dist = f.groupby("district").infra_score.mean().nlargest(10).reset_index()
fig1 = px.bar(infra_by_dist, x="infra_score", y="district",
              orientation="h", labels={"infra_score":"Avg Score"})
st.plotly_chart(fig1, use_container_width=True)

# 2. Electricity·Internet·Library %
st.markdown("#### ⚡ Electricity · Internet · Library")
stack = (
    f.assign(Elec=(f.electricity_availability==1).astype(int),
             Net =(f.internet            ==1).astype(int),
             Lib =(f.library_availability==1).astype(int))
     .melt("district",["Elec","Net","Lib"],"Infra","Has")
     .groupby(["district","Infra"])["Has"].mean().mul(100).reset_index()
)
fig2 = px.bar(stack, x="district", y="Has", color="Infra",
              labels={"Has":"%"}, barmode="group")
st.plotly_chart(fig2, use_container_width=True)

# 3. Building Status Pie
st.markdown("#### 🏗️ Building Status")
bs = f.building_status.value_counts().reset_index()
fig3 = px.pie(bs, values="building_status", names="index")
st.plotly_chart(fig3, use_container_width=True)

# 4. Heatmap: Ramps vs CWSN-ready
st.markdown("#### ♿ Ramps vs CWSN-ready")
heat = f.groupby(["availability_ramps","cwsn_ready"]).size().unstack(fill_value=0)
fig4 = px.imshow(heat, text_auto=True,
                 labels=dict(x="CWSN Ready", y="Ramps", color="Count"))
st.plotly_chart(fig4, use_container_width=True)

# 5. Avg Projectors by School Type
st.markdown("#### 📽️ Avg Projectors by School Type")
proj = f.groupby("school_type").projector.mean().reset_index()
fig5 = px.bar(proj, x="school_type", y="projector",
              labels={"projector":"Avg #"}, title=None)
st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

# ─── Data Table & Download ────────────────────────────────────────────────────
st.markdown("### 📋 Filtered Data (first 200 rows)")
st.dataframe(f.head(200), use_container_width=True)

@st.cache_data
def to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

st.download_button("📥 Download CSV", to_csv(f), "filtered_schools.csv", "text/csv")
