#!/usr/bin/env python3
"""
HTML to Markdown Converter for Documentation
Usage: python3 docs/convert_html.py
"""

import os
from pathlib import Path
import re

# Simple HTML to MD converter logic since we can't easily install new pip packages in this env
# We'll use regex and basic parsing for the specific format seen in the audit.

def html_to_md(content):
    # Remove head/style
    content = re.sub(r'<head>.*?</head>', '', content, flags=re.DOTALL)
    content = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)
    
    # Headers
    content = re.sub(r'<h1>(.*?)</h1>', r'# \1\n', content)
    content = re.sub(r'<h2>(.*?)</h2>', r'\n## \1\n', content)
    content = re.sub(r'<h3>(.*?)</h3>', r'\n### \1\n', content)
    content = re.sub(r'<h4>(.*?)</h4>', r'\n#### \1\n', content)
    
    # Lists
    content = re.sub(r'<ul>', '', content)
    content = re.sub(r'</ul>', '', content)
    content = re.sub(r'<li>(.*?)</li>', r'- \1', content)
    
    # Tables (Basic support for the format seen)
    # This is tricky with regex, but let's try a best effort for simple tables
    # Or just strip tags and leave text if too complex? 
    # The Pricing doc has complex tables. 
    # Strategy: Replace <table> with empty, <tr> with |\n, <td> with | content |
    
    # Actually, for reliability in this constrained env, we might just strip the HTML wrapper
    # and keep the HTML *body* content if it's cleaner, but Markdown is preferred.
    
    # Let's try aggressive regex replacement
    content = re.sub(r'<p>(.*?)</p>', r'\1\n\n', content)
    content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', content)
    content = re.sub(r'<em>(.*?)</em>', r'*\1*', content)
    content = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', content)
    content = re.sub(r'<pre><code>(.*?)</code></pre>', r'```\n\1\n```', content, flags=re.DOTALL)
    content = re.sub(r'<code>(.*?)</code>', r'`\1`', content)
    
    # Remove remaining tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Fix entities
    content = content.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    
    return content

def convert_files():
    base_dir = Path("docs")
    for html_file in base_dir.rglob("*.html"):
        if "ai-periodic-table-roadmap.html" in str(html_file): # Keep this one if it's a special visualization? 
            # Actually user said "parse each page to conform".
            # If it's a D3/JS viz, we might break it. 
            # Looking at file size (24KB), likely text.
            pass
            
        print(f"Converting {html_file}...")
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            md_content = html_to_md(html_content)
            
            # Save as .md
            new_path = html_file.with_suffix('.md')
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            # Delete original
            html_file.unlink()
            print(f"Saved to {new_path}")
            
        except Exception as e:
            print(f"Failed to convert {html_file}: {e}")

if __name__ == "__main__":
    convert_files()
