# 🧭 CalmCompass

**A premium, privacy-first mental health check-in.** One understanding · One action · One reassurance · One support option.

<!-- Replace with a short GIF or image: landing, Support Now, results -->

| *Hero / landing* | *Support Now (timer + grounding)* | *Check-In results (calm meter + 4 outputs)* |
|------------------|-----------------------------------|--------------------------------------------|
| *[Screenshot or GIF]* | *[Screenshot or GIF]* | *[Screenshot or GIF]* |

---

## What you'll get

- **Visually calming experience** — Soft gradient background, glass-style cards, clear step-by-step flow (Step 1 → 2 → 3), and a simple “calm meter” that reflects how much you’ve been carrying (never a diagnosis).
- **Two paths from the start** — **2-Minute Check-In** (guided: how you feel → mood & worry questions → safety question → results) or **Support Now** (60-second breathing timer, 5-4-3-2-1 grounding with checkboxes, and high-contrast crisis resources: 988, Crisis Text Line, 911).
- **One understanding, one action, one reassurance, one support** — Every result gives you exactly that, in a clean result panel, plus an optional “Start 60-second reset” and download summary.
- **Crisis-safe** — If you answer “Yes” to thoughts of self-harm, you see only the crisis panel, grounding, and a way back home. No scores, no ML, no download.
- **Private** — No storage by default. Optional “save this session for export” keeps data only in your browser tab. No external API calls for the core flow.
- **Optional ML** — In “go deeper,” one-sentence feeling can tailor suggestions (confidence-gated; fallback to general suggestions). Set `DISABLE_ML=1` on Streamlit Cloud if you need to skip the model.

---

## Safety disclaimer

This tool is for **awareness and guidance only**. It does **not** provide a diagnosis or treatment. If you are in crisis or having thoughts of self-harm, please contact **988** (US, call or text) or your local crisis line. If you are in immediate danger, call 911 or your local emergency number. **This is not a substitute for professional care.**

---

## Features

| Feature | Description |
|--------|-------------|
| **Landing** | Hero with icon and tagline; two buttons: “2-Minute Check-In” and “Support Now (60 seconds)”. Optional “Save this session for export” and “Clear session data”. |
| **Support Now** | Full-screen style card: 60-second breathing timer (visual countdown), 5-4-3-2-1 grounding with checkboxes, high-contrast crisis resources (988, CTL, 911), “Back to home”. |
| **Check-In** | Step 1: “How are you feeling?” (chips: Overwhelmed / Anxious / Low / Stressed / Numb / Okay). Step 2: PHQ-2 + GAD-2. Step 3: Safety question → results. Partial scoring and “Prefer not to answer” supported. |
| **Results** | Result panel (Understanding, One action, Reassurance, Support), calm meter, “Start 60-second reset” button, download summary, expanders: “Go deeper”, “Copy talk-to-someone message”, coping plan. |
| **Crisis path** | If self-harm = Yes: only crisis panel + grounding + Back to home (no ML, no scores, no download). |
| **Optional: go deeper** | PHQ-9, GAD-7, context, one-sentence feeling with optional ML tailoring; `DISABLE_ML=1` to skip model on Streamlit Cloud. |

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

Open the URL (e.g. http://localhost:8501). Optional: copy `env.example` to `.env` and set `OPENAI_API_KEY` for an AI-enhanced coping plan in “go deeper”.

**Streamlit Cloud:** Deploy by connecting your GitHub repo; main file: **`app.py`**. First run may take a minute (emotion model download). Set **`DISABLE_ML=1`** in app settings if you hit memory limits.

---

## Project layout

| File | Purpose |
|------|--------|
| `app.py` | Streamlit UI: global CSS (gradient, glass cards, stepper), hero, Support Now (timer, grounding, crisis panel), Check-In (feeling → PHQ-2 → GAD-2 → self-harm → results), result panel, calm meter, crisis isolation, expanders. |
| `ui/components.py` | Reusable UI: glass_card, stepper, calm_meter, breathing_timer_placeholder, grounding_checkboxes. |
| `screening.py` | PHQ-2/9, GAD-2/7; scoring (partial, “Prefer not to answer”); interpretations. |
| `resources.py` | Suggestion engine, crisis text, grounding, coping plan, talk-to-someone drafts. |
| `context.py` | Context questions; feeling-today options. |
| `ml/inference.py` | Emotion classifier (DistilBERT); cached; no storage. |
| `emotion.py` | Keyword-based emotion + action fallback. |
| `plan_generator.py` | Optional OpenAI coping plan (env only). |
| `resources/us.json` | US crisis lines (988, Crisis Text Line). |
| `tests/test_inference.py` | Tests for inference and suggestion logic. |

---

## Push to GitHub and deploy

```bash
git add .
git status   # ensure .env is not listed
git commit -m "CalmCompass: premium UI, stepper, calm meter, Support Now timer, crisis isolation"
git remote add origin https://github.com/SiriYellu/mental-health-agent.git
git branch -M main
git push -u origin main
```

Then in **[Streamlit Community Cloud](https://share.streamlit.io/)**: New app → connect **SiriYellu/mental-health-agent** → Branch: **main** → Main file: **app.py**. Optional: set **DISABLE_ML=1** if the app hits memory limits.

---

## License

Use and adapt as you like. Keep the safety disclaimer and crisis resources visible when you share.
