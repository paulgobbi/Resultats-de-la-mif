import re
import pandas as pd


def discipline_order(d: str) -> int:
    if not d:
        return 99
    dl = d.strip().lower()
    if "fl" in dl:
        return 0
    if "chamois" in dl:
        return 1
    return 99


def is_chamois(d: str) -> bool:
    return "chamois" in (d or "").strip().lower()


def is_fleche(d: str) -> bool:
    dl = (d or "").strip().lower()
    return ("fl" in dl) and (not is_chamois(d))


def discipline_label(d: str) -> str:
    return "Chamois" if is_chamois(d) else "Flèche"


def ordered_medal_labels_for_axis(discipline: str) -> list[str]:
    # Chamois : Rien, Cabri, Bronze, Argent, Vermeil, Or
    # Flèche  : Rien, Fléchette, Bronze, Argent, Vermeil, Or
    if is_chamois(discipline):
        return [
            "Rien",
            "Cabri",
            "Chamois de bronze",
            "Chamois d'argent",
            "Chamois de vermeil",
            "Chamois d'or",
        ]
    else:
        return [
            "Rien",
            "Fléchette",
            "Flèche de bronze",
            "Flèche d'argent",
            "Flèche de vermeil",
            "Flèche d'or",
        ]


def parse_event_number(event: str) -> tuple[int, str]:
    if not event:
        return (999, "")
    m = re.match(r"(\d+)(.*)", str(event).strip().lower())
    if not m:
        return (999, str(event))
    return (int(m.group(1)), m.group(2))


def medal_score_new(medal: str | None) -> int:
    if not medal:
        return 0
    m = medal.strip().lower()
    if m == "rien":
        return 0
    if m in {"cabri", "fléchette", "flechette"}:
        return 1
    if m == "bronze":
        return 2
    if m == "argent":
        return 3
    if m == "vermeil":
        return 4
    if m == "or":
        return 5
    return 0


def medal_simple(medal: str | None) -> str:
    if not medal:
        return "Rien"
    m = medal.strip()
    ml = m.lower()
    if ml == "flechette":
        return "Fléchette"
    return m if m else "Rien"


def medal_label_discipline(discipline: str, medal: str | None) -> str:
    if not medal:
        return "Rien"

    m = medal_simple(medal)
    ml = m.lower()

    if ml in {"cabri", "fléchette"}:
        return "Cabri" if ml == "cabri" else "Fléchette"

    if ml == "rien":
        return "Rien"

    d_disp = "Chamois" if is_chamois(discipline) else "Flèche"

    if ml == "or":
        return f"{d_disp} d'or"
    if ml == "argent":
        return f"{d_disp} d'argent"
    return f"{d_disp} de {ml}"


def medal_label_merged(medal: str | None) -> str:
    m = medal_simple(medal)
    ml = m.lower()
    if ml == "rien":
        return "Rien"
    if ml in {"cabri", "fléchette"}:
        return "Cabri/Fléchette"
    if ml == "bronze":
        return "Bronze"
    if ml == "argent":
        return "Argent"
    if ml == "vermeil":
        return "Vermeil"
    if ml == "or":
        return "Or"
    return "Rien"


def avg_top5_open(sub: pd.DataFrame) -> float | None:
    """
    Score OPEN = moyenne des 5 meilleurs Pt Cse (donc les plus petits).
    Si moins de 5 courses => moyenne des disponibles.
    """
    if sub.empty or sub["pt_cse"].notna().sum() == 0:
        return None
    return float(sub["pt_cse"].dropna().nsmallest(5).mean())
