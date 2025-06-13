import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Food Business Challenge", layout="wide")
st.title("🍔 Food Business Challenge")

# Inicjalizacja stanu gry
if "day" not in st.session_state:
    st.session_state.day = 1
    st.session_state.cash = 10000
    st.session_state.history = []
    st.session_state.max_days = 35
    st.session_state.day_complete = False
    st.session_state.mode = None
    st.session_state.foodtruck_days_left = 0
    st.session_state.trolley_days_left = 0
    st.session_state.weather = np.random.choice(["Słonecznie", "Deszczowo", "Pochmurno"])
    st.session_state.weather_factor = {"Słonecznie": 1.2, "Deszczowo": 0.7, "Pochmurno": 1.0}
    st.session_state.base_demand = {
        "Centrum": 100,
        "Kampus": 80,
        "Park": 60,
        "Stadion": 40,
        "Dworzec": 70,
        "Plaża": 150
    }
    st.session_state.pair_demand = {}
    st.session_state.last_report = ""
    st.session_state.choice_selected = None

product_location_weights = {
    "Centrum": {"Lody": 1.2, "Mrożony jogurt": 1.0, "Shake owocowy": 0.9},
    "Kampus": {"Lody": 0.8, "Mrożony jogurt": 1.5, "Shake owocowy": 1.3},
    "Park": {"Lody": 1.1, "Mrożony jogurt": 1.2, "Shake owocowy": 1.4},
    "Stadion": {"Lody": 1.7, "Mrożony jogurt": 0.5, "Shake owocowy": 1.1},
    "Dworzec": {"Lody": 0.7, "Mrożony jogurt": 0.9, "Shake owocowy": 1.6},
    "Plaża": {"Lody": 2.0, "Mrożony jogurt": 1.2, "Shake owocowy": 0.6},
}

locations = {
    "🏙 Centrum": "Centrum",
    "🎓 Kampus": "Kampus",
    "🌳 Park": "Park",
    "🏟 Stadion": "Stadion",
    "🚉 Dworzec": "Dworzec",
    "🏖 Plaża": "Plaża"
}
products = {
    "🍦 Lody": "Lody",
    "🍧 Mrożony jogurt": "Mrożony jogurt",
    "🥤 Shake owocowy": "Shake owocowy"
}
week = (st.session_state.day - 1) // 7 + 1
weekday = (st.session_state.day - 1) % 7 + 1
st.subheader(f"Tydzień {week}, dzień {weekday}")

def get_pair_demand(loc, prod, day=None):
    key = f"{loc}_{prod}"
    if key not in st.session_state.pair_demand:
        base = st.session_state.base_demand[loc]
        factor = st.session_state.weather_factor[st.session_state.weather]
        weight = product_location_weights[loc][prod]
        st.session_state.pair_demand[key] = int(base * factor * weight)
    base_demand = st.session_state.pair_demand[key]
    if day is None:
        day = st.session_state.day
    np.random.seed(hash(f"{loc}_{prod}_{day}") % 2**32)
    variation = np.random.normal(0, base_demand * 0.05)
    return max(0, int(base_demand + variation))

if st.session_state.last_report:
    st.markdown("### Ostatni raport rynkowy")
    st.info(st.session_state.last_report)

if st.session_state.history:
    df_hist = pd.DataFrame(st.session_state.history)
    df_bar = df_hist.copy()
    df_bar["Produkt"] = df_bar["Produkt"].fillna("Raport")
    df_bar["Lokalizacja"] = df_bar["Lokalizacja"].fillna("Brak")
    df_bar["Legenda"] = df_bar["Produkt"] + " @ " + df_bar["Lokalizacja"]
    fig = px.bar(
        df_bar,
        x="Dzień",
        y="Zysk",
        color="Legenda",
        title="Zysk dzienny wg produktu i lokalizacji",
        labels={"Zysk": "Zysk (PLN)", "Legenda": "Produkt i lokalizacja"}
    )
    st.plotly_chart(fig, use_container_width=True)

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
            "Gotówka": st.session_state.cash,
        }
        st.session_state.history.append(result)
        st.session_state.foodtruck_days_left -= 1
        st.session_state.day_complete = True

    elif st.session_state.trolley_days_left > 0:
        with st.form("trolley_form"):
            st.markdown("## Tryb: Trolley (dzień tygodnia)")
            loc_emoji = st.radio("Lokalizacja (dziś)", list(locations.keys()))
            prod_emoji = st.radio("Produkt (dziś)", list(products.keys()))
            loc = locations[loc_emoji]
            prod = products[prod_emoji]
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
                    "Gotówka": st.session_state.cash,
                }
                st.session_state.history.append(result)
                st.session_state.trolley_days_left -= 1
                st.session_state.day_complete = True

    elif st.session_state.mode is None:
        st.markdown("### Wybierz swój ruch na dziś")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📊 Raport rynkowy"):
                st.session_state.choice_selected = "Raport rynkowy"
        with col2:
            if st.button("🚚 Food Truck"):
                st.session_state.choice_selected = "Food Truck"
        with col3:
            if st.button("🛒 Trolley"):
                st.session_state.choice_selected = "Trolley"

        if st.session_state.choice_selected:
            with st.form("main_menu_form"):
                st.write(f"**Wybrana opcja:** {st.session_state.choice_selected}")
                loc_emoji = st.radio("Lokalizacja:", list(locations.keys()))
                prod_emoji = st.radio("Produkt:", list(products.keys()))
                loc = locations[loc_emoji]
                prod = products[prod_emoji]
                submit_main = st.form_submit_button("Zatwierdź decyzję")

                if submit_main:
                    choice = st.session_state.choice_selected
                    if choice == "Raport rynkowy":
                        cost = 500
                        st.session_state.cash -= cost
                        st.session_state.last_report = (
                            "W słoneczne dni największy ruch obserwujemy na Plaży i w Centrum. "
                            "Lody najlepiej sprzedają się na Plaży i Stadionie. "
                            "Mrożony jogurt dominuje na Kampusie i w Parku, podczas gdy Shake owocowy przyciąga klientów na Dworcu."
                        )
                        for i in range(7):
                            st.session_state.history.append({
                                "Dzień": st.session_state.day + i,
                                "Typ": "Raport",
                                "Lokalizacja": None,
                                "Produkt": "Raport",
                                "Sprzedano": 0,
                                "Zysk": -cost // 7,
                                "Gotówka": st.session_state.cash,
                            })
                        st.session_state.day += 7
                        st.session_state.day_complete = True
                    elif choice == "Food Truck":
                        st.session_state.foodtruck_days_left = 7
                        st.session_state.foodtruck_location = loc
                        st.session_state.foodtruck_product = prod
                        st.session_state.mode = "Food Truck"
                        st.rerun()
                    elif choice == "Trolley":
                        st.session_state.trolley_days_left = 6
                        st.session_state.mode = "Trolley"
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
                            "Gotówka": st.session_state.cash,
                        }
                        st.session_state.history.append(result)
                        st.session_state.day_complete = True

# Finalny blok — przeskakiwanie dnia lub zakończenie
if st.session_state.day_complete:
    if st.session_state.day < st.session_state.max_days:
        if result.get("Typ") != "Raport":
            st.write("### Wynik dnia")
            st.json(result)
            st.session_state.day += 1
        st.session_state.day_complete = False
        if st.session_state.foodtruck_days_left == 0 and st.session_state.trolley_days_left == 0:
            st.session_state.mode = None
            st.session_state.choice_selected = None
        st.rerun()
    else:
        st.success(f"🎉 Gra zakończona! Końcowy stan gotówki: {st.session_state.cash} zł")
        df_hist = pd.DataFrame(st.session_state.history)
        st.write("### Historia decyzji")
        st.dataframe(df_hist)
