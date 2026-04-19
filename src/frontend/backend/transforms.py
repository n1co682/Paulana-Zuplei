from typing import List


def esg_to_letter(esg) -> str:
    s = float(esg) / 100.0 if float(esg) > 1.0 else float(esg)
    if s >= 0.95: return "A+"
    if s >= 0.85: return "A"
    if s >= 0.75: return "B+"
    if s >= 0.65: return "B"
    if s >= 0.55: return "B-"
    if s >= 0.45: return "C+"
    if s >= 0.35: return "C"
    return "D"


def quality_to_grade(q: float) -> str:
    q = float(q)
    if q >= 0.75: return "Grade A"
    if q >= 0.50: return "Grade B"
    return "Grade C"


def dollars_to_str(v: float) -> str:
    return f"${float(v):.2f}"


def hours_to_days_str(hours) -> str:
    if not hours: return "N/A"
    d = float(hours) / 24.0
    return f"{round(d)} Days" if d >= 1 else f"{int(float(hours))} Hours"


def to_five(score_01: float) -> float:
    return round(float(score_01) * 5, 1)


def to_rate(q: float) -> int:
    return int(round(float(q) * 100))


def vectors_to_prefs(price, quality, resilience, sustainability, ethics, lead_time) -> dict:
    def i(v): return int(round(float(v) * 100))
    return {
        "price": i(price),
        "quality": i(quality),
        "resilience": i(resilience),
        "sustainability": i(sustainability),
        "ethics": i(ethics),
        "lead_time": i(lead_time),
        "consolidation": 30,
    }


def classify(bom_entry: dict, top_option: dict) -> str:
    """Critical if any single score improves by > 0.20 vs current BOM entry."""
    top_comp = top_option.get("component", {})
    cur_q = float(bom_entry.get("quality") or 0.5)
    cur_eth = float(bom_entry.get("esg_score") or 50) / 100.0
    cur_lead_h = float(bom_entry.get("lead_time") or 72)
    cur_lead_score = 1.0 - min(cur_lead_h / 720.0, 1.0)
    dims = [
        (float(top_comp.get("quality") or 0.5), cur_q),
        (float(top_comp.get("ethics_score") or 0.5), cur_eth),
        (float(top_comp.get("resilience_score") or 0.5), 0.5),
        (float(top_comp.get("lead_time_score") or 0.5), cur_lead_score),
    ]
    return "critical" if any(cand - cur > 0.20 for cand, cur in dims) else "optimization"


def best_improvement(bom_entry: dict, top_comp: dict, total_score: float) -> str:
    cur_lead = float(bom_entry.get("lead_time") or 0)
    cand_lead = float(top_comp.get("lead_time") or 0)
    if cur_lead and cand_lead and cand_lead < cur_lead * 0.9:
        return f"-{round((cur_lead - cand_lead) / 24)} Days Lead Time"
    cur_price = float(bom_entry.get("price") or 0)
    cand_price = float(top_comp.get("price_per_unit") or 0)
    if cur_price and cand_price and cand_price < cur_price * 0.95:
        return f"-{int(round((1 - cand_price / cur_price) * 100))}% Price"
    cur_q = float(bom_entry.get("quality") or 0.5)
    cand_q = float(top_comp.get("quality") or 0.5)
    if cand_q > cur_q + 0.05:
        return f"+{int(round((cand_q - cur_q) * 100))}% Quality"
    return f"+{int(round(total_score * 100))}% Overall Score"
