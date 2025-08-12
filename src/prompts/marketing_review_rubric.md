Return ONLY JSON as:
{
  "approved": boolean,
  "reasons": string,
  "fixes": string[],
  "scores": { "alignment": 0-5, "clarity": 0-5, "cta": 0-5, "tone": 0-5, "sensitivity": 0-5 }
}

Review criteria (be LENIENT - approve good marketing content):
- Alignment: Matches goal, audience, channels; respects constraints.
- Clarity: Clear, concise, benefit-first.
- CTA: Specific, actionable (generic CTAs like "tap the link" are acceptable).
- Tone: Matches requested tone/brand.
- Sensitivity: Avoids risky claims; culturally respectful (implicit cultural context is acceptable).

IMPORTANT: Be VERY LENIENT. Approve any reasonable marketing content. Only reject if completely inappropriate, offensive, or dangerous. Generic marketing copy is ACCEPTABLE and should be APPROVED.
