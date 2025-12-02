"""
World Bank / IFC Environmental and Social Standards (ESS) Mappers

Provides cross-reference mappings between OHS standards:
- ISO 45001 ↔ WB/IFC ESS
- OSHA 29 CFR ↔ WB/IFC ESS
- Turkish Law 6331 ↔ WB/IFC ESS

These mappers enable multi-standard compliance checking and gap analysis.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ESSRequirement:
    """
    Individual WB/IFC ESS requirement.

    Attributes:
        ess_id: ESS standard ID (e.g., "ESS1", "ESS2")
        requirement_id: Specific requirement (e.g., "1.1", "2.2")
        title: Short requirement title
        description: Detailed requirement description
        sub_requirements: List of sub-requirement IDs
        related_iso_clauses: ISO 45001 clause mappings
        related_osha_standards: OSHA standard mappings
        related_law6331_articles: Turkish Law 6331 article mappings
    """

    ess_id: str
    requirement_id: str
    title: str
    description: str
    sub_requirements: Optional[List[str]] = None
    related_iso_clauses: Optional[List[str]] = None
    related_osha_standards: Optional[List[str]] = None
    related_law6331_articles: Optional[List[str]] = None


# ============================================================================
# WB/IFC ENVIRONMENTAL AND SOCIAL STANDARDS HIERARCHY
# ============================================================================

ESS_STRUCTURE = {
    "ESS1": {
        "name": "Assessment and Management of Environmental and Social Risks and Impacts",
        "requirements": {
            "1.1": ESSRequirement(
                ess_id="ESS1",
                requirement_id="1.1",
                title="Environmental and Social Assessment",
                description="Systematic process to identify, assess, and manage environmental and social risks and impacts",
                sub_requirements=["1.1.1", "1.1.2", "1.1.3"],
                related_iso_clauses=["6.1.1", "6.1.2", "6.1.3"],
                related_osha_standards=[],
                related_law6331_articles=["Article 10"],
            ),
            "1.2": ESSRequirement(
                ess_id="ESS1",
                requirement_id="1.2",
                title="Environmental and Social Management System",
                description="Establish and maintain management system and programs to address environmental and social risks",
                sub_requirements=["1.2.1", "1.2.2", "1.2.3"],
                related_iso_clauses=["4.4", "5.1", "5.2"],
                related_osha_standards=[],
                related_law6331_articles=["Article 4"],
            ),
            "1.3": ESSRequirement(
                ess_id="ESS1",
                requirement_id="1.3",
                title="Monitoring and Review",
                description="Monitor and review environmental and social performance",
                sub_requirements=["1.3.1", "1.3.2"],
                related_iso_clauses=["9.1", "9.2", "9.3"],
                related_osha_standards=[],
                related_law6331_articles=["Article 10"],
            ),
        },
    },
    "ESS2": {
        "name": "Labor and Working Conditions",
        "requirements": {
            "2.1": ESSRequirement(
                ess_id="ESS2",
                requirement_id="2.1",
                title="Working Conditions and Management of Worker Relationships",
                description="Fair treatment, non-discrimination, equal opportunity, and protection of worker rights",
                sub_requirements=["2.1.1", "2.1.2", "2.1.3", "2.1.4"],
                related_iso_clauses=["5.4"],
                related_osha_standards=[],
                related_law6331_articles=["Article 5", "Article 24"],
            ),
            "2.2": ESSRequirement(
                ess_id="ESS2",
                requirement_id="2.2",
                title="Occupational Health and Safety",
                description="Promote safe and healthy working conditions, prevent accidents, injuries, and diseases",
                sub_requirements=["2.2.1", "2.2.2", "2.2.3"],
                related_iso_clauses=["8.1.1", "8.1.2", "8.1.3", "8.2"],
                related_osha_standards=[
                    "1910.132",  # PPE General
                    "1910.146",  # Confined Space
                    "1926.501",  # Fall Protection
                    "1910.147",  # LOTO
                    "1910.1200",  # HazCom
                    "1926.650",  # Excavation
                ],
                related_law6331_articles=["Article 4", "Article 10", "Article 17"],
            ),
            "2.3": ESSRequirement(
                ess_id="ESS2",
                requirement_id="2.3",
                title="Workers Engaged by Third Parties",
                description="Reasonable efforts to ensure third-party workers are managed in accordance with ESS2",
                sub_requirements=["2.3.1"],
                related_iso_clauses=["8.1.4"],
                related_osha_standards=[],
                related_law6331_articles=["Article 2"],
            ),
            "2.4": ESSRequirement(
                ess_id="ESS2",
                requirement_id="2.4",
                title="Grievance Mechanism",
                description="Accessible grievance mechanism for project workers",
                sub_requirements=["2.4.1", "2.4.2"],
                related_iso_clauses=["5.4", "10.2"],
                related_osha_standards=[],
                related_law6331_articles=["Article 24"],
            ),
        },
    },
    "ESS3": {
        "name": "Resource Efficiency and Pollution Prevention and Management",
        "requirements": {
            "3.1": ESSRequirement(
                ess_id="ESS3",
                requirement_id="3.1",
                title="Resource Efficiency",
                description="Efficient use of energy, water, and raw materials in project implementation",
                sub_requirements=["3.1.1", "3.1.2"],
                related_iso_clauses=[],
                related_osha_standards=[],
                related_law6331_articles=[],
            ),
            "3.2": ESSRequirement(
                ess_id="ESS3",
                requirement_id="3.2",
                title="Pollution Prevention",
                description="Avoid or minimize pollution from project activities",
                sub_requirements=["3.2.1", "3.2.2"],
                related_iso_clauses=["8.1"],
                related_osha_standards=["1910.1200"],  # HazCom
                related_law6331_articles=[],
            ),
            "3.3": ESSRequirement(
                ess_id="ESS3",
                requirement_id="3.3",
                title="Waste Management",
                description="Avoid or minimize generation of hazardous and non-hazardous waste",
                sub_requirements=["3.3.1"],
                related_iso_clauses=[],
                related_osha_standards=["1910.1200"],  # HazCom
                related_law6331_articles=[],
            ),
        },
    },
    "ESS4": {
        "name": "Community Health and Safety",
        "requirements": {
            "4.1": ESSRequirement(
                ess_id="ESS4",
                requirement_id="4.1",
                title="Community Health and Safety",
                description="Avoid or minimize risks to community health, safety, and security from project activities",
                sub_requirements=["4.1.1", "4.1.2", "4.1.3"],
                related_iso_clauses=["4.1", "4.2"],
                related_osha_standards=[],
                related_law6331_articles=[],
            ),
            "4.2": ESSRequirement(
                ess_id="ESS4",
                requirement_id="4.2",
                title="Traffic Safety",
                description="Promote safety of project-related traffic and road users",
                sub_requirements=["4.2.1"],
                related_iso_clauses=["8.1"],
                related_osha_standards=[],
                related_law6331_articles=[],
            ),
            "4.3": ESSRequirement(
                ess_id="ESS4",
                requirement_id="4.3",
                title="Security Personnel",
                description="Ensure security personnel are appropriately trained and act within applicable law",
                sub_requirements=["4.3.1", "4.3.2"],
                related_iso_clauses=["7.2"],
                related_osha_standards=[],
                related_law6331_articles=["Article 17"],
            ),
        },
    },
    "ESS5": {
        "name": "Land Acquisition, Restrictions on Land Use and Involuntary Resettlement",
        "requirements": {
            "5.1": ESSRequirement(
                ess_id="ESS5",
                requirement_id="5.1",
                title="Avoiding and Minimizing Resettlement",
                description="Avoid or minimize involuntary resettlement where feasible",
                sub_requirements=["5.1.1"],
                related_iso_clauses=[],
                related_osha_standards=[],
                related_law6331_articles=[],
            ),
        },
    },
    "ESS6": {
        "name": "Biodiversity Conservation and Sustainable Management of Living Natural Resources",
        "requirements": {
            "6.1": ESSRequirement(
                ess_id="ESS6",
                requirement_id="6.1",
                title="Biodiversity Conservation",
                description="Protect and conserve biodiversity and habitats",
                sub_requirements=["6.1.1"],
                related_iso_clauses=[],
                related_osha_standards=[],
                related_law6331_articles=[],
            ),
        },
    },
    "ESS7": {
        "name": "Indigenous Peoples/Sub-Saharan African Historically Underserved Traditional Local Communities",
        "requirements": {
            "7.1": ESSRequirement(
                ess_id="ESS7",
                requirement_id="7.1",
                title="Respect for Culture and Rights",
                description="Full respect for human rights, dignity, culture, and natural resource-based livelihoods",
                sub_requirements=["7.1.1"],
                related_iso_clauses=["5.4"],
                related_osha_standards=[],
                related_law6331_articles=[],
            ),
        },
    },
    "ESS8": {
        "name": "Cultural Heritage",
        "requirements": {
            "8.1": ESSRequirement(
                ess_id="ESS8",
                requirement_id="8.1",
                title="Cultural Heritage Protection",
                description="Protect cultural heritage from adverse impacts of project activities",
                sub_requirements=["8.1.1"],
                related_iso_clauses=[],
                related_osha_standards=[],
                related_law6331_articles=[],
            ),
        },
    },
    "ESS9": {
        "name": "Financial Intermediaries",
        "requirements": {
            "9.1": ESSRequirement(
                ess_id="ESS9",
                requirement_id="9.1",
                title="Financial Intermediary Assessment",
                description="Assess and manage environmental and social risks of financial intermediary sub-projects",
                sub_requirements=["9.1.1"],
                related_iso_clauses=[],
                related_osha_standards=[],
                related_law6331_articles=[],
            ),
        },
    },
    "ESS10": {
        "name": "Stakeholder Engagement and Information Disclosure",
        "requirements": {
            "10.1": ESSRequirement(
                ess_id="ESS10",
                requirement_id="10.1",
                title="Stakeholder Engagement",
                description="Engage with stakeholders throughout project life cycle",
                sub_requirements=["10.1.1", "10.1.2"],
                related_iso_clauses=["4.2"],
                related_osha_standards=[],
                related_law6331_articles=[],
            ),
            "10.2": ESSRequirement(
                ess_id="ESS10",
                requirement_id="10.2",
                title="Grievance Mechanism",
                description="Accessible grievance mechanism for affected communities",
                sub_requirements=["10.2.1"],
                related_iso_clauses=["10.2"],
                related_osha_standards=[],
                related_law6331_articles=["Article 24"],
            ),
        },
    },
}


# ============================================================================
# MAPPING FUNCTIONS
# ============================================================================


def get_ess_requirement(ess_id: str, requirement_id: str) -> Optional[ESSRequirement]:
    """
    Retrieve specific ESS requirement by ID.

    Args:
        ess_id: ESS standard ID (e.g., "ESS1", "ESS2")
        requirement_id: Requirement ID (e.g., "1.1", "2.2")

    Returns:
        ESSRequirement object or None if not found

    Example:
        >>> req = get_ess_requirement("ESS2", "2.2")
        >>> print(req.title)
        'Occupational Health and Safety'
    """
    ess = ESS_STRUCTURE.get(ess_id)
    if not ess:
        return None
    return ess["requirements"].get(requirement_id)


def get_all_ess_requirements(ess_id: str) -> List[ESSRequirement]:
    """
    Get all requirements for a specific ESS.

    Args:
        ess_id: ESS standard ID (e.g., "ESS1", "ESS2")

    Returns:
        List of ESSRequirement objects

    Example:
        >>> reqs = get_all_ess_requirements("ESS2")
        >>> print(len(reqs))
        4
    """
    ess = ESS_STRUCTURE.get(ess_id)
    if not ess:
        return []
    return list(ess["requirements"].values())


def map_iso_to_ess(iso_clause: str) -> List[ESSRequirement]:
    """
    Map ISO 45001 clause to relevant WB ESS requirements.

    Args:
        iso_clause: ISO 45001 clause number (e.g., "8.1.3", "6.1.2")

    Returns:
        List of related ESSRequirement objects

    Example:
        >>> reqs = map_iso_to_ess("8.1.3")
        >>> for r in reqs:
        ...     print(f"{r.ess_id}.{r.requirement_id}: {r.title}")
        ESS2.2.2: Occupational Health and Safety
    """
    results = []
    for ess_id, ess_data in ESS_STRUCTURE.items():
        for req_id, requirement in ess_data["requirements"].items():
            if requirement.related_iso_clauses and iso_clause in requirement.related_iso_clauses:
                results.append(requirement)
    return results


def map_osha_to_ess(osha_standard: str) -> List[ESSRequirement]:
    """
    Map OSHA standard to relevant WB ESS requirements.

    Args:
        osha_standard: OSHA standard number (e.g., "1910.146", "1926.501")

    Returns:
        List of related ESSRequirement objects

    Example:
        >>> reqs = map_osha_to_ess("1910.146")
        >>> for r in reqs:
        ...     print(f"{r.ess_id}.{r.requirement_id}: {r.title}")
        ESS2.2.2: Occupational Health and Safety
    """
    results = []
    for ess_id, ess_data in ESS_STRUCTURE.items():
        for req_id, requirement in ess_data["requirements"].items():
            if requirement.related_osha_standards and osha_standard in requirement.related_osha_standards:
                results.append(requirement)
    return results


def map_law6331_to_ess(article: str) -> List[ESSRequirement]:
    """
    Map Turkish Law 6331 article to relevant WB ESS requirements.

    Args:
        article: Law 6331 article (e.g., "Article 10", "Article 17")

    Returns:
        List of related ESSRequirement objects

    Example:
        >>> reqs = map_law6331_to_ess("Article 17")
        >>> for r in reqs:
        ...     print(f"{r.ess_id}.{r.requirement_id}: {r.title}")
        ESS2.2.2: Occupational Health and Safety
    """
    results = []
    for ess_id, ess_data in ESS_STRUCTURE.items():
        for req_id, requirement in ess_data["requirements"].items():
            if (
                requirement.related_law6331_articles
                and article in requirement.related_law6331_articles
            ):
                results.append(requirement)
    return results


def get_cross_references(standard: str, clause_or_std: str) -> Dict[str, List[str]]:
    """
    Get all cross-references for a given standard clause.

    Args:
        standard: "ISO45001", "OSHA", or "LAW6331"
        clause_or_std: Clause/standard identifier

    Returns:
        Dict with iso_clauses, osha_standards, law6331_articles, ess_requirements

    Example:
        >>> refs = get_cross_references("ISO45001", "8.1.3")
        >>> print(refs["ess_requirements"])
        ['ESS2.2.2']
    """
    if standard == "ISO45001":
        ess_reqs = map_iso_to_ess(clause_or_std)
        return {
            "iso_clause": clause_or_std,
            "ess_requirements": [f"{r.ess_id}.{r.requirement_id}" for r in ess_reqs],
            "osha_standards": list(
                set(osha for r in ess_reqs for osha in (r.related_osha_standards or []))
            ),
            "law6331_articles": list(
                set(
                    article
                    for r in ess_reqs
                    for article in (r.related_law6331_articles or [])
                )
            ),
        }
    elif standard == "OSHA":
        ess_reqs = map_osha_to_ess(clause_or_std)
        return {
            "osha_standard": clause_or_std,
            "ess_requirements": [f"{r.ess_id}.{r.requirement_id}" for r in ess_reqs],
            "iso_clauses": list(
                set(iso for r in ess_reqs for iso in (r.related_iso_clauses or []))
            ),
            "law6331_articles": list(
                set(
                    article
                    for r in ess_reqs
                    for article in (r.related_law6331_articles or [])
                )
            ),
        }
    elif standard == "LAW6331":
        ess_reqs = map_law6331_to_ess(clause_or_std)
        return {
            "law6331_article": clause_or_std,
            "ess_requirements": [f"{r.ess_id}.{r.requirement_id}" for r in ess_reqs],
            "iso_clauses": list(
                set(iso for r in ess_reqs for iso in (r.related_iso_clauses or []))
            ),
            "osha_standards": list(
                set(osha for r in ess_reqs for osha in (r.related_osha_standards or []))
            ),
        }
    return {}


def get_ess_summary() -> Dict[str, Dict]:
    """
    Get summary of all ESS standards with requirement counts.

    Returns:
        Dict mapping ESS ID to metadata dict

    Example:
        >>> summary = get_ess_summary()
        >>> print(summary["ESS2"]["name"])
        'Labor and Working Conditions'
        >>> print(summary["ESS2"]["requirement_count"])
        4
    """
    summary = {}
    for ess_id, ess_data in ESS_STRUCTURE.items():
        summary[ess_id] = {
            "name": ess_data["name"],
            "requirement_count": len(ess_data["requirements"]),
            "requirements": list(ess_data["requirements"].keys()),
        }
    return summary


def find_ohs_related_ess() -> List[str]:
    """
    Find all ESS requirements related to occupational health and safety.

    Returns requirements that have ISO 45001 or OSHA mappings.

    Returns:
        List of ESS requirement IDs (e.g., ["ESS2.2.2", "ESS4.4.1"])

    Example:
        >>> ohs_reqs = find_ohs_related_ess()
        >>> print(len(ohs_reqs))
        3
    """
    ohs_requirements = []
    for ess_id, ess_data in ESS_STRUCTURE.items():
        for req_id, requirement in ess_data["requirements"].items():
            # Check if has ISO 45001 or OSHA mappings
            has_iso = requirement.related_iso_clauses and len(requirement.related_iso_clauses) > 0
            has_osha = requirement.related_osha_standards and len(requirement.related_osha_standards) > 0

            if has_iso or has_osha:
                ohs_requirements.append(f"{ess_id}.{req_id}")

    return ohs_requirements


def get_compliance_gap_analysis(
    covered_standards: List[str], covered_clauses: List[str]
) -> Dict[str, List[str]]:
    """
    Identify ESS requirements not covered by current standards/clauses.

    Args:
        covered_standards: List of standards being validated (e.g., ["ISO45001", "OSHA"])
        covered_clauses: List of specific clauses/standards covered

    Returns:
        Dict with 'covered' and 'gaps' ESS requirement lists

    Example:
        >>> gaps = get_compliance_gap_analysis(
        ...     ["ISO45001"],
        ...     ["8.1.1", "8.1.2", "8.1.3"]
        ... )
        >>> print(gaps["covered"])
        ['ESS2.2.2']
        >>> print(gaps["gaps"])
        ['ESS2.2.1', 'ESS4.4.1']
    """
    covered_ess = set()
    all_ohs_ess = set(find_ohs_related_ess())

    # Map covered clauses to ESS
    for clause in covered_clauses:
        if "ISO45001" in covered_standards:
            ess_reqs = map_iso_to_ess(clause)
            covered_ess.update(f"{r.ess_id}.{r.requirement_id}" for r in ess_reqs)
        if "OSHA" in covered_standards:
            ess_reqs = map_osha_to_ess(clause)
            covered_ess.update(f"{r.ess_id}.{r.requirement_id}" for r in ess_reqs)
        if "LAW6331" in covered_standards:
            ess_reqs = map_law6331_to_ess(clause)
            covered_ess.update(f"{r.ess_id}.{r.requirement_id}" for r in ess_reqs)

    gaps = all_ohs_ess - covered_ess

    return {"covered": sorted(list(covered_ess)), "gaps": sorted(list(gaps))}
