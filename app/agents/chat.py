"""Chat agent — multi-turn conversation about a specific paper.

Uses Gemini to answer questions about a paper, grounded in its full text
or abstract. Conversation history is passed in for context.
"""

import os

from google import genai

SYSTEM_PROMPT = """\
You help a student understand a research paper. You have the paper text below.

Rules:
- Answer ONLY what was asked. Do not elaborate beyond the question.
- Use short, simple sentences a university student can follow.
- Keep answers to 2-4 sentences unless more detail is specifically requested.
- If the paper doesn't cover something, say so in one sentence.
- No bullet points or headings unless the user asks for a list.
- No filler, no introductions, no "Great question!" — go straight to the answer.
"""

MAX_MESSAGES = 20  # Hard limit — 10 back-and-forth exchanges


async def chat(
    paper_text: str,
    history: list[dict[str, str]],
    user_message: str,
) -> str | None:
    """Send a message to the chat agent with paper context and conversation history.

    Args:
        paper_text: Full paper text or abstract.
        history: List of {"role": "user"|"assistant", "message": "..."} dicts.
        user_message: The new user message.

    Returns:
        Assistant response string, or None if the call fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        # Build Gemini contents: paper context, then conversation history, then new message
        contents = []

        # Paper context as first user message
        contents.append({
            "role": "user",
            "parts": [{"text": f"Here is the paper text:\n\n{paper_text}"}],
        })
        contents.append({
            "role": "model",
            "parts": [{"text": "I've read the paper. What would you like to know?"}],
        })

        # Conversation history
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg["message"]}],
            })

        # New user message
        contents.append({
            "role": "user",
            "parts": [{"text": user_message}],
        })

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
            ),
        )
        return response.text.strip()

    except Exception:
        return None
