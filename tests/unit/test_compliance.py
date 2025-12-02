"""
Unit tests for compliance.py CAG engine.

Tests all validation functions with positive and negative test cases.
"""

from src.utils.compliance import (
    get_available_categories,
    get_available_standards,
    get_rules_summary,
    validate_confined_space_entry_permit,
    validate_document,
    validate_emergency_procedures,
    validate_ess2_ohs,
    validate_ess2_working_conditions,
    validate_ess4_community_safety,
    validate_excavation_safety,
    validate_fall_protection_plan,
    validate_law6331_ohs_specialist,
    validate_law6331_worker_training,
    validate_law6331_workplace_physician,
    validate_loto_procedure,
    validate_ppe_requirements,
    validate_risk_assessment,
)

# ============================================================================
# ISO 45001 VALIDATION TESTS
# ============================================================================


class TestPPEValidation:
    """Test PPE requirement validation (ISO 45001 8.1.3)."""

    def test_excavation_complete(self):
        """Test excavation with all required PPE."""
        text = """
        Excavation Safety Procedure
        Required PPE:
        - Hard hat
        - Safety glasses
        - Steel-toed boots
        - High-visibility vest
        """
        context = {"activity": "excavation"}

        is_compliant, violations = validate_ppe_requirements(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_excavation_missing_ppe(self):
        """Test excavation with missing PPE items."""
        text = "Excavation procedure requires hard hat and safety glasses."
        context = {"activity": "excavation"}

        is_compliant, violations = validate_ppe_requirements(text, context)

        assert not is_compliant
        assert len(violations) == 2
        assert "steel-toed boots" in str(violations)
        assert "high-visibility vest" in str(violations)

    def test_confined_space_complete(self):
        """Test confined space with all required PPE."""
        text = """
        Confined Space Entry Procedure
        Required PPE:
        - Hard hat
        - Safety harness
        - Gas monitor
        - Respirator
        """
        context = {"activity": "confined_space"}

        is_compliant, violations = validate_ppe_requirements(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_general_work_minimal(self):
        """Test general work with minimal PPE."""
        text = "General work requires hard hat, safety glasses, and steel-toed boots."
        context = {"activity": "general"}

        is_compliant, violations = validate_ppe_requirements(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_hot_work_missing(self):
        """Test hot work with missing PPE."""
        text = "Hot work procedure with welding helmet."
        context = {"activity": "hot_work"}

        is_compliant, violations = validate_ppe_requirements(text, context)

        assert not is_compliant
        assert "fire-resistant clothing" in str(violations)
        assert "leather gloves" in str(violations)


class TestRiskAssessment:
    """Test risk assessment validation (ISO 45001 6.1.2)."""

    def test_complete_risk_assessment(self):
        """Test document with complete risk assessment."""
        text = """
        Risk Assessment Procedure

        Hazard Identification:
        All potential hazards are identified through job hazard analysis.

        Risk Assessment Methodology:
        Risks are assessed using a 5x5 risk matrix considering severity and likelihood.

        Risk Matrix:
        Severity levels: 1-5
        Probability levels: 1-5
        Risk rating = Severity × Probability

        Control Measures:
        Following hierarchy of controls:
        1. Elimination
        2. Substitution
        3. Engineering controls
        4. Administrative controls
        5. PPE
        """
        context = {}

        is_compliant, violations = validate_risk_assessment(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_missing_hazard_identification(self):
        """Test missing hazard identification section."""
        text = """
        Safety Procedure
        Some control measures are in place.
        """
        context = {}

        is_compliant, violations = validate_risk_assessment(text, context)

        assert not is_compliant
        assert any("Hazard identification" in v for v in violations)

    def test_missing_hierarchy_of_controls(self):
        """Test missing hierarchy of controls."""
        text = """
        Hazard Identification: Conducted
        Risk Assessment: Completed
        Risk Matrix: 3x3 matrix used
        Control Measures: Various controls implemented
        """
        context = {}

        is_compliant, violations = validate_risk_assessment(text, context)

        assert not is_compliant
        assert any("hierarchy of controls" in v for v in violations)


class TestEmergencyProcedures:
    """Test emergency procedures validation (ISO 45001 8.2)."""

    def test_complete_emergency_plan(self):
        """Test complete emergency preparedness plan."""
        text = """
        Emergency Response Plan

        Emergency Contact Numbers:
        - Emergency Coordinator: 555-0100
        - First Aid: 555-0101
        - Fire Department: 911

        Evacuation Procedures:
        All personnel must evacuate via marked exits.

        First Aid:
        First aid kits are located at main office and workshop.

        Emergency Assembly Point:
        North parking lot, 100 meters from building.

        Emergency Drills:
        Quarterly evacuation drills and annual training for all staff.
        """
        context = {}

        is_compliant, violations = validate_emergency_procedures(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_missing_elements(self):
        """Test missing emergency elements."""
        text = "Emergency contact: 911"
        context = {}

        is_compliant, violations = validate_emergency_procedures(text, context)

        assert not is_compliant
        assert len(violations) >= 3
        assert any("evacuation" in v for v in violations)
        assert any("first aid" in v for v in violations)


# ============================================================================
# OSHA VALIDATION TESTS
# ============================================================================


class TestConfinedSpaceEntry:
    """Test confined space entry validation (OSHA 1910.146)."""

    def test_complete_permit(self):
        """Test complete confined space entry permit."""
        text = """
        Confined Space Entry Procedure

        Atmospheric Testing:
        Test for oxygen (19.5-23.5%), LEL (<10%), H2S (<10ppm), CO (<35ppm)

        Entry Supervisor:
        John Doe, certified entry supervisor

        Attendant:
        Jane Smith will remain outside during entry

        Emergency Rescue Plan:
        Emergency rescue team on standby with rescue equipment
        Non-entry rescue preferred

        Communication Procedure:
        Radio check every 15 minutes
        Visual contact maintained

        Equipment:
        - Gas monitor (calibrated)
        - Ventilation fan (explosion-proof)
        - Rescue equipment (tripod, winch, harness)
        """
        context = {}

        is_compliant, violations = validate_confined_space_entry_permit(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_missing_atmospheric_testing(self):
        """Test missing atmospheric testing."""
        text = """
        Confined space entry with entry supervisor and attendant.
        Rescue plan in place.
        Communication via radio.
        """
        context = {}

        is_compliant, violations = validate_confined_space_entry_permit(text, context)

        assert not is_compliant
        assert any("Atmospheric testing" in v for v in violations)

    def test_missing_equipment(self):
        """Test missing required equipment."""
        text = """
        Atmospheric Testing: Completed
        Entry Supervisor: John Doe
        Attendant: Jane Smith
        Rescue Plan: Emergency team ready
        Communication Procedure: Radio every 15 min
        """
        context = {}

        is_compliant, violations = validate_confined_space_entry_permit(text, context)

        assert not is_compliant
        assert any("gas monitor" in v for v in violations)
        assert any("ventilation" in v for v in violations)


class TestFallProtection:
    """Test fall protection validation (OSHA 1926.501)."""

    def test_work_at_height_with_protection(self):
        """Test work above 6 feet with fall protection."""
        text = """
        Working at Height Procedure

        Work will be conducted at 10 feet above ground level.

        Fall Protection System:
        Personal fall arrest system with full-body harness, shock-absorbing lanyard,
        and certified anchor point.

        Competent Person:
        John Doe, certified competent person for fall protection, will inspect
        all equipment before use.

        Anchor Point:
        Structural steel beam, load-tested to 5000 lbs.
        """
        context = {}

        is_compliant, violations = validate_fall_protection_plan(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_high_work_no_protection(self):
        """Test work above 6 feet without fall protection."""
        text = """
        Maintenance procedure at 8 feet height.
        Use ladder to access equipment.
        """
        context = {}

        is_compliant, violations = validate_fall_protection_plan(text, context)

        assert not is_compliant
        assert any("fall protection system" in v for v in violations)

    def test_missing_competent_person(self):
        """Test missing competent person designation."""
        text = """
        Work at 10 feet with guardrails installed.
        """
        context = {}

        is_compliant, violations = validate_fall_protection_plan(text, context)

        assert not is_compliant
        assert any("competent person" in v for v in violations)

    def test_harness_without_anchor(self):
        """Test harness mentioned but no anchor point."""
        text = """
        Work at 12 feet height.
        Workers will wear safety harness and lanyard.
        Competent person: John Doe
        """
        context = {}

        is_compliant, violations = validate_fall_protection_plan(text, context)

        assert not is_compliant
        assert any("anchor point" in v for v in violations)


class TestLOTO:
    """Test lockout/tagout validation (OSHA 1910.147)."""

    def test_complete_loto_procedure(self):
        """Test complete 7-step LOTO procedure."""
        text = """
        Lockout/Tagout Procedure

        1. Preparation: Identify energy sources and isolation points
        2. Shutdown: Orderly shutdown of equipment
        3. Isolation: Disconnect or isolate all energy sources
        4. Lockout/Tagout: Apply locks and tags to isolation devices
        5. Stored Energy: Release or restrain stored energy (springs, hydraulics, capacitors)
        6. Verification: Test equipment to ensure energy isolation
        7. Restoration: Restore equipment to normal operation after work completion

        Authorized Employees:
        - John Doe (Electrician, Certificate #12345)
        - Jane Smith (Maintenance, Certificate #67890)

        Lockout Devices:
        Personal padlocks with unique keys
        Danger tags with employee name and date
        """
        context = {}

        is_compliant, violations = validate_loto_procedure(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_missing_steps(self):
        """Test LOTO with missing steps."""
        text = """
        LOTO Procedure:
        Preparation and shutdown completed.
        Apply locks to equipment.
        Authorized employees listed.
        """
        context = {}

        is_compliant, violations = validate_loto_procedure(text, context)

        assert not is_compliant
        assert len(violations) >= 3  # Missing isolation, stored energy, verification, restoration


class TestExcavationSafety:
    """Test excavation safety validation (OSHA 1926.650)."""

    def test_complete_excavation_plan(self):
        """Test complete excavation safety plan."""
        text = """
        Excavation Safety Plan

        Soil Classification:
        Type B soil (cohesive with unconfined compressive strength 0.5-1.5 tsf)

        Protective System:
        Trench box rated for 12 feet depth, installed before entry

        Competent Person:
        John Doe, certified competent person, will conduct daily inspections

        Atmospheric Testing:
        Required for excavations 4+ feet deep
        Test for oxygen, flammable gases, and toxic substances

        Access and Egress:
        Ladder provided every 25 feet for excavations 5+ feet deep
        """
        context = {}

        is_compliant, violations = validate_excavation_safety(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_missing_protective_system(self):
        """Test missing protective system."""
        text = """
        Excavation to 8 feet depth.
        Soil Classification: Type B
        Competent Person: John Doe
        """
        context = {}

        is_compliant, violations = validate_excavation_safety(text, context)

        assert not is_compliant
        assert any("Protective system" in v for v in violations)


# ============================================================================
# TURKISH LAW 6331 TESTS
# ============================================================================


class TestLaw6331:
    """Test Turkish Law 6331 validation."""

    def test_workplace_physician_complete(self):
        """Test complete workplace physician documentation."""
        text = """
        Occupational Health Program

        Workplace Physician:
        Dr. Mehmet Yılmaz, licensed workplace physician

        Occupational Health Services:
        - Health surveillance
        - Workplace health assessments
        - First aid and emergency response

        Periodic Health Examination:
        Annual health exams for all employees
        Pre-employment and job change exams as required
        """
        context = {}

        is_compliant, violations = validate_law6331_workplace_physician(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_ohs_specialist_complete(self):
        """Test complete OHS specialist documentation."""
        text = """
        Occupational Safety Program

        OHS Specialist (İş Güvenliği Uzmanı):
        Ahmet Demir, Class A OHS Specialist

        Risk Assessment by Specialist:
        Comprehensive risk assessment conducted by OHS specialist
        following Turkish Law 6331 requirements.
        """
        context = {}

        is_compliant, violations = validate_law6331_ohs_specialist(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_training_complete(self):
        """Test complete OHS training documentation."""
        text = """
        OHS Training Program

        Training Duration:
        - New employees: 16 hours minimum OHS training
        - Annual refresher: 8 hours
        - Job-specific training as required

        Training Documentation:
        Training records maintained for all employees
        Certificates issued upon completion
        """
        context = {}

        is_compliant, violations = validate_law6331_worker_training(text, context)

        assert is_compliant
        assert len(violations) == 0


# ============================================================================
# WB/IFC ESS TESTS
# ============================================================================


class TestESSValidation:
    """Test WB/IFC ESS validation."""

    def test_ess2_working_conditions_complete(self):
        """Test complete ESS2 working conditions."""
        text = """
        Labor Management Plan

        Non-Discrimination Policy:
        No discrimination based on gender, age, ethnicity, religion, or disability

        Equal Opportunity:
        Equal pay for equal work
        Equal access to training and promotion

        Grievance Mechanism:
        Workers can submit grievances anonymously
        Response within 30 days

        Working Hours:
        8 hours per day, 48 hours per week maximum
        Overtime voluntary and compensated

        Child Labor Prohibition:
        Minimum age 18 years for all positions
        Age verification during hiring
        """
        context = {}

        is_compliant, violations = validate_ess2_working_conditions(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_ess2_ohs_complete(self):
        """Test complete ESS2 OHS requirements."""
        text = """
        OHS Management System

        Hazard Identification:
        Systematic process for identifying workplace hazards

        Incident Reporting and Investigation:
        All incidents reported within 24 hours
        Root cause analysis conducted

        Safety Training:
        Mandatory OHS training for all workers
        Job-specific training provided

        Emergency Preparedness and Response:
        Emergency procedures documented
        Drills conducted quarterly
        """
        context = {}

        is_compliant, violations = validate_ess2_ohs(text, context)

        assert is_compliant
        assert len(violations) == 0

    def test_ess4_community_safety_complete(self):
        """Test complete ESS4 community safety."""
        text = """
        Community Health and Safety Plan

        Community Impact Assessment:
        Stakeholder consultation conducted
        Community concerns documented

        Traffic Safety:
        Speed limits enforced near residential areas
        Warning signs installed

        Site Security:
        Security personnel trained in community relations
        Emergency contact information shared with community
        """
        context = {}

        is_compliant, violations = validate_ess4_community_safety(text, context)

        assert is_compliant
        assert len(violations) == 0


# ============================================================================
# MAIN VALIDATION ORCHESTRATOR TESTS
# ============================================================================


class TestValidateDocument:
    """Test main validate_document() orchestrator."""

    def test_single_standard_compliant(self):
        """Test validation with single standard, all rules pass."""
        text = """
        Safety Procedure
        Required PPE: hard hat, safety glasses, steel-toed boots
        """
        standards = ["ISO45001"]
        context = {"activity": "general"}

        result = validate_document(text, standards, context, categories=["ppe"])

        assert result.ok
        assert len(result.violations) == 0
        assert result.stats["rules_checked"] >= 1
        assert result.stats["rules_passed"] >= 1

    def test_single_standard_violations(self):
        """Test validation with violations."""
        text = "Minimal safety procedure."
        standards = ["ISO45001"]
        context = {"activity": "excavation"}

        result = validate_document(text, standards, context, categories=["ppe"])

        assert not result.ok
        assert len(result.violations) > 0
        assert result.stats["violations_found"] > 0

    def test_multiple_standards(self):
        """Test validation across multiple standards."""
        text = """
        Complete Safety Procedure
        PPE: hard hat, safety glasses, steel-toed boots
        """
        standards = ["ISO45001", "OSHA"]
        context = {"activity": "general"}

        result = validate_document(text, standards, context)

        assert result.stats["rules_checked"] > 1

    def test_invalid_standard(self):
        """Test validation with invalid standard."""
        text = "Test"
        standards = ["INVALID_STANDARD"]
        context = {}

        result = validate_document(text, standards, context)

        assert len(result.warnings) > 0
        assert any("Unknown standard" in w["message"] for w in result.warnings)

    def test_severity_sorting(self):
        """Test that violations are sorted by severity."""
        text = "Incomplete procedure"
        standards = ["ISO45001", "OSHA"]
        context = {"activity": "confined_space"}

        result = validate_document(text, standards, context)

        if len(result.violations) > 1:
            # Check critical comes before major, major before minor
            severities = [v["severity"] for v in result.violations]
            severity_order = {"critical": 0, "major": 1, "minor": 2}
            severity_values = [severity_order[s] for s in severities]
            assert severity_values == sorted(severity_values)

    def test_category_filtering(self):
        """Test filtering by category."""
        text = "Test procedure"
        standards = ["ISO45001"]
        context = {"activity": "general"}

        result_all = validate_document(text, standards, context)
        result_filtered = validate_document(text, standards, context, categories=["ppe"])

        assert result_filtered.stats["rules_checked"] < result_all.stats["rules_checked"]

    def test_stats_calculation(self):
        """Test statistics are calculated correctly."""
        text = """
        Safety Procedure
        PPE: hard hat, safety glasses, steel-toed boots
        Hazard identification conducted
        Risk assessment completed
        """
        standards = ["ISO45001"]
        context = {"activity": "general"}

        result = validate_document(text, standards, context)

        assert result.stats["rules_checked"] == (
            result.stats["rules_passed"] + result.stats["violations_found"]
        )
        assert result.stats["violations_found"] == (
            result.stats["critical_violations"]
            + result.stats["major_violations"]
            + result.stats["minor_violations"]
        )


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================


class TestUtilityFunctions:
    """Test utility and helper functions."""

    def test_get_available_standards(self):
        """Test getting available standards."""
        standards = get_available_standards()

        assert isinstance(standards, list)
        assert "ISO45001" in standards
        assert "OSHA" in standards
        assert "LAW6331" in standards
        assert "WB_ESS" in standards

    def test_get_available_categories(self):
        """Test getting available categories."""
        categories = get_available_categories()

        assert isinstance(categories, list)
        assert "ppe" in categories
        assert "confined_space" in categories
        assert "risk_assessment" in categories

    def test_get_rules_summary(self):
        """Test getting rules summary."""
        summary = get_rules_summary()

        assert isinstance(summary, dict)
        assert "ISO45001" in summary
        assert "OSHA" in summary
        assert summary["ISO45001"] > 0
        assert summary["OSHA"] > 0
