import markdown
import sys
import os

import markdown
import sys
import os
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Convert Markdown to HTML with styling.')
parser.add_argument('input_file', help='Path to the input Markdown file')
parser.add_argument('output_file', help='Path to the output HTML file')
args = parser.parse_args()

input_path = args.input_file
output_path = args.output_file

# CSS for better readability
css = """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f9f9f9;
    }
    h1, h2, h3 {
        color: #111;
        margin-top: 1.5em;
    }
    h1 { border-bottom: 2px solid #eaeaea; padding-bottom: 0.3em; }
    h2 { border-bottom: 1px solid #eaeaea; padding-bottom: 0.3em; }
    code {
        background-color: #eee;
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
        font-size: 85%;
    }
    pre {
        background-color: #f6f8fa;
        padding: 1rem;
        border-radius: 6px;
        overflow-x: auto;
    }
    pre code {
        background-color: transparent;
        padding: 0;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
    }
    th, td {
        border: 1px solid #dfe2e5;
        padding: 0.6rem 1rem;
    }
    th {
        background-color: #f6f8fa;
        font-weight: 600;
    }
    tr:nth-child(even) {
        background-color: #fff;
    }
    a { color: #0366d6; text-decoration: none; }
    a:hover { text-decoration: underline; }
    blockquote {
        border-left: 4px solid #dfe2e5;
        color: #6a737d;
        margin: 0;
        padding: 0 1rem;
    }
</style>
"""

try:
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Convert markdown to HTML with extensions for tables and fenced code blocks
    html_content = markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'])
    
    # Wrap in full HTML structure
    full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Enterprise Agentic Stack</title>
    {css}
</head>
<body>
    {html_content}
</body>
</html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
        
    print(f"Successfully converted {input_path} to {output_path}")

except Exception as e:
    print(f"Error converting file: {e}")
    sys.exit(1)
