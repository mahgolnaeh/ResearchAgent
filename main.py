"""
Main entry point for the Research Assistant.
Provides a command-line interface for conducting research tasks.
"""

import argparse
import json
from pathlib import Path
from config import validate_config
from workflow import ResearchWorkflow


def save_results(results: dict, output_file: str):
    """Save results to a file."""
    output_path = Path(output_file)
    
    if output_path.suffix == '.json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    else:
        # Save as text/markdown
        with open(output_path, 'w', encoding='utf-8') as f:
            if 'literature_review' in results:
                f.write(f"# Literature Review: {results.get('topic', 'Unknown')}\n\n")
                f.write(results.get('literature_review', ''))
                f.write("\n\n## Sources\n\n")
                for source in results.get('sources', []):
                    f.write(f"- [{source.get('title', 'N/A')}]({source.get('url', 'N/A')})\n")
            elif 'report' in results:
                f.write(results.get('report', ''))
    
    print(f"✓ Results saved to: {output_file}")


def conduct_literature_review(args):
    """Conduct a literature review."""
    print("=" * 60)
    print("Conducting Literature Review")
    print("=" * 60)
    print(f"Topic: {args.topic}")
    if args.questions:
        print(f"Research Questions: {len(args.questions)}")
    print()
    
    workflow = ResearchWorkflow(
        model=args.model,
        enable_reflexion=not args.no_reflexion
    )
    
    research_questions = args.questions if args.questions else None
    
    results = workflow.conduct_literature_review(
        research_topic=args.topic,
        research_questions=research_questions,
        max_sources=args.max_sources
    )
    
    # Display summary
    print("\n" + "=" * 60)
    print("Literature Review Complete")
    print("=" * 60)
    print(f"Sources found: {len(results.get('sources', []))}")
    print(f"Review length: {len(results.get('literature_review', ''))} characters")
    
    if args.reflection:
        reflection = results.get('agent_results', {}).get('reflection')
        if reflection:
            print(f"\nReflection Confidence: {reflection.confidence:.2f}")
            if reflection.observations:
                print("\nObservations:")
                for obs in reflection.observations[:3]:
                    print(f"  - {obs[:100]}...")
    
    # Save results
    if args.output:
        save_results(results, args.output)
    else:
        # Default output
        default_output = f"literature_review_{args.topic.replace(' ', '_')[:30]}.md"
        save_results(results, default_output)
    
    return results


def draft_report(args):
    """Draft a research report."""
    print("=" * 60)
    print("Drafting Research Report")
    print("=" * 60)
    print(f"Topic: {args.topic}")
    print(f"Research Questions: {len(args.questions)}")
    for i, q in enumerate(args.questions, 1):
        print(f"  {i}. {q}")
    print()
    
    workflow = ResearchWorkflow(
        model=args.model,
        enable_reflexion=not args.no_reflexion
    )
    
    # Load literature review if provided
    literature_review_data = None
    if args.literature_review:
        review_path = Path(args.literature_review)
        if review_path.exists():
            with open(review_path, 'r', encoding='utf-8') as f:
                if review_path.suffix == '.json':
                    literature_review_data = json.load(f)
                else:
                    literature_review_data = {"literature_review": f.read()}
            print(f"✓ Loaded literature review from: {args.literature_review}")
    
    results = workflow.draft_research_report(
        research_topic=args.topic,
        research_questions=args.questions,
        literature_review_data=literature_review_data,
        additional_context=args.context
    )
    
    # Display summary
    print("\n" + "=" * 60)
    print("Research Report Complete")
    print("=" * 60)
    print(f"Report length: {len(results.get('report', ''))} characters")
    print(f"Sections: {len(results.get('sections', {}))}")
    
    if args.reflection:
        reflection = results.get('agent_results', {}).get('reflection')
        if reflection:
            print(f"\nReflection Confidence: {reflection.confidence:.2f}")
    
    # Save results
    if args.output:
        save_results(results, args.output)
    else:
        # Default output
        default_output = f"research_report_{args.topic.replace(' ', '_')[:30]}.md"
        save_results(results, default_output)
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Research Assistant - Conduct literature reviews and draft research reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Conduct a literature review
  python main.py review --topic "Machine Learning in Healthcare" --questions "What are the main applications?" "What are the challenges?"

  # Draft a research report
  python main.py report --topic "AI Ethics" --questions "What are ethical concerns?" "How can they be addressed?" --output report.md

  # Use a different model
  python main.py review --topic "Climate Change" --model "anthropic/claude-3.5-sonnet"
        """
    )
    
    # Global arguments
    parser.add_argument(
        '--model',
        default='openai/gpt-4o-mini',
        help='LLM model identifier for OpenRouter (default: openai/gpt-4o-mini)'
    )
    parser.add_argument(
        '--no-reflexion',
        action='store_true',
        help='Disable reflexion (faster but less self-correcting)'
    )
    parser.add_argument(
        '--reflection',
        action='store_true',
        help='Show reflection details in output'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path (supports .json, .md, .txt)'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Literature review command
    review_parser = subparsers.add_parser('review', help='Conduct a literature review')
    review_parser.add_argument('--topic', '-t', required=True, help='Research topic')
    review_parser.add_argument(
        '--questions', '-q',
        nargs='+',
        help='Research questions to address'
    )
    review_parser.add_argument(
        '--max-sources', '-s',
        type=int,
        default=10,
        help='Maximum number of sources to review (default: 10)'
    )
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Draft a research report')
    report_parser.add_argument('--topic', '-t', required=True, help='Research topic')
    report_parser.add_argument(
        '--questions', '-q',
        nargs='+',
        required=True,
        help='Research questions to address'
    )
    report_parser.add_argument(
        '--literature-review', '-l',
        help='Path to existing literature review file (JSON or Markdown)'
    )
    report_parser.add_argument(
        '--context', '-c',
        help='Additional context or requirements'
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    # Execute command
    if args.command == 'review':
        conduct_literature_review(args)
    elif args.command == 'report':
        draft_report(args)
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
