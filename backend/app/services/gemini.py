from google import genai
from google.genai import types

from config import GOOGLE_API_KEY

from app.models.scoring import ScoringResult


client = genai.Client(
    api_key=GOOGLE_API_KEY
)


def score_proposal(
    proposal_text: str,
    criteria,
) -> ScoringResult:

    criteria_block = "\n\n".join(
        f"""
ID: {criterion.id}
Name: {criterion.name}
Definition: {criterion.definition}
1 = {criterion.anchor_low}
5 = {criterion.anchor_high}
""".strip()
        for criterion in criteria
    )

    prompt = f"""
Du bist ein erfahrener Sales-Reviewer.

Bewerte das folgende Proposal anhand der Kriterien
auf einer Skala von 1 bis 5.

KRITERIEN:

{criteria_block}

REGELN:

1. Bewerte jedes Kriterium genau einmal.
2. Verwende exakt die vorgegebenen criterion_id Werte.
3. Verwende exakt die vorgegebenen criterion_name Werte.
4. Score muss zwischen 1 und 5 liegen.
5. max_score ist immer 5.
6. Jeder Kommentar muss sich konkret auf das Proposal beziehen.
7. Erfinde keine Informationen.
8. Gib ausschließlich das definierte JSON-Format zurück.

PROPOSAL:

{proposal_text}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ScoringResult,
        ),
    )

    return ScoringResult.model_validate_json(
        response.text
    )