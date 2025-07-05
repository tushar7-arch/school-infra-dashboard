
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="School Infra Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("sample_school_data.csv")
    df["infra_score"] = (
        df[["electricity_availability", "internet", "library_availability", "playground_available"]]
        .replace(2, 0).sum(axis=1)
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

# Sidebar Filters
st.sidebar.header("Filters")
building_status = st.sidebar.multiselect(
    "Building Status", df["building_status"].dropna().unique(), default=list(df["building_status"].dropna().unique())
)
library_filter = st.sidebar.selectbox("Library Available?", ["All", "Yes", "No"])
internet_filter = st.sidebar.selectbox("Internet?", ["All", "Yes", "No"])

filtered_df = df[df["building_status"].isin(building_status)]
if library_filter != "All":
    filtered_df = filtered_df[filtered_df["library_availability"] == (1 if library_filter == "Yes" else 2)]
if internet_filter != "All":
    filtered_df = filtered_df[filtered_df["internet"] == (1 if internet_filter == "Yes" else 2)]

# KPIs
total_schools = filtered_df.shape[0]
electricity_pct = (filtered_df["electricity_availability"] == 1).mean() * 100
internet_pct = (filtered_df["internet"] == 1).mean() * 100
library_pct = (filtered_df["library_availability"] == 1).mean() * 100
avg_classrooms = filtered_df["total_class_rooms"].mean()

st.title("📊 School Infrastructure Dashboard")
st.markdown("### National Infra Snapshot")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Schools", f"{total_schools:,}")
col2.metric("Electricity Available", f"{electricity_pct:.1f}%")
col3.metric("Internet Available", f"{internet_pct:.1f}%")
col4.metric("Library Available", f"{library_pct:.1f}%")
col5.metric("Avg. Classrooms", f"{avg_classrooms:.1f}")

# Charts
st.markdown("### 🔌 Internet vs Library Availability")
internet_lib = filtered_df.groupby(["internet", "library_availability"]).size().reset_index(name="Count")
fig1 = px.bar(internet_lib, x="internet", y="Count", color="library_availability", barmode="group",
              labels={"internet": "Internet", "library_availability": "Library"})
st.plotly_chart(fig1, use_container_width=True)

st.markdown("### 🏫 Infra Score Distribution")
fig2 = px.histogram(filtered_df, x="infra_score", nbins=6, title="Infra Score (0–4)")
st.plotly_chart(fig2, use_container_width=True)

# Table
st.markdown("### 📋 Filtered School Data")
st.dataframe(filtered_df.head(100))

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df(filtered_df)
st.download_button("📥 Download Filtered Data", csv, "filtered_schools.csv", "text/csv")
