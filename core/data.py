import pandas as pd
import streamlit as st

from core.config import DATA_FILE, PEOPLE, BIRTHDATES
from core.metrics import (
    discipline_order,
    parse_event_number,
    medal_score_new,
    medal_simple,
    medal_label_discipline,
    medal_label_merged,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_parquet(DATA_FILE)
    df = df[df["person"].isin(PEOPLE)].copy()

    df["season_num"] = pd.to_numeric(df["season"], errors="coerce")
    df["discipline_ord"] = df["discipline"].apply(discipline_order)

    ev_num, ev_suf = zip(*df["event"].apply(parse_event_number))
    df["event_num"] = ev_num
    df["event_suf"] = ev_suf

    df["pt_cse"] = pd.to_numeric(df["pt_cse"], errors="coerce")

    df["medal_score_new"] = df["medal"].apply(medal_score_new)
    df["medal_simple"] = df["medal"].apply(medal_simple)
    df["medal_label"] = df.apply(lambda r: medal_label_discipline(r["discipline"], r["medal"]), axis=1)
    df["medal_label_merged"] = df["medal"].apply(medal_label_merged)

    # --- Dates ---
    df["event_dt"] = pd.to_datetime(df.get("event_date", None), errors="coerce")

    # Fallback date logic: season-01-01 + event_num days + discipline_ord seconds
    season_int = df["season_num"].fillna(1900).astype(int).astype(str)
    season_base = pd.to_datetime(season_int + "-01-01", errors="coerce")

    fallback_dt = (
        season_base
        + pd.to_timedelta(df["event_num"].fillna(0).astype(int), unit="D")
        + pd.to_timedelta(df["discipline_ord"].fillna(0).astype(int), unit="s")
    )
    df["event_dt"] = df["event_dt"].fillna(fallback_dt)

    # Birth dates + age in years at the event
    df["birth_dt"] = pd.to_datetime(df["person"].map(BIRTHDATES), errors="coerce")
    df["age_years"] = (df["event_dt"] - df["birth_dt"]).dt.total_seconds() / (365.25 * 24 * 3600)

    # Stable ordering for internal course index
    df = df.sort_values(
        ["season_num", "event_num", "discipline_ord", "event_suf", "pdf_file"],
        ascending=[True, True, True, True, True],
    )

    df["course_id"] = (
        df["season"].astype(str)
        + " | "
        + df["discipline"].astype(str)
        + "-"
        + df["event"].astype(str)
        + " | "
        + df["pdf_file"].astype(str)
    )

    course_order = (
        df[["course_id", "season_num", "event_num", "discipline_ord", "event_suf", "pdf_file"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    course_order["course_order"] = range(len(course_order))
    df = df.merge(course_order[["course_id", "course_order"]], on="course_id", how="left")

    df["course_label"] = df["season"].astype(str) + " " + df["discipline"].astype(str) + "-" + df["event"].astype(str)

    return df
