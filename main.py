#!/usr/bin/env python3
"""
AI4OHS Hybrid - Main Entry Point
AI for Health and Safety Expert Assistant
"""

import sys
import argparse
from typing import Optional

from src.core.assistant import AI4OHSAssistant, QueryContext
from src.api.server import start_server
from src.utils.config import get_config


def interactive_mode():
    """Run assistant in interactive CLI mode"""
    assistant = AI4OHSAssistant()
    
    print("=" * 70)
    print("AI4OHS Hybrid Assistant - Interactive Mode")
    print("=" * 70)
    print("\nSupported Standards:")
    print("  • Turkish OHS Law (Law No. 6331)")
    print("  • OSHA Standards")
    print("  • ISO 45001:2018")
    print("  • World Bank EHS Guidelines")
    print("  • IFC Environmental and Social Standards")
    print("\nType 'exit' or 'quit' to end the session")
    print("Type 'help' for assistance")
    print("=" * 70)
    print()
    
    while True:
        try:
            query = input("\n🔍 Your OHS Question: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("\nThank you for using AI4OHS Hybrid Assistant!")
                break
            
            if query.lower() == 'help':
                print("\n📚 Help:")
                print("  - Ask questions about OHS regulations and standards")
                print("  - Example: 'What are risk assessment requirements?'")
                print("  - Example: 'How does Turkish law define workplace safety?'")
                print("  - Example: 'What training is required under ISO 45001?'")
                print("  - Type 'regulations' to see all available standards")
                continue
            
            if query.lower() == 'regulations':
                print("\n📋 Available Regulations:")
                for reg_type in assistant.supported_standards:
                    reg = assistant.regulations.get_regulation(reg_type)
                    if reg:
                        print(f"  • {reg.name} ({reg.code})")
                continue
            
            # Process the query
            context = QueryContext(query=query)
            response = assistant.process_query(context)
            
            # Display response
            print("\n" + "=" * 70)
            print("📝 Answer:")
            print("-" * 70)
            print(response.answer)
            
            if response.recommendations:
                print("\n💡 Recommendations:")
                print("-" * 70)
                for i, rec in enumerate(response.recommendations, 1):
                    print(f"  {i}. {rec}")
            
            if response.references:
                print("\n📚 References:")
                print("-" * 70)
                for ref in response.references:
                    print(f"  • {ref}")
            
            print("=" * 70)
            
        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def query_mode(query: str, focus: Optional[str] = None):
    """Run a single query"""
    assistant = AI4OHSAssistant()
    
    regulation_focus = None
    if focus:
        regulation_focus = [f.strip() for f in focus.split(',')]
    
    context = QueryContext(
        query=query,
        regulation_focus=regulation_focus
    )
    
    response = assistant.process_query(context)
    
    print("\n" + "=" * 70)
    print("AI4OHS Hybrid Assistant Response")
    print("=" * 70)
    print("\n📝 Answer:")
    print(response.answer)
    
    if response.recommendations:
        print("\n💡 Recommendations:")
        for i, rec in enumerate(response.recommendations, 1):
            print(f"  {i}. {rec}")
    
    if response.references:
        print("\n📚 References:")
        for ref in response.references:
            print(f"  • {ref}")
    
    print("=" * 70)


def regulation_info_mode(regulation_type: str):
    """Display information about a specific regulation"""
    assistant = AI4OHSAssistant()
    summary = assistant.get_regulation_summary(regulation_type)
    
    if not summary:
        print(f"❌ Error: Regulation '{regulation_type}' not found")
        print(f"Available regulations: {', '.join(assistant.supported_standards)}")
        return
    
    print("\n" + "=" * 70)
    print(f"{summary['name']}")
    print("=" * 70)
    print(f"\n📋 Code: {summary['code']}")
    print(f"\n📖 Description:")
    print(f"  {summary['description']}")
    
    print(f"\n✅ Key Requirements:")
    for i, req in enumerate(summary['key_requirements'], 1):
        print(f"  {i}. {req}")
    
    print(f"\n🏢 Applicable Sectors:")
    for sector in summary['applicable_sectors']:
        print(f"  • {sector}")
    
    print("=" * 70)


def api_mode():
    """Start API server"""
    config = get_config()
    print(f"\n🚀 Starting AI4OHS API Server on {config.api_host}:{config.api_port}")
    print(f"📚 API Documentation: http://{config.api_host}:{config.api_port}/docs")
    start_server(host=config.api_host, port=config.api_port)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI4OHS Hybrid - AI for Health and Safety Expert Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python main.py

  # Single query
  python main.py --query "What are risk assessment requirements?"

  # Query with regulation focus
  python main.py --query "Training requirements" --focus "turkish_law,iso45001"

  # Get regulation information
  python main.py --info turkish_law

  # Start API server
  python main.py --api

Supported Regulations:
  • turkish_law - Turkish OHS Law (Law No. 6331)
  • osha - OSHA Standards
  • iso45001 - ISO 45001:2018
  • world_bank - World Bank EHS Guidelines
  • ifc_ess - IFC Environmental and Social Standards
        """
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Ask a single OHS-related question'
    )
    
    parser.add_argument(
        '--focus', '-f',
        type=str,
        help='Focus on specific regulations (comma-separated: turkish_law,osha,iso45001,world_bank,ifc_ess)'
    )
    
    parser.add_argument(
        '--info', '-i',
        type=str,
        help='Get detailed information about a specific regulation'
    )
    
    parser.add_argument(
        '--api', '-a',
        action='store_true',
        help='Start the API server'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    if args.api:
        api_mode()
    elif args.info:
        regulation_info_mode(args.info)
    elif args.query:
        query_mode(args.query, args.focus)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
