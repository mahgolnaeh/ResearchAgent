"""
Academic writing guidelines and standards for research reports.
"""

from typing import Dict, List, Any


class AcademicGuidelines:
    """Academic writing guidelines and standards."""
    
    STRUCTURE = {
        "literature_review": {
            "sections": [
                "Introduction",
                "Methodology/Search Strategy",
                "Thematic Organization",
                "Critical Analysis",
                "Gaps and Future Directions",
                "Conclusion"
            ],
            "requirements": [
                "Use formal, objective language",
                "Cite sources appropriately",
                "Organize by themes or chronology",
                "Include critical analysis, not just summaries",
                "Identify gaps in existing research"
            ]
        },
        "research_report": {
            "sections": [
                "Abstract",
                "Introduction",
                "Literature Review",
                "Methodology",
                "Results/Findings",
                "Discussion",
                "Conclusion",
                "References"
            ],
            "requirements": [
                "Clear research question or objective",
                "Rigorous methodology",
                "Evidence-based conclusions",
                "Proper citation format",
                "Critical analysis and synthesis"
            ]
        }
    }
    
    WRITING_STANDARDS = {
        "tone": "Formal, objective, and scholarly",
        "voice": "Third person preferred (avoid 'I', 'we', 'you')",
        "evidence": "All claims must be supported by evidence or citations",
        "clarity": "Clear, concise, and precise language",
        "structure": "Logical flow with clear transitions",
        "citations": "Consistent citation style (APA, MLA, or specified)",
        "objectivity": "Avoid bias and present balanced perspectives"
    }
    
    @staticmethod
    def get_structure(report_type: str) -> Dict[str, Any]:
        """
        Get the structure for a specific report type.
        
        Args:
            report_type: Type of report ("literature_review" or "research_report")
        
        Returns:
            Dictionary with sections and requirements
        """
        return AcademicGuidelines.STRUCTURE.get(
            report_type,
            AcademicGuidelines.STRUCTURE["research_report"]
        )
    
    @staticmethod
    def get_guidelines_prompt(report_type: str = "research_report") -> str:
        """
        Get a formatted prompt with academic writing guidelines.
        
        Args:
            report_type: Type of report to generate guidelines for
        
        Returns:
            Formatted string with guidelines
        """
        structure = AcademicGuidelines.get_structure(report_type)
        standards = AcademicGuidelines.WRITING_STANDARDS
        
        prompt = f"""ACADEMIC WRITING GUIDELINES

Report Type: {report_type.replace('_', ' ').title()}

Required Sections:
{chr(10).join(f"- {section}" for section in structure['sections'])}

Writing Requirements:
{chr(10).join(f"- {req}" for req in structure['requirements'])}

Writing Standards:
- Tone: {standards['tone']}
- Voice: {standards['voice']}
- Evidence: {standards['evidence']}
- Clarity: {standards['clarity']}
- Structure: {standards['structure']}
- Citations: {standards['citations']}
- Objectivity: {standards['objectivity']}

Follow these guidelines strictly when generating academic content."""
        
        return prompt
    
    @staticmethod
    def validate_section(section_name: str, content: str, report_type: str = "research_report") -> Dict[str, Any]:
        """
        Validate if a section meets academic writing standards.
        
        Args:
            section_name: Name of the section
            content: Content to validate
            report_type: Type of report
        
        Returns:
            Dictionary with validation results
        """
        structure = AcademicGuidelines.get_structure(report_type)
        issues = []
        strengths = []
        
        # Check if section is in required structure
        if section_name not in structure['sections']:
            issues.append(f"Section '{section_name}' not in standard structure")
        
        # Basic quality checks
        if len(content) < 100:
            issues.append("Content is too short for academic standards")
        else:
            strengths.append("Adequate length")
        
        # Check for informal language
        informal_words = ["I think", "I believe", "we", "you", "gonna", "wanna", "kinda"]
        found_informal = [word for word in informal_words if word.lower() in content.lower()]
        if found_informal:
            issues.append(f"Informal language detected: {', '.join(found_informal)}")
        else:
            strengths.append("Formal tone maintained")
        
        # Check for citations (basic)
        if "[" in content and "]" in content:
            strengths.append("Citations present")
        elif "(" in content and ")" in content:
            strengths.append("Possible citations present")
        else:
            issues.append("No clear citations found")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "strengths": strengths,
            "score": max(0, 1.0 - len(issues) * 0.2)
        }
