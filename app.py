import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Callcenter Overig Dashboard", layout="wide")

st.title("📞 Callcenter Overig Analyse Dashboard")

uploaded_file = st.file_uploader("Upload CRM Excel", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    required_cols = ["Onderwerp","Beschrijving","Gemaakt op","Gemaakt door"]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"Kolom ontbreekt: {col}")
            st.stop()

    df["Beschrijving"] = df["Beschrijving"].astype(str).str.lower()

    df["Gemaakt op"] = pd.to_datetime(df["Gemaakt op"], dayfirst=True)

    df = df.dropna(subset=["Gemaakt op"])

    df["datum"] = df["Gemaakt op"].dt.date

    # onderwerp splitsen
    split = df["Onderwerp"].astype(str).str.split(r"\s-\s-\s", expand=True)

    df["Onderwerp_type"] = split[0].fillna("Onbekend")
    df["Onderwerp_cat"] = split[1].fillna("Onbekend")
    df["Onderwerp_sub"] = split[2].fillna("Onbekend")

    # OVERIG detectie
    df["Overig_flag"] = df["Onderwerp"].str.lower().str.contains("overig")

    # periode bepalen
    periode_van = df["Gemaakt op"].min()
    periode_tot = df["Gemaakt op"].max()

    # =========================
    # PERIODE FILTER
    # =========================

    st.sidebar.header("Periode filter")

    filter_optie = st.sidebar.selectbox(

        "Selecteer periode",

        [
            "Alles",
            "Laatste 7 dagen",
            "Laatste 30 dagen",
            "Aangepaste periode"
        ]

    )

    if filter_optie == "Laatste 7 dagen":

        cutoff = periode_tot - pd.Timedelta(days=7)

        df = df[df["Gemaakt op"] >= cutoff]

    elif filter_optie == "Laatste 30 dagen":

        cutoff = periode_tot - pd.Timedelta(days=30)

        df = df[df["Gemaakt op"] >= cutoff]

    elif filter_optie == "Aangepaste periode":

        start = st.sidebar.date_input("Startdatum", periode_van)

        end = st.sidebar.date_input("Einddatum", periode_tot)

        df = df[(df["datum"] >= start) & (df["datum"] <= end)]

    # =========================
    # KPI OVERZICHT
    # =========================

    total_calls = len(df)

    overig_calls = df["Overig_flag"].sum()

    st.header("📊 KPI Overzicht")

    st.info(
        f"Analyseperiode: {periode_van.strftime('%d-%m-%Y')} t/m {periode_tot.strftime('%d-%m-%Y')}"
    )

    col1,col2,col3 = st.columns(3)

    col1.metric("Totaal calls", total_calls)

    col2.metric("Overig calls", overig_calls)

    col3.metric(
        "Overig %",
        round(overig_calls / total_calls * 100,2) if total_calls > 0 else 0
    )

    # =========================
    # MEDEWERKER ANALYSE
    # =========================

    st.header("👨‍💼 Overig Analyse per Medewerker")

    agent_stats = df.groupby("Gemaakt door").agg(

        totaal_calls=("Onderwerp","count"),
        overig_calls=("Overig_flag","sum")

    ).reset_index()

    agent_stats["overig_percentage"] = (

        agent_stats["overig_calls"] /

        agent_stats["totaal_calls"] * 100

    ).round(2)

    # ranking percentage

    st.subheader("🏆 Ranking op percentage Overig")

    ranking_percentage = agent_stats.sort_values(

        "overig_percentage",

        ascending=False

    )

    st.dataframe(ranking_percentage, use_container_width=True)

    # ranking aantal

    st.subheader("📞 Ranking op aantal Overig calls")

    ranking_aantal = agent_stats.sort_values(

        "overig_calls",

        ascending=False

    )

    st.dataframe(ranking_aantal, use_container_width=True)

    # =========================
    # GRAFIEKEN
    # =========================

    st.header("📈 Visualisaties")

    fig1 = px.bar(

        ranking_percentage,

        x="Gemaakt door",

        y="overig_percentage",

        title="Percentage Overig per medewerker"

    )

    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(

        ranking_aantal,

        x="Gemaakt door",

        y="overig_calls",

        title="Aantal Overig calls per medewerker"

    )

    st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # TOP OVERIG ONDERWERPEN
    # =========================

    st.header("📂 Wat wordt als Overig gelogd")

    overig_df = df[df["Overig_flag"]]

    top_overig = overig_df["Onderwerp"].value_counts().head(15)

    fig3 = px.bar(

        top_overig,

        title="Top onderwerpen binnen Overig"

    )

    st.plotly_chart(fig3, use_container_width=True)
