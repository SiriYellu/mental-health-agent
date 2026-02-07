"""
Optional AI-generated coping plan. Only runs if OPENAI_API_KEY is set in .env.
Uses minimal, anonymized context (no names, no detailed history).
"""

import os

def get_coping_plan_enhanced(hardest: str | None, phq2_level: str, gad2_level: str) -> str | None:
    """
    If OPENAI_API_KEY is set, ask for a short, kind coping plan.
    Otherwise return None (app uses static plan).
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        context = f"Mood check-in result: {phq2_level}. Anxiety check-in result: {gad2_level}."
        if hardest:
            context += f" The person said the hardest area right now is: {hardest}."
        prompt = (
            "You are a supportive, brief mental-health assistant. Based only on this anonymized check-in summary, "
            "write a short, kind 1-page coping plan in plain language. Include: (1) 2-3 triggers to watch for, "
            "(2) 2-3 early warning signs, (3) 3 simple coping tools, (4) a reminder to list 2 people to contact, "
            "(5) when to seek professional help or call 988. Do not diagnose. Keep it under 300 words. "
            "Summary: " + context
        )
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        if r.choices and r.choices[0].message.content:
            return r.choices[0].message.content.strip()
    except Exception:
        pass
    return None
