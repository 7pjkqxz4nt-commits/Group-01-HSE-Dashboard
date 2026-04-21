import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="Group 01 Assignment", layout="wide")

st.markdown(
    """### Prepared by –
  **Group-01 - Assignment - HSE Dashboard**  
  **Samar Zaiton**  
  **Mohamed Gamal**  
  **Ahmed Badawy**  
  **Hazem Hashem**  
  **Mohamed Abd Elrheem**  
  **Mohamed Abd Elrazek**  
  **Amir Salem**"""
)

uploaded_file = st.file_uploader("📎 Attach Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    df["Year"] = df["Year\n[Note 1]"].astype(str).str.replace("p", "", regex=False)
    df["Year_num"] = df["Year"].str.extract(r'(\d{4})').astype(int)
    df.rename(columns={"Top-level Industry (SIC section)\n[Note 5]": "Industry"}, inplace=True)

    st.sidebar.header("Filters")
    years = st.sidebar.multiselect("Year", df["Year"].unique(), df["Year"].unique())
    regions = st.sidebar.multiselect("Region", df["Region"].dropna().unique(), df["Region"].dropna().unique())
    authorities = st.sidebar.multiselect("Authority", df["Enforcing authority [Note 3]"].dropna().unique(), df["Enforcing authority [Note 3]"].dropna().unique())
    industries = st.sidebar.multiselect("Industry", df["Industry"].dropna().unique(), df["Industry"].dropna().unique())
    accidents = st.sidebar.multiselect("Accident Type", df["Kind of accident"].dropna().unique(), df["Kind of accident"].dropna().unique())
    age_band = st.sidebar.multiselect("Age Band", df["Age band"].dropna().unique(), df["Age band"].dropna().unique())

    filtered_df = df[
        (df["Year"].isin(years)) &
        (df["Region"].isin(regions)) &
        (df["Enforcing authority [Note 3]"].isin(authorities)) &
        (df["Industry"].isin(industries)) &
        (df["Kind of accident"].isin(accidents)) &
        (df["Age band"].isin(age_band))
    ].copy()

    trend = filtered_df.groupby("Year_num").size().sort_index()
    total_fatalities = len(filtered_df)
    avg_per_year = round(trend.mean(), 1) if len(trend) > 0 else 0
    max_value = trend.max() if len(trend) > 0 else 0
    max_year = trend.idxmax() if len(trend) > 0 else "N/A"
    percent_change = ((trend.iloc[-1] - trend.iloc[0]) / trend.iloc[0]) * 100 if len(trend) > 1 and trend.iloc[0] != 0 else 0
    yoy_change = trend.iloc[-1] - trend.iloc[-2] if len(trend) > 1 else 0

    st.subheader("📊 Executive KPIs")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total", total_fatalities)
    col2.metric("Avg/Year", avg_per_year)
    col3.metric("Peak Year", f"{max_year} ({max_value})")
    col4.metric("Trend %", f"{percent_change:.1f}%")
    col5.metric("YoY Change", yoy_change)

    st.subheader("📈 Fatalities Trend")
    fig, ax = plt.subplots()
    ax.plot(trend.index, trend.values, marker='o')
    ax.set_xlabel("Year")
    ax.set_ylabel("Fatalities")
    ax.grid()
    st.pyplot(fig)

    # Charts
    st.subheader("🏢 Authority Distribution")
    all_authorities = df["Enforcing authority [Note 3]"].dropna().unique()
    authority_counts = filtered_df["Enforcing authority [Note 3]"].value_counts()
    authority_counts = authority_counts.reindex(all_authorities, fill_value=0).sort_values(ascending=False)
    authority_df = authority_counts.reset_index()
    authority_df.columns = ["Authority", "Fatalities"]
    st.bar_chart(authority_df.set_index("Authority"))

    st.subheader("🌍 Top Regions")
    region_counts = filtered_df["Region"].value_counts(ascending=False).reset_index()
    region_counts.columns = ["Region", "Fatalities"]
    st.bar_chart(region_counts.set_index("Region").head(10))

    st.subheader("🏭 Top Industries")
    industry_counts = filtered_df["Industry"].value_counts(ascending=False).reset_index()
    industry_counts.columns = ["Industry", "Fatalities"]
    st.bar_chart(industry_counts.set_index("Industry").head(10))

    st.subheader("⚠️ Accident Types")
    accident_counts = filtered_df["Kind of accident"].value_counts(ascending=False).reset_index()
    accident_counts.columns = ["Accident Type", "Fatalities"]
    st.bar_chart(accident_counts.set_index("Accident Type").head(10))

    # AI Insights
    st.subheader("🤖 AI Insights")
    if len(trend) > 1:
        st.write(f"Peak fatalities: {max_value} in {max_year}")
        if percent_change > 0:
            st.error("🚨 Increasing trend — Action required")
        else:
            st.success("✅ Decreasing trend — Good performance")
    if len(industry_counts) > 0:
        st.error(f"🚨 Highest risk industry: {industry_counts.iloc[0,0]}")
    if len(accident_counts) > 0:
        st.error(f"🚨 Most dangerous accident: {accident_counts.iloc[0,0]}")

    # AI Prediction
    st.subheader("🔮 AI Prediction")
    if len(trend) > 2:
        years_numeric = np.array(trend.index).reshape(-1, 1)
        fatalities = trend.values
        model = LinearRegression()
        model.fit(years_numeric, fatalities)
        next_year = int(max(trend.index)) + 1
        prediction = model.predict([[next_year]])[0]
        st.metric("Predicted Next Year", int(prediction))
        fig2, ax2 = plt.subplots()
        ax2.plot(trend.index, trend.values, marker='o', label="Actual")
        ax2.scatter(next_year, prediction, color="red", label="Prediction")
        ax2.legend()
        st.pyplot(fig2)

    # Map
    st.subheader("🗺️ Map")
    map_data = filtered_df["Region"].value_counts().reset_index()
    map_data.columns = ["Region", "Fatalities"]
    coords = {
        "London": [51.5074, -0.1278],
        "North West": [53.4808, -2.2426],
        "Scotland": [55.9533, -3.1883],
        "Wales": [51.4816, -3.1791],
        "Yorkshire": [53.8008, -1.5491]
    }
    map_data["lat"] = map_data["Region"].map(lambda x: coords.get(x, [None, None])[0])
    map_data["lon"] = map_data["Region"].map(lambda x: coords.get(x, [None, None])[1])
    map_data = map_data.dropna()
    st.map(map_data.rename(columns={"lat": "latitude", "lon": "longitude"}))

    # PDF Generation
    def generate_pdf():
        file_path = "report.pdf"
        doc = SimpleDocTemplate(file_path)
        styles = getSampleStyleSheet()
        content = []
        content.append(Paragraph("HSE Fatalities Report", styles['Title']))
        content.append(Spacer(1, 10))
        content.append(Paragraph(f"Total: {total_fatalities}", styles['Normal']))
        content.append(Paragraph(f"Avg: {avg_per_year}", styles['Normal']))
        content.append(Paragraph(f"Trend: {percent_change:.2f}%", styles['Normal']))
        content.append(Spacer(1, 20))
        content.append(Paragraph(
            "Prepared by – Samar Zaiton, Mohamed Gamal, Ahmed Badawy, Hazem Hashem, "
            "Mohamed Abd Elrheem, Mohamed Abd Elrazek, Amir Salem",
            styles['Italic']
        ))
        doc.build(content)
        return file_path

    # Email Function
    def send_email(file_path):
        sender_email = "amirsalemm@gmail.com"
        app_password = "aktv feke emcl zuib"
        msg = EmailMessage()
        msg["Subject"] = "HSE Fatalities Report"
        msg["From"] = sender_email
        msg["To"] = sender_email
        msg.set_content(
            "Attached is the HSE Fatalities Report.\n\n"
            "Prepared by – Samar Zaiton, Mohamed Gamal, Ahmed Badawy, Hazem Hashem, "
            "Mohamed Abd Elrheem, Mohamed Abd Elrazek, Amir Salem"
        )
        with open(file_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="report.pdf")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)

    # Button
    if st.button("📄 Generate & Email PDF"):
        pdf = generate_pdf()
        send_email(pdf)
        st.success("PDF generated and emailed automatically to amirsalemm@gmail.com")
