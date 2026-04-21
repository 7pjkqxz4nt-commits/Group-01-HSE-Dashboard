import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="HSE Dashboard", layout="wide")

st.title("📊 HSE AI Dashboard")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    df["Year"] = df["Year\n[Note 1]"].astype(str).str.replace("p", "", regex=False)
    df["Year_num"] = df["Year"].str.extract(r'(\d{4})').astype(int)

    df.rename(columns={
        "Top-level Industry (SIC section)\n[Note 5]": "Industry"
    }, inplace=True)

    # ==============================
    # FILTERS
    # ==============================
    st.sidebar.header("Filters")

    years = st.sidebar.multiselect("Year", df["Year"].unique(), df["Year"].unique())
    regions = st.sidebar.multiselect("Region", df["Region"].dropna().unique(), df["Region"].dropna().unique())
    industries = st.sidebar.multiselect("Industry", df["Industry"].dropna().unique(), df["Industry"].dropna().unique())

    filtered_df = df[
        (df["Year"].isin(years)) &
        (df["Region"].isin(regions)) &
        (df["Industry"].isin(industries))
    ]

    trend = filtered_df.groupby("Year_num").size().reset_index(name="Fatalities")

    # ==============================
    # KPIs
    # ==============================
    st.subheader("📊 KPIs")

    total = len(filtered_df)
    avg = int(trend["Fatalities"].mean()) if len(trend) else 0

    col1, col2 = st.columns(2)
    col1.metric("Total Fatalities", total)
    col2.metric("Average", avg)

    # ==============================
    # TREND CHART (FIXED)
    # ==============================
    st.subheader("📈 Trend")

    fig = px.line(trend, x="Year_num", y="Fatalities", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # INDUSTRY CHART
    # ==============================
    st.subheader("🏭 Industry")

    industry_counts = filtered_df["Industry"].value_counts().reset_index()
    industry_counts.columns = ["Industry", "Fatalities"]

    fig2 = px.bar(industry_counts, x="Industry", y="Fatalities")
    st.plotly_chart(fig2, use_container_width=True)

    # ==============================
    # AI PREDICTION (FIXED)
    # ==============================
    st.subheader("🔮 Prediction")

    if len(trend) > 2:
        X = np.array(trend["Year_num"]).reshape(-1, 1)
        y = trend["Fatalities"]

        model = LinearRegression()
        model.fit(X, y)

        next_year = int(trend["Year_num"].max()) + 1
        pred = model.predict([[next_year]])[0]

        st.metric("Next Year Prediction", int(pred))

        fig3 = px.scatter(trend, x="Year_num", y="Fatalities")
        fig3.add_scatter(x=[next_year], y=[pred], mode="markers", name="Prediction")
        st.plotly_chart(fig3)

    # ==============================
    # ACTIONS
    # ==============================
    st.subheader("🎯 Actions")

    actions = []

    if total > avg:
        actions.append("Increase safety inspections.")

    if not actions:
        actions.append("Performance stable.")

    for a in actions:
        st.write(f"- {a}")

else:
    st.info("Upload file to start")
