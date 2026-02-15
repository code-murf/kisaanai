# Deep Research Technical Report: Agri-Analytics Stack

## 1. Advanced Machine Learning Strategy
Moving beyond basic LSTM/XGBoost to "Winning" SOTA models.

### Selected Model Architecture: **Temporal Fusion Transformer (TFT)**
*   **Why:** outperformed LSTM in multi-horizon forecasting (2024/2025 research).
*   **Key Advantage:** "Interpretability" - TFTs provide attention weights, showing *why* a prediction was made (e.g., "70% weight on last week's rain"). This directly powers our **Explainable AI (XAI)** differentiator.
*   **Library:** `pytorch-forecasting` or Google's `temporal-fusion-transformer`.
*   **Hybrid Approach:**
    *   **TFT:** For complex, long-term price trends (1-3 months).
    *   **XGBoost:** For short-term (1-7 days) precision using immediate features (recent mandi arrivals).

## 2. Voice & Accessibility (The "Bhashini" Edge)
To truly "win", we will use **Bhashini**, the Government of India's National Language Mission API.
*   **Why:** It's a government initiative (major brownie points in a national competition) and supports 22 Indian languages with native Indian accents.
*   **Integration:**
    *   **ASR (Speech-to-Text):** Bhashini ASR API (real-time streaming).
    *   **Translation:** Bhashini NMT (Neural Machine Translation) to convert query to English for processing.
    *   **TTS (Text-to-Speech):** Bhashini TTS to read back the price in the farmer's dialect.
*   **Backup:** OpenAI Whisper (if Bhashini API has latency/access issues during dev).

## 3. Data Source Validation
*   **Agmarknet:**
    *   *Status:* Validated. Over 300 commodities.
    *   *Access:* Open Government Data (OGD) API or direct portal scraping (HTML tables are standard).
*   **Sentinel-2 (Satellite):**
    *   *Status:* Validated. 10m resolution (Red/NIR bands) is perfect for NDVI (Crop Health).
    *   *Access:* `sentinehub-py` or `copernicus` open access hub.
    *   *Frequency:* 5-day revisit cycle (good for weekly crop health updates).

## 4. WhatsApp Integration
*   **Platform:** **Twilio** Sandbox for WhatsApp (easiest for hackathon/competition demo).
*   **Workflow:**
    1.  Farmer sends "Hi" -> Bot replies "Select Language/Crop".
    2.  Farmer sends " Potato Lucknow" -> Bot hits our FastAPI backend -> Returns current price + Forecast curve image.

## 5. Final Stack Recommendation
*   **ML:** PyTorch Forecasting (TFT), XGBoost.
*   **Voice:** Bhashini API (via Python `requests`).
*   **Backend:** FastAPI (Async is crucial for model inference + API calls).
*   **DB:** PostgreSQL + PostGIS (for "Nearest Mandi" logic).
