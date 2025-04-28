from flask import Flask, render_template, request, jsonify
import os
import subprocess
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    repo_path = request.form.get('repo_path')
    if not repo_path:
        return jsonify({"error": "Repository path is required"}), 400
    
    try:
        # Run inframate analyze command
        result = subprocess.run(
            ['inframate', 'analyze', repo_path, '--terraform'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extract terraform template from output
        output = result.stdout
        terraform_template = output.split("Generated Terraform Template:")[-1].strip()
        
        return jsonify({
            "success": True,
            "terraform_template": terraform_template,
            "full_output": output
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Analysis failed",
            "details": e.stderr
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 