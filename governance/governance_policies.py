"""
Governance policies (kod içi kullanım için) - governance_policies.yaml'ın minimal gömülü hali.
"""

SAFETY_POLICIES = [
    {
        "id": "SAF-001",
        "description": "Yüksek riskli işlerde (WAH, kazı, kapalı alan, kaldırma) yeterli kontrol olmadan çalışmayı önermeyin.",
    },
    {
        "id": "SAF-002",
        "description": "Kontrol hiyerarşisi: elimine -> mühendislik -> idari -> KKD; önerilerde öncelik bu sırayla olmalı.",
    },
]

COMPLIANCE_POLICIES = [
    {
        "id": "COM-001",
        "description": "Tüm çıktılar 6331 ve ilgili yönetmeliklerle uyumlu olmalı.",
    },
    {
        "id": "COM-002",
        "description": "6331, OSHA, ISO 45001, IFC ESS arasında en sıkı kural geçerlidir (strictest rule wins).",
    },
    {
        "id": "COM-003",
        "description": "Bilgi yetersizse belirsizliği belirt ve konservatif geçici önlemler öner.",
    },
]
