#!/usr/bin/env python3
"""
Example Python client for AI4OHS Hybrid Assistant
Demonstrates how to use the assistant programmatically
"""

import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.assistant import AI4OHSAssistant, QueryContext


def example_basic_query():
    """Example: Basic query without specific focus"""
    print("=" * 70)
    print("Example 1: Basic Query")
    print("=" * 70)
    
    assistant = AI4OHSAssistant()
    context = QueryContext(query="What are the main requirements for risk assessment?")
    response = assistant.process_query(context)
    
    print("\nQuery:", context.query)
    print("\nAnswer:", response.answer)
    print("\nRecommendations:")
    for rec in response.recommendations:
        print(f"  - {rec}")
    print()


def example_focused_query():
    """Example: Query focused on specific regulations"""
    print("=" * 70)
    print("Example 2: Focused Query (Turkish Law)")
    print("=" * 70)
    
    assistant = AI4OHSAssistant()
    context = QueryContext(
        query="What training is required for employees?",
        regulation_focus=["turkish_law"],
        country="Turkey"
    )
    response = assistant.process_query(context)
    
    print("\nQuery:", context.query)
    print("Focus:", context.regulation_focus)
    print("\nAnswer:", response.answer)
    print("\nRelevant Regulations:")
    for reg in response.relevant_regulations:
        print(f"  - {reg}")
    print()


def example_regulation_details():
    """Example: Get detailed information about a regulation"""
    print("=" * 70)
    print("Example 3: Regulation Details")
    print("=" * 70)
    
    assistant = AI4OHSAssistant()
    
    # Get Turkish Law details
    summary = assistant.get_regulation_summary("turkish_law")
    
    print(f"\nRegulation: {summary['name']}")
    print(f"Code: {summary['code']}")
    print(f"\nDescription:")
    print(f"  {summary['description']}")
    print(f"\nKey Requirements:")
    for i, req in enumerate(summary['key_requirements'], 1):
        print(f"  {i}. {req}")
    print()


def example_multiple_regulations():
    """Example: Query involving multiple regulations"""
    print("=" * 70)
    print("Example 4: Multi-Regulation Query")
    print("=" * 70)
    
    assistant = AI4OHSAssistant()
    context = QueryContext(
        query="What are PPE requirements?",
        regulation_focus=["osha", "iso45001"]
    )
    response = assistant.process_query(context)
    
    print("\nQuery:", context.query)
    print("Focus:", context.regulation_focus)
    print("\nAnswer:", response.answer)
    print("\nReferences:")
    for ref in response.references:
        print(f"  - {ref}")
    print()


def example_regulation_comparison():
    """Example: Compare different regulations"""
    print("=" * 70)
    print("Example 5: Regulation Comparison")
    print("=" * 70)
    
    assistant = AI4OHSAssistant()
    
    regulations_to_compare = ["turkish_law", "osha", "iso45001"]
    comparison = assistant.compare_regulations(regulations_to_compare)
    
    print("\nComparing:", ", ".join(regulations_to_compare))
    print("\nComparison Results:")
    for reg_type, details in comparison.items():
        print(f"\n  {details['name']}:")
        print(f"    - Requirements: {details['key_requirements_count']}")
        print(f"    - Sectors: {', '.join(details['sectors'])}")
    print()


def example_search_requirements():
    """Example: Search for specific requirements across all regulations"""
    print("=" * 70)
    print("Example 6: Search Requirements")
    print("=" * 70)
    
    assistant = AI4OHSAssistant()
    
    keyword = "training"
    results = assistant.regulations.search_requirements(keyword)
    
    print(f"\nSearching for requirements containing: '{keyword}'")
    print("\nResults:")
    for regulation_name, requirements in results:
        print(f"\n  {regulation_name}:")
        for req in requirements:
            print(f"    - {req}")
    print()


def example_sector_specific():
    """Example: Industry sector specific query"""
    print("=" * 70)
    print("Example 7: Sector-Specific Query")
    print("=" * 70)
    
    assistant = AI4OHSAssistant()
    context = QueryContext(
        query="What are the main safety hazards in construction?",
        industry_sector="construction",
        country="Turkey"
    )
    response = assistant.process_query(context)
    
    print("\nQuery:", context.query)
    print("Sector:", context.industry_sector)
    print("Country:", context.country)
    print("\nAnswer:", response.answer)
    print("\nRecommendations:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"  {i}. {rec}")
    print()


def example_all_regulations():
    """Example: List all available regulations"""
    print("=" * 70)
    print("Example 8: All Available Regulations")
    print("=" * 70)
    
    assistant = AI4OHSAssistant()
    all_regs = assistant.regulations.get_all_regulations()
    
    print("\nAvailable Regulations:")
    for reg_type, reg in all_regs.items():
        print(f"\n  {reg.name}")
        print(f"    Code: {reg.code}")
        print(f"    Type: {reg_type}")
        print(f"    Sectors: {', '.join(reg.applicable_sectors)}")
    print()


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("AI4OHS Hybrid Assistant - Python Client Examples")
    print("=" * 70)
    print()
    
    try:
        # Run all examples
        example_basic_query()
        example_focused_query()
        example_regulation_details()
        example_multiple_regulations()
        example_regulation_comparison()
        example_search_requirements()
        example_sector_specific()
        example_all_regulations()
        
        print("=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
