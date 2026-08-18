import os

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ["Mandarin_speakers_learn_phrases"])

MODEL = "claude-haiku-4-5"

SYSTEM_PROMPT = (
    "You are a friendly conversation partner helping a Mandarin-speaking English "
    "learner practice the phrasal verb \"figure out\" (meaning: to understand or "
    "solve something) in natural conversation. Lead the student through a variety "
    "of everyday scenarios and topics (e.g. work, travel, technology, relationships, "
    "hobbies) that create natural opportunities to use \"figure out\" - move on to a "
    "new scenario every few exchanges so they see the phrase used in different "
    "situations. Ask open questions that invite the student to reply using the "
    "phrase themselves. Keep replies short (2-4 sentences), warm, and conversational. "
    "If the student uses \"figure out\" correctly, briefly affirm it. If they avoid it "
    "or use it awkwardly, gently model correct usage in your reply and invite them to "
    "try again. If there is no conversation history yet, start by introducing a "
    "scenario and asking a question."
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    history = data.get("messages") or [
        {"role": "user", "content": "Let's start practicing."}
    ]

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=history,
        )
    except anthropic.RateLimitError:
        return jsonify({"error": "Rate limited - please wait a moment and try again."}), 429
    except anthropic.APIStatusError as e:
        return jsonify({"error": f"API error: {e.message}"}), 502
    except anthropic.APIConnectionError:
        return jsonify({"error": "Network error connecting to Claude API."}), 502

    reply = next((block.text for block in response.content if block.type == "text"), "")
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)
