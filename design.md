# KisaanAI - System Design

## Architecture
1. **API Layer**: FastAPI REST endpoints
2. **AI Engine**: TensorFlow disease detection + XGBoost price forecasting
3. **Voice Pipeline**: ElevenLabs TTS + STT
4. **Data Layer**: PostgreSQL + Redis cache

## Key Modules
- Voice Agent Service
- Weather Service  
- Price Service (Agmarknet scraper)
- Disease Detection (CNN classifier)
- User Management (JWT auth)

## Data Flow
User Voice → Whisper STT → LLM Intent → Service Router → Response → ElevenLabs TTS → User
