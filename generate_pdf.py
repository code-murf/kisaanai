from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'KisaanAI - AWS AI for Bharat Hackathon Submission', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def chapter_title(self, num, label):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, 'Slide %d : %s' % (num, label), 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, body)
        self.ln()

pdf = PDF()
pdf.alias_nb_pages()

slides = [
    ("Introduction", "Team Name: Antigravity AI\nProblem: Information Asymmetry & Market Inefficiency\nLeader: KisaanAI Team Lead"),
    ("Brief Idea", "KisaanAI is a voice-first, AI-powered platform that empowers farmers with real-time mandi prices, weather forecasts, and crop advisory services in their local language. It bridges the information gap, enabling data-driven decisions for better profitability."),
    ("Proposed Solution & USP", "1. Voice-First Interface: Breaks literacy barriers using Bhashini AI.\n2. Predictive Intelligence: 7-day price forecasts using Temporal Fusion Transformers.\n3. Smart Routing: Calculates Net Profit (Price - Transport Cost).\n4. Explainable AI: Provides reasoning to build trust."),
    ("Key Features", "- KisaanCredit (New): AI-based credit scoring using yield forecasts for instant micro-loans.\n- AI Price Forecasting: Accurate predictions for Potato, Onion, Tomato.\n- Voice Assistant: 'Bolo aur Jaano' interface.\n- Smart Routing: Real-time transport cost calculation.\n- WhatsApp Bot: Low-bandwidth access.\n- Crop Doctor: Image-based disease detection."),
    ("Technology Stack", "- Cloud: AWS\n- AI/ML: PyTorch, XGBoost, TFT\n- Voice/NLP: Bhashini API, Twilio\n- Web: Next.js, Tailwind CSS\n- Backend: FastAPI, PostgreSQL"),
    ("Implementation Cost", "- Infrastructure: ~$50/month (AWS Spot).\n- Data: Free (Open Gov Data).\n- Feasibility: MVP ready in 4 weeks."),
    ("Business Impact", "- Impact: 15-20% projected income increase for farmers.\n- Scale: Extensible to 50+ crops.\n- Future: FPO integration.")
]

# Ensure ASCII compatibility
slides = [(title, body.encode('latin-1', 'replace').decode('latin-1')) for title, body in slides]


for i, (title, body) in enumerate(slides):
    pdf.add_page()
    pdf.chapter_title(i+1, title)
    pdf.chapter_body(body)

pdf.output('KisaanAI_Hackathon_Submission.pdf', 'F')
print("PDF generated successfully.")
