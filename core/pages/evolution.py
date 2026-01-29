import pandas as pd
import streamlit as st
import plotly.express as px

from core.config import MERGED_ORDER, PEOPLE
from core.metrics import (
    ordered_medal_labels_for_axis,
    is_fleche,
    discipline_label,
    medal_label_discipline,
)


def render_evolution_page(f: pd.DataFrame, discipline_sel: list[str]) -> None:
    st.subheader("Évolution")

    # -------------------------
    # Controls (top)
    # -------------------------
    disciplines_sorted = sorted(discipline_sel, key=lambda x: (0 if is_fleche(x) else 1, str(x)))
    separer_disciplines = (len(disciplines_sorted) > 1) and st.toggle("Séparer les disciplines", value=True)
    
    age_equal = st.toggle("À âge égal", value=False)

    def _on_best_season_change():
        if st.session_state.get("best_season", False):
            st.session_state["best_ever"] = False

    def _on_best_ever_change():
        if st.session_state.get("best_ever", False):
            st.session_state["best_season"] = False

    best_season = st.toggle(
        "Garder uniquement le meilleur résultat de la saison",
        value=False,
        key="best_season",
        on_change=_on_best_season_change,
    )

    best_ever = st.toggle(
        "Garder uniquement le meilleur résultat",
        value=False,
        key="best_ever",
        on_change=_on_best_ever_change,
    )

    evo = f[f["pt_cse"].notna()].copy()

    # Best per season PER PERSON + PER DISCIPLINE
    if best_season:
        evo = evo.dropna(subset=["season_num"]).copy()
        evo = evo.loc[evo.groupby(["person", "discipline", "season_num"])["pt_cse"].idxmin()].copy()

    # X axis
    if age_equal:
        x_col = "age_years"
        x_label = "Âge"
        evo = evo.sort_values([x_col, "discipline_ord", "person"], ascending=[True, True, True])
    else:
        x_col = "event_dt"
        x_label = "Saison"
        evo = evo.sort_values([x_col, "discipline_ord", "person"], ascending=[True, True, True])

    # Keep only successive personal improvements (records) per discipline
    if best_ever:
        evo = evo.sort_values([x_col, "discipline_ord", "person"], ascending=[True, True, True]).copy()
        evo["best_so_far"] = evo.groupby(["person", "discipline"])["pt_cse"].cummin()
        evo = evo[evo["pt_cse"] == evo["best_so_far"]].copy()
        evo = evo.drop(columns=["best_so_far"])

    # -------------------------
    # Points course
    # -------------------------
    st.subheader("Points course")

    if separer_disciplines:
        c1, c2 = st.columns(2)
        for col, d in zip((c1, c2), disciplines_sorted[:2]):
            with col:
                evo_d = evo[evo["discipline"] == d].copy()
                fig = px.line(
                    evo_d,
                    x=x_col,
                    y="pt_cse",
                    color="person",
                    markers=True,
                    hover_data=[
                        "event_date",
                        "course_label",
                        "rank",
                        "participants_count",
                        "medal_label",
                        "pdf_file",
                        "age_years",
                    ],
                    labels={x_col: x_label, "pt_cse": "Points course"},
                    title=discipline_label(d),
                )
                if not age_equal:
                    fig.update_xaxes(tickformat="%Y")
                st.plotly_chart(fig, use_container_width=True)
    else:
        fig1 = px.line(
            evo,
            x=x_col,
            y="pt_cse",
            color="person",
            line_dash="discipline",
            markers=True,
            hover_data=[
                "event_date",
                "course_label",
                "rank",
                "participants_count",
                "medal_label",
                "pdf_file",
                "age_years",
            ],
            labels={x_col: x_label, "pt_cse": "Points course"},
        )

        if not age_equal:
            fig1.update_xaxes(tickformat="%Y")

        st.plotly_chart(fig1, use_container_width=True)

    # -------------------------
    # Médailles
    # -------------------------
    st.subheader("Médailles")

    def build_medal_fig_by_discipline(evo_sub: pd.DataFrame, discipline_name: str):
        evo_sub = evo_sub.copy()

        medal_col = "medal_simple" if "medal_simple" in evo_sub.columns else "medal"
        evo_sub[medal_col] = evo_sub[medal_col].fillna("Rien")

        # Recompute label by discipline (évite le mélange Flèche/Chamois sur l’axe Y)
        evo_sub["medal_display"] = evo_sub[medal_col].apply(lambda m: medal_label_discipline(discipline_name, m))
        category_order = ordered_medal_labels_for_axis(discipline_name)

        fig = px.line(
            evo_sub,
            x=x_col,
            y="medal_display",
            color="person",
            markers=True,
            hover_data=["event_date", "course_label", "pt_cse", "pdf_file", "age_years"],
            labels={x_col: x_label, "medal_display": "Médaille"},
            category_orders={"medal_display": category_order},
            title=discipline_label(discipline_name),
        )
        fig.update_yaxes(autorange="reversed")
        if not age_equal:
            fig.update_xaxes(tickformat="%Y")
        return fig

    def build_medal_fig_merged(evo_sub: pd.DataFrame):
        evo_sub = evo_sub.copy()
        fig = px.line(
            evo_sub,
            x=x_col,
            y="medal_label_merged",
            color="person",
            line_dash="discipline",
            markers=True,
            hover_data=["event_date", "course_label", "pt_cse", "pdf_file", "age_years"],
            labels={x_col: x_label, "medal_label_merged": "Médaille"},
            category_orders={"medal_label_merged": MERGED_ORDER},
            title="Flèche + Chamois",
        )
        fig.update_yaxes(autorange="reversed")
        if not age_equal:
            fig.update_xaxes(tickformat="%Y")
        return fig

    # --- Affichage des graphes ---
    if len(disciplines_sorted) == 1:
        d = disciplines_sorted[0]
        evo_d = evo[evo["discipline"] == d]
        st.plotly_chart(build_medal_fig_by_discipline(evo_d, d), use_container_width=True)
    else:
        d1, d2 = disciplines_sorted[0], disciplines_sorted[1]

        if separer_disciplines:
            c1, c2 = st.columns(2)
            with c1:
                evo_d1 = evo[evo["discipline"] == d1]
                st.plotly_chart(build_medal_fig_by_discipline(evo_d1, d1), use_container_width=True)
            with c2:
                evo_d2 = evo[evo["discipline"] == d2]
                st.plotly_chart(build_medal_fig_by_discipline(evo_d2, d2), use_container_width=True)
        else:
            evo_mix = evo[evo["discipline"].isin([d1, d2])].copy()
            st.plotly_chart(build_medal_fig_merged(evo_mix), use_container_width=True)

    # -------------------------
    # Récap médailles par saison (disciplines mélangées)
    # - Rien affiché uniquement si participation sans médaille
    # - "" si aucune participation
    # - Si best_season : meilleure médaille de la saison
    # - Si best_ever : on n’affiche pas le tableau
    # -------------------------
    if not best_ever:

        base = f.copy()
        if discipline_sel:
            base = base[base["discipline"].isin(discipline_sel)].copy()

        # Colonnes = uniquement personnes réellement présentes (donc pas de colonnes “fantômes”)
        people_cols = [p for p in PEOPLE if not base[base["person"] == p].empty]

        if base.empty or not people_cols:
            st.info("Aucune donnée.")
        else:
            # saisons
            seasons = (
                base["season_num"]
                .dropna()
                .astype(int)
                .sort_values()
                .unique()
                .tolist()
            )

            # Ordres d’affichage (par box)
            FLECHE_ORDER = [
                "Rien",
                "Fléchette",
                "Flèche de bronze",
                "Flèche d'argent",
                "Flèche de vermeil",
                "Flèche d'or",
            ]
            CHAMOIS_ORDER = [
                "Rien",
                "Cabri",
                "Chamois de bronze",
                "Chamois d'argent",
                "Chamois de vermeil",
                "Chamois d'or",
            ]
            fleche_rank = {m: i for i, m in enumerate(FLECHE_ORDER)}
            chamois_rank = {m: i for i, m in enumerate(CHAMOIS_ORDER)}

            def _label_row(r) -> str:
                # on préfère la colonne déjà calculée si elle existe
                if "medal_label" in base.columns and pd.notna(r.get("medal_label", None)):
                    return str(r["medal_label"])
                return medal_label_discipline(r["discipline"], r.get("medal", None))

            def _render_cell(season: int, person: str) -> str:
                sub = base[(base["season_num"] == season) & (base["person"] == person)].copy()
                if sub.empty:
                    return ""  # aucune participation

                if best_season:
                    # meilleure médaille de la saison (toutes disciplines mélangées)
                    if "medal_score_new" in sub.columns and sub["medal_score_new"].notna().any():
                        best_row = sub.loc[sub["medal_score_new"].idxmax()]
                    else:
                        # fallback : si pas de score, on prend la 1ère ligne
                        best_row = sub.iloc[0]
                    lbl = _label_row(best_row) or "Rien"
                    # si participation mais lbl vide -> Rien
                    if not lbl.strip():
                        lbl = "Rien"
                    return f'<div class="one">{lbl}</div>'

                # Sinon : tous les résultats (avec "Rien" si une participation sans médaille)
                sub["lbl"] = sub.apply(_label_row, axis=1)

                # split par discipline
                fle = sub[sub["discipline"].apply(is_fleche)].copy()
                cha = sub[~sub["discipline"].apply(is_fleche)].copy()

                fle_list = [x for x in fle["lbl"].dropna().astype(str).tolist() if x.strip()]
                cha_list = [x for x in cha["lbl"].dropna().astype(str).tolist() if x.strip()]

                # tri par ordre demandé (puis alpha pour stabilité)
                fle_list = sorted(fle_list, key=lambda x: (fleche_rank.get(x, 999), x))
                cha_list = sorted(cha_list, key=lambda x: (chamois_rank.get(x, 999), x))

                # Si une discipline n’a aucune course cette saison => box vide (mais la box existe)
                def _box(lines: list[str], cls: str) -> str:
                    if not lines:
                        return f'<div class="box {cls}"></div>'
                    items = "".join([f'<div class="m">{v}</div>' for v in lines])
                    return f'<div class="box {cls}">{items}</div>'

                return _box(fle_list, "top") + _box(cha_list, "bot")

            # --- HTML table ---
            css = """
            <style>
            .med-recap-wrap { margin-top: 8px; }
            table.med-recap { width:100%; border-collapse: collapse; }
            table.med-recap th, table.med-recap td { padding:10px 8px; vertical-align: top; border: none; }
            table.med-recap thead th { font-weight: 700; text-align: center; }
            table.med-recap tbody td.season { text-align:center; font-weight:700; white-space:nowrap; }
            table.med-recap tbody tr { border-top: 1px solid rgba(255,255,255,0.12); }
            .cell { display:flex; flex-direction: column; gap:8px; }
            .one { padding:8px 10px; border-radius:8px; background: rgba(255,255,255,0.04); text-align:center; }
            .box { padding:8px 10px; border-radius:8px; background: rgba(255,255,255,0.04); }
            .box.top { }
            .box.bot { }
            .m { line-height: 1.25; }
            </style>
            """

            head = "".join([f"<th>{p}</th>" for p in people_cols])
            rows_html = []
            for s in seasons:
                tds = []
                for p in people_cols:
                    content = _render_cell(s, p)
                    if content:
                        cell_html = f'<div class="cell">{content}</div>'
                    else:
                        cell_html = ""  # pas de participation => rien du tout
                    tds.append(f"<td>{cell_html}</td>")
                rows_html.append(f'<tr><td class="season">{s}</td>{"".join(tds)}</tr>')

            html = f"""
            {css}
            <div class="med-recap-wrap">
            <table class="med-recap">
                <thead>
                <tr>
                    <th>Saison</th>
                    {head}
                </tr>
                </thead>
                <tbody>
                {''.join(rows_html)}
                </tbody>
            </table>
            </div>
            """

            st.markdown(html, unsafe_allow_html=True)
