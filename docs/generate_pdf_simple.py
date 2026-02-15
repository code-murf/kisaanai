"""
Generate PDF documentation using reportlab (simpler, no external dependencies).
Install: pip install reportlab markdown2
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import markdown2
from pathlib import Path
import re

def create_pdf():
    # Read markdown
    md_file = Path("PROJECT_DOCUMENTATION.md")
    md_content = md_file.read_text(encoding='utf-8')
    
    # Create PDF
    pdf_file = "AgriBharat_Documentation.pdf"
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=colors.HexColor('#2c5f2d'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=24,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c5f2d'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#2c5f2d'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#388E3C'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        leftIndent=20,
        spaceAfter=10,
    )
    
    # Cover page
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("AgriBharat", title_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("Agricultural Analytics Platform", subtitle_style))
    elements.append(Paragraph("Complete Project Documentation", subtitle_style))
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Version 1.0", body_style))
    elements.append(Paragraph("February 15, 2026", body_style))
    elements.append(PageBreak())
    
    # Parse markdown content
    lines = md_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Headers
        if line.startswith('# '):
            text = line[2:].strip()
            if text != "AgriBharat - Agricultural Analytics Platform":  # Skip title
                elements.append(PageBreak())
                elements.append(Paragraph(text, h1_style))
                elements.append(Spacer(1, 0.2*inch))
        
        elif line.startswith('## '):
            text = line[3:].strip()
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(text, h2_style))
            elements.append(Spacer(1, 0.1*inch))
        
        elif line.startswith('### '):
            text = line[4:].strip()
            elements.append(Paragraph(text, h3_style))
        
        # Horizontal rule
        elif line.startswith('---'):
            elements.append(Spacer(1, 0.2*inch))
        
        # Code blocks
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code_text = '\n'.join(code_lines)
            elements.append(Preformatted(code_text, code_style))
        
        # Tables
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            i -= 1
            
            # Parse table
            table_data = []
            for tline in table_lines:
                if '---' not in tline:  # Skip separator line
                    cells = [cell.strip() for cell in tline.split('|')[1:-1]]
                    table_data.append(cells)
            
            if table_data:
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 0.2*inch))
        
        # Bullet points
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:].strip()
            bullet_text = f"• {text}"
            elements.append(Paragraph(bullet_text, body_style))
        
        # Regular paragraphs
        else:
            if line and not line.startswith('#'):
                # Clean up markdown formatting
                text = line.replace('**', '<b>').replace('**', '</b>')
                text = text.replace('`', '<font name="Courier">')
                text = text.replace('`', '</font>')
                elements.append(Paragraph(text, body_style))
        
        i += 1
    
    # Build PDF
    doc.build(elements)
    print(f"✅ PDF generated successfully: {pdf_file}")
    print(f"📄 Total pages: ~{len(elements) // 20}")

if __name__ == "__main__":
    create_pdf()
