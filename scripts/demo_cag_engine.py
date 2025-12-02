"""
CAG Compliance Engine Demo

Demonstrates the production-ready compliance validation system.
"""

from src.utils.compliance import (
    get_available_standards,
    get_rules_summary,
    validate_document,
)


def demo_compliant_document():
    """Demo: Compliant excavation safety plan."""
    print("=" * 70)
    print("DEMO 1: COMPLIANT EXCAVATION SAFETY PLAN")
    print("=" * 70)

    text = """
    Excavation Safety Plan

    PPE Requirements:
    - Hard hat (ANSI Z89.1)
    - Safety glasses (ANSI Z87.1)
    - Steel-toed boots (ASTM F2413)
    - High-visibility vest (ANSI/ISEA 107)

    Soil Classification: Type B soil (cohesive)
    Protective System: Trench box rated for 12 feet depth
    Competent Person: John Doe, certified
    Atmospheric Testing: Required for excavations 4+ feet deep
    Access and Egress: Ladder provided every 25 feet

    Hazard Identification: Completed via job hazard analysis
    Risk Assessment: 5x5 risk matrix applied
    Control Measures: Following hierarchy of controls
    Emergency Response: Emergency contacts, evacuation procedures, first aid kit
    """

    result = validate_document(
        text=text,
        standards=["ISO45001", "OSHA"],
        context={"activity": "excavation"},
    )

    print(f"\nCompliance Status: {'✅ COMPLIANT' if result.ok else '❌ NON-COMPLIANT'}")
    print(f"Rules Checked: {result.stats['rules_checked']}")
    print(f"Rules Passed: {result.stats['rules_passed']}")
    print(f"Violations: {result.stats['violations_found']}")
    print(f"  - Critical: {result.stats['critical_violations']}")
    print(f"  - Major: {result.stats['major_violations']}")
    print(f"  - Minor: {result.stats['minor_violations']}")


def demo_non_compliant_document():
    """Demo: Non-compliant confined space entry."""
    print("\n" + "=" * 70)
    print("DEMO 2: NON-COMPLIANT CONFINED SPACE ENTRY")
    print("=" * 70)

    text = """
    Confined Space Entry Procedure

    Workers will enter the tank for inspection.
    Entry supervisor assigned.
    """

    result = validate_document(
        text=text,
        standards=["OSHA"],
        context={"activity": "confined_space"},
        categories=["confined_space"],
    )

    print(f"\nCompliance Status: {'✅ COMPLIANT' if result.ok else '❌ NON-COMPLIANT'}")
    print(f"Rules Checked: {result.stats['rules_checked']}")
    print(f"Violations Found: {result.stats['violations_found']}")

    print("\n--- VIOLATIONS ---")
    for i, v in enumerate(result.violations[:3], 1):  # Show first 3
        print(f"\n{i}. Rule: {v['rule_id']}")
        print(f"   Standard: {v['standard']}")
        print(f"   Severity: {v['severity'].upper()}")
        print(f"   Requirement: {v['requirement']}")
        print("   Issues:")
        for issue in v["issues"][:2]:  # Show first 2 issues
            print(f"     - {issue}")
        if v.get("remediation"):
            print(f"   Remediation: {v['remediation'][:100]}...")


def demo_multi_standard_validation():
    """Demo: Multi-standard validation (ISO + OSHA + LAW6331 + WB_ESS)."""
    print("\n" + "=" * 70)
    print("DEMO 3: MULTI-STANDARD INFRASTRUCTURE PROJECT VALIDATION")
    print("=" * 70)

    text = """
    Infrastructure Project Safety Plan

    PPE: Hard hat, safety glasses, steel-toed boots, high-visibility vest

    Hazard Identification: Comprehensive job hazard analysis
    Risk Assessment: 5x5 risk matrix with severity and likelihood
    Control Measures: Hierarchy of controls applied

    Emergency Response:
    - Emergency contacts: Site manager 555-0100
    - Evacuation procedures documented
    - First aid kits available
    - Emergency assembly point: North parking lot

    Workplace Physician: Dr. Mehmet Yılmaz
    OHS Specialist: Ahmet Demir
    OHS Training: 16 hours minimum for new employees

    Non-discrimination policy in place
    Equal opportunity for all workers
    Grievance mechanism established
    Working hours: 8 hours/day, 48 hours/week max
    Child labor prohibited: minimum age 18 years
    """

    result = validate_document(
        text=text,
        standards=["ISO45001", "OSHA", "LAW6331", "WB_ESS"],
        context={"activity": "general", "location": "turkey"},
    )

    print(f"\nCompliance Status: {'✅ COMPLIANT' if result.ok else '❌ NON-COMPLIANT'}")
    print(f"Rules Checked: {result.stats['rules_checked']}")
    print(f"Rules Passed: {result.stats['rules_passed']}")
    print(f"Pass Rate: {result.stats['rules_passed'] / result.stats['rules_checked'] * 100:.1f}%")

    if result.violations:
        print(f"\nRemaining Violations: {len(result.violations)}")
        print("Standards need attention:")
        violation_standards = set(v["standard"] for v in result.violations)
        for std in violation_standards:
            count = sum(1 for v in result.violations if v["standard"] == std)
            print(f"  - {std}: {count} violations")


def demo_system_info():
    """Demo: System information and capabilities."""
    print("\n" + "=" * 70)
    print("CAG COMPLIANCE ENGINE - SYSTEM INFORMATION")
    print("=" * 70)

    print("\nSupported Standards:")
    for std in get_available_standards():
        print(f"  - {std}")

    print("\nRegistered Rules by Standard:")
    summary = get_rules_summary()
    total_rules = 0
    for std, count in summary.items():
        print(f"  - {std}: {count} rules")
        total_rules += count

    print(f"\nTotal Rules: {total_rules}")
    print("Validation Mode: 100% Offline (No LLM dependencies)")
    print("Technologies: Regex, keyword matching, structural analysis")


if __name__ == "__main__":
    print("\n🔒 AI4OHS-HYBRID CAG COMPLIANCE ENGINE DEMO")
    print("Compliance-Augmented Generation for OHS Standards")
    print("Version: 1.0.0 | Mode: Offline | Engine: Rule-based\n")

    demo_system_info()
    demo_compliant_document()
    demo_non_compliant_document()
    demo_multi_standard_validation()

    print("\n" + "=" * 70)
    print("✅ CAG ENGINE DEMO COMPLETE")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. Start API: uvicorn src.ohs.api.main:app --reload")
    print("2. Test endpoint: POST http://localhost:8000/validate")
    print("3. View docs: http://localhost:8000/docs")
    print()
