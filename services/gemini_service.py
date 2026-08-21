"""
Gemini API service.

Wraps all calls to Google's Gemini API for:
  - Quiz question generation
  - Interview question generation
  - Interview answer evaluation

If no GEMINI_API_KEY is configured, each function falls back to a locally
generated mock response so the app remains usable as a demo. When a key is
configured, Gemini errors are reported instead of being hidden by demo data.
"""
import json
import re
import random
from flask import current_app

_client = None
_client_key = None


class GeminiServiceError(RuntimeError):
    """A Gemini request failed after the app was configured with an API key."""


def _get_client():
    """Lazily build a google-genai Client, return (client, model_name) or (None, None)."""
    global _client, _client_key
    api_key = (current_app.config.get('GEMINI_API_KEY') or '').strip()
    if not api_key:
        current_app.logger.warning("GEMINI_API_KEY is not set; using fallback demo content.")
        return None, None
    try:
        from google import genai
        if _client is None or _client_key != api_key:
            _client = genai.Client(api_key=api_key)
            _client_key = api_key
        model_name = (current_app.config.get('GEMINI_MODEL') or 'gemini-3.6-flash').strip()
        return _client, model_name
    except Exception as exc:
        current_app.logger.exception("Failed to initialize google-genai client.")
        raise GeminiServiceError(
            "Gemini could not be initialized. Verify google-genai is installed and GEMINI_API_KEY is valid."
        ) from exc


def _extract_json(text):
    """Extract the first JSON object/array found in a text blob (Gemini sometimes wraps in markdown)."""
    text = text.strip()
    text = re.sub(r'^```(json)?', '', text.strip())
    text = re.sub(r'```$', '', text.strip())
    text = text.strip()
    # Find first [ or { and matching close
    start_candidates = [i for i, c in enumerate(text) if c in '[{']
    if not start_candidates:
        raise ValueError("No JSON found in response")
    start = start_candidates[0]
    end_char = ']' if text[start] == '[' else '}'
    end = text.rfind(end_char)
    if end == -1:
        raise ValueError("No closing bracket found in response")
    return json.loads(text[start:end + 1])


def _call_gemini(prompt):
    client, model_name = _get_client()
    if client is None:
        return None
    try:
        from google.genai import types
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8192,
                response_mime_type='application/json',
            ),
        )
        text = response.text
        if not text:
            current_app.logger.warning(
                f"Gemini returned no text (possible safety block or truncation). "
                f"finish_reason(s): {[c.finish_reason for c in (response.candidates or [])]}"
            )
            raise GeminiServiceError(
                "Gemini returned an empty response. Check the server log for the finish reason."
            )
        return text
    except GeminiServiceError:
        raise
    except Exception as exc:
        current_app.logger.exception("Gemini API call failed.")
        raise GeminiServiceError(
            f"Gemini could not generate content using model '{model_name}'. "
            "Check GEMINI_API_KEY, GEMINI_MODEL, quota, and the server log."
        ) from exc


# ---------------------------------------------------------------------------
# QUIZ GENERATION
# ---------------------------------------------------------------------------

def generate_quiz_questions(topic, difficulty, num_questions):
    """
    Returns a list of dicts:
    [{question, option_a, option_b, option_c, option_d, correct_option, explanation}, ...]
    """
    prompt = f"""You are an expert quiz creator. Generate {num_questions} multiple-choice questions
about the topic "{topic}" at "{difficulty}" difficulty level.

Return ONLY valid JSON (no markdown, no commentary) as an array with this exact structure:
[
  {{
    "question": "question text here",
    "option_a": "first option",
    "option_b": "second option",
    "option_c": "third option",
    "option_d": "fourth option",
    "correct_option": "A",
    "explanation": "brief explanation of why this answer is correct"
  }}
]

Rules:
- correct_option must be exactly one of "A", "B", "C", "D"
- Make questions clear, accurate, and appropriate for {difficulty} difficulty
- Provide exactly {num_questions} questions
- Explanations should be 1-3 sentences
"""
    raw = _call_gemini(prompt)
    if raw:
        try:
            data = _extract_json(raw)
            questions = _normalize_quiz_questions(data)
            if len(questions) > 0:
                return questions[:num_questions]
        except Exception as exc:
            current_app.logger.warning("Failed to parse Gemini quiz JSON: %s", exc)
            raise GeminiServiceError("Gemini returned invalid quiz data. Please try again.") from exc

    return _fallback_quiz_questions(topic, difficulty, num_questions)


def _normalize_quiz_questions(data):
    normalized = []
    for item in data:
        try:
            normalized.append({
                'question': item['question'],
                'option_a': item['option_a'],
                'option_b': item['option_b'],
                'option_c': item['option_c'],
                'option_d': item['option_d'],
                'correct_option': str(item['correct_option']).strip().upper()[0],
                'explanation': item.get('explanation', ''),
            })
        except (KeyError, IndexError, TypeError):
            continue
    return normalized


def _fallback_quiz_questions(topic, difficulty, num_questions):
    """Locally generated placeholder questions used when Gemini API is unavailable."""
    questions = []
    for i in range(1, num_questions + 1):
        correct = random.choice(['A', 'B', 'C', 'D'])
        questions.append({
            'question': f"[Demo Question {i}] Which of the following best relates to '{topic}' "
                        f"at {difficulty} difficulty?",
            'option_a': f"{topic} concept A",
            'option_b': f"{topic} concept B",
            'option_c': f"{topic} concept C",
            'option_d': f"{topic} concept D",
            'correct_option': correct,
            'explanation': f"This is a demo explanation because no GEMINI_API_KEY is configured. "
                            f"Option {correct} is marked correct for demonstration purposes.",
        })
    return questions


# ---------------------------------------------------------------------------
# INTERVIEW QUESTION GENERATION
# ---------------------------------------------------------------------------

def generate_interview_questions(job_role, experience_level, num_questions):
    """Returns a list of question strings."""
    prompt = f"""You are an expert technical interviewer. Generate {num_questions} interview questions
for a "{job_role}" position, for a candidate at "{experience_level}" experience level.

Mix behavioral and technical/role-specific questions appropriate for this experience level.

Return ONLY valid JSON (no markdown, no commentary) as an array of strings:
["question 1", "question 2", ...]

Provide exactly {num_questions} questions.
"""
    raw = _call_gemini(prompt)
    if raw:
        try:
            data = _extract_json(raw)
            questions = [str(q) for q in data if str(q).strip()]
            if len(questions) > 0:
                return questions[:num_questions]
        except Exception as exc:
            current_app.logger.warning("Failed to parse Gemini interview JSON: %s", exc)
            raise GeminiServiceError("Gemini returned invalid interview data. Please try again.") from exc

    return _fallback_interview_questions(job_role, experience_level, num_questions)


def _fallback_interview_questions(job_role, experience_level, num_questions):
    templates = [
        f"Tell me about yourself and your experience relevant to the {job_role} role.",
        f"What interests you about working as a {job_role}?",
        f"Describe a challenging project you worked on and how you handled it.",
        f"What are your key technical strengths relevant to {job_role}?",
        f"How do you stay updated with the latest trends relevant to {job_role}?",
        f"Describe a time you disagreed with a teammate. How did you resolve it?",
        f"What is your approach to debugging a difficult problem?",
        f"How do you prioritize tasks when handling multiple deadlines?",
        f"Where do you see yourself in the next few years as a {job_role}?",
        f"What is your greatest professional achievement so far?",
    ]
    random.shuffle(templates)
    while len(templates) < num_questions:
        templates.append(f"[Demo Question] Describe your experience level ({experience_level}) with a key "
                          f"skill required for {job_role}.")
    return templates[:num_questions]


# ---------------------------------------------------------------------------
# INTERVIEW ANSWER EVALUATION
# ---------------------------------------------------------------------------

def evaluate_interview_answer(job_role, experience_level, question, user_answer):
    """
    Returns dict: {score (0-10 float), strengths, weaknesses, improved_answer, tips}
    """
    prompt = f"""You are an expert interview coach evaluating a candidate for a "{job_role}" position
at "{experience_level}" experience level.

Question asked: "{question}"
Candidate's answer: "{user_answer}"

Evaluate the answer and return ONLY valid JSON (no markdown, no commentary) with this exact structure:
{{
  "score": 7.5,
  "strengths": "what the candidate did well, 1-3 sentences",
  "weaknesses": "what could be improved, 1-3 sentences",
  "improved_answer": "a strong example answer to this question, 2-4 sentences",
  "tips": "actionable tips for improvement, 1-3 sentences"
}}

score must be a number between 0 and 10 (can include decimals).
If the candidate's answer is empty or says "I don't know", score should be low (0-3).
"""
    raw = _call_gemini(prompt)
    if raw:
        try:
            data = _extract_json(raw)
            return {
                'score': max(0.0, min(10.0, float(data.get('score', 0)))),
                'strengths': data.get('strengths', ''),
                'weaknesses': data.get('weaknesses', ''),
                'improved_answer': data.get('improved_answer', ''),
                'tips': data.get('tips', ''),
            }
        except Exception as exc:
            current_app.logger.warning("Failed to parse Gemini evaluation JSON: %s", exc)
            raise GeminiServiceError("Gemini returned invalid evaluation data. Please try again.") from exc

    return _fallback_evaluation(user_answer)


def _fallback_evaluation(user_answer):
    answer_len = len(user_answer.strip()) if user_answer else 0
    if answer_len == 0:
        score = 0.0
    elif answer_len < 30:
        score = 3.5
    elif answer_len < 100:
        score = 6.0
    else:
        score = 7.5
    return {
        'score': score,
        'strengths': "[Demo feedback] You provided a response covering the key points asked." if answer_len else
                     "No answer was provided.",
        'weaknesses': "[Demo feedback] Consider adding more specific examples and quantifiable results. "
                      "(This is a placeholder because GEMINI_API_KEY is not configured.)",
        'improved_answer': "[Demo] A strong answer would use the STAR method (Situation, Task, Action, "
                            "Result) and include a concrete, measurable outcome.",
        'tips': "[Demo] Practice structuring answers with a clear beginning, middle, and end. Be concise "
                "and specific.",
    }
