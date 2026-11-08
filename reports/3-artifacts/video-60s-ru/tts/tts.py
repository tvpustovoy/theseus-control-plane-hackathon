#!/usr/bin/env python3
"""Gemini TTS voice-over for the Theseus 60 s video (REST, stdlib only). Adapted from the Frosty video script
(~/Projects/anthropic-snowflake-hackathon/video/tts/tts.py). Setu.Hackathon, 07.11.2026.

Usage:  cortex secret run --map gemini_api_key=GEMINI_API_KEY -- python3 tts.py [--voice Kore]
Output: out/<id>.wav per line (existing files are kept) + ../assets/voiceover.wav placed on a 60 s track.
"""
import argparse, base64, json, os, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

MODEL = "gemini-3.8-flash-tts"
URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
HERE = Path(__file__).parent
OUT = HERE / "out"
DUR = 60

# (id, start_sec, style, text) — timings follow index.html scenes
SCRIPT = [
    ("01_opening", 0.5, "calm, thoughtful documentary narrator",
     "Your AI-native organization changes every hour. <short pause> How do you notice it's no longer what you intended?"),
    ("02_commit", 9.6, "warm, confident, unhurried",
     "Theseus starts with a commitment: your goals, your principles, and the culture to protect."),
    ("03_culture", 17.85, "attentive, clear",
     "It watches what agents and people actually do."),
    ("04_drift", 22.6, "focused, slightly serious",
     "And shows you where behavior drifts from what you committed to."),
    ("05_correction", 28.5, "clear, practical",
     "It proposes one fix on three levels: agent rules, people's onboarding, and the environment itself."),
    ("06_decision", 36.45, "calm, decisive",
     "You approve. <short pause> Checks run. <short pause> The new rule applies."),
    ("07_outcome", 42.3, "assured",
     "Then it tracks whether the change actually worked."),
    ("08_close", 46.8, "warm, uplifting, finishing strong",
     "Let AI employees improve your company. <short pause> Keep your goals, rules, and culture."),
    ("09_tech", 53.5, "friendly, matter-of-fact",
     "Built with Gemini, Meta, Sub Q, Fetch AI, and MongoDB."),
]


def synth(text, style, voice, key):
    body = {"model": MODEL,
            "input": [{"type": "user_input", "content": [{"type": "text", "text": text,
                       "annotations": [{"type": "speech_metadata", "style": style}]}]}],
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": voice}]}}
    for attempt in range(6):
        req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                resp = json.load(r)
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400]
            if e.code == 429 and attempt < 5:
                print("429, waiting 25 s", flush=True); time.sleep(25); continue
            sys.exit(f"HTTP {e.code}: {msg}")
    for step in resp.get("steps", []):
        for c in step.get("content", []) or []:
            if c.get("type") == "audio" and c.get("data"):
                return base64.b64decode(c["data"])
    sys.exit("No audio in response: " + json.dumps(resp)[:400])


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "default=nw=1:nk=1", str(p)]).decode().strip())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--voice", default="Kore"); a = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY") or sys.exit("Set GEMINI_API_KEY")
    OUT.mkdir(exist_ok=True)
    files = []
    for i, (lid, start, style, text) in enumerate(SCRIPT):
        p = OUT / f"{lid}.wav"
        if not p.exists():
            p.write_bytes(synth(text, style, a.voice, key))
            if i < len(SCRIPT) - 1:
                time.sleep(2)
        nxt = SCRIPT[i + 1][1] if i + 1 < len(SCRIPT) else DUR
        d = dur(p)
        print(f"ok {lid} start={start} dur={d:.2f} slot={nxt - start:.1f}{'  OVERRUN' if start + d > nxt - 0.2 else ''}", flush=True)
        files.append((p, start))
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for p, _ in files:
        cmd += ["-i", str(p)]
    delays = "".join(f"[{i}]adelay={int(s*1000)}|{int(s*1000)}[d{i}];" for i, (_, s) in enumerate(files))
    mix = "".join(f"[d{i}]" for i in range(len(files)))
    out = HERE.parent / "assets" / "voiceover.wav"
    cmd += ["-filter_complex", f"{delays}{mix}amix=inputs={len(files)}:normalize=0,apad=whole_dur={DUR},loudnorm=I=-16[a]",
            "-map", "[a]", "-t", str(DUR), "-ar", "48000", str(out)]
    subprocess.check_call(cmd)
    print("voiceover", out, f"{dur(out):.2f}s")


if __name__ == "__main__":
    main()
