from app.models.criteria import Criterion


DEFAULT_CRITERIA = [
    Criterion(
        id="problem_understanding",
        name="Problem Understanding",
        definition="Versteht das Proposal das Kundenproblem?",
        anchor_low="Generische Floskeln, kein Bezug zum konkreten Problem",
        anchor_high="Präzise Beschreibung des spezifischen Kundenkontexts",
    ),

    Criterion(
        id="scope_deliverables",
        name="Scope & Deliverables Clarity",
        definition="Sind Leistungen konkret benannt?",
        anchor_low="Vage Feature-Liste ohne Substanz",
        anchor_high="Klar abgegrenzte, konkrete Deliverables",
    ),

    Criterion(
        id="pricing_clarity",
        name="Pricing Clarity",
        definition="Ist die Preisgestaltung klar kommuniziert?",
        anchor_low="Komplett aufgeschoben",
        anchor_high="Klare Zahlen oder Preisstruktur",
    ),

    Criterion(
        id="timeline_clarity",
        name="Timeline Clarity",
        definition="Sind Termine und Meilensteine konkret benannt?",
        anchor_low="Keine Daten oder Meilensteine",
        anchor_high="Konkrete Termine und Meilensteine",
    ),

    Criterion(
        id="completeness",
        name="Completeness",
        definition="Wirkt das Proposal vollständig?",
        anchor_low="Offensichtliche Lücken",
        anchor_high="Wirkt vollständig",
    ),

    Criterion(
        id="tone_persuasiveness",
        name="Tone & Persuasiveness",
        definition="Ist der Ton überzeugend und zugeschnitten?",
        anchor_low="Generisches Boilerplate",
        anchor_high="Zugeschnitten und überzeugend",
    ),

    Criterion(
        id="risk_transparency",
        name="Risk/Assumptions Transparency",
        definition="Werden Risiken und Annahmen offengelegt?",
        anchor_low="Nichts offengelegt",
        anchor_high="Risiken und Annahmen klar benannt",
    ),
]