"""
CAG (Compliance-Augmented Generation) Engine

Rule-based validation system for OHS compliance standards:
- ISO 45001: Occupational Health and Safety Management Systems
- OSHA 29 CFR: US Occupational Safety and Health Standards
- Turkish Law 6331: Occupational Health and Safety Law
- WB/IFC ESS: World Bank/IFC Environmental and Social Standards

This module provides deterministic validation without LLM dependencies.
All rules operate 100% offline using regex, keyword matching, and structural analysis.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple


class Severity(str, Enum):
    """Violation severity levels for risk prioritization."""

    CRITICAL = "critical"  # Immediate safety risk, project stopper
    MAJOR = "major"  # Regulatory violation, must fix before audit
    MINOR = "minor"  # Best practice, improvement recommended


class Standard(str, Enum):
    """Supported OHS compliance standards."""

    ISO45001 = "ISO45001"
    OSHA = "OSHA"
    LAW6331 = "LAW6331"
    WB_ESS = "WB_ESS"


class RuleCategory:
    """Standard rule categories for organizational clarity."""

    PPE = "ppe"
    CONFINED_SPACE = "confined_space"
    HOT_WORK = "hot_work"
    EXCAVATION = "excavation"
    WORKING_AT_HEIGHT = "working_at_height"
    ELECTRICAL_SAFETY = "electrical_safety"
    HAZCOM = "hazcom"
    EMERGENCY_RESPONSE = "emergency_response"
    RISK_ASSESSMENT = "risk_assessment"
    TRAINING = "training"
    INCIDENT_MANAGEMENT = "incident_management"


@dataclass
class ComplianceRule:
    """
    Individual compliance rule with validation function.

    Attributes:
        rule_id: Unique identifier (e.g., "ISO45001-8.1.3-PPE")
        standard: Which standard this rule enforces
        category: Logical grouping (PPE, confined space, etc.)
        requirement: Human-readable requirement description
        severity: Risk level (critical, major, minor)
        validation_fn: Function that validates text against this rule
        description: Detailed explanation of the rule
        remediation: Guidance for fixing violations
    """

    rule_id: str
    standard: Standard
    category: str
    requirement: str
    severity: Severity
    validation_fn: Callable[[str, Dict], Tuple[bool, List[str]]]
    description: Optional[str] = None
    remediation: Optional[str] = None


@dataclass
class ValidationResult:
    """
    Result of document validation.

    Attributes:
        ok: True if no violations found
        violations: List of violation details
        warnings: List of non-critical warnings
        stats: Execution statistics
    """

    ok: bool
    violations: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)


# ============================================================================
# VALIDATION HELPER FUNCTIONS
# ============================================================================


def has_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> List[str]:
    """
    Check which keywords are missing from text.

    Args:
        text: Document text to search
        keywords: List of required keywords
        case_sensitive: Whether to match case

    Returns:
        List of missing keywords
    """
    target = text if case_sensitive else text.lower()
    missing = []
    for kw in keywords:
        search_kw = kw if case_sensitive else kw.lower()
        if search_kw not in target:
            missing.append(kw)
    return missing


def has_section_header(text: str, header_pattern: str) -> bool:
    """
    Check if text contains a section with given header pattern.

    Args:
        text: Document text to search
        header_pattern: Regex pattern for section header

    Returns:
        True if header found
    """
    pattern = re.compile(header_pattern, re.IGNORECASE | re.MULTILINE)
    return bool(pattern.search(text))


def extract_numeric_values(text: str, pattern: re.Pattern) -> List[float]:
    """
    Extract numeric values matching pattern (e.g., '50 feet', '2 meters').

    Args:
        text: Document text to search
        pattern: Compiled regex pattern with numeric capture group

    Returns:
        List of extracted numeric values
    """
    matches = pattern.findall(text)
    values = []
    for m in matches:
        try:
            # Handle both string and tuple matches
            val = m[0] if isinstance(m, tuple) else m
            values.append(float(val))
        except (ValueError, IndexError):
            continue
    return values


def has_any_keyword(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
    """
    Check if text contains any of the keywords.

    Args:
        text: Document text to search
        keywords: List of keywords to check
        case_sensitive: Whether to match case

    Returns:
        True if any keyword found
    """
    target = text if case_sensitive else text.lower()
    for kw in keywords:
        search_kw = kw if case_sensitive else kw.lower()
        if search_kw in target:
            return True
    return False


# ============================================================================
# VALIDATION FUNCTIONS - ISO 45001
# ============================================================================


def validate_ppe_requirements(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    ISO 45001 8.1.3 - PPE requirements must be documented.

    Validates that all activity-specific PPE is explicitly mentioned.

    Args:
        text: Document text to validate
        context: Must contain 'activity' key (excavation, confined_space, hot_work, general)

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    activity = context.get("activity", "general")

    # Activity-specific PPE requirements
    ppe_map = {
        "excavation": [
            "hard hat",
            "safety glasses",
            "steel-toed boots",
            "high-visibility vest",
        ],
        "confined_space": ["hard hat", "safety harness", "gas monitor", "respirator"],
        "hot_work": ["welding helmet", "fire-resistant clothing", "leather gloves"],
        "working_at_height": ["hard hat", "safety harness", "lanyard", "anchor point"],
        "electrical": ["arc-rated clothing", "insulated gloves", "face shield"],
        "general": ["hard hat", "safety glasses", "steel-toed boots"],
    }

    required_ppe = ppe_map.get(activity, ppe_map["general"])
    missing = has_keywords(text, required_ppe)

    violations = [f"Missing PPE requirement: {item}" for item in missing]
    return (len(violations) == 0, violations)


def validate_risk_assessment(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    ISO 45001 6.1.2 - Hazard identification and risk assessment required.

    Validates that document includes risk assessment methodology and results.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Required risk assessment components
    required_sections = [
        (r"hazard\s+identification", "Hazard identification section"),
        (r"risk\s+assessment", "Risk assessment methodology"),
        (r"risk\s+matrix|severity|likelihood|probability", "Risk rating system"),
        (r"control\s+measures|mitigation", "Control measures"),
    ]

    for pattern, description in required_sections:
        if not has_section_header(text, pattern):
            violations.append(f"Missing required section: {description}")

    # Check for hierarchy of controls mention
    hierarchy_terms = [
        "elimination",
        "substitution",
        "engineering controls",
        "administrative controls",
        "ppe",
    ]
    if not has_any_keyword(text, hierarchy_terms):
        violations.append("Missing hierarchy of controls reference")

    return (len(violations) == 0, violations)


def validate_emergency_procedures(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    ISO 45001 8.2 - Emergency preparedness and response.

    Validates that emergency procedures are documented.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Required emergency components
    required_elements = [
        "emergency contact",
        "evacuation",
        "first aid",
        "emergency assembly point",
    ]
    missing = has_keywords(text, required_elements)
    violations.extend([f"Missing emergency element: {elem}" for elem in missing])

    # Check for emergency drills mention
    if not has_section_header(text, r"drill|exercise|training"):
        violations.append("Missing emergency drill/training procedure")

    return (len(violations) == 0, violations)


# ============================================================================
# VALIDATION FUNCTIONS - OSHA
# ============================================================================


def validate_confined_space_entry_permit(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    OSHA 29 CFR 1910.146 - Confined space entry procedures.

    Validates permit-required confined space entry requirements.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Required sections per OSHA 1910.146
    required_sections = [
        (r"atmospheric\s+testing", "Atmospheric testing procedure"),
        (r"entry\s+supervisor", "Entry supervisor designation"),
        (r"attendant", "Attendant designation"),
        (r"rescue\s+plan|emergency\s+rescue", "Emergency rescue plan"),
        (r"communication\s+procedure", "Communication procedure"),
    ]

    for pattern, description in required_sections:
        if not has_section_header(text, pattern):
            violations.append(f"Missing required section: {description}")

    # Required equipment
    required_equipment = ["gas monitor", "ventilation", "rescue equipment"]
    missing_equipment = has_keywords(text, required_equipment)
    violations.extend([f"Missing equipment: {eq}" for eq in missing_equipment])

    # Check for acceptable atmospheric conditions
    if not has_section_header(text, r"oxygen.*19\.5.*23\.5|o2.*level"):
        violations.append("Missing oxygen level requirements (19.5-23.5%)")

    return (len(violations) == 0, violations)


def validate_fall_protection_plan(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    OSHA 29 CFR 1926.501 - Fall protection at heights.

    Validates fall protection requirements for work at 6 feet or greater.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Extract height values (e.g., "6 feet", "2 meters")
    height_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(?:feet|ft|meters|m)\b", re.IGNORECASE)
    heights = extract_numeric_values(text, height_pattern)

    # Check if fall protection is mentioned for work above 6 feet
    if any(h >= 6 for h in heights):
        fall_protection_terms = [
            "guardrail",
            "safety net",
            "personal fall arrest",
            "harness",
        ]
        if not has_any_keyword(text, fall_protection_terms):
            violations.append("Work at 6+ feet requires fall protection system")

        # Check for anchor point specification if harness is used
        if has_any_keyword(text, ["harness", "lanyard"]):
            # Need at least one: "anchor point" OR "anchorage"
            if not has_any_keyword(text, ["anchor point", "anchorage"]):
                violations.append("Fall arrest system requires anchor point specification")

    # Check for competent person designation (only required if working at height)
    if heights and any(h >= 6 for h in heights):
        missing_competent = has_keywords(text, ["competent person"])
        if missing_competent:  # If has_keywords returns non-empty list, item is missing
            violations.append("Missing competent person designation for fall protection")

    return (len(violations) == 0, violations)


def validate_loto_procedure(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    OSHA 29 CFR 1910.147 - Lockout/Tagout procedures.

    Validates energy control procedures (LOTO).

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Required 7-step LOTO procedure
    required_steps = [
        "preparation",
        "shutdown",
        "isolation",
        "lockout",
        "stored energy",
        "verification",
        "restoration",
    ]
    missing_steps = has_keywords(text, required_steps)
    violations.extend([f"Missing LOTO step: {step}" for step in missing_steps])

    # Check for authorized employee list
    if not has_section_header(text, r"authorized\s+(?:employees?|personnel)"):
        violations.append("Missing authorized employee designation")

    # Check for lockout device specification
    if not has_any_keyword(text, ["lockout device", "lock", "tag"]):
        violations.append("Missing lockout device specification")

    return (len(violations) == 0, violations)


def validate_hazcom_program(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    OSHA 29 CFR 1910.1200 - Hazard Communication Standard.

    Validates HazCom program requirements.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Required HazCom elements
    required_elements = [
        "safety data sheet",
        "chemical inventory",
        "labeling",
        "training",
    ]
    missing = has_keywords(text, required_elements)
    violations.extend([f"Missing HazCom element: {elem}" for elem in missing])

    # Check for GHS mention
    if not has_any_keyword(text, ["ghs", "globally harmonized system"]):
        violations.append("Missing GHS (Globally Harmonized System) reference")

    return (len(violations) == 0, violations)


def validate_excavation_safety(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    OSHA 29 CFR 1926.650 - Excavation safety requirements.

    Validates excavation and trenching procedures.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Required excavation safety elements
    required_sections = [
        (r"soil\s+classification", "Soil classification"),
        (r"protective\s+system|shoring|sloping|trench\s+box", "Protective system"),
        (r"competent\s+person", "Competent person designation"),
        (r"atmospheric\s+testing", "Atmospheric testing for 4+ feet depth"),
    ]

    for pattern, description in required_sections:
        if not has_section_header(text, pattern):
            violations.append(f"Missing required section: {description}")

    # Check for depth-specific requirements
    depth_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(?:feet|ft)\s+(?:deep|depth)", re.IGNORECASE)
    depths = extract_numeric_values(text, depth_pattern)

    if any(d >= 5 for d in depths):
        if not has_any_keyword(text, ["ladder", "access", "egress"]):
            violations.append("Excavations 5+ feet deep require safe access/egress (ladder)")

    return (len(violations) == 0, violations)


# ============================================================================
# VALIDATION FUNCTIONS - TURKISH LAW 6331
# ============================================================================


def validate_law6331_workplace_physician(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    Turkish Law 6331 Article 6 - Workplace physician requirements.

    Validates that workplace physician obligations are documented.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Required elements per Law 6331
    required_elements = [
        "workplace physician",
        "occupational health",
        "periodic health examination",
    ]
    missing = has_keywords(text, required_elements)
    violations.extend([f"Missing Law 6331 requirement: {elem}" for elem in missing])

    return (len(violations) == 0, violations)


def validate_law6331_ohs_specialist(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    Turkish Law 6331 Article 8 - OHS specialist requirements.

    Validates that OHS specialist obligations are documented.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Required OHS specialist elements
    if not has_any_keyword(text, ["ohs specialist", "occupational safety specialist", "iş güvenliği uzmanı"]):
        violations.append("Missing OHS specialist designation (Law 6331 Article 8)")

    # Check for risk assessment by specialist
    if not has_section_header(text, r"risk\s+assessment.*specialist"):
        violations.append("Missing OHS specialist risk assessment requirement")

    return (len(violations) == 0, violations)


def validate_law6331_worker_training(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    Turkish Law 6331 Article 17 - Worker OHS training requirements.

    Validates training obligations.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # Required training elements
    required_training = [
        "ohs training",
        "training duration",
        "training documentation",
    ]
    missing = has_keywords(text, required_training)
    violations.extend([f"Missing training requirement: {elem}" for elem in missing])

    # Check for minimum training hours (Law 6331 specifies minimums)
    if not has_section_header(text, r"\d+\s*(?:hours?|saat).*training"):
        violations.append("Missing training duration specification")

    return (len(violations) == 0, violations)


# ============================================================================
# VALIDATION FUNCTIONS - WB/IFC ESS
# ============================================================================


def validate_ess2_working_conditions(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    WB/IFC ESS2 - Labor and working conditions.

    Validates fair treatment, non-discrimination, and worker rights.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # ESS2 core requirements
    required_elements = [
        "non-discrimination",
        "equal opportunity",
        "grievance mechanism",
        "working hours",
    ]
    missing = has_keywords(text, required_elements)
    violations.extend([f"Missing ESS2 requirement: {elem}" for elem in missing])

    # Check for child labor prohibition
    if not has_any_keyword(text, ["child labor", "minimum age"]):
        violations.append("Missing child labor prohibition (ESS2.2.1)")

    return (len(violations) == 0, violations)


def validate_ess2_ohs(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    WB/IFC ESS2.2 - Occupational health and safety.

    Validates OHS management system requirements.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # ESS2.2 OHS requirements
    required_sections = [
        (r"hazard.*identification", "Hazard identification"),
        (r"incident.*(?:reporting|investigation)", "Incident reporting"),
        (r"safety.*training", "Safety training"),
        (r"emergency.*(?:preparedness|response)", "Emergency response"),
    ]

    for pattern, description in required_sections:
        if not has_section_header(text, pattern):
            violations.append(f"Missing ESS2.2 requirement: {description}")

    return (len(violations) == 0, violations)


def validate_ess4_community_safety(text: str, context: Dict) -> Tuple[bool, List[str]]:
    """
    WB/IFC ESS4 - Community health and safety.

    Validates community impact considerations.

    Args:
        text: Document text to validate
        context: Optional metadata

    Returns:
        Tuple of (is_compliant, list_of_violations)
    """
    violations = []

    # ESS4 community safety elements
    required_elements = [
        "community",
        "stakeholder",
        "traffic safety",
        "site security",
    ]
    missing = has_keywords(text, required_elements)
    violations.extend([f"Missing ESS4 requirement: {elem}" for elem in missing])

    return (len(violations) == 0, violations)


# ============================================================================
# RULE REGISTRY
# ============================================================================

# Rule registry organized by standard and category
RULES: Dict[Standard, Dict[str, List[ComplianceRule]]] = {
    Standard.ISO45001: {
        RuleCategory.PPE: [],
        RuleCategory.RISK_ASSESSMENT: [],
        RuleCategory.EMERGENCY_RESPONSE: [],
        RuleCategory.TRAINING: [],
    },
    Standard.OSHA: {
        RuleCategory.CONFINED_SPACE: [],
        RuleCategory.WORKING_AT_HEIGHT: [],
        RuleCategory.ELECTRICAL_SAFETY: [],
        RuleCategory.HAZCOM: [],
        RuleCategory.EXCAVATION: [],
    },
    Standard.LAW6331: {
        RuleCategory.TRAINING: [],
        RuleCategory.RISK_ASSESSMENT: [],
    },
    Standard.WB_ESS: {
        RuleCategory.RISK_ASSESSMENT: [],
        RuleCategory.EMERGENCY_RESPONSE: [],
    },
}

# Register ISO 45001 rules
RULES[Standard.ISO45001][RuleCategory.PPE].append(
    ComplianceRule(
        rule_id="ISO45001-8.1.3-PPE",
        standard=Standard.ISO45001,
        category=RuleCategory.PPE,
        requirement="Personal protective equipment shall be documented",
        severity=Severity.MAJOR,
        validation_fn=validate_ppe_requirements,
        description="All required PPE must be explicitly listed in work procedures based on hazard analysis",
        remediation="Add comprehensive PPE list based on activity type: hard hat, safety glasses, steel-toed boots, high-visibility vest (excavation), respirator (confined space), etc.",
    )
)

RULES[Standard.ISO45001][RuleCategory.RISK_ASSESSMENT].append(
    ComplianceRule(
        rule_id="ISO45001-6.1.2-RISK-ASSESSMENT",
        standard=Standard.ISO45001,
        category=RuleCategory.RISK_ASSESSMENT,
        requirement="Hazard identification and risk assessment required",
        severity=Severity.CRITICAL,
        validation_fn=validate_risk_assessment,
        description="Document must include systematic hazard identification, risk assessment methodology, risk matrix, and control measures following hierarchy of controls",
        remediation="Include: hazard identification section, risk assessment methodology, risk matrix (severity/likelihood), control measures, and hierarchy of controls (elimination, substitution, engineering, administrative, PPE)",
    )
)

RULES[Standard.ISO45001][RuleCategory.EMERGENCY_RESPONSE].append(
    ComplianceRule(
        rule_id="ISO45001-8.2-EMERGENCY",
        standard=Standard.ISO45001,
        category=RuleCategory.EMERGENCY_RESPONSE,
        requirement="Emergency preparedness and response procedures",
        severity=Severity.CRITICAL,
        validation_fn=validate_emergency_procedures,
        description="Document must include emergency contact information, evacuation procedures, first aid provisions, assembly points, and drill schedules",
        remediation="Add: emergency contact numbers, evacuation routes/procedures, first aid kit locations, emergency assembly point, and drill/training schedule",
    )
)

# Register OSHA rules
RULES[Standard.OSHA][RuleCategory.CONFINED_SPACE].append(
    ComplianceRule(
        rule_id="OSHA-1910.146-CS-PERMIT",
        standard=Standard.OSHA,
        category=RuleCategory.CONFINED_SPACE,
        requirement="Confined space entry permit requirements",
        severity=Severity.CRITICAL,
        validation_fn=validate_confined_space_entry_permit,
        description="Entry permits must include all OSHA-required elements: atmospheric testing, entry supervisor, attendant, rescue plan, communication procedures, and equipment",
        remediation="Include: atmospheric testing procedure (O2 19.5-23.5%, LEL <10%, H2S <10ppm), entry supervisor designation, attendant designation, emergency rescue plan, communication procedures, and required equipment (gas monitor, ventilation, rescue equipment)",
    )
)

RULES[Standard.OSHA][RuleCategory.WORKING_AT_HEIGHT].append(
    ComplianceRule(
        rule_id="OSHA-1926.501-FALL-PROTECTION",
        standard=Standard.OSHA,
        category=RuleCategory.WORKING_AT_HEIGHT,
        requirement="Fall protection for work above 6 feet",
        severity=Severity.CRITICAL,
        validation_fn=validate_fall_protection_plan,
        description="Fall protection required for work at heights 6 feet or greater; must specify system type (guardrails, safety nets, or personal fall arrest) and competent person",
        remediation="Specify: fall protection system type (guardrails, safety nets, or personal fall arrest with harness/lanyard/anchor point), competent person designation, and anchor point specifications",
    )
)

RULES[Standard.OSHA][RuleCategory.ELECTRICAL_SAFETY].append(
    ComplianceRule(
        rule_id="OSHA-1910.147-LOTO",
        standard=Standard.OSHA,
        category=RuleCategory.ELECTRICAL_SAFETY,
        requirement="Lockout/Tagout procedures",
        severity=Severity.CRITICAL,
        validation_fn=validate_loto_procedure,
        description="Energy isolation procedures must follow 7-step LOTO process with authorized employee designations and lockout device specifications",
        remediation="Document 7 steps: (1) preparation, (2) shutdown, (3) isolation, (4) lockout/tagout application, (5) stored energy release, (6) verification, (7) restoration. Include authorized employee list and lockout device specifications.",
    )
)

RULES[Standard.OSHA][RuleCategory.HAZCOM].append(
    ComplianceRule(
        rule_id="OSHA-1910.1200-HAZCOM",
        standard=Standard.OSHA,
        category=RuleCategory.HAZCOM,
        requirement="Hazard Communication Program",
        severity=Severity.MAJOR,
        validation_fn=validate_hazcom_program,
        description="HazCom program must include chemical inventory, safety data sheets (SDS), labeling requirements, training, and GHS compliance",
        remediation="Include: chemical inventory list, SDS management procedure, container labeling requirements (GHS), employee training program, and GHS (Globally Harmonized System) compliance statement",
    )
)

RULES[Standard.OSHA][RuleCategory.EXCAVATION].append(
    ComplianceRule(
        rule_id="OSHA-1926.650-EXCAVATION",
        standard=Standard.OSHA,
        category=RuleCategory.EXCAVATION,
        requirement="Excavation and trenching safety",
        severity=Severity.CRITICAL,
        validation_fn=validate_excavation_safety,
        description="Excavation procedures must include soil classification, protective systems (shoring/sloping/trench box), competent person designation, atmospheric testing for depths 4+ feet, and safe access/egress for depths 5+ feet",
        remediation="Add: soil classification (Type A/B/C), protective system specification (shoring, sloping, or trench box), competent person designation, atmospheric testing for 4+ feet depth, and ladder/safe access for 5+ feet depth",
    )
)

# Register Turkish Law 6331 rules
RULES[Standard.LAW6331][RuleCategory.RISK_ASSESSMENT].append(
    ComplianceRule(
        rule_id="LAW6331-ART6-PHYSICIAN",
        standard=Standard.LAW6331,
        category=RuleCategory.RISK_ASSESSMENT,
        requirement="Workplace physician obligations",
        severity=Severity.MAJOR,
        validation_fn=validate_law6331_workplace_physician,
        description="Document must reference workplace physician designation, occupational health services, and periodic health examination requirements per Turkish Law 6331 Article 6",
        remediation="Include: workplace physician designation, occupational health service scope, and periodic health examination schedule",
    )
)

RULES[Standard.LAW6331][RuleCategory.RISK_ASSESSMENT].append(
    ComplianceRule(
        rule_id="LAW6331-ART8-OHS-SPECIALIST",
        standard=Standard.LAW6331,
        category=RuleCategory.RISK_ASSESSMENT,
        requirement="OHS specialist obligations",
        severity=Severity.MAJOR,
        validation_fn=validate_law6331_ohs_specialist,
        description="Document must reference OHS specialist designation and risk assessment responsibilities per Turkish Law 6331 Article 8",
        remediation="Include: OHS specialist designation (İş Güvenliği Uzmanı) and risk assessment conducted by specialist statement",
    )
)

RULES[Standard.LAW6331][RuleCategory.TRAINING].append(
    ComplianceRule(
        rule_id="LAW6331-ART17-TRAINING",
        standard=Standard.LAW6331,
        category=RuleCategory.TRAINING,
        requirement="Worker OHS training requirements",
        severity=Severity.MAJOR,
        validation_fn=validate_law6331_worker_training,
        description="Document must specify OHS training program, duration (minimum hours per Law 6331), and documentation requirements per Article 17",
        remediation="Include: OHS training program description, minimum training hours (per Law 6331 regulations), training documentation/record-keeping system",
    )
)

# Register WB/IFC ESS rules
RULES[Standard.WB_ESS][RuleCategory.RISK_ASSESSMENT].append(
    ComplianceRule(
        rule_id="ESS2-2.1-WORKING-CONDITIONS",
        standard=Standard.WB_ESS,
        category=RuleCategory.RISK_ASSESSMENT,
        requirement="Labor and working conditions (ESS2.2.1)",
        severity=Severity.MAJOR,
        validation_fn=validate_ess2_working_conditions,
        description="Document must address non-discrimination, equal opportunity, grievance mechanisms, working hours, and child labor prohibition per WB/IFC ESS2",
        remediation="Include: non-discrimination policy, equal opportunity statement, grievance mechanism description, working hours limits, and child labor prohibition (minimum age requirements)",
    )
)

RULES[Standard.WB_ESS][RuleCategory.EMERGENCY_RESPONSE].append(
    ComplianceRule(
        rule_id="ESS2-2.2-OHS",
        standard=Standard.WB_ESS,
        category=RuleCategory.EMERGENCY_RESPONSE,
        requirement="Occupational health and safety (ESS2.2.2)",
        severity=Severity.CRITICAL,
        validation_fn=validate_ess2_ohs,
        description="Document must include hazard identification, incident reporting, safety training, and emergency response per WB/IFC ESS2.2",
        remediation="Include: hazard identification process, incident reporting/investigation procedures, safety training program, and emergency preparedness/response plan",
    )
)

RULES[Standard.WB_ESS][RuleCategory.EMERGENCY_RESPONSE].append(
    ComplianceRule(
        rule_id="ESS4-4.1-COMMUNITY-SAFETY",
        standard=Standard.WB_ESS,
        category=RuleCategory.EMERGENCY_RESPONSE,
        requirement="Community health and safety (ESS4.4.1)",
        severity=Severity.MAJOR,
        validation_fn=validate_ess4_community_safety,
        description="Document must address community impact considerations including stakeholder engagement, traffic safety, and site security per WB/IFC ESS4",
        remediation="Include: community impact assessment, stakeholder engagement plan, traffic safety measures, and site security procedures",
    )
)


# ============================================================================
# MAIN VALIDATION ORCHESTRATOR
# ============================================================================


def validate_document(
    text: str,
    standards: List[str],
    context: Dict,
    categories: Optional[List[str]] = None,
) -> ValidationResult:
    """
    Execute compliance validation against specified standards.

    This is the main entry point for CAG validation. Executes all registered
    rules for the specified standards and returns comprehensive results.

    Args:
        text: Document text to validate
        standards: List of standard names (e.g., ["ISO45001", "OSHA"])
        context: Metadata dict (activity, location, project_type, etc.)
        categories: Optional list to filter specific rule categories

    Returns:
        ValidationResult with violations, warnings, and execution stats

    Example:
        >>> result = validate_document(
        ...     text="Safety procedure...",
        ...     standards=["ISO45001", "OSHA"],
        ...     context={"activity": "excavation"}
        ... )
        >>> print(f"Compliant: {result.ok}")
        >>> print(f"Violations: {len(result.violations)}")
    """
    violations = []
    warnings = []
    rules_checked = 0
    rules_passed = 0

    for standard_name in standards:
        # Validate standard name
        try:
            standard = Standard(standard_name)
        except ValueError:
            warnings.append(
                {
                    "message": f"Unknown standard: {standard_name}",
                    "severity": "info",
                }
            )
            continue

        # Get rules for this standard
        standard_rules = RULES.get(standard, {})

        for category, rules in standard_rules.items():
            # Filter by category if specified
            if categories and category not in categories:
                continue

            for rule in rules:
                rules_checked += 1
                try:
                    # Execute validation function
                    is_compliant, issues = rule.validation_fn(text, context)

                    if not is_compliant:
                        violations.append(
                            {
                                "rule_id": rule.rule_id,
                                "standard": rule.standard.value,
                                "category": rule.category,
                                "severity": rule.severity.value,
                                "requirement": rule.requirement,
                                "issues": issues,
                                "description": rule.description,
                                "remediation": rule.remediation,
                            }
                        )
                    else:
                        rules_passed += 1

                except Exception as e:
                    # Catch validation function errors
                    warnings.append(
                        {
                            "message": f"Rule {rule.rule_id} execution failed: {str(e)}",
                            "severity": "error",
                        }
                    )

    # Calculate statistics
    stats = {
        "rules_checked": rules_checked,
        "rules_passed": rules_passed,
        "violations_found": len(violations),
        "critical_violations": sum(1 for v in violations if v["severity"] == "critical"),
        "major_violations": sum(1 for v in violations if v["severity"] == "major"),
        "minor_violations": sum(1 for v in violations if v["severity"] == "minor"),
    }

    # Sort violations by severity (critical first, then major, then minor)
    sorted_violations = sorted(
        violations,
        key=lambda x: (
            0 if x["severity"] == "critical" else 1 if x["severity"] == "major" else 2,
            x["rule_id"],
        ),
    )

    return ValidationResult(
        ok=len(violations) == 0, violations=sorted_violations, warnings=warnings, stats=stats
    )


def get_available_standards() -> List[str]:
    """
    Get list of all supported standards.

    Returns:
        List of standard names
    """
    return [s.value for s in Standard]


def get_available_categories() -> List[str]:
    """
    Get list of all available rule categories.

    Returns:
        List of category names
    """
    return [
        RuleCategory.PPE,
        RuleCategory.CONFINED_SPACE,
        RuleCategory.HOT_WORK,
        RuleCategory.EXCAVATION,
        RuleCategory.WORKING_AT_HEIGHT,
        RuleCategory.ELECTRICAL_SAFETY,
        RuleCategory.HAZCOM,
        RuleCategory.EMERGENCY_RESPONSE,
        RuleCategory.RISK_ASSESSMENT,
        RuleCategory.TRAINING,
        RuleCategory.INCIDENT_MANAGEMENT,
    ]


def get_rules_summary() -> Dict[str, int]:
    """
    Get summary of registered rules by standard.

    Returns:
        Dict mapping standard name to rule count
    """
    summary = {}
    for standard, categories in RULES.items():
        rule_count = sum(len(rules) for rules in categories.values())
        summary[standard.value] = rule_count
    return summary
