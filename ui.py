"""
Simple web UI for the Research Assistant.
Run this file to start the web interface.
"""

from flask import Flask, render_template, request, jsonify, session
from config import validate_config
from workflow import ResearchWorkflow
import json
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Validate configuration on startup
try:
    validate_config()
    config_valid = True
except ValueError as e:
    config_valid = False
    config_error = str(e)


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html', config_valid=config_valid)


@app.route('/api/review', methods=['POST'])
def conduct_review():
    """API endpoint to conduct a literature review."""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        questions = data.get('questions', [])
        max_sources = int(data.get('max_sources', 10))
        model = data.get('model', 'openai/gpt-4o-mini')
        enable_reflexion = data.get('enable_reflexion', True)
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Filter out empty questions
        questions = [q.strip() for q in questions if q.strip()]
        
        # Create workflow
        workflow = ResearchWorkflow(
            model=model,
            enable_reflexion=enable_reflexion
        )
        
        # Conduct review
        results = workflow.conduct_literature_review(
            research_topic=topic,
            research_questions=questions if questions else None,
            max_sources=max_sources
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report', methods=['POST'])
def draft_report():
    """API endpoint to draft a research report."""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        questions = data.get('questions', [])
        model = data.get('model', 'openai/gpt-4o-mini')
        enable_reflexion = data.get('enable_reflexion', True)
        additional_context = data.get('additional_context', '').strip()
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        if not questions:
            return jsonify({'error': 'At least one research question is required'}), 400
        
        # Filter out empty questions
        questions = [q.strip() for q in questions if q.strip()]
        
        if not questions:
            return jsonify({'error': 'At least one research question is required'}), 400
        
        # Create workflow
        workflow = ResearchWorkflow(
            model=model,
            enable_reflexion=enable_reflexion
        )
        
        # Draft report
        results = workflow.draft_research_report(
            research_topic=topic,
            research_questions=questions,
            additional_context=additional_context if additional_context else None
        )
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def download_results():
    """Download results as a file."""
    try:
        data = request.json
        results = data.get('results')
        filename = data.get('filename', 'results')
        filetype = data.get('filetype', 'md')
        
        if not results:
            return jsonify({'error': 'No results to download'}), 400
        
        # Create downloads directory if it doesn't exist
        downloads_dir = Path('downloads')
        downloads_dir.mkdir(exist_ok=True)
        
        output_path = downloads_dir / f"{filename}.{filetype}"
        
        if filetype == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        else:
            # Markdown or text
            with open(output_path, 'w', encoding='utf-8') as f:
                if 'literature_review' in results:
                    f.write(f"# Literature Review: {results.get('topic', 'Unknown')}\n\n")
                    f.write(results.get('literature_review', ''))
                    f.write("\n\n## Sources\n\n")
                    for source in results.get('sources', []):
                        f.write(f"- [{source.get('title', 'N/A')}]({source.get('url', 'N/A')})\n")
                elif 'report' in results:
                    f.write(results.get('report', ''))
        
        return jsonify({
            'success': True,
            'filepath': str(output_path)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    if not config_valid:
        print(f"Warning: {config_error}")
        print("The UI will start, but API calls may fail.")
    
    print("\n" + "="*60)
    print("Research Assistant - Web UI")
    print("="*60)
    print("Starting server...")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
