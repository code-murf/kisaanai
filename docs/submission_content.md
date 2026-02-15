HACKATHON IDEA SUBMISSION: KISAANAI

Theme: AWS AI for Bharat
Team Name: Antigravity AI

SLIDE 1: INTRODUCTION

Project Name: KisaanAI
Tagline: Bridging the Information Gap for Indian Farmers with AI
Team: Antigravity AI (10 Members)


SLIDE 2: PROBLEM STATEMENT

The Challenge

Information Asymmetry
Small farmers lack real-time access to mandi prices, often leading to distress selling at lower rates.

Language Barrier
Most existing applications require literacy and the ability to type in English or Hindi, effectively excluding millions of farmers.

Logistics and Profitability
Farmers often do not know where to sell for maximum profit after accounting for transport costs. The nearest mandi is not always the most profitable one.

Trust Deficit
AI predictions are frequently perceived as black boxes. Farmers are skeptical of advice when they do not understand the reasoning behind it.


SLIDE 3: PROPOSED SOLUTION

KisaanAI is a comprehensive, voice-first platform tailored to empower farmers with data-driven decisions.

Core Value Proposition

Predictive Intelligence
We utilize advanced AI, specifically Temporal Fusion Transformers, to forecast commodity prices 7 to 30 days in advance with high accuracy.

Universal Accessibility
The platform features a Voice-to-Voice interaction model in local dialects, powered by the Bhashini API, ensuring even illiterate farmers can use it.

Actionable Insights
Our system calculates Net Profit by subtracting transport costs from the market price. It recommends the best mandi to sell at, rather than just the nearest one.


SLIDE 4: KEY FEATURES

AI Price Forecasting
Accurate price predictions for key vegetables like Potato, Onion, and Tomato using satellite data (Sentinel-2 NDVI) and weather patterns.

Voice Assistant
The Bolo aur Jaano (Speak and Know) interface designed specifically for users with limited literacy.

Smart Routing
Integration with OpenStreetMap to calculate real-time transport costs to different mandis, ensuring accurate profit estimation.

WhatsApp Bot
Provides low-bandwidth access to alerts and daily price updates, meeting farmers where they already are.

Crop Doctor
Farmers can upload a photo of a leaf, and our AI detects diseases and provides voice-based advisory on cures.


SLIDE 5: UNIQUE SELLING PROPOSITION (USP)

Interface
Competitors use text and menu-based navigation. KisaanAI uses a Voice-First interface powered by Bhashini.

Forecasting
Competitors rely on historical averages. KisaanAI employs State-of-the-Art Deep Learning (TFT) for precision.

Explanation
Competitors offer black-box predictions. KisaanAI provides Explainable AI (XAI) to build trust.

Logistics
Competitors calculate distance only. KisaanAI optimizes for Net Profit.


SLIDE 6: SYSTEM ARCHITECTURE

Data Layer
Aggregates prices from Agmarknet, satellite imagery from Sentinel-2, and weather data from IMD.

Ingestion
Python and Airflow pipelines clean and store data in PostgreSQL with PostGIS extensions.

Intelligence Layer
The ML Engine runs PyTorch for forecasting and YOLO for disease detection. GenAI components use Llama-2 and Bhashini for voice and text processing.

Application Layer
A FastAPI Backend serves the Next.js Progressive Web App and the WhatsApp Bot.


SLIDE 7: TECHNOLOGY STACK

Cloud
AWS EC2 for hosting, S3 for data lake, and RDS for database management.

AI and Machine Learning
PyTorch, XGBoost, and Temporal Fusion Transformer key libraries.

Voice and NLP
Bhashini API (Government of India) and Twilio for WhatsApp integration.

Frontend
Next.js, Tailwind CSS, and Leaflet Maps.

Backend
FastAPI, PostgreSQL, and MinIO.


SLIDE 8: IMPLEMENTATION COST AND FEASIBILITY

Infrastructure
We utilize AWS Free Tier and Spot Instances to keep training costs low, estimated at around $50 per month initially.

Data Costs
Agmarknet and Sentinel-2 data are available via Open Government Data and free tiers, incurring zero cost.

API Costs
Bhashini is free for research and government usage. The WhatsApp sandbox minimizes development costs.

Feasibility
The MVP is ready for deployment in 4 weeks with our structured 10-person squad.


SLIDE 9: BUSINESS IMPACT AND FUTURE SCOPE

Impact
We project an increase in farmer income by 15-20% through arbitrage, enabling them to sell at the right place and time.

Scale
The platform is designed to extend to over 50 crops and provide nationwide coverage.

Future
We plan to integrate with Farmer Producer Organizations (FPOs) to enable collective bargaining power.
