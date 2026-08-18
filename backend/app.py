import os
import random

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())
client = anthropic.Anthropic(api_key=os.environ["Mandarin_speakers_learn_phrases"])

MODEL = "claude-haiku-4-5"

PHRASES = [
    {
        "id": "figure_out",
        "phrase": "figure out",
        "meaning": "to understand or solve something",
        "dialogue": [
            ("A", "I need to figure out what's going on with this bill."),
            ("B", "Yeah, it's confusing — let's look into it together."),
        ],
    },
    {
        "id": "look_into",
        "phrase": "look into",
        "meaning": "to investigate or examine something",
        "dialogue": [
            ("A", "Can you look into why the server keeps crashing?"),
            ("B", "Sure, I'll check the logs and get back to you."),
        ],
    },
    {
        "id": "come_up_with",
        "phrase": "come up with",
        "meaning": "to think of or produce an idea or plan",
        "dialogue": [
            ("A", "We need to come up with a new marketing plan by Friday."),
            ("B", "Let's brainstorm some ideas this afternoon."),
        ],
    },
    {
        "id": "run_into",
        "phrase": "run into",
        "meaning": "to meet someone unexpectedly, or to encounter a problem",
        "dialogue": [
            ("A", "I ran into my old roommate at the grocery store yesterday."),
            ("B", "No way — small world!"),
        ],
    },
    {
        "id": "put_off",
        "phrase": "put off",
        "meaning": "to postpone or delay something",
        "dialogue": [
            ("A", "I keep putting off my dentist appointment."),
            ("B", "You should just book it before it gets worse."),
        ],
    },
]

PHRASES_BY_ID = {p["id"]: p for p in PHRASES}


@app.route("/")
def index():
    return render_template("index.html", phrases=PHRASES)


@app.route("/api/discrimination/new", methods=["POST"])
def discrimination_new():
    data = request.get_json(silent=True) or {}
    seen_ids = [i for i in data.get("seen_ids", []) if i in PHRASES_BY_ID]

    if len(seen_ids) < 2:
        return jsonify({"error": "Not enough phrases learned yet."}), 400

    target_id = random.choice(seen_ids)
    target = PHRASES_BY_ID[target_id]

    prompt = (
        f"Write one short, natural sentence or two-sentence scenario (under 30 words) "
        f"describing a situation where someone would want to say they need to "
        f"'{target['meaning']}'. Do not use the phrase '{target['phrase']}' or any "
        f"part of it anywhere in your response. Reply with only the sentence, no preamble."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.RateLimitError:
        return jsonify({"error": "Rate limited - please wait a moment and try again."}), 429
    except anthropic.APIStatusError as e:
        return jsonify({"error": f"API error: {e.message}"}), 502
    except anthropic.APIConnectionError:
        return jsonify({"error": "Network error connecting to Claude API."}), 502

    sentence = next((block.text for block in response.content if block.type == "text"), "")

    session["discrimination_target"] = target_id

    options = [{"id": i, "phrase": PHRASES_BY_ID[i]["phrase"]} for i in seen_ids]
    random.shuffle(options)

    return jsonify({"sentence": sentence, "options": options})


@app.route("/api/discrimination/check", methods=["POST"])
def discrimination_check():
    data = request.get_json(silent=True) or {}
    selected_id = data.get("selected_id")

    target_id = session.pop("discrimination_target", None)
    if not target_id:
        return jsonify({"error": "No active round - start a new one."}), 400

    target = PHRASES_BY_ID[target_id]

    return jsonify({
        "correct": selected_id == target_id,
        "correct_phrase": target["phrase"],
        "meaning": target["meaning"],
    })


if __name__ == "__main__":
    app.run(debug=True)
