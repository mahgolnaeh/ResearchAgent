# Research Assistant

A research assistant that operationalizes agentic patterns (planning, tool use, reflexion, and final LLM synthesis) to support literature review and structured report drafting under explicit academic writing guidelines.

## Setup Instructions

### Step 1: Install Python
Make sure you have Python installed. You can download it from [python.org](https://www.python.org/downloads/).

### Step 2: Install Required Packages
Open a terminal/command prompt in this folder and run:
```
pip install -r requirements.txt
```

### Step 3: Add Your API Keys

1. **Open the `.env` file** in this folder (you can use any text editor like Notepad)

2. **Get your OpenRouter API Key:**
   - Go to https://openrouter.ai/keys
   - Copy your API key
   - In the `.env` file, replace `your_openrouter_key_here` with your actual key
   - Example: `OPENROUTER_API_KEY=sk-or-v1-abc123...`

3. **Get your Tavily API Key:**
   - Go to https://tavily.com/
   - Copy your API key
   - In the `.env` file, replace `your_tavily_key_here` with your actual key
   - Example: `TAVILY_API_KEY=tvly-abc123...`

4. **Save the `.env` file**

### Step 4: Test Your Setup
Run the test script to verify your keys work:
```
python test_setup.py
```

## Usage

### Web UI (Recommended)

The easiest way to use the Research Assistant is through the web interface:

1. **Start the web server:**
   ```bash
   python ui.py
   ```

2. **Open your browser** and go to: `http://localhost:5000`

3. **Use the interface:**
   - Switch between "Literature Review" and "Research Report" tabs
   - Enter your research topic and questions
   - Click the button to start
   - View results and download them as Markdown or JSON

### Command-Line Interface

#### Conduct a Literature Review

```bash
python main.py review --topic "Machine Learning in Healthcare"
```

With specific research questions:

```bash
python main.py review --topic "Climate Change Impacts" \
  --questions "What are the main environmental impacts?" \
              "How do they vary by region?" \
  --max-sources 15 \
  --output literature_review.md
```

#### Draft a Research Report

```bash
python main.py report --topic "AI Ethics" \
  --questions "What are the main ethical concerns with AI?" \
              "How can these concerns be addressed?" \
  --output research_report.md
```

Using an existing literature review:

```bash
python main.py report --topic "AI Ethics" \
  --questions "What are the main ethical concerns?" \
  --literature-review literature_review.md \
  --output research_report.md
```

### Command-Line Options

**Global Options:**
- `--model`: Specify LLM model (default: `openai/gpt-4o-mini`)
- `--no-reflexion`: Disable reflexion for faster execution
- `--reflection`: Show reflection details in output
- `--output` / `-o`: Output file path (supports `.json`, `.md`, `.txt`)

**Review Command:**
- `--topic` / `-t`: Research topic (required)
- `--questions` / `-q`: Research questions (optional, multiple allowed)
- `--max-sources` / `-s`: Maximum sources to include in output (default: 10); sources are ranked by relevance score and the top N are kept

**Report Command:**
- `--topic` / `-t`: Research topic (required)
- `--questions` / `-q`: Research questions (required, multiple allowed)
- `--literature-review` / `-l`: Path to existing literature review
- `--context` / `-c`: Additional context or requirements

### Programmatic Usage

```python
from workflow import ResearchWorkflow

# Initialize workflow
workflow = ResearchWorkflow(model="openai/gpt-4o-mini")

# Conduct literature review
results = workflow.conduct_literature_review(
    research_topic="Machine Learning in Healthcare",
    research_questions=[
        "What are the main applications?",
        "What are the key challenges?"
    ],
    max_sources=10
)

# Draft research report
report = workflow.draft_research_report(
    research_topic="Machine Learning in Healthcare",
    research_questions=["What are the main applications?"],
    literature_review_data=results
)
```

## Architecture

The Research Assistant implements the following pipeline for each task:

```
User Input
    │
    ▼
Planning        — Generates a focused 5–8 step plan strictly on-topic
    │
    ▼
Execution       — Runs each step; uses Tavily search when needed
    │
    ▼
Reflexion       — Self-evaluates quality every 3 steps (optional)
    │
    ▼
Final Synthesis — Single LLM call that produces the structured output:
                  removes duplicates, filters off-topic content,
                  replaces "Result N" with real source titles
    │
    ▼
Structured Output (Markdown)
```

### Output Structure

**Literature Review** produces the following sections:
- Introduction
- Theoretical Frameworks and Background
- Key Themes and Findings
- Critical Analysis
- Gaps and Future Directions
- Conclusion

**Research Report** produces the following sections:
- Abstract
- Introduction
- Literature Review
- Methodology
- Results and Findings
- Discussion
- Conclusion
- References

### Source Handling

Sources collected during execution are deduplicated, sorted by Tavily relevance score (highest first), and trimmed to `max_sources` before being passed to the final synthesis step. This means the final output cites only the most relevant sources up to the requested limit.

### Core Components

| File | Responsibility |
|------|----------------|
| `tools.py` | `SearchTool` (Tavily) and `LLMTool` (OpenRouter) wrappers |
| `agent.py` | `ResearchAgent` — planning, step execution, tool calling, reflexion |
| `workflow.py` | `ResearchWorkflow` — orchestration, source extraction, final LLM synthesis |
| `academic_guidelines.py` | Writing standards and section structure definitions |
| `main.py` | Command-line interface |
| `ui.py` | Flask web server and REST API (`/api/review`, `/api/report`, `/api/download`) |

### Default Model

The default model is `openai/gpt-4o-mini` accessed through [OpenRouter](https://openrouter.ai). Any model available on OpenRouter can be specified via `--model`, for example:

```bash
python main.py review --topic "Quantum Computing" --model "anthropic/claude-3.5-sonnet"
```

## Important Notes

- **Never share your `.env` file** — it contains your secret API keys
- The `.env` file is already in `.gitignore` so it will not be accidentally committed to git
- If you need to share your code, use `.env.example` as a template (it contains no real keys)
- The agent makes multiple API calls per task; costs depend on your OpenRouter and Tavily plans
- For best results, use specific and focused research topics and questions
