import os
import random
import sqlite3
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())
client = anthropic.Anthropic(api_key=os.environ["Mandarin_speakers_learn_phrases"])

MODEL = "claude-haiku-4-5"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "progress.db")
os.makedirs(DATA_DIR, exist_ok=True)

PHRASES = [
    {
        "id": "figure_out",
        "phrase": "figure out",
        "meaning": "to understand or solve something",
        "meaning_zh": "理解或解決某事",
        "dialogue": [
            ("A", "I need to figure out what's going on with this bill."),
            ("B", "Yeah, it's confusing — let's look into it together."),
        ],
    },
    {
        "id": "look_into",
        "phrase": "look into",
        "meaning": "to investigate or examine something",
        "meaning_zh": "調查或檢查某事",
        "dialogue": [
            ("A", "Can you look into why the server keeps crashing?"),
            ("B", "Sure, I'll check the logs and get back to you."),
        ],
    },
    {
        "id": "come_up_with",
        "phrase": "come up with",
        "meaning": "to think of or produce an idea or plan",
        "meaning_zh": "想到或提出一個想法或計畫",
        "dialogue": [
            ("A", "We need to come up with a new marketing plan by Friday."),
            ("B", "Let's brainstorm some ideas this afternoon."),
        ],
    },
    {
        "id": "run_into",
        "phrase": "run into",
        "meaning": "to meet someone unexpectedly, or to encounter a problem",
        "meaning_zh": "意外地遇見某人，或遇到問題",
        "dialogue": [
            ("A", "I always run into my old roommate at this coffee shop."),
            ("B", "No way — small world!"),
        ],
    },
    {
        "id": "put_off",
        "phrase": "put off",
        "meaning": "to postpone or delay something",
        "meaning_zh": "推遲或延後某事",
        "dialogue": [
            ("A", "I always put off my dentist appointments until they're overdue."),
            ("B", "You should just book it before it gets worse."),
        ],
    },
    {
        "id": "give_up",
        "phrase": "give up",
        "meaning": "to stop trying, to quit",
        "meaning_zh": "停止嘗試，放棄",
        "dialogue": [
            ("A", "I've been trying to solve this puzzle for an hour."),
            ("B", "Just give up — it's not worth the stress."),
        ],
    },
    {
        "id": "get_along",
        "phrase": "get along",
        "meaning": "to have a friendly relationship with someone",
        "meaning_zh": "與某人有友好的關係",
        "dialogue": [
            ("A", "How's your new roommate?"),
            ("B", "We get along really well, actually."),
        ],
    },
    {
        "id": "hang_out",
        "phrase": "hang out",
        "meaning": "to spend time relaxing or socializing",
        "meaning_zh": "花時間放鬆或社交",
        "dialogue": [
            ("A", "Want to hang out this weekend?"),
            ("B", "Sure, let's grab coffee on Saturday."),
        ],
    },
    {
        "id": "bring_up",
        "phrase": "bring up",
        "meaning": "to mention or start talking about a topic",
        "meaning_zh": "提及或開始談論某個話題",
        "dialogue": [
            ("A", "I don't want to bring up the accident again, but we need to talk about it."),
            ("B", "I know, it's hard, but we should."),
        ],
    },
    {
        "id": "break_down",
        "phrase": "break down",
        "meaning": "to stop functioning, or to lose emotional control",
        "meaning_zh": "停止運作，或失去情緒控制",
        "dialogue": [
            ("A", "My car might break down on this trip."),
            ("B", "You should get it checked before we leave."),
        ],
    },
    {
        "id": "check_in",
        "phrase": "check in",
        "meaning": "to register at a hotel or airport, or to touch base with someone",
        "meaning_zh": "在旅館或機場登記，或與某人保持聯繫",
        "dialogue": [
            ("A", "Don't forget to check in online before the flight."),
            ("B", "Already done — I got a window seat."),
        ],
    },
    {
        "id": "deal_with",
        "phrase": "deal with",
        "meaning": "to handle or take care of a problem or situation",
        "meaning_zh": "處理或解決問題或情況",
        "dialogue": [
            ("A", "I have so many complaints to deal with today."),
            ("B", "Want some help going through them?"),
        ],
    },
    {
        "id": "end_up",
        "phrase": "end up",
        "meaning": "to eventually arrive at a situation or place, often unplanned",
        "meaning_zh": "最終到達某個情況或地點，通常是計畫外的",
        "dialogue": [
            ("A", "How did you end up working in marketing?"),
            ("B", "Honestly, it was a total accident."),
        ],
    },
    {
        "id": "fill_out",
        "phrase": "fill out",
        "meaning": "to complete a form with information",
        "meaning_zh": "用信息填寫表格",
        "dialogue": [
            ("A", "Can you fill out this form before your appointment?"),
            ("B", "Sure, do you have a pen?"),
        ],
    },
    {
        "id": "get_over",
        "phrase": "get over",
        "meaning": "to recover from something, like an illness or disappointment",
        "meaning_zh": "從某事恢復，如疾病或失望",
        "dialogue": [
            ("A", "I hope you get over your cold soon."),
            ("B", "Thanks, I'm already feeling better."),
        ],
    },
    {
        "id": "hold_on",
        "phrase": "hold on",
        "meaning": "to wait a moment",
        "meaning_zh": "稍等一下",
        "dialogue": [
            ("A", "Hold on, I think I forgot my keys."),
            ("B", "No worries, take your time."),
        ],
    },
    {
        "id": "keep_up_with",
        "phrase": "keep up with",
        "meaning": "to stay at the same pace or level as someone or something",
        "meaning_zh": "與某人或某事保持同步或相同水平",
        "dialogue": [
            ("A", "It's hard to keep up with all these new phone updates."),
            ("B", "I know, they change something every month."),
        ],
    },
    {
        "id": "let_down",
        "phrase": "let down",
        "meaning": "to disappoint someone",
        "meaning_zh": "使某人失望",
        "dialogue": [
            ("A", "I never want to let down my closest friends."),
            ("B", "Everyone feels that way sometimes — you're human."),
        ],
    },
    {
        "id": "make_up",
        "phrase": "make up",
        "meaning": "to invent a story, or to reconcile after an argument",
        "meaning_zh": "編造故事，或在爭論後和解",
        "dialogue": [
            ("A", "Did you two make up after the fight?"),
            ("B", "Yeah, we talked it out last night."),
        ],
    },
    {
        "id": "pass_out",
        "phrase": "pass out",
        "meaning": "to lose consciousness, to faint",
        "meaning_zh": "失去意識，昏迷",
        "dialogue": [
            ("A", "I'm worried she might pass out from the heat during the hike."),
            ("B", "Let's bring extra water just in case."),
        ],
    },
    {
        "id": "pick_up",
        "phrase": "pick up",
        "meaning": "to learn something quickly or casually, or to collect someone or something",
        "meaning_zh": "快速或隨意地學習某事，或收集某人或某物",
        "dialogue": [
            ("A", "Where did you pick up your Spanish?"),
            ("B", "I lived in Madrid for two years."),
        ],
    },
    {
        "id": "point_out",
        "phrase": "point out",
        "meaning": "to indicate or draw attention to something",
        "meaning_zh": "指出或吸引注意某事",
        "dialogue": [
            ("A", "I just want to point out that the report has a typo."),
            ("B", "Thanks, I'll fix it now."),
        ],
    },
    {
        "id": "put_up_with",
        "phrase": "put up with",
        "meaning": "to tolerate something unpleasant",
        "meaning_zh": "容忍令人不快的事",
        "dialogue": [
            ("A", "I don't know how you put up with all that noise."),
            ("B", "You get used to it eventually."),
        ],
    },
    {
        "id": "show_up",
        "phrase": "show up",
        "meaning": "to arrive, especially at an event",
        "meaning_zh": "到達，特別是在活動中",
        "dialogue": [
            ("A", "Did everyone show up for the meeting?"),
            ("B", "Almost everyone — just two people were late."),
        ],
    },
    {
        "id": "turn_down",
        "phrase": "turn down",
        "meaning": "to reject an offer or request",
        "meaning_zh": "拒絕提議或請求",
        "dialogue": [
            ("A", "Are you really going to turn down the job offer?"),
            ("B", "Yeah, the salary was too low."),
        ],
    },
]

PHRASES_BY_ID = {p["id"]: p for p in PHRASES}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_phrases (
            phrase_id TEXT PRIMARY KEY,
            seen_at TEXT NOT NULL
        )
        """
    )
    return conn


def get_seen_ids():
    conn = get_db()
    try:
        rows = conn.execute("SELECT phrase_id FROM seen_phrases").fetchall()
    finally:
        conn.close()
    return [row[0] for row in rows if row[0] in PHRASES_BY_ID]


def mark_seen(phrase_id):
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO seen_phrases (phrase_id, seen_at) VALUES (?, ?)",
            (phrase_id, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def ask_claude(prompt, max_tokens=150):
    """Returns (text, None) on success, or (None, (json_response, status)) on failure."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.RateLimitError:
        return None, (jsonify({"error": "Rate limited - please wait a moment and try again."}), 429)
    except anthropic.APIStatusError as e:
        return None, (jsonify({"error": f"API error: {e.message}"}), 502)
    except anthropic.APIConnectionError:
        return None, (jsonify({"error": "Network error connecting to Claude API."}), 502)

    text = next((block.text for block in response.content if block.type == "text"), "")
    return text, None


@app.route("/")
def index():
    return render_template("index.html", phrases=PHRASES, seen_ids=get_seen_ids())


@app.route("/api/progress/seen", methods=["POST"])
def progress_seen():
    data = request.get_json(silent=True) or {}
    phrase_id = data.get("phrase_id")

    if phrase_id not in PHRASES_BY_ID:
        return jsonify({"error": "Unknown phrase id."}), 400

    mark_seen(phrase_id)
    return jsonify({"seen_ids": get_seen_ids()})


@app.route("/api/phrase/explain", methods=["POST"])
def phrase_explain():
    data = request.get_json(silent=True) or {}
    phrase = PHRASES_BY_ID.get(data.get("phrase_id"))
    if not phrase:
        return jsonify({"error": "Unknown phrase id."}), 400

    prompt = (
        f"Give a different, more detailed explanation (2-3 short sentences) of what "
        f"the English phrasal verb '{phrase['phrase']}' means, for a Mandarin-speaking "
        f"English learner at an intermediate level. Their basic definition is: "
        f"'{phrase['meaning']}'. Expand on this with more nuance or an example use case, "
        f"using simple vocabulary. Do not use the phrase '{phrase['phrase']}' itself, "
        f"and do not use another phrasal verb or idiom. Reply with only the explanation, "
        f"no preamble."
    )

    explanation, error = ask_claude(prompt, max_tokens=200)
    if error:
        return error

    return jsonify({"explanation": explanation})


@app.route("/api/phrase/example", methods=["POST"])
def phrase_example():
    data = request.get_json(silent=True) or {}
    phrase = PHRASES_BY_ID.get(data.get("phrase_id"))
    if not phrase:
        return jsonify({"error": "Unknown phrase id."}), 400

    prompt = (
        f"Write one new short example sentence (or two-line dialogue) that naturally "
        f"uses the English phrasal verb '{phrase['phrase']}' (meaning: "
        f"'{phrase['meaning']}'), different from a typical textbook example. You MUST "
        f"include the exact literal text '{phrase['phrase']}' character-for-character "
        f"somewhere in your response - do NOT conjugate, inflect, or change the tense "
        f"of the verb in any way (no past tense, no '-ing' form, no third-person '-s'). "
        f"Build the sentence so the phrase naturally stays in this exact base form, for "
        f"example using present tense with 'I'/'you'/'we', an imperative, or 'to "
        f"{phrase['phrase']}'. Reply with only the example, no preamble."
    )

    example, error = ask_claude(prompt, max_tokens=150)
    if error:
        return error

    return jsonify({"example": example})


@app.route("/api/discrimination/new", methods=["POST"])
def discrimination_new():
    seen_ids = get_seen_ids()

    if len(seen_ids) < 2:
        return jsonify({"error": "Not enough phrases learned yet."}), 400

    target_id = random.choice(seen_ids)
    target = PHRASES_BY_ID[target_id]

    prompt = (
        f"Write one short, natural sentence or two-sentence scenario (under 30 words) "
        f"describing a situation where someone would want to say they need to "
        f"'{target['meaning']}'. Do not use the phrase '{target['phrase']}' or any "
        f"part of it anywhere in your response. The meaning given may be a longer "
        f"descriptive phrase - in your sentence, replace the core action with a "
        f"single plain, literal, non-idiomatic verb of at most 2 words (e.g. 'solve', "
        f"'invent', 'tolerate', 'recover from') that could substitute for "
        f"'{target['phrase']}', never another phrasal verb or idiom, since the "
        f"student may not have learned it yet. Wrap ONLY that single substitute verb "
        f"in double asterisks, like **this** - do not include any surrounding object, "
        f"preposition, or context words inside the asterisks. "
        f"Reply with only the sentence, no preamble."
    )

    sentence, error = ask_claude(prompt, max_tokens=100)
    if error:
        return error

    session["discrimination_target"] = target_id

    distractor_pool = [i for i in seen_ids if i != target_id]
    distractors = random.sample(distractor_pool, k=min(3, len(distractor_pool)))
    option_ids = distractors + [target_id]
    random.shuffle(option_ids)

    options = [{"id": i, "phrase": PHRASES_BY_ID[i]["phrase"]} for i in option_ids]

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
