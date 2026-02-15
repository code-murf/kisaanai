"""
Run 10 harder typed voice-assistant test cases against project AI flow.

Flow per case:
1) Query text -> GroqAIService.process_voice_query()
2) Response text -> GroqAIService.text_to_speech()

Also performs STT smoke check with available local audio files.
"""

import asyncio
import importlib.util
import json
import re
import time
from pathlib import Path
from typing import Any


def load_ai_service_getter():
    module_path = Path(__file__).resolve().parents[1] / "app" / "services" / "ai_service.py"
    spec = importlib.util.spec_from_file_location("voice_ai_service_local_hard", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_ai_service


CASE_DEFS: list[dict[str, Any]] = [
    {
        "id": "H1",
        "type": "agri_timing",
        "language_code": "hi-IN",
        "query": "धान की रोपाई के बाद यूरिया पहली बार कितने दिन बाद डालना चाहिए और दूसरी बार कब?",
        "keywords": ["रोपाई", "यूरिया", "दिन", "split", "top", "धान"],
        "min_hits": 2,
    },
    {
        "id": "H2",
        "type": "agri_timing",
        "language_code": "hi-IN",
        "query": "गेहूं में पहली सिंचाई बुवाई के कितने दिन बाद करनी चाहिए? अगर ठंड ज्यादा हो तो क्या बदलना चाहिए?",
        "keywords": ["गेहूं", "पहली", "सिंचाई", "दिन", "बुवाई", "cri"],
        "min_hits": 2,
    },
    {
        "id": "H3",
        "type": "risk_decision",
        "language_code": "en-IN",
        "query": "IMD shows 70mm rain in 2 days for tomato. Should I spray fungicide now or wait? Give practical rule.",
        "keywords": ["rain", "fungicide", "spray", "wait", "window", "tomato"],
        "min_hits": 2,
    },
    {
        "id": "H4",
        "type": "nutrient_plan",
        "language_code": "en-IN",
        "query": "Soil test says low zinc and medium nitrogen in paddy. Give a 30-day nutrient plan with per-acre doses.",
        "keywords": ["zinc", "nitrogen", "paddy", "acre", "dose", "plan"],
        "min_hits": 3,
    },
    {
        "id": "H5",
        "type": "ipm_threshold",
        "language_code": "en-IN",
        "query": "Cotton pink bollworm trap count is 8 moths/night. Is threshold crossed? What should I do this week?",
        "keywords": ["cotton", "pink bollworm", "threshold", "trap", "spray", "monitor"],
        "min_hits": 2,
    },
    {
        "id": "H6",
        "type": "market_economics",
        "language_code": "en-IN",
        "query": "Onion mandi price is ₹1500/quintal. Store for 20 days or sell now? Assume 2% loss and storage cost.",
        "keywords": ["onion", "store", "sell", "loss", "cost", "price"],
        "min_hits": 3,
    },
    {
        "id": "H7",
        "type": "pest_weather",
        "language_code": "hi-IN",
        "query": "सरसों में माहू लग गया है और बारिश आने वाली है। दवा कब छिड़कूं और कितने अंतराल पर?",
        "keywords": ["माहू", "सरसों", "बारिश", "छिड़क", "अंतराल", "दवा"],
        "min_hits": 2,
    },
    {
        "id": "H8",
        "type": "water_management",
        "language_code": "en-IN",
        "query": "For drip chili in 42C heatwave, give morning-evening irrigation schedule for next 5 days.",
        "keywords": ["drip", "chili", "heatwave", "irrigation", "irrigate", "6am", "4pm", "morning", "evening"],
        "min_hits": 3,
    },
    {
        "id": "H9",
        "type": "scheme_troubleshooting",
        "language_code": "hi-IN",
        "query": "PM-KISAN installment नहीं आई, DBT pending दिखा रहा है. Step-by-step complaint process बताओ.",
        "keywords": [
            "pm-kisan", "dbt", "pending", "complaint", "portal", "helpline", "helpdesk", "email", "website",
            "शिकायत", "हेल्पलाइन", "वेबसाइट", "ईमेल", "मदद"
        ],
        "min_hits": 2,
    },
    {
        "id": "H10",
        "type": "resource_optimization",
        "language_code": "en-IN",
        "query": "I have 3 acres maize+paddy and pump runs only 2 hours/day. Optimize 7-day water allocation.",
        "keywords": ["maize", "paddy", "water", "allocation", "schedule", "priority"],
        "min_hits": 3,
    },
]


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def score_keywords(response: str, keywords: list[str]) -> tuple[int, list[str]]:
    text = _normalize_text(response)
    hits: list[str] = []
    for kw in keywords:
        if _normalize_text(kw) in text:
            hits.append(kw)
    return len(hits), hits


async def run_stt_smoke(ai_service) -> dict[str, Any]:
    backend_dir = Path(__file__).resolve().parents[1]
    root_dir = backend_dir.parent

    candidates: list[Path] = []
    primary = backend_dir / "test_audio.wav"
    if primary.exists():
        candidates.append(primary)
    candidates.extend(sorted((backend_dir / "static" / "audio").glob("*.mp3"))[:5])
    candidates.extend(sorted((root_dir / "static" / "audio").glob("*.mp3"))[:5])

    attempts: list[dict[str, Any]] = []
    for audio_path in candidates:
        ext = audio_path.suffix.lower()
        content_type = "audio/wav" if ext == ".wav" else "audio/mpeg"
        audio_bytes = audio_path.read_bytes()
        start = time.perf_counter()
        transcript = await ai_service.transcribe_audio(
            audio_content=audio_bytes,
            language_code="hi-IN",
            filename=audio_path.name,
            content_type=content_type,
        )
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        attempts.append(
            {
                "file": str(audio_path),
                "ok": bool(transcript),
                "latency_ms": latency_ms,
                "transcript_preview": (transcript or "")[:160],
            }
        )
        if transcript:
            return {
                "ok": True,
                "file": str(audio_path),
                "latency_ms": latency_ms,
                "transcript_preview": transcript[:160],
                "attempts": attempts,
            }
    return {
        "ok": False,
        "error": "No candidate audio file produced transcript",
        "attempts": attempts,
    }


async def run_case(ai_service, case: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    llm_result = await ai_service.process_voice_query(
        transcribed_text=case["query"],
        context={"location": "India"},
        language="hi" if case["language_code"].startswith("hi") else "en",
    )
    llm_ms = round((time.perf_counter() - start) * 1000, 2)

    response = llm_result.get("response") or ""
    response_ok = bool(response.strip())

    tts_start = time.perf_counter()
    tts_audio = await ai_service.text_to_speech(response, language_code=case["language_code"])
    tts_ms = round((time.perf_counter() - tts_start) * 1000, 2)

    hit_count, hit_terms = score_keywords(response, case["keywords"])
    keyword_ok = hit_count >= case["min_hits"]

    return {
        "id": case["id"],
        "type": case["type"],
        "query": case["query"],
        "response_ok": response_ok,
        "keyword_ok": keyword_ok,
        "tts_ok": bool(tts_audio),
        "hit_count": hit_count,
        "min_hits": case["min_hits"],
        "hit_terms": hit_terms,
        "llm_latency_ms": llm_ms,
        "tts_latency_ms": tts_ms,
        "response_preview": response[:220],
    }


async def main() -> None:
    get_ai_service = load_ai_service_getter()
    ai_service = get_ai_service()

    report: dict[str, Any] = {
        "suite": "hard_10",
        "stt_smoke": {},
        "cases": [],
        "summary": {},
    }

    report["stt_smoke"] = await run_stt_smoke(ai_service)

    for case in CASE_DEFS:
        result = await run_case(ai_service, case)
        report["cases"].append(result)
        print(
            f"[{result['id']}] type={result['type']} "
            f"response_ok={result['response_ok']} keyword_ok={result['keyword_ok']} "
            f"tts_ok={result['tts_ok']} hits={result['hit_count']}/{result['min_hits']} "
            f"llm_ms={result['llm_latency_ms']} tts_ms={result['tts_latency_ms']}"
        )

    total = len(report["cases"])
    response_pass = sum(1 for c in report["cases"] if c["response_ok"])
    keyword_pass = sum(1 for c in report["cases"] if c["keyword_ok"])
    tts_pass = sum(1 for c in report["cases"] if c["tts_ok"])
    full_pass = sum(
        1 for c in report["cases"] if c["response_ok"] and c["keyword_ok"] and c["tts_ok"]
    )

    report["summary"] = {
        "total_cases": total,
        "response_pass": response_pass,
        "keyword_pass": keyword_pass,
        "tts_pass": tts_pass,
        "full_pass": full_pass,
    }

    out_path = Path(__file__).resolve().parents[1] / "voice_e2e_hard_10_case_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nSummary:")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Report written to: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
