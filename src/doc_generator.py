"""
Document generation: cover letters and CV summaries via Anthropic API.
"""

import os
import anthropic

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def generate_cover_letter(job: dict, profile: dict) -> str:
    """Generate a tailored cover letter for a specific job."""
    client = _get_client()

    prompt = f"""Write a tailored cover letter for {profile['name']} applying for the following role.

ROLE: {job.get('title')} at {job.get('company')} ({job.get('location')})
ROLE DESCRIPTION: {job.get('summary', 'Not provided')}
TAGS / SECTOR: {', '.join(job.get('tags', []))}

CANDIDATE BACKGROUND:
{profile['background_summary']}

FULL CV:
{profile['cv_text']}

INSTRUCTIONS:
- Open with genuine enthusiasm for THIS specific company and role (not generic phrases)
- Connect Bryce's VC + medical device + commercial background directly to what this role needs
- Include 2-3 specific achievements with numbers (e.g. 59% revenue growth, board observer roles)
- Address relocation from NZ naturally and positively (immediate, no commitments)
- Mention European experience (Karolinska Institute, Synergus AB in Stockholm) if relevant
- Close confidently with a clear call to action
- Length: 350-450 words, 4 paragraphs
- Tone: warm, professional, confident — not stiff or formulaic
- Do NOT use phrases like "I am writing to express my interest" or "I believe I would be a great fit"

Start with: Dear Hiring Manager,
End with: Kind regards,\\nBryce Lowen

Output ONLY the letter body. No subject line, no address blocks."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()


def generate_cv_summary(job: dict, profile: dict) -> str:
    """Generate a tailored CV summary/highlights for a specific role."""
    client = _get_client()

    prompt = f"""Create a tailored CV profile section for {profile['name']} for the following role.

ROLE: {job.get('title')} at {job.get('company')} ({job.get('location')})
ROLE DESCRIPTION: {job.get('summary', 'Not provided')}
TAGS / SECTOR: {', '.join(job.get('tags', []))}

CANDIDATE BACKGROUND:
{profile['background_summary']}

FULL CV:
{profile['cv_text']}

OUTPUT FORMAT (plain text, ready to paste into a CV):

PROFESSIONAL PROFILE
[3-4 sentences tailored to this role. Lead with what makes Bryce uniquely suited. 
Be specific about the VC + commercial + medical device combination. Don't be generic.]

KEY HIGHLIGHTS FOR THIS ROLE
• [Most relevant achievement — include numbers]
• [Second most relevant — link to role requirements]
• [Third — sector or geography relevant point]
• [Fourth — operational or commercial strength]
• [Fifth — soft skill or leadership evidence]

WHY THIS ROLE
[2-3 sentences Bryce could use verbatim in an email or interview. Specific to this company.]

Only use experience that's in the CV — do not invent anything.
Output ONLY the formatted text above."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
