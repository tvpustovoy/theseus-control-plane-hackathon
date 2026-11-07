#!/usr/bin/env python3
"""Build voice-over, scene timings and subtitles for the Theseus 60 s video. Setu.Hackathon, 07.11.2026.

Usage:  cortex secret run --map gemini_api_key=GEMINI_API_KEY -- python3 build.py [--voice Kore] [--tempo 1.12]

1. Synthesizes missing lines with Gemini 3.8 Flash TTS (tts.synth) into out/<id>.wav (existing files are kept).
2. Speeds every line up by --tempo (ffmpeg atempo, pitch preserved) into out/<id>.fast.wav.
3. Places lines back to back with short gaps; each scene starts 0.3 s before its line.
4. Mixes ../assets/voiceover.wav (60 s) and rewrites in ../index.html: scene data-start/data-duration, the SCENES
   block for GSAP, and sentence-level subtitles for the screen scenes (the same words the voice reads, TTS tags removed).
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from tts import synth, dur  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "out"
INDEX = HERE.parent / "index.html"
DUR = 60.0
GAP = 0.4
EXTRA = {"03_culture": 0.3, "04_drift": 0.3, "06_decision": 0.3, "07_outcome": 0.3}

# (id, scene element id, style, text)
LINES = [
    ("01_opening", "s0", "calm, thoughtful documentary narrator",
     "Your AI-native organization changes every hour. <short pause> How do you notice it's no longer what you intended?"),
    ("02_commit", "s1", "warm, confident, unhurried",
     "Theseus starts with a commitment: your goals, your principles, and the culture to protect."),
    ("02b_thesis", "sT", "confident, brisk, a little faster than usual",
     "From then on, hundreds of agents and people work at once. <short pause> And you NO LONGER have to watch them by reading hundreds of chats."),
    ("03_culture", "s2", "attentive, clear",
     "It watches what agents and people actually do."),
    ("04_drift", "s3", "focused, slightly serious",
     "And shows you where behavior drifts from what you committed to."),
    ("05_correction", "s4", "clear, practical",
     "It proposes one fix on three levels: agent rules, people's onboarding, and the environment itself."),
    ("06_decision", "s5", "calm, decisive",
     "You approve. <short pause> Checks run. <short pause> The new rule applies."),
    ("07_outcome", "s6", "assured",
     "Then it tracks whether the change actually worked."),
    ("08_close", "s7", "warm, uplifting, finishing strong",
     "Let AI employees improve your company. <short pause> Keep your goals, rules, and culture."),
    ("09_tech", "tech", "friendly, matter-of-fact",
     "Built with Gemini, Meta, Sub Q, Fetch AI, and MongoDB."),
]
SUB_SCENES = {"s1", "sT", "s2", "s3", "s4", "s5", "s6"}  # opening, close and tools slide keep their own big text
CAPTION_FIX = {"Sub Q": "SubQ", "Fetch AI": "Fetch.ai", "NO LONGER": "no longer"}


def clean(text):
    t = re.sub(r"<[^>]+>", "", text)
    for a, b in CAPTION_FIX.items():
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def chunks(text):
    parts = re.split(r"(?<=[.?!])\s+", clean(text))
    out = []
    for p in parts:
        if len(p) > 72 and ":" in p:
            a, b = p.split(":", 1)
            out += [a + ":", b.strip()]
        else:
            out.append(p)
    return [p for p in out if p]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default="Kore")
    ap.add_argument("--tempo", type=float, default=1.12)
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    key = os.environ.get("GEMINI_API_KEY")
    timeline, t = [], 0.5
    for lid, scene, style, text in LINES:
        raw = OUT / f"{lid}.wav"
        if not raw.exists():
            if not key:
                sys.exit("Set GEMINI_API_KEY to synthesize " + lid)
            raw.write_bytes(synth(text, style, a.voice, key)); time.sleep(2)
        fast = OUT / f"{lid}.fast.wav"
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw), "-filter:a", f"atempo={a.tempo}", str(fast)])
        d = dur(fast)
        timeline.append({"id": lid, "scene": scene, "start": round(t, 2), "dur": round(d, 2), "text": text})
        t += d + GAP + EXTRA.get(lid, 0)
    end = timeline[-1]["start"] + timeline[-1]["dur"]
    if end > DUR - 0.2:
        sys.exit(f"Voice ends at {end:.2f}s, over {DUR}s: raise --tempo or shorten lines")
    # scenes
    scenes = []
    for i, ln in enumerate(timeline):
        s0 = 0.0 if i == 0 else round(ln["start"] - 0.3, 2)
        s1 = DUR if i == len(timeline) - 1 else round(timeline[i + 1]["start"] - 0.3, 2)
        scenes.append({"id": ln["scene"], "start": s0, "dur": round(s1 - s0, 2)})
    tech = scenes[-1]
    if tech["dur"] < 5:
        sys.exit(f"Tools slide only {tech['dur']}s; owner asked for at least 5 s")
    # mix
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for ln in timeline:
        cmd += ["-i", str(OUT / f"{ln['id']}.fast.wav")]
    delays = "".join(f"[{i}]adelay={int(ln['start']*1000)}|{int(ln['start']*1000)}[d{i}];" for i, ln in enumerate(timeline))
    mix = "".join(f"[d{i}]" for i in range(len(timeline)))
    cmd += ["-filter_complex", f"{delays}{mix}amix=inputs={len(timeline)}:normalize=0,apad=whole_dur={int(DUR)},loudnorm=I=-16[a]",
            "-map", "[a]", "-t", str(int(DUR)), "-ar", "48000", str(HERE.parent / "assets" / "voiceover.wav")]
    subprocess.check_call(cmd)
    # subtitles: split each line's time over its sentences by character share
    caps = []
    for ln in timeline:
        if ln["scene"] not in SUB_SCENES:
            continue
        cs = chunks(ln["text"]); total = sum(len(c) for c in cs); t0 = ln["start"]
        for c in cs:
            d = ln["dur"] * len(c) / total
            caps.append((round(t0, 2), round(d + 0.15, 2), c)); t0 += d
    html = INDEX.read_text()
    for sc in scenes:
        html, n = re.subn(r'(id="%s" class="[^"]*clip[^"]*"[^>]*?data-start=")[0-9.]+(" data-duration=")[0-9.]+' % sc["id"],
                          r"\g<1>%s\g<2>%s" % (sc["start"], sc["dur"]), html)
        if n != 1:
            sys.exit("scene not found in index.html: " + sc["id"])
    block = "\n".join(f'        <div class="cap clip" data-start="{s}" data-duration="{d}" data-track-index="{5 + i % 2}"><span>{c}</span></div>'
                      for i, (s, d, c) in enumerate(caps))
    html = re.sub(r"<!--CAPS-->.*?<!--/CAPS-->", "<!--CAPS-->\n" + block + "\n        <!--/CAPS-->", html, flags=re.S)
    html = re.sub(r"/\*SCENES\*/.*?/\*/SCENES\*/", "/*SCENES*/ " + json.dumps(scenes) + " /*/SCENES*/", html, flags=re.S)
    INDEX.write_text(html)
    for ln in timeline:
        print(f"{ln['id']:14} start={ln['start']:6.2f} dur={ln['dur']:5.2f}")
    print(f"voice ends {end:.2f}s · tools slide {tech['start']}–60 s ({tech['dur']} s) · {len(caps)} subtitles")


if __name__ == "__main__":
    main()
