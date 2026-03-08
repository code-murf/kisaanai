<div align="center">

# 🌾 KisaanAI

### AI-Powered Agricultural Intelligence Platform for Indian Farmers

[![AWS Hackathon](https://img.shields.io/badge/AWS-AI%20for%20Bharat%202026-FF9900?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com)
[![Live Demo](https://img.shields.io/badge/Live-Demo-success?style=for-the-badge&logo=google-chrome)](https://kisaanai.duckdns.org)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/code-murf/kisaanai)

---

### 🎥 Product Demo

https://github.com/user-attachments/assets/1zkjXlti0JMv8zF4Sc9KxnW6bH58dxdaL

**[📺 Watch Full Demo on Google Drive](https://drive.google.com/file/d/1zkjXlti0JMv8zF4Sc9KxnW6bH58dxdaL/view?usp=sharing)**

---

</div>

## 🎯 The Problem

India has **100+ million farmers** facing critical challenges:

- **70% are illiterate** and cannot use text-based applications
- **Language barriers** prevent access to modern agricultural technology
- **Limited access** to market intelligence and price information
- **No access** to agricultural experts for crop disease diagnosis
- **Inefficient market selection** leading to reduced profits

## 💡 Our Solution

**KisaanAI** is a voice-first agricultural intelligence platform that empowers farmers with AI-powered insights in their native language.

### ✨ Key Features

<table>
<tr>
<td width="50%">

**🎤 Voice Assistant**
- Speak in Hindi, English, or regional languages
- Get instant answers to farming questions
- No typing required - perfect for illiterate farmers
- Real-time weather and market updates

</td>
<td width="50%">

**🌾 Crop Disease Detection**
- Upload crop photos for instant diagnosis
- AI-powered disease identification
- Treatment recommendations in local language
- Secure image storage

</td>
</tr>
<tr>
<td width="50%">

**📊 Price Forecasting**
- ML-powered price predictions
- 7, 14, and 30-day forecasts
- Historical price trends
- Confidence intervals for planning

</td>
<td width="50%">

**🗺️ Smart Mandi Recommendations**
- Find best markets for your crops
- Price comparison across mandis
- Distance and transport cost calculation
- Maximize your profits

</td>
</tr>
</table>

## ☁️ Powered by AWS

KisaanAI leverages **5 AWS services** for a scalable, production-ready solution:

<div align="center">

| AWS Service | Purpose |
|------------|---------|
| **🤖 Amazon Bedrock** | AI intelligence with Claude 3 Haiku & Nova Lite |
| **📦 Amazon S3** | Secure image storage with presigned URLs |
| **📊 Amazon CloudWatch** | Real-time monitoring and metrics |
| **🎤 AWS Transcribe** | Multilingual speech-to-text |
| **☁️ Amazon EC2** | Production hosting with Docker |

</div>

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│           Frontend (Next.js 15 + React Native)          │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS/REST API
┌────────────────────────▼────────────────────────────────┐
│              Backend Services (FastAPI)                  │
│   Voice • Disease Detection • Forecasting • Mandi       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  AWS Services Layer                      │
│  Bedrock • S3 • CloudWatch • Transcribe • EC2           │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│         Data Layer (PostgreSQL + Redis + ML)            │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Tech Stack

<table>
<tr>
<td width="33%">

**Frontend**
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- React Native + Expo

</td>
<td width="33%">

**Backend**
- FastAPI (Python 3.11+)
- PostgreSQL + PostGIS
- Redis Cache
- XGBoost + Prophet
- SHAP (Explainability)

</td>
<td width="33%">

**Infrastructure**
- Docker + Docker Compose
- Nginx Reverse Proxy
- HTTPS/SSL
- AWS EC2
- GitHub Actions CI/CD

</td>
</tr>
</table>

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker & Docker Compose
- AWS Account (for Bedrock, S3, CloudWatch)

### Docker Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/code-murf/kisaanai.git
cd kisaanai

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

**Mobile App**:
```bash
cd agribharat-mobile
npm install
npx expo start
```

## 📚 Documentation

<div align="center">

| Document | Description |
|----------|-------------|
| [Technical Documentation](TECHNICAL_DOCUMENTATION.md) | Complete technical guide |
| [AWS Integration Guide](AWS_INTEGRATION_GUIDE.md) | AWS services integration |
| [API Reference](API_QUICK_REFERENCE.md) | API endpoints documentation |

</div>

## 🌟 Key Differentiators

1. **Voice-First Accessibility** - Unique for agriculture sector, addresses 70% illiterate farmers
2. **Production-Ready** - Live HTTPS deployment, not just a demo
3. **Real AWS Integration** - Actual Bedrock API calls, not mockups
4. **Explainable AI** - SHAP values for price forecasts build farmer trust
5. **Multilingual Support** - Hindi, English, and regional languages

## 🗺️ Future Roadmap

**Q2 2026** - WhatsApp Integration
- Daily price alerts via WhatsApp
- Conversational queries through WhatsApp bot
- Image-based disease detection via WhatsApp

**Q3 2026** - Regional Language Expansion
- Tamil, Telugu, Bengali, Marathi support
- Regional crop-specific features
- Local mandi integration

**Q4 2026** - Blockchain Supply Chain
- Transparent supply chain tracking
- Direct farmer-to-consumer marketplace
- Smart contracts for fair pricing

**2027** - Pan-India Rollout
- Partnerships with agri-input companies
- Integration with banks for credit
- Government collaboration
- Target: 10M+ farmers

## 🏆 AWS AI for Bharat Hackathon 2026

<div align="center">

### 📦 Submission Deliverables

| Item | Link |
|------|------|
| 🚀 **Live Prototype** | [kisaanai.duckdns.org](https://kisaanai.duckdns.org) |
| 💻 **GitHub Repository** | [github.com/code-murf/kisaanai](https://github.com/code-murf/kisaanai) |
| 🎥 **Demo Video** | [Watch Video](https://drive.google.com/file/d/1zkjXlti0JMv8zF4Sc9KxnW6bH58dxdaL/view) |
| 📝 **Blog Post** | [AWS Builder Center](#) |

</div>

## 🤝 Contributing

We welcome contributions! This project was built for the AWS AI for Bharat Hackathon 2026.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

<div align="center">

[![Live Demo](https://img.shields.io/badge/🚀-Try_Live_Demo-success?style=for-the-badge)](https://kisaanai.duckdns.org)
[![GitHub](https://img.shields.io/badge/💻-View_Code-181717?style=for-the-badge&logo=github)](https://github.com/code-murf/kisaanai)
[![Video Demo](https://img.shields.io/badge/🎥-Watch_Demo-red?style=for-the-badge)](https://drive.google.com/file/d/1zkjXlti0JMv8zF4Sc9KxnW6bH58dxdaL/view)

---

**Built with ❤️ for AWS AI for Bharat Hackathon 2026**

**Empowering 100M+ Indian Farmers with AI Technology**

</div>
