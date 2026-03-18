"""
Core agent class implementing planning, tool use, and reflexion patterns.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from tools import SearchTool, LLMTool


class AgentState(Enum):
    """Agent execution states."""
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Plan:
    """Represents an agent's plan."""
    steps: List[str] = field(default_factory=list)
    current_step: int = 0
    
    def add_step(self, step: str):
        """Add a step to the plan."""
        self.steps.append(step)
    
    def next_step(self) -> Optional[str]:
        """Get the next step in the plan."""
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self.current_step += 1
            return step
        return None
    
    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return self.current_step >= len(self.steps)


@dataclass
class Reflection:
    """Represents an agent's reflection on its work."""
    observations: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    
    def add_observation(self, observation: str):
        """Add an observation."""
        self.observations.append(observation)
    
    def add_improvement(self, improvement: str):
        """Add a suggested improvement."""
        self.improvements.append(improvement)


class ResearchAgent:
    """
    Research agent implementing planning, tool use, and reflexion patterns.
    """
    
    def __init__(
        self,
        model: str = "openai/gpt-4o-mini",
        enable_reflexion: bool = True,
        max_iterations: int = 10
    ):
        """
        Initialize the research agent.
        
        Args:
            model: LLM model identifier for OpenRouter
            enable_reflexion: Whether to enable reflexion after each step
            max_iterations: Maximum number of execution iterations
        """
        self.llm = LLMTool(model=model)
        self.search_tool = SearchTool()
        self.enable_reflexion = enable_reflexion
        self.max_iterations = max_iterations
        
        self.state = AgentState.PLANNING
        self.plan: Optional[Plan] = None
        self.reflection: Optional[Reflection] = None
        self.execution_history: List[Dict[str, Any]] = []
        self.iteration_count = 0
    
    def create_plan(self, task: str, context: Optional[str] = None) -> Plan:
        """
        Create an execution plan for the given task.
        
        Args:
            task: The task description
            context: Optional context or constraints
        
        Returns:
            A Plan object with steps
        """
        planning_prompt = f"""You are a research assistant. Create a detailed step-by-step plan to accomplish the following task:

Task: {task}
{f'Context/Constraints: {context}' if context else ''}

IMPORTANT RULES for the plan:
- Every search step must be DIRECTLY related to the main task topic
- Do NOT plan searches for tangential or loosely related subjects
- Keep the number of steps minimal and focused (5-8 steps maximum)
- Each step must clearly contribute to the final output

Provide a clear, actionable plan with specific steps. Each step should be concrete and executable.
Format your response as a JSON array of step strings, like: ["Step 1", "Step 2", "Step 3"]

Plan:"""

        messages = [
            {"role": "system", "content": "You are a helpful research assistant that creates focused, on-topic, and actionable plans. You never plan searches for irrelevant subjects."},
            {"role": "user", "content": planning_prompt}
        ]
        
        response = self.llm.generate(messages, temperature=0.3)
        
        # Try to parse JSON from response
        try:
            # Extract JSON array from response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                steps = json.loads(json_match.group())
            else:
                # Fallback: split by numbered lines
                steps = [line.strip() for line in response.split('\n') if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-'))]
                steps = [s.lstrip('0123456789.-) ').strip() for s in steps if s]
        except Exception:
            # Fallback: create simple plan
            steps = [f"Step {i+1}: {line.strip()}" for i, line in enumerate(response.split('\n')) if line.strip()][:10]
        
        plan = Plan(steps=steps if steps else [task])
        self.plan = plan
        self.state = AgentState.EXECUTING
        return plan
    
    def execute_step(self, step: str, previous_results: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a single step of the plan.
        
        Args:
            step: The step description to execute
            previous_results: Results from previous steps
        
        Returns:
            Dictionary with execution results
        """
        if previous_results is None:
            previous_results = []
        
        # Build context from previous results
        context = ""
        if previous_results:
            context = "\n\nPrevious results:\n"
            for i, result in enumerate(previous_results[-3:], 1):  # Last 3 results
                context += f"{i}. {result.get('step', '')}: {result.get('result', '')[:200]}...\n"
        
        execution_prompt = f"""You are executing a research step.

Current step: {step}
{context}

Determine what actions are needed. You can:
1. Search for information using the search tool
2. Analyze and synthesize information
3. Generate content or reports

IMPORTANT: If you use the search tool, your query must be specific and directly related to the current step. Do NOT search for broad or tangential topics.

Provide your response. If you need to search, indicate what to search for. Otherwise, provide your analysis or output directly.

Response:"""
        
        # Define tools available to the agent
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the web for information on a given query",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        messages = [
            {"role": "system", "content": "You are a research assistant. Use tools when you need to search for information."},
            {"role": "user", "content": execution_prompt}
        ]
        
        # Try tool calling first
        result = self.llm.generate_with_tools(messages, tools, tool_choice="auto", temperature=0.5)
        
        execution_result = {
            "step": step,
            "reasoning": result.get('content', ''),
            "actions": [],
            "result": ""
        }
        
        # Handle tool calls
        if result.get('tool_calls'):
            for tool_call in result['tool_calls']:
                func_name = tool_call['function']['name']
                args = tool_call['function']['arguments']
                
                if func_name == "search":
                    query = args.get('query', '')
                    max_results = args.get('max_results', 5)
                    search_results = self.search_tool.search(query, max_results=max_results)
                    
                    execution_result["actions"].append({
                        "type": "search",
                        "query": query,
                        "results": search_results
                    })
                    
                    # Synthesize search results
                    if search_results:
                        synthesis_prompt = f"""Based on the following search results for "{query}", provide a comprehensive summary and analysis:

{self._format_search_results(search_results)}

Provide a clear, well-structured summary that addresses the query."""

                        synthesis_messages = [
                            {"role": "system", "content": "You are a research assistant that synthesizes information from search results."},
                            {"role": "user", "content": synthesis_prompt}
                        ]
                        
                        synthesis = self.llm.generate(synthesis_messages, temperature=0.3)
                        execution_result["result"] = synthesis
                    else:
                        execution_result["result"] = f"No results found for query: {query}"
        else:
            # No tool calls, use direct response
            execution_result["result"] = result.get('content', '')
        
        return execution_result
    
    def reflect(self, execution_results: List[Dict[str, Any]], task: str) -> Reflection:
        """
        Reflect on the execution results and suggest improvements.
        
        Args:
            execution_results: List of execution results
            task: Original task description
        
        Returns:
            Reflection object with observations and improvements
        """
        results_summary = "\n".join([
            f"Step {i+1}: {r.get('step', '')}\nResult: {r.get('result', '')[:300]}..."
            for i, r in enumerate(execution_results)
        ])
        
        reflection_prompt = f"""You are reflecting on a research task execution.

Original task: {task}

Execution results:
{results_summary}

Analyze the execution:
1. What observations can you make about the quality and completeness of the work?
2. What improvements or additional steps might be needed?
3. Rate your confidence in the results (0.0 to 1.0).

Provide your reflection in a structured format."""

        messages = [
            {"role": "system", "content": "You are a reflective research assistant that critically evaluates work quality."},
            {"role": "user", "content": reflection_prompt}
        ]
        
        response = self.llm.generate(messages, temperature=0.3)
        
        reflection = Reflection()
        
        # Parse reflection (simple extraction)
        lines = response.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'observation' in line_lower or 'noticed' in line_lower or 'found' in line_lower:
                reflection.add_observation(line.strip())
            elif 'improvement' in line_lower or 'suggest' in line_lower or 'should' in line_lower:
                reflection.add_improvement(line.strip())
            elif 'confidence' in line_lower:
                # Try to extract confidence score
                import re
                match = re.search(r'(\d+\.?\d*)', line)
                if match:
                    try:
                        reflection.confidence = min(1.0, max(0.0, float(match.group(1)) / 100.0 if float(match.group(1)) > 1 else float(match.group(1))))
                    except Exception:
                        pass
        
        # If no structured parsing, add full response as observation
        if not reflection.observations:
            reflection.add_observation(response[:500])
        
        self.reflection = reflection
        return reflection
    
    def execute(self, task: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a complete research task.
        
        Args:
            task: The task description
            context: Optional context or constraints
        
        Returns:
            Dictionary with final results, plan, and reflection
        """
        self.state = AgentState.PLANNING
        self.iteration_count = 0
        self.execution_history = []
        
        # Create plan
        plan = self.create_plan(task, context)
        
        # Execute plan
        execution_results = []
        while not plan.is_complete() and self.iteration_count < self.max_iterations:
            step = plan.next_step()
            if not step:
                break
            
            self.state = AgentState.EXECUTING
            result = self.execute_step(step, execution_results)
            execution_results.append(result)
            self.execution_history.append(result)
            self.iteration_count += 1
            
            # Optional: reflexion after each step
            if self.enable_reflexion and self.iteration_count % 3 == 0:
                self.state = AgentState.REFLECTING
                reflection = self.reflect(execution_results, task)
                # Could use reflection to modify plan or retry steps
        
        # Final reflection
        if self.enable_reflexion:
            self.state = AgentState.REFLECTING
            reflection = self.reflect(execution_results, task)
        else:
            reflection = None
        
        self.state = AgentState.COMPLETED
        
        return {
            "task": task,
            "plan": plan.steps,
            "results": execution_results,
            "reflection": reflection,
            "status": "completed"
        }
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for LLM consumption."""
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"""
Result {i}:
Title: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}
Content: {result.get('content', 'N/A')[:500]}
""")
        return "\n".join(formatted)

