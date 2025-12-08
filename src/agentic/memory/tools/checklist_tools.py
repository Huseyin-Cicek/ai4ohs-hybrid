"""
Checklist Tools – ESS10 Expanded Risk Scoring
"""


def ess10_risk_score(prob, severity, vulnerability):
    """
    ESS10 Risk Score = P x S x V
    P: 1–5
    S: 1–5
    V: 1–5 (topluluk kırılganlığı)
    """
    return prob * severity * vulnerability


def generate_checklist(item_list):
    checklist = []
    for item in item_list:
        entry = {
            "item": item["name"],
            "evidence": "",
            "status": "K/E/H",
            "comments": "",
        }

        if "ess10" in item:
            entry["ess10_risk"] = ess10_risk_score(
                item["ess10"]["prob"], item["ess10"]["severity"], item["ess10"]["vulnerability"]
            )

        checklist.append(entry)

    return checklist
