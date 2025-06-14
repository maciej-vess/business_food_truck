import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Food Business Challenge", layout="wide")
st.title("🍦 Food Business Challenge")

if "last_report" in st.session_state and st.session_state.last_report:
    st.markdown("### 📈 Analiza rynku (na podstawie zakupionego raportu)")
    st.info(st.session_state.last_report)
# --- Inicjalizacja gry ---
if "day" not in st.session_state:
    st.session_state.day = 1
    st.session_state.cash = 10000
    st.session_state.history = []
    st.session_state.max_days = 35
    st.session_state.day_complete = False
    st.session_state.mode = None
    st.session_state.trolley_days_left = 0
    st.session_state.foodtruck_days_left = 0
    st.session_state.base_demand = {
        "Centrum": 160,
        "Kampus": 140,
        "Dworzec": 120,
        "Plaża": 180,
        "Targowisko": 100,
        "Dzielnica Sztuki": 110
    }
    st.session_state.pair_demand = {}
    st.session_state.last_report = ""

# --- Mapowanie emoji ---
product_options = {
    "🍦 Lody": "Lody",
    "🍧 Mrożony jogurt": "Mrożony jogurt",
    "🥤 Shake owocowy": "Shake owocowy"
}
location_options = {
    "🏙 Centrum": "Centrum",
    "🎓 Kampus": "Kampus",
    "🚉 Dworzec": "Dworzec",
    "🏖 Plaża": "Plaża",
    "🛍 Targowisko": "Targowisko",
    "🎭 Dzielnica Sztuki": "Dzielnica Sztuki"
}

# --- Popyt bazowy i wagi ---
base_demand = {
    "Centrum": 160,          # obszar biurowy, dużo osób w ciągu dnia roboczego
    "Kampus": 140,           # studenci, popyt głównie w tygodniu
    "Dworzec": 120,          # ruchliwa lokalizacja tranzytowa
    "Plaża": 180,            # sezonowa, wysoka frekwencja w ciepłe dni
    "Targowisko": 100,       # osoby starsze, mieszkańcy lokalni
    "Dzielnica Sztuki": 110  # młodsze pokolenie, kreatywni mieszkańcy
}

product_location_weights = {
    "Centrum": {"Lody": 0.8, "Mrożony jogurt": 1.3, "Shake owocowy": 1.4},             # profesjonaliści
    "Kampus": {"Lody": 0.7, "Mrożony jogurt": 1.5, "Shake owocowy": 1.6},              # studenci
    "Park": {"Lody": 1.0, "Mrożony jogurt": 1.2, "Shake owocowy": 1.3},                # rodziny
    "Stadion": {"Lody": 1.8, "Mrożony jogurt": 0.6, "Shake owocowy": 1.0},             # eventy, dzieci
    "Dworzec": {"Lody": 0.6, "Mrożony jogurt": 1.0, "Shake owocowy": 1.6},             # dorośli dojeżdżający
    "Plaża": {"Lody": 1.6, "Mrożony jogurt": 1.3, "Shake owocowy": 1.2},               # dzieci + studenci
    "Targowisko": {"Lody": 1.5, "Mrożony jogurt": 1.0, "Shake owocowy": 0.8},          # starsze pary
    "Dzielnica Sztuki": {"Lody": 1.4, "Mrożony jogurt": 1.3, "Shake owocowy": 0.9},    # dzieci + pary
}


# --- Funkcja popytu ---
def get_pair_demand(loc, prod, day=None):
    key = f"{loc}_{prod}"
    if key not in st.session_state.pair_demand:
        base = base_demand[loc]
        factor = 1
        weight = product_location_weights[loc][prod]
        st.session_state.pair_demand[key] = int(base * factor * weight)

    base_d = st.session_state.pair_demand[key]
    if day is None:
        day = st.session_state.day

    np.random.seed(hash(f"{loc}_{prod}_{day}") % 2**32)
    variation = np.random.normal(0, base_d * 0.05)
    return max(0, int(base_d + variation))

# --- Tydzień i dzień ---
week = (st.session_state.day - 1) // 7 + 1
weekday = (st.session_state.day - 1) % 7 + 1
st.subheader(f"Tydzień {week}, dzień {weekday}")

# === GRA ===
tab1, tab2 = st.tabs(["🎮 Gra", "📄 Raporty Rynkowe"])

with tab1:
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        df["Legenda"] = df["Produkt"].fillna("Raport") + " @ " + df["Lokalizacja"].fillna("Brak")
        fig = px.bar(df, x="Dzień", y="Zysk", color="Legenda", title="Zysk dzienny")
        st.plotly_chart(fig, use_container_width=True, key=f'chart_game_{len(df)}')

    result = {}

    if not st.session_state.day_complete:
        if st.session_state.foodtruck_days_left > 0:
            loc = st.session_state.foodtruck_location
            prod = st.session_state.foodtruck_product
            demand = get_pair_demand(loc, prod)
            sold = min(demand, 150)
            profit = sold * 12
            st.session_state.cash += profit
            result = {
                "Dzień": st.session_state.day,
                "Typ": "Food Truck",
                "Lokalizacja": loc,
                "Produkt": prod,
                "Sprzedano": sold,
                "Zysk": profit,
                "Gotówka": st.session_state.cash
            }
            st.session_state.history.append(result)
            st.session_state.foodtruck_days_left -= 1
            st.session_state.day_complete = True

        elif st.session_state.trolley_days_left > 0:
            with st.form("trolley_form"):
                st.markdown("## Tryb: Trolley – wybierz lokalizację i produkt na dziś")
                loc_sel = st.radio("Lokalizacja:", list(location_options.keys()))
                prod_sel = st.radio("Produkt:", list(product_options.keys()))
                loc = location_options[loc_sel]
                prod = product_options[prod_sel]
                submitted = st.form_submit_button("Zatwierdź decyzję")
                if submitted:
                    demand = get_pair_demand(loc, prod)
                    sold = min(int(demand * 0.3), 50)
                    profit = sold * 12
                    st.session_state.cash += profit
                    result = {
                        "Dzień": st.session_state.day,
                        "Typ": "Trolley",
                        "Lokalizacja": loc,
                        "Produkt": prod,
                        "Sprzedano": sold,
                        "Zysk": profit,
                        "Gotówka": st.session_state.cash
                    }
                    st.session_state.history.append(result)
                    st.session_state.trolley_days_left -= 1
                    st.session_state.day_complete = True

        elif st.session_state.mode is None:
            st.markdown("### Wybierz swój ruch na dziś")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📊 Analiza raportu"):
                    st.session_state.choice_selected = "Analiza"
            with col2:
                if st.button("🚚 Food Truck"):
                    st.session_state.choice_selected = "Food Truck"
            with col3:
                if st.button("🛒 Trolley"):
                    st.session_state.choice_selected = "Trolley"

            if "choice_selected" in st.session_state:
                with st.form("decision_form"):
                    st.write(f"Wybrano: {st.session_state.choice_selected}")
                    if st.session_state.choice_selected != "Analiza":
                        loc_sel = st.radio("Lokalizacja:", list(location_options.keys()))
                        prod_sel = st.radio("Produkt:", list(product_options.keys()))
                        loc = location_options[loc_sel]
                        prod = product_options[prod_sel]
                    submit_main = st.form_submit_button("Zatwierdź decyzję")

                    if submit_main:
                        if st.session_state.choice_selected == "Analiza":
                            cost = 500
                            st.session_state.cash -= cost
                            st.session_state.last_report = (
                                "- Centrum i Plaża przyciągają największy ruch.\n"
                                "- Lody najlepiej sprzedają się na Plaży i Targowisku.\n"
                                "- Mrożony jogurt dominuje na Kampusie i w Dzielnicy Sztuki.\n"
                                "- Shake owocowy jest popularny na Dworcu i w Centrum.\n\n"
                            )
                            for i in range(7):
                                st.session_state.history.append({
                                    "Dzień": st.session_state.day + i,
                                    "Typ": "Raport",
                                    "Lokalizacja": None,
                                    "Produkt": "Raport",
                                    "Sprzedano": 0,
                                    "Zysk": -cost // 7,
                                    "Gotówka": st.session_state.cash
                                })
                            st.session_state.day += 6
                            st.session_state.day_complete = True
                        elif st.session_state.choice_selected == "Food Truck":
                            st.session_state.foodtruck_days_left = 7
                            st.session_state.foodtruck_location = loc
                            st.session_state.foodtruck_product = prod
                            st.session_state.mode = "Food Truck"
                            st.rerun()
                        elif st.session_state.choice_selected == "Trolley":
                            st.session_state.trolley_days_left = 6
                            st.session_state.mode = "Trolley"
                            demand = get_pair_demand(loc, prod)
                            sold = min(int(demand * 0.3), 50)
                            profit = sold * 12
                            st.session_state.cash += profit
                            st.session_state.history.append({
                                "Dzień": st.session_state.day,
                                "Typ": "Trolley",
                                "Lokalizacja": loc,
                                "Produkt": prod,
                                "Sprzedano": sold,
                                "Zysk": profit,
                                "Gotówka": st.session_state.cash
                            })
                            st.session_state.day_complete = True

    if st.session_state.day_complete:
        if st.session_state.day < st.session_state.max_days:
            st.success(f"Wynik dnia {st.session_state.day}: {result.get('Zysk', 0)} zł")
            st.session_state.day += 1
            st.session_state.day_complete = False
            if st.session_state.foodtruck_days_left == 0 and st.session_state.trolley_days_left == 0:
                st.session_state.mode = None
            st.rerun()
        else:
            st.header("🎯 Gra zakończona!")
            st.subheader(f"💰 Końcowy stan gotówki: {st.session_state.cash} zł")
            df_hist = pd.DataFrame(st.session_state.history)
            st.dataframe(df_hist)

# === RAPORTY RYNKOWE ===

with tab2:
    st.header("📊 Raport Rynkowy Przemysłu Mrożonych Przysmaków (2017)")

    st.markdown("""
    **Wzrost i wielkość rynku**
    - Oczekiwany roczny wzrost: **1%**
    - Wartość rynku: **$12 mld**
    - Sprzedaż z punktów gastronomicznych: **$3.2 mld**
    """)

    df_pie = pd.DataFrame({
        "Produkt": ["Lody", "Mrożony jogurt", "Inne"],
        "Udział w rynku (%)": [59, 22, 19]
    })
    fig_pie = px.pie(df_pie, names="Produkt", values="Udział w rynku (%)", title="Udział produktów w rynku (ogółem)")
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("**Udział w gastronomii:**")
    st.dataframe(pd.DataFrame({
        "Produkt": ["Lody", "Mrożony jogurt", "Inne"],
        "Udział (%) w gastronomii": [45, 32, 23]
    }))

    st.subheader("📌 Wnioski rynkowe")
    st.markdown("""
    1. **Świadomość zdrowotna:** Preferencje klientów przesuwają się w stronę mrożonego jogurtu i smoothie jako zdrowszych opcji.
    2. **Fragmentacja rynku:** Coraz więcej niszowych produktów rozdrabnia konkurencję.
    3. **Lokalność:** Rosnąca popularność lokalnych i rzemieślniczych marek wzmacnia mniejsze podmioty.
    """)

    st.header("🏙 Konkurencja lokalna (obecny rok)")
    st.markdown("""
    - Miasto wydało tylko 5 licencji – masz jedną z nich!
    - Pozostałe 4 to food trucki z jedzeniem wytrawnym (falafel, burgery itp.)
    - Lokale mrożonych przysmaków:
        - **Centrum**: 1 smoothie, 1 jogurt
        - **Targowisko**: 1 lody, 1 smoothie
        - **Dworzec**: 1 jogurt
        - **Dzielnica Sztuki**: 1 jogurt, 1 lody
        - **Kampus**: brak
        - **Plaża**: 1 jogurt, 1 lody
    """)

    st.header("🚶‍♀️ Ruch pieszy wg lokalizacji (2015)")
    df_traffic = pd.DataFrame({
        "Lokalizacja": ["Dworzec", "Centrum", "Kampus", "Targowisko", "Dzielnica Sztuki", "Plaża"],
        "Średni ruch dzienny": [19432, 14170, 9247, 8582, 7091, 3120]
    })
    fig_traffic = px.bar(df_traffic, x="Lokalizacja", y="Średni ruch dzienny", title="Ruch pieszy wg lokalizacji")
    st.plotly_chart(fig_traffic, use_container_width=True)

    st.header("🧑‍🤝‍🧑 Demografia wg lokalizacji (2016)")
    st.markdown("""
    - **Plaża**: młode rodziny z dziećmi, studenci  
    - **Dzielnica Sztuki**: dzieci, młode i starsze pary  
    - **Dworzec**: dojeżdżający pracownicy  
    - **Kampus**: studenci  
    - **Centrum**: pracownicy biurowi  
    - **Targowisko**: młode i starsze pary  
    """)

    st.header("📊 Sprzedaż wg grup demograficznych (2016)")
    df_demo = pd.DataFrame({
        "Grupa wiekowa": ["Dzieci", "Młodzi dorośli", "Dorośli", "Seniorzy"],
        "Lody": [470, 362, 278, 346],
        "Mrożony jogurt": [194, 387, 306, 154],
        "Smoothie": [135, 221, 243, 132]
    })
    st.dataframe(df_demo)

    st.subheader("📌 Wnioski demograficzne")
    st.markdown("""
    - **Dzieci:** Lody dominują, choć jogurt zyskuje na popularności.
    - **Młodzi dorośli:** Jogurt i smoothie doganiają lody.
    - **Dorośli:** Świadomość zdrowotna przesuwa wybór ku jogurtom i smoothie.
    - **Seniorzy:** Lody nadal preferowane.
    """)
