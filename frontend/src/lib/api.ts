/**
 * API Client with retry logic and error handling
 * Implements exponential backoff for 5xx errors
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://13.53.186.103/api';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // ms
const REQUEST_TIMEOUT = 30000; // 30 seconds

interface DiagnosisResult {
  disease_name: string;
  confidence: number;
  treatment: string;
  severity: string;
  image_url?: string;
  s3_key?: string;
  timestamp?: string;
}

interface VoiceQueryResult {
  query: string;
  response: string;
  audio: string;
  language: string;
  session_id?: string;
}

interface ForecastResult {
  predicted_price: number;
  confidence_lower: number;
  confidence_upper: number;
  horizon_days: number;
  explanation?: any;
}

/**
 * Fetch with retry logic and exponential backoff
 */
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  retries = MAX_RETRIES
): Promise<Response> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Retry on 5xx errors
    if (!response.ok && retries > 0 && response.status >= 500) {
      const delay = RETRY_DELAY * (MAX_RETRIES - retries + 1);
      console.log(`Retrying request after ${delay}ms (${retries} retries left)`);
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1);
    }

    return response;
  } catch (error) {
    // Retry on network errors
    if (retries > 0) {
      const delay = RETRY_DELAY * (MAX_RETRIES - retries + 1);
      console.log(`Retrying request after ${delay}ms (${retries} retries left)`);
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1);
    }
    throw error;
  }
}

/**
 * Diagnose plant disease from image
 */
export async function diagnosePlant(imageFile: File): Promise<DiagnosisResult> {
  const formData = new FormData();
  formData.append('file', imageFile);

  const response = await fetchWithRetry(
    `${API_BASE_URL}/diseases/diagnose`,
    {
      method: 'POST',
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Disease diagnosis failed' }));
    throw new Error(error.detail || 'Disease diagnosis failed');
  }

  return response.json();
}

/**
 * Process voice query
 */
export async function processVoiceQuery(
  audioBlob: Blob,
  language: string = 'hi-IN'
): Promise<VoiceQueryResult> {
  const formData = new FormData();
  formData.append('file', audioBlob, 'audio.wav');
  formData.append('language', language);

  const response = await fetchWithRetry(
    `${API_BASE_URL}/voice/query`,
    {
      method: 'POST',
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Voice query failed' }));
    throw new Error(error.detail || 'Voice query failed');
  }

  return response.json();
}

/**
 * Process text voice query (for web speech recognition)
 */
export async function processTextVoiceQuery(
  text: string,
  language: string = 'hi-IN'
): Promise<VoiceQueryResult> {
  const response = await fetchWithRetry(
    `${API_BASE_URL}/voice/text`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, language }),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Text voice query failed' }));
    throw new Error(error.detail || 'Text voice query failed');
  }

  return response.json();
}

/**
 * Get price forecast
 */
export async function getPriceForecast(
  commodityId: number,
  mandiId: number,
  horizonDays: number = 7
): Promise<ForecastResult> {
  const response = await fetchWithRetry(
    `${API_BASE_URL}/forecasts/${commodityId}/${mandiId}?horizon_days=${horizonDays}`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Forecast failed' }));
    throw new Error(error.detail || 'Forecast failed');
  }

  return response.json();
}

/**
 * Get commodities list
 */
export async function getCommodities(): Promise<any[]> {
  const response = await fetchWithRetry(
    `${API_BASE_URL}/commodities`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch commodities');
  }

  return response.json();
}

/**
 * Get mandis list
 */
export async function getMandis(): Promise<any[]> {
  const response = await fetchWithRetry(
    `${API_BASE_URL}/mandis`,
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to fetch mandis');
  }

  return response.json();
}

export { API_BASE_URL };
