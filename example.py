"""
Example script demonstrating how to use the Research Assistant programmatically.
"""

from workflow import ResearchWorkflow
from config import validate_config


def example_literature_review():
    """Example: Conduct a literature review."""
    print("Example 1: Conducting a Literature Review")
    print("=" * 60)
    
    workflow = ResearchWorkflow()
    
    results = workflow.conduct_literature_review(
        research_topic="Large Language Models in Education",
        research_questions=[
            "How are LLMs being used in educational settings?",
            "What are the benefits and challenges?"
        ],
        max_sources=5  # Reduced for example
    )
    
    print(f"\n✓ Literature review completed!")
    print(f"  Topic: {results['topic']}")
    print(f"  Sources found: {len(results['sources'])}")
    print(f"  Review length: {len(results['literature_review'])} characters")
    
    # Display first few sources
    if results['sources']:
        print("\n  Sample sources:")
        for source in results['sources'][:3]:
            print(f"    - {source['title']}")
            print(f"      URL: {source['url']}")
    
    return results


def example_research_report():
    """Example: Draft a research report."""
    print("\n\nExample 2: Drafting a Research Report")
    print("=" * 60)
    
    workflow = ResearchWorkflow()
    
    results = workflow.draft_research_report(
        research_topic="Ethical Considerations in AI Development",
        research_questions=[
            "What are the main ethical concerns?",
            "How can developers address these concerns?"
        ],
        additional_context="Focus on practical implementation strategies."
    )
    
    print(f"\n✓ Research report completed!")
    print(f"  Topic: {results['topic']}")
    print(f"  Report length: {len(results['report'])} characters")
    print(f"  Sections: {len(results['sections'])}")
    
    # Display section names
    if results['sections']:
        print("\n  Sections:")
        for section_name in list(results['sections'].keys())[:5]:
            print(f"    - {section_name}")
    
    return results


if __name__ == "__main__":
    # Validate configuration
    try:
        validate_config()
        print("✓ Configuration validated\n")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("Please ensure your API keys are set in the .env file.")
        exit(1)
    
    # Run examples (comment out if you want to run only one)
    print("\n" + "=" * 60)
    print("Research Assistant Examples")
    print("=" * 60 + "\n")
    
    # Note: These examples will make API calls and may take some time
    # Uncomment to run:
    
    # example_literature_review()
    # example_research_report()
    
    print("\n" + "=" * 60)
    print("Examples are commented out to avoid API calls.")
    print("Uncomment the function calls above to run them.")
    print("=" * 60)
