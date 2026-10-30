import os
import time

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors

# --------------------------------------------------
# 1. APP CONFIGURATION
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-flash-lite-latest"
).strip()

# Backup model used if the primary model is temporarily unavailable.
BACKUP_MODEL = os.getenv(
    "GEMINI_BACKUP_MODEL",
    "gemini-3.8-flash"
).strip()

client = genai.Client(api_key=API_KEY) if API_KEY else None


# --------------------------------------------------
# 2. COLLEGEBOT PERSONALITY AND INSTRUCTIONS
# --------------------------------------------------

SYSTEM_INSTRUCTION = """
You are CollegeBot Premium AI, a friendly, intelligent, and professional
college enquiry assistant.

YOUR RESPONSIBILITIES:
- Help students with courses, admissions, fees, scholarships, examinations,
  timetables, assignments, campus facilities, and student life.
- Explain AI, programming, computer engineering, mathematics, science,
  and other academic topics in beginner-friendly language.
- Answer general educational questions helpfully.
- Give clear, accurate, natural answers instead of generic scripted replies.
- Use headings, bullet points, and numbered steps when useful.
- Keep simple answers concise. Provide more detail when the student asks.
- Understand follow-up questions using the available conversation context.
- Never invent college-specific fees, dates, policies, course lists,
  contact details, or facilities.
- If the student has not identified their college, ask for its name when
  accurate college-specific information is required.
- If verified college information is unavailable, direct the student to
  the official college website or administration.
- Never claim to have accessed live college records or websites unless
  that information is actually provided.
- Be respectful, supportive, and professional.
- Do not repeatedly ask for information the student has already provided.
- Format answers in readable plain text or Markdown.

IMPORTANT:
You are an AI assistant. Your responses can contain errors. Encourage
students to verify important admission, fee, examination, and administrative
details with their college.
"""


# --------------------------------------------------
# 3. GEMINI RESPONSE GENERATION
# --------------------------------------------------

def generate_with_model(model_name, message):
    """Generate an answer using the specified Gemini model."""

    response = client.models.generate_content(
        model=model_name,
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
            max_output_tokens=700,
        ),
    )

    answer = (response.text or "").strip()

    if not answer:
        raise ValueError(
            f"Gemini model {model_name} returned an empty response."
        )

    return answer


def get_bot_reply(message):
    """Generate a Gemini answer with retry and backup-model handling."""

    text = (message or "").strip()

    if not text:
        return "Please type a question, and I'll do my best to help."

    if len(text) > 5000:
        return (
            "Your question is too long. Please shorten it to "
            "5,000 characters or fewer."
        )

    if client is None:
        app.logger.error("GEMINI_API_KEY is missing.")
        return (
            "CollegeBot AI is not configured. Please check your .env "
            "file and restart the application."
        )

    # Try the configured model first, followed by the backup model.
    models_to_try = [MODEL_NAME]

    if BACKUP_MODEL and BACKUP_MODEL != MODEL_NAME:
        models_to_try.append(BACKUP_MODEL)

    for model_name in models_to_try:
        # One retry for temporary server or rate-limit errors.
        for attempt in range(2):
            try:
                app.logger.info(
                    "Requesting response from model: %s",
                    model_name
                )

                answer = generate_with_model(model_name, text)

                app.logger.info(
                    "Gemini response generated successfully using %s",
                    model_name
                )

                return answer

            except errors.APIError as error:
                status_code = getattr(error, "code", None)

                app.logger.warning(
                    "Gemini API error using %s (attempt %s): %s",
                    model_name,
                    attempt + 1,
                    error
                )

                # Retry temporary errors once after a short delay.
                if status_code in (429, 500, 502, 503, 504):
                    if attempt == 0:
                        time.sleep(1)
                        continue

                    # Temporary failure: try the backup model.
                    break

                # Model not found, invalid request, or authentication
                # errors will not improve by retrying the same request.
                break

            except Exception:
                app.logger.exception(
                    "Unexpected error using Gemini model %s",
                    model_name
                )
                break

    app.logger.error(
        "All configured Gemini models failed for this request."
    )

    return (
        "I'm temporarily unable to generate an AI response. "
        "The AI service may be busy. Please wait a few seconds and "
        "send your question again."
    )


# --------------------------------------------------
# 4. HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# 5. CHAT API
# --------------------------------------------------

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    message = data.get("message", "")

    if not isinstance(message, str):
        return jsonify({
            "reply": "Please enter your question as text."
        }), 400

    message = message.strip()

    if not message:
        return jsonify({
            "reply": "Please type a question first."
        }), 400

    reply = get_bot_reply(message)

    return jsonify({
        "reply": reply
    }), 200


# --------------------------------------------------
# 6. HEALTH CHECK
# --------------------------------------------------

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "CollegeBot Premium AI",
        "ai_configured": client is not None,
        "primary_model": MODEL_NAME,
        "backup_model": BACKUP_MODEL
    })


# --------------------------------------------------
# 7. RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))

    app.run(
        host="127.0.0.1",
        port=port,
        debug=False
    )
