import streamlit as st

from core.config import PAGE_TITLE, PEOPLE
from core.data import load_data
from core.metrics import discipline_order
from core.pages.comparison import render_comparison_page
from core.pages.evolution import render_evolution_page

# Pour lancer la page : python -m streamlit run app.py

st.set_page_config(page_title=PAGE_TITLE, layout="wide")

df = load_data()

# =========================
# Sidebar filters
# =========================
st.sidebar.title("Filtres")

disciplines = sorted([x for x in df["discipline"].dropna().unique()], key=discipline_order)

year_start, year_end = st.sidebar.slider(
    "Années",
    min_value=2009,
    max_value=2026,
    value=(2009, 2026),
    step=1,
)

# --- Discipline : boutons cliquables (checkbox) ---
st.sidebar.subheader("Discipline")
discipline_sel = [
    d for d in disciplines
    if st.sidebar.checkbox(d, value=True, key=f"disc_{d}")
]

# --- Personnes : boutons cliquables (checkbox) ---
people_list = [p for p in PEOPLE if p in set(df["person"].dropna().unique())]
st.sidebar.subheader("Personnes")
people_sel = [
    p for p in people_list
    if st.sidebar.checkbox(p, value=True, key=f"person_{p}")
]

f = df.copy()
f = f[(f["season_num"] >= year_start) & (f["season_num"] <= year_end)]
f = f[f["discipline"].isin(discipline_sel)]
f = f[f["person"].isin(people_sel)]

page = st.sidebar.radio("Page", ["Comparaison", "Évolution"])

st.title(PAGE_TITLE)

if f.empty:
    st.warning("Aucun résultat avec ces filtres.")
    st.stop()

# =========================
# Pages
# =========================
if page == "Comparaison":
    render_comparison_page(f, discipline_sel=discipline_sel)

else:
    render_evolution_page(f, discipline_sel=discipline_sel)
