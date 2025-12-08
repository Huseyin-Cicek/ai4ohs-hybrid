"""
CAG (Compliance-Augmented Generation) API Router

Provides compliance validation endpoints for OHS standards.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.utils.compliance import get_available_standards, get_rules_summary, validate_document
from governance.cag_rules_engine import CAGRulesEngine
from governance.ess_compliance_scorer import ess_score_from_items

router = APIRouter()


class ValidateRequest(BaseModel):
    """Request model for compliance validation."""

    text: str = Field(..., description="Document text to validate", min_length=1)
    standards: List[str] = Field(
        ...,
        description="Standards to validate against (ISO45001, OSHA, LAW6331, WB_ESS)",
        min_length=1,
    )
    context: Dict = Field(
        default_factory=dict,
        description="Context metadata (activity, location, project_type, etc.)",
    )
    categories: Optional[List[str]] = Field(
        None, description="Optional filter by rule categories (ppe, confined_space, etc.)"
    )


class ViolationDetail(BaseModel):
    """Individual violation detail."""

    rule_id: str
    standard: str
    category: str
    severity: str
    requirement: str
    issues: List[str]
    description: Optional[str] = None
    remediation: Optional[str] = None


class WarningDetail(BaseModel):
    """Warning detail."""

    message: str
    severity: str


class ValidationStats(BaseModel):
    """Validation execution statistics."""

    rules_checked: int
    rules_passed: int
    violations_found: int
    critical_violations: int
    major_violations: int
    minor_violations: int


class ValidateResponse(BaseModel):
    """Response model for compliance validation."""

    ok: bool = Field(..., description="True if no violations found")
    violations: List[ViolationDetail] = Field(
        default_factory=list, description="List of violations by severity"
    )
    warnings: List[WarningDetail] = Field(
        default_factory=list, description="Non-critical warnings"
    )
    stats: ValidationStats = Field(..., description="Execution statistics")


@router.post("", response_model=ValidateResponse, tags=["cag"])
def validate(request: ValidateRequest):
    """
    Validate document against OHS compliance standards.

    Executes rule-based validation without LLM dependencies (100% offline).
    Returns compliance status, violations by severity, and remediation guidance.

    **Supported Standards:**
    - ISO45001: ISO 45001 Occupational Health and Safety Management Systems
    - OSHA: OSHA 29 CFR US Occupational Safety and Health Standards
    - LAW6331: Turkish Law 6331 Occupational Health and Safety Law
    - WB_ESS: World Bank/IFC Environmental and Social Standards

    **Severity Levels:**
    - critical: Immediate safety risk, project stopper
    - major: Regulatory violation, must fix before audit
    - minor: Best practice, improvement recommended

    **Example Request:**
    ```json
    {
        "text": "Excavation procedure requires hard hat and safety glasses.",
        "standards": ["ISO45001", "OSHA"],
        "context": {"activity": "excavation"}
    }
    ```

    **Example Response (Non-Compliant):**
    ```json
    {
        "ok": false,
        "violations": [
            {
                "rule_id": "ISO45001-8.1.3-PPE",
                "standard": "ISO45001",
                "category": "ppe",
                "severity": "major",
                "requirement": "Personal protective equipment shall be documented",
                "issues": ["Missing PPE requirement: steel-toed boots", "Missing PPE requirement: high-visibility vest"],
                "remediation": "Add comprehensive PPE list: hard hat, safety glasses, steel-toed boots, high-visibility vest"
            }
        ],
        "warnings": [],
        "stats": {
            "rules_checked": 15,
            "rules_passed": 14,
            "violations_found": 1,
            "critical_violations": 0,
            "major_violations": 1,
            "minor_violations": 0
        }
    }
    ```
    """
    try:
        # Validate standards
        available_standards = get_available_standards()
        invalid_standards = [s for s in request.standards if s not in available_standards]
        if invalid_standards:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid standards: {invalid_standards}. Available: {available_standards}",
            )

        # Execute validation (rule-based)
        result = validate_document(
            text=request.text,
            standards=request.standards,
            context=request.context,
            categories=request.categories,
        )

        # Lightweight CAG rulepack load for visibility (no heavy processing)
        try:
            cag_engine = CAGRulesEngine()
            rule_count = len(cag_engine.list_rules())
            result.warnings.append(
                {
                    "message": f"CAG rulepack loaded ({rule_count} rules)",
                    "severity": "info",
                }
            )
        except Exception:
            # CAG yüklenemezse mevcut sonucu bozma
            result.warnings.append(
                {
                    "message": "CAG rulepack could not be loaded; skipping deep check",
                    "severity": "warning",
                }
            )

        # ESS skor bilgilendirmesi (isteğe bağlı)
        try:
            ess_items = request.context.get("ess_items") or []
            if ess_items:
                ess_summary = ess_score_from_items(ess_items)
                result.warnings.append(
                    {
                        "message": f"ESS overall score: {ess_summary.get('overall_score', 0):.1f}",
                        "severity": "info",
                    }
                )
        except Exception:
            pass

        # Convert to response model
        return ValidateResponse(
            ok=result.ok,
            violations=[ViolationDetail(**v) for v in result.violations],
            warnings=[WarningDetail(**w) for w in result.warnings],
            stats=ValidationStats(**result.stats),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.get("/standards", tags=["cag"])
def list_standards():
    """
    List all supported compliance standards.

    Returns available standards and their rule counts.

    **Example Response:**
    ```json
    {
        "standards": ["ISO45001", "OSHA", "LAW6331", "WB_ESS"],
        "rules_by_standard": {
            "ISO45001": 3,
            "OSHA": 5,
            "LAW6331": 3,
            "WB_ESS": 3
        }
    }
    ```
    """
    return {"standards": get_available_standards(), "rules_by_standard": get_rules_summary()}


@router.get("/categories", tags=["cag"])
def list_categories():
    """
    List all available rule categories.

    Returns category names for filtering validation rules.

    **Example Response:**
    ```json
    {
        "categories": [
            "ppe",
            "confined_space",
            "working_at_height",
            "electrical_safety",
            "hazcom",
            "excavation",
            "risk_assessment",
            "emergency_response",
            "training"
        ]
    }
    ```
    """
    from src.utils.compliance import get_available_categories

    return {"categories": get_available_categories()}
