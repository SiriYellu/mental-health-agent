# 🌿 CalmCompass

**A privacy-first mental health check-in. Two choices: 2-Minute Check-In or Support Now (60 seconds).**

Every user gets: **1 understanding** (empathetic, non-clinical) · **1 action** (one small step) · **1 reassurance** · **1 support option** (988, Crisis Text Line + “not a substitute for care”).

**Privacy:** We do not store your data. Inputs are processed to generate your response and are not saved. When you use the app (including on Streamlit Cloud), nothing is sent to third parties; optional “save this session for export” keeps data only in your browser tab.

---

## Value proposition

- **Fast** — Land on two buttons. Check-in is PHQ-2 + GAD-2 (4 questions) and one optional safety question. Support Now skips everything and goes straight to breathing + grounding + resources.
- **Clear** — One understanding line, one immediate action, two optional next steps. No clinical jargon.
- **Private** — No server storage. No tracking. Optional “save this session for export” keeps data only in this browser tab; “Clear session data” wipes it.
- **Safe** — Optional question: “Are you having thoughts of harming yourself today?” If you answer Yes, you see only the crisis panel (988, Crisis Text Line, 911) and grounding. No other content.

**Who it’s for:** Anyone who wants a quick signal about mood and worry and one clear next step.

**What we don’t do:** We don’t diagnose, don’t match you to a therapist, and don’t replace a doctor or therapist.

---

## Safety disclaimer

This tool is for awareness and guidance only. It does **not** provide a diagnosis or treatment. If you are in crisis or having thoughts of self-harm, please contact **988** (US, call or text) or your local crisis line. If you are in immediate danger, call 911 or your local emergency number. **This is not a substitute for professional care.**

---

## Features

| Feature | Description |
|--------|-------------|
| **Landing** | Two buttons: “2-Minute Check-In” and “Support Now (60 seconds)”. Optional “Save this session for export” and “Clear session data”. |
| **Support Now** | 60-second breathing (4-7-8), 30-second grounding (5-4-3-2-1), crisis resources (988, Crisis Text Line). No screening. |
| **Check-In** | PHQ-2 (mood) + GAD-2 (worry) → optional self-harm question → results. Partial scoring: if you skip one item, we score from the other and show “based on 1/2 answers” + a short note. |
| **4 outputs** | One understanding line, one immediate action, one reassurance line, one support option (988 + CTL + not a substitute). |
| **Crisis path** | If you answer Yes to “thoughts of harming yourself today”, only crisis panel + grounding + support + Back to home. |
| **Suggestion engine** | Severity (from PHQ-2/GAD-2) + optional context → one action + two next steps. Mappings live in `resources.py` (no hardcoding in app). |
| **Download summary** | Plain-text export: date/time, answers (no PII), scores, chosen action, next steps, resources. |
| **Optional: go deeper** | Expander: full PHQ-9, GAD-7, context (sleep, social, workload, activity), one-sentence feeling. ML emotion model (DistilBERT) can tailor the understanding and action; set `DISABLE_ML=1` to skip the model (e.g. on memory-limited Streamlit Cloud). “Update suggestions” refines action and next steps. |
| **Accessibility** | High-contrast theme, “Prefer not to answer” on questions, short sentences. |

---

## Screenshots

<!-- Replace with real screenshots when you have them -->

| Landing | Support Now | Check-In results |
|--------|-------------|------------------|
| *[Screenshot: two buttons + disclaimer]* | *[Screenshot: breathing + grounding + 988]* | *[Screenshot: 4 blocks + download]* |

---

## Run it locally

```bash
git clone https://github.com/SiriYellu/mental-health-agent.git
cd mental-health-agent
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
streamlit run app.py
```

Open the URL (e.g. http://localhost:8501). Optional: copy `env.example` to `.env` and set `OPENAI_API_KEY` for an AI-enhanced coping plan in “go deeper”; nothing is sent except anonymized summary.

**Streamlit Cloud:** Deploy by connecting your GitHub repo; point to `app.py`. First run may take a minute (emotion model download ~250MB).

**Model size escape hatch:** If the app runs out of memory or model download fails, set **`DISABLE_ML=1`** in Streamlit Cloud (App settings → Secrets/environment variables). The app will skip loading the emotion model and always use rule-based suggestions. You can also remove `transformers`, `torch`, and `accelerate` from `requirements.txt` for a lighter deploy.

### Deployment checklist
1. Push to GitHub: `requirements.txt`, `ml/`, `app.py`, `screening.py`, `resources.py`, `tests/`.
2. In [Streamlit Community Cloud](https://share.streamlit.io/): **New app** → connect repo `SiriYellu/mental-health-agent` → Branch: `main` → Main file: `app.py`.
3. (Optional) Set `DISABLE_ML=1` in app settings if you hit memory limits.
4. After launch: run “go deeper” → enter one sentence → confirm tailored output or “Using general suggestions” fallback.

---

## Project layout

| File | Purpose |
|------|--------|
| `app.py` | Streamlit UI: landing (2 buttons), Support Now, Check-In (PHQ-2 → GAD-2 → self-harm → 4 outputs), crisis-only path, expander “go deeper”, download, session opt-in / Clear data. Cached ML emotion model when “one sentence” is used. |
| `ml/inference.py` | Lightweight emotion classifier (HuggingFace DistilBERT). Cached load; no external API; no storage. Maps emotion → understanding + action. |
| `screening.py` | PHQ-2/9, GAD-2/7, PSS-4; scoring; interpretations |
| `resources.py` | Suggestion engine (SUGGESTION_ENGINE, get_suggestion), crisis text, grounding, coping plan, talk-to-someone drafts |
| `context.py` | Context questions (sleep, social, workload, activity); feeling-today options |
| `emotion.py` | One-sentence feeling → emotion + one action (keyword-based) |
| `plan_generator.py` | Optional OpenAI coping plan (env only) |
| `resources/us.json` | US crisis lines (988, Crisis Text Line) |
| `tests/test_inference.py` | Tests: state mapping, empty text, low-confidence fallback |

---

## References (inspiration, not code reuse)

- [MindEase](https://github.com/PoyBoi/MindEase) — AI mental health counsellor; we do not diagnose or use their stack; we share the goal of low-barrier, anonymous support.
- [EmoAgent](https://github.com/1akaman/EmoAgent) — Evaluates mental health safety in AI conversations; uses PHQ-9 and related tools. We use validated instruments (PHQ-2/9, GAD-2/7) for screening only and do not train models.

---

## Push to GitHub and deploy

From your project folder (with code ready):

```bash
git add .
git status   # ensure .env is not listed
git commit -m "CalmCompass: check-in, partial scoring, ML emotion, DISABLE_ML, tests"
git remote add origin https://github.com/SiriYellu/mental-health-agent.git
git branch -M main
git push -u origin main
```

If the repo already has a remote, use `git push` instead of adding the remote again.

Then in **[Streamlit Community Cloud](https://share.streamlit.io/)**: New app → connect **SiriYellu/mental-health-agent** → Main file: **app.py**. Optional: add env var **DISABLE_ML** = **1** if the app hits memory limits.

---

## License

Use and adapt as you like. Keep the safety disclaimer and crisis resources visible when you share.
