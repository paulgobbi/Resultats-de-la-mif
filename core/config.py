import streamlit as st

PAGE_TITLE = "ComparaMif du ski"
DATA_FILE = "results.parquet"

BIRTHDATES = {
    "Lucas": "1998-12-03",
    "Léa": "2001-09-29",
    "Paul": "2004-02-25",
    "Papa": "1967-09-20",
}

PEOPLE = ["Lucas", "Léa", "Paul", "Papa"]

MERGED_ORDER = ["Rien", "Cabri/Fléchette", "Bronze", "Argent", "Vermeil", "Or"]


def apply_css() -> None:
    st.markdown(
        """
        <style>
        .mif-card {
            background: #2f2f2f;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.20);
            margin-bottom: 14px;
            color: #ffffff;
            overflow: hidden;
            width: 100%;
            box-sizing: border-box;
        }

        .mif-card-header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin: 0 0 10px 0;
        }

        .mif-card-header .name {
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
        }

        .mif-card-header .age {
            font-size: 13px;
            color: rgba(255,255,255,0.75);
        }

        .mif-section-title {
            margin-top: 10px;
            font-size: 14px;
            font-weight: 700;
            color: #ffffff;
            opacity: 0.95;
        }

        .mif-divider {
            height: 1px;
            background: rgba(255,255,255,0.10);
            margin: 12px 0;
        }

        /* KPI rows: grid for clean alignment */
        .mif-card .kpi {
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: center;
            margin: 6px 0;
            font-size: 14px;
            color: #eaeaea;
            gap: 18px;
            overflow: hidden;
        }

        /* Label: 1 line, no ellipsis */
        .mif-card .kpi span {
            min-width: 0;
            white-space: nowrap;
            overflow: hidden;
        }

        /* Value: always on one line */
        .mif-card .kpi b {
            font-weight: 700;
            color: #ffffff;
            white-space: nowrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
