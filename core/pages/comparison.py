import pandas as pd
import streamlit as st
import plotly.express as px

from core.config import PEOPLE, BIRTHDATES, apply_css
from core.metrics import is_fleche, is_chamois, discipline_label, avg_top5_open


def render_comparison_page(f: pd.DataFrame, discipline_sel: list[str]) -> None:
    apply_css()

    # =========================
    # Cartes
    # =========================
    st.subheader("Cartes")

    cols = st.columns(3)

    # âge actuel
    age_now = {}
    today = pd.Timestamp.today().normalize()
    for p in PEOPLE:
        birth_dt = pd.to_datetime(BIRTHDATES.get(p), errors="coerce")
        if pd.isna(birth_dt):
            age_now[p] = None
        else:
            age_now[p] = int(((today - birth_dt).days) // 365)

    cards = []
    for p in PEOPLE:
        sub_p = f[f["person"] == p]
        if sub_p.empty:
            continue

        blocks = []
        for d in sorted(sub_p["discipline"].dropna().unique(), key=lambda x: (0 if is_fleche(x) else 1, str(x))):
            sub = sub_p[sub_p["discipline"] == d]
            if sub.empty:
                continue

            n = len(sub)

            # épreuves finies (taux)
            if "status" in sub.columns and sub["status"].notna().any():
                # On ignore les DNS
                sub_run = sub[sub["status"] != "DNS"]

                n_run = len(sub_run)

                if n_run > 0:
                    finished = int((sub_run["status"] == "FINISHED").sum())
                    finished_rate = 100.0 * finished / n_run
                else:
                    finished_rate = None
            else:
                # si pas de colonne status, on considère tout "fini"
                finished = n
                finished_rate = 100.0 if n > 0 else None

            best_medal = sub.loc[sub["medal_score_new"].idxmax(), "medal_simple"]
            best_pt = sub["pt_cse"].min() if sub["pt_cse"].notna().any() else None

            blocks.append((d, n, finished_rate, best_medal, best_pt))

        cards.append((p, blocks))

    for idx, (p, blocks) in enumerate(cards):
        col = cols[idx % 3]
        age_txt = "—" if age_now.get(p) is None else f"{age_now[p]} ans"

        parts = []
        for d, n, finished_rate, best_medal, best_pt in blocks:
            record_txt = f"{best_pt:.2f}" if best_pt is not None else "—"
            finished_txt = "—" if finished_rate is None else f"{finished_rate:.0f}%"

            parts.append(
                f"""
                <div class="mif-section-title">{discipline_label(d)}</div>
                <div class="kpi"><span>Participations</span><b>{n}</b></div>
                <div class="kpi"><span>Épreuves finies</span><b>{finished_txt}</b></div>
                <div class="kpi"><span>Meilleure médaille</span><b>{best_medal}</b></div>
                <div class="kpi"><span>Record Points OPEN (sur une course)</span><b>{record_txt}</b></div>
                """.strip()
            )

        parts_html = "\n<div class='mif-divider'></div>\n".join(parts)

        html = f"""
        <div class="mif-card">
            <div class="mif-card-header">
                <div class="name">{p}</div>
                <div class="age">{age_txt}</div>
            </div>
            {parts_html}
        </div>
        """.strip()

        with col:
            st.markdown(html, unsafe_allow_html=True)

    # =========================
    # Résultats
    # =========================
    st.divider()
    st.subheader("Résultats")

    src = f.copy()
    if src.empty:
        st.info("Aucune donnée.")
    else:
        disciplines_res = sorted(
            src["discipline"].dropna().unique().tolist(),
            key=lambda x: (0 if is_fleche(x) else 1, str(x)),
        )

        tabs_res = st.tabs([discipline_label(d) for d in disciplines_res])

        for tab, d in zip(tabs_res, disciplines_res):
            with tab:
                df_d = src[src["discipline"] == d].copy()
                if df_d.empty:
                    st.info("Aucun résultat pour cette discipline.")
                    continue

                people_present = [p for p in PEOPLE if not df_d[df_d["person"] == p].empty]
                if not people_present:
                    st.info("Aucune personne pour cette discipline.")
                    continue

                cols_people = st.columns(3)

                for i, p in enumerate(people_present):
                    with cols_people[i % 3]:
                        sub = df_d[df_d["person"] == p].copy()
                        if sub.empty:
                            continue

                        # --- Stats ---
                        total = len(sub)
                        if "status" in sub.columns:
                            finished = int((sub["status"] == "FINISHED").sum())
                            abandons = int((sub["status"] == "DNF").sum())
                            disq = int((sub["status"] == "DSQ").sum())
                            dns = int((sub["status"] == "DNS").sum())
                        else:
                            finished, abandons, disq, dns = total, 0, 0, 0

                        # Bloc à hauteur fixe (SANS indentation -> pas de "code block")
                        extra_lines = []
                        if abandons > 0:
                            extra_lines.append(f"<div>Abandons : <b>{abandons}</b></div>")
                        if disq > 0:
                            extra_lines.append(f"<div>Disqualifications : <b>{disq}</b></div>")
                        if dns > 0:
                            extra_lines.append(f"<div>Départs non pris : <b>{dns}</b></div>")

                        stats_html = (
                            "<div style='min-height:140px;'>"
                            f"<div style='font-size:1.1rem;font-weight:700;margin-bottom:0.35rem;'>{p}</div>"
                            f"<div>Participations : <b>{total}</b></div>"
                            f"<div>Épreuves finies : <b>{finished}</b></div>"
                            + "".join(extra_lines)
                            + "</div>"
                        )

                        st.markdown(stats_html, unsafe_allow_html=True)

                        # =========================
                        # Histogramme médailles (Cabri/Fléchette -> Or)
                        # =========================
                        medal_col = "medal_simple" if "medal_simple" in sub.columns else "medal"
                        sub[medal_col] = sub[medal_col].fillna("Rien")

                        low_label = "Cabri" if is_chamois(d) else "Fléchette"
                        medal_axis = [low_label, "Bronze", "Argent", "Vermeil", "Or"]

                        counts = (
                            sub[medal_col]
                            .value_counts(dropna=False)
                            .reindex(medal_axis, fill_value=0)
                            .reset_index()
                        )
                        counts.columns = ["Médaille", "Nombre"]

                        color_map = {
                            low_label: "#FFFFFF",
                            "Bronze": "#8C6239",
                            "Argent": "#B0B0B0",
                            "Vermeil": "#87CEFA",
                            "Or": "#FFD700",
                        }

                        fig_medals = px.bar(
                            counts,
                            x="Médaille",
                            y="Nombre",
                            color="Médaille",
                            text="Nombre",
                            category_orders={"Médaille": medal_axis},
                            color_discrete_map=color_map,
                        )
                        fig_medals.update_layout(
                            showlegend=False,
                            height=240,
                            margin=dict(l=0, r=0, t=10, b=0),
                        )
                        fig_medals.update_traces(
                            marker_line_width=1,
                            marker_line_color="rgba(255,255,255,0.35)",
                        )

                        st.plotly_chart(fig_medals, use_container_width=True, config={"displayModeBar": False})

    # =========================
    # Statistiques
    # =========================
    st.divider()
    st.subheader("Statistiques")

    now = pd.Timestamp.now(tz=None)
    cutoff_3y = now - pd.DateOffset(years=3)

    def _mean_or_none(s: pd.Series) -> float | None:
        s = pd.to_numeric(s, errors="coerce").dropna()
        return float(s.mean()) if not s.empty else None

    def _fmt_num(x: float | None, digits: int = 2) -> str:
        return "—" if x is None else f"{x:.{digits}f}"

    def _fmt_pct(x: float | None, digits: int = 1) -> str:
        return "—" if x is None else f"{x:.{digits}f}%"

    stats_src = f.copy()

    if stats_src.empty:
        st.info("Aucune donnée.")
    else:
        disciplines_stats = sorted(
            stats_src["discipline"].dropna().unique().tolist(),
            key=lambda x: (0 if is_fleche(x) else 1, str(x)),
        )

        tabs_stats = st.tabs([discipline_label(d) for d in disciplines_stats])

        for tab, d in zip(tabs_stats, disciplines_stats):
            with tab:
                df_d = stats_src[stats_src["discipline"] == d].copy()
                if df_d.empty:
                    st.info("Aucune donnée pour cette discipline.")
                    continue

                people_present = [p for p in PEOPLE if not df_d[df_d["person"] == p].empty]
                if not people_present:
                    st.info("Aucune personne pour cette discipline.")
                    continue

                for p in people_present:
                    sub = df_d[df_d["person"] == p].copy()
                    if sub.empty:
                        continue

                    # -------------------------
                    # Points OPEN (pt_cse)
                    # -------------------------
                    sub_pt = sub[sub["pt_cse"].notna()].copy()

                    pt_mean_all = _mean_or_none(sub_pt["pt_cse"])
                    pt_mean_top5 = _mean_or_none(sub_pt.nsmallest(5, "pt_cse")["pt_cse"]) if len(sub_pt) > 0 else None

                    sub_3y_pt = sub_pt[sub_pt["event_dt"].notna() & (sub_pt["event_dt"] >= cutoff_3y)]
                    pt_mean_3y = _mean_or_none(sub_3y_pt["pt_cse"])

                    pt_record = float(sub_pt["pt_cse"].min()) if len(sub_pt) > 0 else None

                    # -------------------------
                    # Centile (rank_relative * 100)
                    # -------------------------
                    sub_rr = sub[sub["rank_relative"].notna()].copy()
                    sub_rr["centile"] = pd.to_numeric(sub_rr["rank_relative"], errors="coerce") * 100

                    c_mean_all = _mean_or_none(sub_rr["centile"])

                    # Top5 = basé sur les 5 meilleures courses en pt_cse (si possible), puis moyenne centile sur ces courses
                    if len(sub_pt) > 0 and sub_rr["centile"].notna().any():
                        top5_idx = sub_pt.nsmallest(5, "pt_cse").index
                        c_mean_top5 = _mean_or_none(sub_rr.loc[sub_rr.index.intersection(top5_idx), "centile"])
                    else:
                        c_mean_top5 = None

                    sub_rr_3y = sub_rr[sub_rr["event_dt"].notna() & (sub_rr["event_dt"] >= cutoff_3y)]
                    c_mean_3y = _mean_or_none(sub_rr_3y["centile"])

                    # Record centile = meilleur = plus petit
                    c_best = float(sub_rr["centile"].min()) if sub_rr["centile"].notna().any() else None

                    # -------------------------
                    # Render (2 lignes x 4 colonnes)
                    # -------------------------
                    st.markdown(f"### {p}")

                    stats_rows = [
                        {
                            "Stat": "Points OPEN",
                            "Moyenne totale": _fmt_num(pt_mean_all, 2),
                            "Moyenne top 5": _fmt_num(pt_mean_top5, 2),
                            "Moyenne ≤ 3 ans": _fmt_num(pt_mean_3y, 2),
                            "Record": _fmt_num(pt_record, 2),
                        },
                        {
                            "Stat": "Centile",
                            "Moyenne totale": _fmt_pct(c_mean_all, 1),
                            "Moyenne top 5": _fmt_pct(c_mean_top5, 1),
                            "Moyenne ≤ 3 ans": _fmt_pct(c_mean_3y, 1),
                            "Record": _fmt_pct(c_best, 1),
                        },
                    ]

                    st.dataframe(pd.DataFrame(stats_rows), width="stretch", hide_index=True)
                    st.markdown("---")

    # =========================
    # Performances récentes (≤ 3 ans)
    # =========================
    st.divider()
    st.subheader("Performances récentes (≤ 3 ans)")

    today = pd.Timestamp.today().normalize()
    cutoff = today - pd.DateOffset(years=3)

    recent = f.copy()

    # Filtre date (event_dt prioritaire, fallback event_date)
    if "event_dt" in recent.columns:
        recent = recent[recent["event_dt"].notna()]
    elif "event_date" in recent.columns:
        recent["event_dt"] = pd.to_datetime(recent["event_date"], errors="coerce")
        recent = recent[recent["event_dt"].notna()]
    else:
        recent = recent.iloc[0:0]

    recent = recent[recent["event_dt"] >= cutoff]

    if recent.empty:
        st.info("Aucune course dans les 3 dernières années.")
    else:
        disciplines_recent = sorted(
            recent["discipline"].dropna().unique().tolist(),
            key=lambda x: (0 if is_fleche(x) else 1, str(x)),
        )

        tabs_recent = st.tabs([discipline_label(d) for d in disciplines_recent])

        for tab, d in zip(tabs_recent, disciplines_recent):
            with tab:
                df_d = recent[recent["discipline"] == d].copy()
                if df_d.empty:
                    st.info("Aucun résultat récent pour cette discipline.")
                    continue

                # Tri : récent -> ancien (puis event_num)
                df_d = df_d.sort_values(
                    ["event_dt", "season_num", "event_num"],
                    ascending=[False, False, False],
                )

                for p in PEOPLE:
                    df_p = df_d[df_d["person"] == p].copy()
                    if df_p.empty:
                        continue

                    rows = []
                    for _, r in df_p.iterrows():
                        pt = r.get("pt_cse", None)
                        rank = r.get("rank", None)
                        participants = r.get("participants_count", None)

                        # Statut (si pas de points)
                        status = str(r.get("status", "") or "").upper()
                        is_no_points = (pt is None) or (pd.isna(pt))

                        if is_no_points:
                            if status == "DNF":
                                pt_txt = "Abandon"
                                classement = "Abandon"
                            elif status == "DNS":
                                pt_txt = "Départ non pris"
                                classement = "Départ non pris"
                            elif status == "DSQ":
                                pt_txt = "Disqualifié"
                                classement = "Disqualifié"
                            else:
                                pt_txt = "—"
                                classement = "—"
                        else:
                            pt_txt = f"{float(pt):.2f}"
                            if pd.notna(rank) and pd.notna(participants):
                                classement = f"{int(rank)}/{int(participants)}"
                            else:
                                classement = "—"

                        rows.append(
                            {
                                "Saison": (
                                    int(r["season_num"])
                                    if pd.notna(r.get("season_num", None))
                                    else r.get("season", "—")
                                ),
                                "Station": r.get("station") or "Inconnue",
                                "Point course": pt_txt,
                                "Médaille": r.get("medal_simple", r.get("medal", "Rien")),
                                "Classement": classement,
                            }

                        )

                    st.markdown(f"### {p}")
                    recent_df = pd.DataFrame(rows)

                    if recent_df.empty:
                        st.info("Aucun résultat exploitable.")
                    else:
                        st.dataframe(recent_df, width="stretch", hide_index=True)


    # =========================
    # Top 5 performances
    # =========================
    st.divider()
    st.subheader("Top 5 performances")

    disciplines_sorted = sorted(discipline_sel, key=lambda x: (0 if is_fleche(x) else 1, str(x)))
    tabs = st.tabs([discipline_label(d) for d in disciplines_sorted])

    for tab, d in zip(tabs, disciplines_sorted):
        with tab:
            df_d = f[(f["discipline"] == d) & (f["pt_cse"].notna())].copy()
            if df_d.empty:
                st.info("Aucun résultat avec Pt Cse pour cette discipline.")
                continue

            for p in PEOPLE:
                df_p = df_d[df_d["person"] == p].copy()
                if df_p.empty:
                    continue

                # Tri "invisible" : à points égaux, on départage par la date réelle
                df_p = df_p.copy()
                if "event_dt" not in df_p.columns:
                    # fallback si jamais event_dt n'existe pas
                    df_p["event_dt"] = pd.to_datetime(df_p.get("event_date"), errors="coerce")

                top5 = df_p.sort_values(
                    ["pt_cse", "event_dt", "season_num", "event_num"],
                    ascending=[True, False, True, True],  # points meilleurs d'abord, puis plus récent d'abord
                ).head(5)

                rows = []
                for _, r in top5.iterrows():
                    rank = r.get("rank", None)
                    participants = r.get("participants_count", None)

                    if pd.notna(rank) and pd.notna(participants):
                        classement = f"{int(rank)}/{int(participants)}"
                    else:
                        classement = "—"

                    rows.append(
                        {
                            "Saison": int(r["season_num"]) if pd.notna(r["season_num"]) else r["season"],
                            "Station": r.get("station") or "Inconnue",
                            "Points course": float(r["pt_cse"]) if pd.notna(r["pt_cse"]) else None,
                            "Médaille": r["medal_simple"],
                            "Classement": classement,
                        }
                    )

                st.markdown(f"### {p}")
                top_df = pd.DataFrame(rows)

                if top_df.empty:
                    st.info("Aucun résultat exploitable.")
                else:
                    st.dataframe(top_df, width="stretch", hide_index=True)
