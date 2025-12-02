"""
API integration tests for /validate endpoint (CAG compliance validation).

Tests the guardrails router with various request scenarios.
"""

from fastapi.testclient import TestClient

from src.ohs.api.main import app

client = TestClient(app)


class TestValidateEndpoint:
    """Test /validate POST endpoint."""

    def test_validate_compliant_document(self):
        """Test validation of compliant document."""
        payload = {
            "text": """
            Safety Procedure
            Required PPE: hard hat, safety glasses, steel-toed boots
            """,
            "standards": ["ISO45001"],
            "context": {"activity": "general"},
            "categories": ["ppe"],
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["violations"]) == 0
        assert data["stats"]["rules_checked"] >= 1

    def test_validate_non_compliant_document(self):
        """Test validation of non-compliant document."""
        payload = {
            "text": "Minimal safety procedure.",
            "standards": ["ISO45001"],
            "context": {"activity": "excavation"},
            "categories": ["ppe"],
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert len(data["violations"]) > 0
        assert data["stats"]["violations_found"] > 0

        # Check violation structure
        violation = data["violations"][0]
        assert "rule_id" in violation
        assert "standard" in violation
        assert "severity" in violation
        assert "issues" in violation
        assert isinstance(violation["issues"], list)

    def test_validate_multiple_standards(self):
        """Test validation across multiple standards."""
        payload = {
            "text": """
            Excavation Safety Procedure
            PPE: hard hat, safety glasses, steel-toed boots, high-visibility vest
            Soil classification: Type B
            Protective system: Trench box
            Competent person: John Doe
            """,
            "standards": ["ISO45001", "OSHA"],
            "context": {"activity": "excavation"},
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["rules_checked"] > 1

    def test_validate_confined_space_critical_violations(self):
        """Test confined space with critical violations."""
        payload = {
            "text": "Enter confined space with caution.",
            "standards": ["OSHA"],
            "context": {"activity": "confined_space"},
            "categories": ["confined_space"],
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert not data["ok"]
        assert data["stats"]["critical_violations"] > 0

        # Check severity sorting (critical first)
        if len(data["violations"]) > 1:
            first_severity = data["violations"][0]["severity"]
            assert first_severity == "critical"

    def test_validate_invalid_standard(self):
        """Test validation with invalid standard name."""
        payload = {
            "text": "Test procedure",
            "standards": ["INVALID_STANDARD"],
            "context": {},
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 400
        assert "Invalid standards" in response.json()["detail"]

    def test_validate_empty_text(self):
        """Test validation with empty text."""
        payload = {"text": "", "standards": ["ISO45001"], "context": {}}

        response = client.post("/validate", json=payload)

        # Should fail validation (min_length=1)
        assert response.status_code == 422

    def test_validate_no_standards(self):
        """Test validation with no standards specified."""
        payload = {"text": "Test procedure", "standards": [], "context": {}}

        response = client.post("/validate", json=payload)

        # Should fail validation (min_items=1)
        assert response.status_code == 422

    def test_validate_with_context(self):
        """Test validation with rich context metadata."""
        payload = {
            "text": """
            Excavation procedure requires:
            - Hard hat
            - Safety glasses
            - Steel-toed boots
            - High-visibility vest
            """,
            "standards": ["ISO45001"],
            "context": {
                "activity": "excavation",
                "location": "construction_site",
                "project_type": "infrastructure",
            },
            "categories": ["ppe"],  # Only check PPE, not other requirements
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()
        # With complete PPE for excavation, should pass
        assert data["ok"] is True

    def test_validate_category_filtering(self):
        """Test category filtering works correctly."""
        payload = {
            "text": "Test procedure",
            "standards": ["ISO45001"],
            "context": {},
            "categories": ["ppe"],
        }

        response_filtered = client.post("/validate", json=payload)
        assert response_filtered.status_code == 200

        payload["categories"] = None
        response_all = client.post("/validate", json=payload)
        assert response_all.status_code == 200

        # Filtered should check fewer rules
        assert (
            response_filtered.json()["stats"]["rules_checked"]
            <= response_all.json()["stats"]["rules_checked"]
        )

    def test_validate_wb_ess(self):
        """Test WB/IFC ESS standard validation."""
        payload = {
            "text": """
            Labor Management Plan
            Non-discrimination policy in place
            Equal opportunity for all workers
            Grievance mechanism established
            Working hours: 8 hours/day, 48 hours/week max
            Child labor prohibited: minimum age 18 years
            """,
            "standards": ["WB_ESS"],
            "context": {},
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should have some violations or be compliant
        assert "ok" in data

    def test_validate_turkish_law_6331(self):
        """Test Turkish Law 6331 validation."""
        payload = {
            "text": """
            OHS Program
            Workplace physician: Dr. Mehmet Yılmaz
            OHS specialist (İş Güvenliği Uzmanı): Ahmet Demir
            OHS training: 16 hours minimum for new employees
            Training documentation maintained
            """,
            "standards": ["LAW6331"],
            "context": {},
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "ok" in data

    def test_validate_remediation_provided(self):
        """Test that violations include remediation guidance."""
        payload = {
            "text": "Incomplete safety procedure",
            "standards": ["ISO45001"],
            "context": {"activity": "excavation"},
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()

        if len(data["violations"]) > 0:
            violation = data["violations"][0]
            # Check that remediation is provided
            assert "remediation" in violation


class TestStandardsEndpoint:
    """Test /standards GET endpoint."""

    def test_list_standards(self):
        """Test getting list of available standards."""
        response = client.get("/validate/standards")

        assert response.status_code == 200
        data = response.json()
        assert "standards" in data
        assert "rules_by_standard" in data

        # Check expected standards
        assert "ISO45001" in data["standards"]
        assert "OSHA" in data["standards"]
        assert "LAW6331" in data["standards"]
        assert "WB_ESS" in data["standards"]

        # Check rule counts
        assert data["rules_by_standard"]["ISO45001"] > 0
        assert data["rules_by_standard"]["OSHA"] > 0


class TestCategoriesEndpoint:
    """Test /categories GET endpoint."""

    def test_list_categories(self):
        """Test getting list of available categories."""
        response = client.get("/validate/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data

        # Check expected categories
        assert "ppe" in data["categories"]
        assert "confined_space" in data["categories"]
        assert "working_at_height" in data["categories"]
        assert "risk_assessment" in data["categories"]


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_infrastructure_project_validation(self):
        """Test complete infrastructure project safety plan."""
        payload = {
            "text": """
            Infrastructure Project Safety Plan

            PPE Requirements:
            - Hard hat (ANSI Z89.1)
            - Safety glasses (ANSI Z87.1)
            - Steel-toed boots (ASTM F2413)
            - High-visibility vest (ANSI/ISEA 107)

            Hazard Identification:
            Comprehensive job hazard analysis completed for all activities.

            Risk Assessment:
            5x5 risk matrix applied with severity and likelihood scoring.

            Control Measures:
            Following hierarchy of controls:
            1. Elimination: Remove hazards where possible
            2. Substitution: Replace with less hazardous alternatives
            3. Engineering controls: Guards, ventilation
            4. Administrative controls: Procedures, training
            5. PPE: As last line of defense

            Emergency Preparedness:
            Emergency contacts: Site manager 555-0100, First aid 555-0101
            Evacuation procedures documented
            First aid kits at main office and field office
            Emergency assembly point: North parking lot
            Quarterly emergency drills conducted

            Competent Person:
            John Doe, certified competent person for all activities

            Training:
            - New employee OHS training: 16 hours
            - Activity-specific training provided
            - Training records maintained
            """,
            "standards": ["ISO45001", "OSHA", "LAW6331", "WB_ESS"],
            "context": {
                "activity": "general",
                "project_type": "infrastructure",
                "location": "turkey",
            },
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Should have reasonable pass rate for comprehensive plan
        # Not expecting 100% due to some missing standard-specific requirements
        if data["stats"]["rules_checked"] > 0:
            pass_rate = data["stats"]["rules_passed"] / data["stats"]["rules_checked"]
            # At least 20% pass rate shows some compliance
            assert pass_rate > 0.2
            # Should have checked multiple rules
            assert data["stats"]["rules_checked"] > 5

    def test_excavation_project_validation(self):
        """Test excavation-specific safety plan."""
        payload = {
            "text": """
            Excavation Safety Plan

            Soil Classification: Type B soil
            Protective System: Trench box rated for 12 feet depth
            Competent Person: John Doe, certified
            Atmospheric Testing: For excavations 4+ feet deep
            Access/Egress: Ladder every 25 feet for 5+ feet depth

            PPE: Hard hat, safety glasses, steel-toed boots, high-visibility vest

            Emergency Response:
            Emergency contacts available
            Evacuation procedures established
            First aid kit on site
            Assembly point designated
            """,
            "standards": ["OSHA"],
            "context": {"activity": "excavation"},
            "categories": ["excavation", "ppe", "emergency_response"],
        }

        response = client.post("/validate", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Should have good compliance for complete plan
        assert data["stats"]["critical_violations"] == 0
