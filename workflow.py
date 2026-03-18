"""
Research workflow orchestrator for literature review and report drafting.
"""

from typing import Dict, List, Any, Optional
from agent import ResearchAgent
from academic_guidelines import AcademicGuidelines


class ResearchWorkflow:
    """
    Orchestrates research workflows for literature review and report generation.
    """
    
    def __init__(
        self,
        model: str = "openai/gpt-4o-mini",
        enable_reflexion: bool = True
    ):
        """
        Initialize the research workflow.
        
        Args:
            model: LLM model identifier
            enable_reflexion: Whether to enable reflexion
        """
        self.agent = ResearchAgent(model=model, enable_reflexion=enable_reflexion)
        self.guidelines = AcademicGuidelines()
    
    def conduct_literature_review(
        self,
        research_topic: str,
        research_questions: Optional[List[str]] = None,
        max_sources: int = 10
    ) -> Dict[str, Any]:
        """
        Conduct a structured literature review.
        
        Args:
            research_topic: The main research topic
            research_questions: Optional list of specific research questions
            max_sources: Maximum number of sources to review
        
        Returns:
            Dictionary with literature review results
        """
        # Build task description
        task_parts = [f"Conduct a comprehensive literature review on: {research_topic}"]
        
        if research_questions:
            task_parts.append(f"\nAddress the following research questions:")
            for i, q in enumerate(research_questions, 1):
                task_parts.append(f"{i}. {q}")
        
        task_parts.append(f"\nReview up to {max_sources} relevant sources.")
        task_parts.append("\nOrganize findings by themes and provide critical analysis.")
        
        task = "\n".join(task_parts)
        
        # Add academic guidelines to context
        context = self.guidelines.get_guidelines_prompt("literature_review")
        
        # Execute
        result = self.agent.execute(task, context)

        # Extract sources first (needed for synthesis citations)
        sources = self._extract_sources(result, max_sources)

        # Final LLM synthesis into a proper structured literature review
        literature_review = self._synthesize_literature_review(
            result, research_topic, research_questions or [], sources
        )

        # Structure the output
        return {
            "topic": research_topic,
            "research_questions": research_questions or [],
            "literature_review": literature_review,
            "sources": sources,
            "agent_results": result
        }
    
    def draft_research_report(
        self,
        research_topic: str,
        research_questions: List[str],
        literature_review_data: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Draft a structured research report.
        
        Args:
            research_topic: The main research topic
            research_questions: List of research questions to address
            literature_review_data: Optional pre-conducted literature review
            additional_context: Additional context or requirements
        
        Returns:
            Dictionary with research report
        """
        # Build task description
        task_parts = [
            f"Draft a comprehensive research report on: {research_topic}",
            f"\nResearch Questions:",
        ]
        
        for i, q in enumerate(research_questions, 1):
            task_parts.append(f"{i}. {q}")
        
        if literature_review_data:
            task_parts.append("\n\nLiterature Review Summary:")
            task_parts.append(literature_review_data.get('literature_review', '')[:1000])
        
        if additional_context:
            task_parts.append(f"\n\nAdditional Context: {additional_context}")
        
        task = "\n".join(task_parts)
        
        # Add academic guidelines
        context = self.guidelines.get_guidelines_prompt("research_report")
        
        # Execute
        result = self.agent.execute(task, context)

        # Extract sources for citations
        sources = self._extract_sources(result)

        # Final LLM synthesis into a proper structured report
        report = self._synthesize_report(result, research_topic, research_questions, sources)

        return {
            "topic": research_topic,
            "research_questions": research_questions,
            "report": report,
            "sections": self._extract_sections(report),
            "agent_results": result
        }
    
    def _synthesize_literature_review(
        self,
        agent_result: Dict[str, Any],
        research_topic: str,
        research_questions: List[str],
        sources: List[Dict[str, str]]
    ) -> str:
        """
        Use LLM to synthesize a proper, structured, non-repetitive literature review
        from raw agent step results.
        """
        results = agent_result.get("results", [])

        if not results:
            return "No results generated."

        # Collect raw content from all agent steps
        raw_parts = []
        for r in results:
            content = r.get("result", "")
            if content and len(content.strip()) > 50:
                raw_parts.append(content)

        if not raw_parts:
            return "No content was generated by the agent."

        raw_content = "\n\n---\n\n".join(raw_parts)
        # Limit to avoid token overflow
        if len(raw_content) > 8000:
            raw_content = raw_content[:8000] + "\n...[additional content truncated]"

        # Build source list for proper citations
        sources_ref = "\n".join([
            f"- {s['title']} | {s['url']}" for s in sources
        ]) if sources else "No sources available."

        # Research questions text
        rq_text = "\n".join([
            f"{i+1}. {q}" for i, q in enumerate(research_questions)
        ]) if research_questions else "General comprehensive review."

        synthesis_prompt = f"""You are an expert academic researcher. Using the raw research findings below, write a complete, well-structured, and non-repetitive literature review.

TOPIC: {research_topic}

RESEARCH QUESTIONS:
{rq_text}

VERIFIED SOURCES (use these for citations):
{sources_ref}

RAW RESEARCH FINDINGS (may contain duplicates and off-topic content):
{raw_content}

STRICT INSTRUCTIONS:
1. Structure the review with EXACTLY these sections using ## for main headers:
   ## Introduction
   ## Theoretical Frameworks and Background
   ## Key Themes and Findings
   ## Critical Analysis
   ## Gaps and Future Directions
   ## Conclusion

2. Quality rules:
   - Include ONLY content directly relevant to "{research_topic}"
   - Remove ALL duplicate paragraphs or repeated ideas
   - Replace every "Result 1", "Result 2", "Result 3" etc. with the actual source title from VERIFIED SOURCES
   - Use ### for subsection headers
   - Write in formal academic third-person language
   - Every claim must relate to the main topic

Write the complete literature review now:"""

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert academic researcher who writes clear, well-structured, "
                    "non-repetitive literature reviews. You strictly follow the topic and remove "
                    "all duplicate or irrelevant content."
                )
            },
            {"role": "user", "content": synthesis_prompt}
        ]

        try:
            return self.agent.llm.generate(messages, temperature=0.3, max_tokens=4000)
        except Exception:
            # Fallback to simple join if synthesis call fails
            return "\n\n".join(raw_parts)
    
    def _extract_sources(self, agent_result: Dict[str, Any], max_sources: int = None) -> List[Dict[str, str]]:
        """Extract source URLs from agent execution results."""
        sources = []
        results = agent_result.get("results", [])

        for result in results:
            actions = result.get("actions", [])
            for action in actions:
                if action.get("type") == "search":
                    search_results = action.get("results", [])
                    for sr in search_results:
                        sources.append({
                            "title": sr.get("title", ""),
                            "url": sr.get("url", ""),
                            "relevance_score": sr.get("score", 0.0)
                        })

        # Remove duplicates
        seen_urls = set()
        unique_sources = []
        for source in sources:
            if source["url"] not in seen_urls:
                seen_urls.add(source["url"])
                unique_sources.append(source)

        # Sort by relevance score (highest first) and enforce max_sources limit
        unique_sources.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
        if max_sources is not None:
            unique_sources = unique_sources[:max_sources]

        return unique_sources
    
    def _synthesize_report(
        self,
        agent_result: Dict[str, Any],
        research_topic: str,
        research_questions: List[str],
        sources: List[Dict[str, str]]
    ) -> str:
        """
        Use LLM to synthesize a proper, structured research report
        from raw agent step results.
        """
        results = agent_result.get("results", [])

        if not results:
            return "No report generated."

        # Collect raw content from all agent steps
        raw_parts = []
        for r in results:
            content = r.get("result", "")
            if content and len(content.strip()) > 50:
                raw_parts.append(content)

        if not raw_parts:
            return "No content was generated by the agent."

        raw_content = "\n\n---\n\n".join(raw_parts)
        if len(raw_content) > 8000:
            raw_content = raw_content[:8000] + "\n...[additional content truncated]"

        # Build source list for citations
        sources_ref = "\n".join([
            f"- {s['title']} | {s['url']}" for s in sources
        ]) if sources else "No sources available."

        rq_text = "\n".join([
            f"{i+1}. {q}" for i, q in enumerate(research_questions)
        ])

        synthesis_prompt = f"""You are an expert academic researcher. Using the raw research findings below, write a complete and well-structured research report.

TOPIC: {research_topic}

RESEARCH QUESTIONS:
{rq_text}

VERIFIED SOURCES (use these for citations):
{sources_ref}

RAW RESEARCH FINDINGS (may contain duplicates and off-topic content):
{raw_content}

STRICT INSTRUCTIONS:
1. Structure the report with EXACTLY these sections using ## for main headers:
   # {research_topic}
   ## Abstract
   ## Introduction
   ## Literature Review
   ## Methodology
   ## Results and Findings
   ## Discussion
   ## Conclusion
   ## References

2. Quality rules:
   - Include ONLY content relevant to "{research_topic}"
   - Remove ALL duplicate or repeated content
   - Replace every "Result 1", "Result 2" etc. with proper in-text citations using source titles
   - Use ### for subsections
   - Write in formal academic language throughout
   - In the References section, list all used sources with their URLs

Write the complete research report now:"""

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert academic researcher who writes clear, well-structured, "
                    "evidence-based research reports. You remove all duplicates and irrelevant content."
                )
            },
            {"role": "user", "content": synthesis_prompt}
        ]

        try:
            return self.agent.llm.generate(messages, temperature=0.3, max_tokens=4000)
        except Exception:
            # Fallback to simple join
            topic = research_topic
            return f"# {topic}\n\n" + "\n\n".join(raw_parts)
    
    def _extract_sections(self, report: str) -> Dict[str, str]:
        """Extract sections from a report."""
        sections = {}
        current_section = "Introduction"
        current_content = []
        
        lines = report.split("\n")
        for line in lines:
            # Check if line is a section header
            if line.startswith("#"):
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                
                # Start new section
                current_section = line.lstrip("#").strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = "\n".join(current_content)
        
        return sections
