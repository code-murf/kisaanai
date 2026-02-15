"""
Generate PDF documentation from markdown with images.
Requires: pip install markdown2 weasyprint pillow
"""
import markdown2
from weasyprint import HTML, CSS
from pathlib import Path
import base64

# Read the markdown file
md_file = Path("PROJECT_DOCUMENTATION.md")
md_content = md_file.read_text(encoding='utf-8')

# Convert markdown to HTML
html_content = markdown2.markdown(
    md_content,
    extras=[
        "tables",
        "fenced-code-blocks",
        "code-friendly",
        "header-ids",
        "toc"
    ]
)

# Create HTML template with styling
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AgriBharat - Project Documentation</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }}
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
        }}
        
        h1 {{
            color: #2c5f2d;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
            page-break-before: always;
            margin-top: 0;
        }}
        
        h1:first-of-type {{
            page-break-before: avoid;
            font-size: 36pt;
            text-align: center;
            margin-top: 100px;
        }}
        
        h2 {{
            color: #2c5f2d;
            border-bottom: 2px solid #81C784;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        
        h3 {{
            color: #388E3C;
            margin-top: 20px;
        }}
        
        h4 {{
            color: #4CAF50;
        }}
        
        code {{
            background-color: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        pre {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
            overflow-x: auto;
            page-break-inside: avoid;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            page-break-inside: avoid;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        blockquote {{
            border-left: 4px solid #4CAF50;
            padding-left: 20px;
            margin-left: 0;
            color: #666;
            font-style: italic;
        }}
        
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 5px 0;
        }}
        
        a {{
            color: #4CAF50;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .page-break {{
            page-break-after: always;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}
        
        .cover-page {{
            text-align: center;
            padding: 100px 0;
        }}
        
        .cover-title {{
            font-size: 48pt;
            color: #2c5f2d;
            margin-bottom: 20px;
        }}
        
        .cover-subtitle {{
            font-size: 24pt;
            color: #666;
            margin-bottom: 40px;
        }}
        
        .cover-info {{
            font-size: 14pt;
            color: #888;
            margin-top: 60px;
        }}
    </style>
</head>
<body>
    <div class="cover-page">
        <div class="cover-title">AgriBharat</div>
        <div class="cover-subtitle">Agricultural Analytics Platform</div>
        <div class="cover-subtitle">Complete Project Documentation</div>
        <div class="cover-info">
            <p>Version 1.0</p>
            <p>February 15, 2026</p>
        </div>
    </div>
    <div class="page-break"></div>
    
    {html_content}
</body>
</html>
"""

# Generate PDF
output_file = Path("AgriBharat_Documentation.pdf")
HTML(string=html_template).write_pdf(output_file)

print(f"✅ PDF generated successfully: {output_file}")
print(f"📄 File size: {output_file.stat().st_size / 1024:.2f} KB")
