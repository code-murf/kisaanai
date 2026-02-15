"""
Run 10 end-to-end typed voice-assistant test cases against project AI flow.

Flow per case:
1) Query text -> GroqAIService.process_voice_query()
2) Response text -> GroqAIService.text_to_speech()

Additionally performs one STT smoke check using backend/test_audio.wav.
"""

import asyncio
import importlib.util
import json
import time
from pathlib import Path
from typing import Any


def load_ai_service_getter():
    """Load ai_service module directly to avoid importing app.services package init."""
    module_path = Path(__file__).resolve().parents[1] / "app" / "services" / "ai_service.py"
    spec = importlib.util.spec_from_file_location("voice_ai_service_local", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_ai_service


CASE_DEFS: list[dict[str, Any]] = [
    {
        "id": "P1",
        "type": "platform",
        "language_code": "en-IN",
        "query": (
            "What can this AgriBharat platform do for farmers? "
            "Mention mandi prices, weather, disease help, and voice support."
        ),
        "keywords": ["mandi", "price", "weather", "disease", "voice", "farm"],
        "min_hits": 3,
    },
    {
        "id": "P2",
        "type": "platform",
        "language_code": "en-IN",
        "query": (
            "I am in Maharashtra. How can I use this platform daily from morning "
            "to evening to decide selling and crop care?"
        ),
        "keywords": ["maharashtra", "sell", "mandi", "weather", "crop", "advice"],
        "min_hits": 2,
    },
    {
        "id": "P3",
        "type": "platform",
        "language_code": "hi-IN",
        "query": (
            "Is app se mandi bhaav, mausam aur fasal bimari kaise check kar sakte hain? "
            "Kadam batao."
        ),
        "keywords": ["mandi", "भाव", "mausam", "मौसम", "bimari", "रोग", "fasal"],
        "min_hits": 2,
    },
    {
        "id": "P4",
        "type": "platform",
        "language_code": "en-IN",
        "query": (
            "Give me a short workflow to ask voice questions and get audio replies "
            "in Hindi for farmers."
        ),
        "keywords": ["voice", "audio", "hindi", "question", "reply", "farmer"],
        "min_hits": 2,
    },
    {
        "id": "A1",
        "type": "agriculture",
        "language_code": "en-IN",
        "query": "Explain Kharif vs Rabi crops in India with examples and sowing windows.",
        "keywords": ["kharif", "rabi", "india", "sowing", "rice", "wheat"],
        "min_hits": 3,
    },
    {
        "id": "A2",
        "type": "agriculture",
        "language_code": "en-IN",
        "query": (
            "Current wheat MSP in India and how should farmers decide mandi sale timing?"
        ),
        "keywords": ["wheat", "msp", "india", "mandi", "sale", "price"],
        "min_hits": 3,
    },
    {
        "id": "A3",
        "type": "agriculture",
        "language_code": "hi-IN",
        "query": (
            "Punjab mein gehu mein yellow rust ke lakshan aur turant upay batao."
        ),
        "keywords": ["yellow rust", "gehu", "गेहूं", "lakshan", "उपाय", "fungicide"],
        "min_hits": 2,
    },
    {
        "id": "A4",
        "type": "agriculture",
        "language_code": "en-IN",
        "query": (
            "My cotton crop in Maharashtra has pink bollworm risk. "
            "Give integrated pest management steps."
        ),
        "keywords": ["cotton", "pink bollworm", "trap", "ipm", "spray", "monitor"],
        "min_hits": 2,
    },
    {
        "id": "A5",
        "type": "agriculture",
        "language_code": "en-IN",
        "query": (
            "For paddy in eastern India, suggest irrigation and fertilizer schedule "
            "for tillering to panicle stage."
        ),
        "keywords": ["paddy", "irrigation", "fertilizer", "tillering", "panicle", "nitrogen"],
        "min_hits": 2,
    },
    {
        "id": "A6",
        "type": "agriculture",
        "language_code": "hi-IN",
        "query": (
            "PM-KISAN aur Fasal Bima Yojana ka fayda kya hai, apply kaise karein?"
        ),
        "keywords": ["pm-kisan", "fasal bima", "yojana", "apply", "benefit", "farmer"],
        "min_hits": 2,
    },
]


def score_keywords(response: str, keywords: list[str]) -> tuple[int, list[str]]:
    text = response.lower()
    hits: list[str] = []
    for kw in keywords:
        if kw.lower() in text:
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

    out_path = Path(__file__).resolve().parents[1] / "voice_e2e_10_case_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nSummary:")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Report written to: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
