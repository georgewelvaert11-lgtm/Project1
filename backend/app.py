import json
import os
import random
import re
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
    {
        "id": "pile_up",
        "phrase": "pile up",
        "meaning": "to gradually accumulate or build up in quantity",
        "meaning_zh": "堆積",
        "dialogue": [
            ("A", "My emails always pile up when I go on vacation."),
            ("B", "Same here — I dread opening my inbox after a trip."),
        ],
    },
    {
        "id": "carry_out",
        "phrase": "carry out",
        "meaning": "to perform or complete a task, plan, or instruction",
        "meaning_zh": "執行",
        "dialogue": [
            ("A", "The manager asked us to carry out a safety inspection today."),
            ("B", "No problem, I'll start with the fire exits."),
        ],
    },
    {
        "id": "catch_up",
        "phrase": "catch up",
        "meaning": "to reach the same level or progress as someone else, or to share recent news with someone",
        "meaning_zh": "趕上",
        "dialogue": [
            ("A", "Let's catch up over coffee soon — it's been ages."),
            ("B", "Definitely, I have so much to tell you."),
        ],
    },
    {
        "id": "check_out",
        "phrase": "check out",
        "meaning": "to look at or investigate something, or to leave a hotel after paying the bill",
        "meaning_zh": "查看",
        "dialogue": [
            ("A", "You should check out this new restaurant downtown."),
            ("B", "I've heard great things — let's go this weekend."),
        ],
    },
    {
        "id": "cut_down",
        "phrase": "cut down",
        "meaning": "to reduce the amount of something, like a habit or expense",
        "meaning_zh": "減少",
        "dialogue": [
            ("A", "I'm trying to cut down on sugar this year."),
            ("B", "That's a good goal — maybe start with soda."),
        ],
    },
    {
        "id": "fall_apart",
        "phrase": "fall apart",
        "meaning": "to break into pieces, or to become extremely upset or unable to cope",
        "meaning_zh": "崩潰",
        "dialogue": [
            ("A", "These cheap headphones fall apart after a month."),
            ("B", "Yeah, I've had the same problem twice."),
        ],
    },
    {
        "id": "find_out",
        "phrase": "find out",
        "meaning": "to discover information about something",
        "meaning_zh": "發現",
        "dialogue": [
            ("A", "I need to find out what time the store closes."),
            ("B", "I'll check their website for you."),
        ],
    },
    {
        "id": "get_away",
        "phrase": "get away",
        "meaning": "to escape from somewhere, or to go on a vacation",
        "meaning_zh": "逃脫",
        "dialogue": [
            ("A", "We really need to get away for the weekend."),
            ("B", "Agreed, let's book a cabin somewhere quiet."),
        ],
    },
    {
        "id": "get_through",
        "phrase": "get through",
        "meaning": "to successfully deal with or survive something difficult, or to reach someone by phone",
        "meaning_zh": "度過",
        "dialogue": [
            ("A", "I don't know how I'll get through this exam period."),
            ("B", "One day at a time — you've got this."),
        ],
    },
    {
        "id": "go_over",
        "phrase": "go over",
        "meaning": "to review or examine something carefully",
        "meaning_zh": "複習",
        "dialogue": [
            ("A", "Can we go over the budget one more time before the meeting?"),
            ("B", "Sure, give me five minutes to pull it up."),
        ],
    },
    {
        "id": "grow_up",
        "phrase": "grow up",
        "meaning": "to become an adult, or to stop behaving in a childish way",
        "meaning_zh": "長大",
        "dialogue": [
            ("A", "Kids grow up so fast these days."),
            ("B", "I know — mine changes every week."),
        ],
    },
    {
        "id": "look_after",
        "phrase": "look after",
        "meaning": "to take care of someone or something",
        "meaning_zh": "照顧",
        "dialogue": [
            ("A", "Can you look after my cat while I'm traveling?"),
            ("B", "Of course, just leave me some instructions."),
        ],
    },
    {
        "id": "look_forward_to",
        "phrase": "look forward to",
        "meaning": "to feel excited or pleased about something that is going to happen",
        "meaning_zh": "期待",
        "dialogue": [
            ("A", "I really look forward to the holidays every year."),
            ("B", "Same — the food alone makes it worth the wait."),
        ],
    },
    {
        "id": "move_on",
        "phrase": "move on",
        "meaning": "to stop dwelling on a difficult situation and continue with life",
        "meaning_zh": "繼續前進",
        "dialogue": [
            ("A", "It took a while, but I've finally learned to move on from that breakup."),
            ("B", "I'm proud of you — that wasn't easy."),
        ],
    },
    {
        "id": "pay_off",
        "phrase": "pay off",
        "meaning": "to be worth the effort in the end, or to fully repay a debt",
        "meaning_zh": "值得",
        "dialogue": [
            ("A", "All those late nights studying finally pay off when you see your grades."),
            ("B", "Exactly, hard work always pays off eventually."),
        ],
    },
    {
        "id": "run_out",
        "phrase": "run out",
        "meaning": "to have none of something left",
        "meaning_zh": "用完",
        "dialogue": [
            ("A", "We're about to run out of milk again."),
            ("B", "I'll grab some on my way home."),
        ],
    },
    {
        "id": "set_up",
        "phrase": "set up",
        "meaning": "to arrange, prepare, or put something in place",
        "meaning_zh": "建立",
        "dialogue": [
            ("A", "Can you help me set up the projector for the presentation?"),
            ("B", "Sure, give me a minute to find the cables."),
        ],
    },
    {
        "id": "show_off",
        "phrase": "show off",
        "meaning": "to try to impress people by displaying your abilities or possessions",
        "meaning_zh": "炫耀",
        "dialogue": [
            ("A", "He always likes to show off his new gadgets."),
            ("B", "Yeah, but they usually are pretty cool."),
        ],
    },
    {
        "id": "sort_out",
        "phrase": "sort out",
        "meaning": "to resolve a problem, or to organize something",
        "meaning_zh": "解決",
        "dialogue": [
            ("A", "We still need to sort out the seating for the wedding."),
            ("B", "Let's do it together this weekend."),
        ],
    },
    {
        "id": "stand_out",
        "phrase": "stand out",
        "meaning": "to be easily noticed because of being different or better than others",
        "meaning_zh": "脫穎而出",
        "dialogue": [
            ("A", "Her designs always stand out in a crowd."),
            ("B", "She has a real eye for color."),
        ],
    },
    {
        "id": "take_off",
        "phrase": "take off",
        "meaning": "for a plane to leave the ground, or for something to become suddenly successful",
        "meaning_zh": "起飛",
        "dialogue": [
            ("A", "Our flight is about to take off, so please turn off your phone."),
            ("B", "Got it, switching to airplane mode now."),
        ],
    },
    {
        "id": "turn_out",
        "phrase": "turn out",
        "meaning": "to happen or end in a particular way, especially unexpectedly",
        "meaning_zh": "結果是",
        "dialogue": [
            ("A", "I'm curious how this recipe will turn out."),
            ("B", "Let me know — I might try it too."),
        ],
    },
    {
        "id": "wake_up",
        "phrase": "wake up",
        "meaning": "to stop sleeping and become conscious",
        "meaning_zh": "醒來",
        "dialogue": [
            ("A", "I always wake up before my alarm goes off."),
            ("B", "I wish I had that problem — I sleep through mine."),
        ],
    },
    {
        "id": "work_out",
        "phrase": "work out",
        "meaning": "to exercise, or for a plan or situation to end successfully",
        "meaning_zh": "成功",
        "dialogue": [
            ("A", "I try to work out at the gym three times a week."),
            ("B", "That's impressive — I can barely manage once."),
        ],
    },
    {
        "id": "call_off",
        "phrase": "call off",
        "meaning": "to cancel something that was planned",
        "meaning_zh": "取消",
        "dialogue": [
            ("A", "They had to call off the picnic because of the storm."),
            ("B", "That's a shame, we were looking forward to it."),
        ],
    },
]


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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS phrase_results (
            phrase_id TEXT PRIMARY KEY,
            correct_count INTEGER NOT NULL DEFAULT 0,
            incorrect_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS custom_phrases (
            id TEXT PRIMARY KEY,
            phrase TEXT NOT NULL,
            meaning TEXT NOT NULL,
            meaning_zh TEXT NOT NULL,
            dialogue TEXT NOT NULL,
            added_at TEXT NOT NULL
        )
        """
    )
    return conn


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "phrase"


def get_custom_phrases():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, phrase, meaning, meaning_zh, dialogue FROM custom_phrases"
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "id": row[0],
            "phrase": row[1],
            "meaning": row[2],
            "meaning_zh": row[3],
            "dialogue": json.loads(row[4]),
        }
        for row in rows
    ]


def add_custom_phrase(phrase, meaning, meaning_zh, dialogue):
    existing_ids = {p["id"] for p in get_all_phrases()}
    base_id = slugify(phrase)
    phrase_id = base_id
    suffix = 2
    while phrase_id in existing_ids:
        phrase_id = f"{base_id}_{suffix}"
        suffix += 1

    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO custom_phrases (id, phrase, meaning, meaning_zh, dialogue, added_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (phrase_id, phrase, meaning, meaning_zh, json.dumps(dialogue), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "id": phrase_id,
        "phrase": phrase,
        "meaning": meaning,
        "meaning_zh": meaning_zh,
        "dialogue": dialogue,
    }


def get_all_phrases():
    return PHRASES + get_custom_phrases()


def get_all_phrases_by_id():
    return {p["id"]: p for p in get_all_phrases()}


def get_seen_ids():
    conn = get_db()
    try:
        rows = conn.execute("SELECT phrase_id FROM seen_phrases").fetchall()
    finally:
        conn.close()
    valid_ids = get_all_phrases_by_id()
    return [row[0] for row in rows if row[0] in valid_ids]


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


def get_results():
    """Returns {phrase_id: (correct_count, incorrect_count)}."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT phrase_id, correct_count, incorrect_count FROM phrase_results"
        ).fetchall()
    finally:
        conn.close()
    return {row[0]: (row[1], row[2]) for row in rows}


def record_result(phrase_id, correct):
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO phrase_results (phrase_id, correct_count, incorrect_count)
            VALUES (?, ?, ?)
            ON CONFLICT(phrase_id) DO UPDATE SET
                correct_count = correct_count + excluded.correct_count,
                incorrect_count = incorrect_count + excluded.incorrect_count
            """,
            (phrase_id, 1 if correct else 0, 0 if correct else 1),
        )
        conn.commit()
    finally:
        conn.close()


def weighted_target_choice(seen_ids, results):
    """Picks a target phrase, weighting toward ones answered incorrectly more
    often than correctly. Never-attempted and mastered phrases keep a floor
    weight of 1 so every seen phrase can still come up occasionally."""
    weights = []
    for phrase_id in seen_ids:
        correct, incorrect = results.get(phrase_id, (0, 0))
        weight = max(1, 1 + incorrect - correct)
        weights.append(weight)
    return random.choices(seen_ids, weights=weights, k=1)[0]


def compute_progress_summary():
    total = len(get_all_phrases())
    seen_ids = set(get_seen_ids())
    results = get_results()

    not_started = total - len(seen_ids)
    seen_untested = 0
    practicing = 0
    mastered = 0

    for phrase_id in seen_ids:
        correct, incorrect = results.get(phrase_id, (0, 0))
        if correct + incorrect == 0:
            seen_untested += 1
        elif correct > incorrect:
            mastered += 1
        else:
            practicing += 1

    return {
        "total": total,
        "not_started": not_started,
        "seen_untested": seen_untested,
        "practicing": practicing,
        "mastered": mastered,
    }


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
    return render_template(
        "index.html",
        phrases=get_all_phrases(),
        seen_ids=get_seen_ids(),
        progress_summary=compute_progress_summary(),
    )


@app.route("/api/progress/summary")
def progress_summary_route():
    return jsonify(compute_progress_summary())


@app.route("/api/progress/seen", methods=["POST"])
def progress_seen():
    data = request.get_json(silent=True) or {}
    phrase_id = data.get("phrase_id")

    if phrase_id not in get_all_phrases_by_id():
        return jsonify({"error": "Unknown phrase id."}), 400

    mark_seen(phrase_id)
    return jsonify({"seen_ids": get_seen_ids()})


@app.route("/api/phrases/add", methods=["POST"])
def add_phrase():
    data = request.get_json(silent=True) or {}
    phrase_text = (data.get("phrase") or "").strip()

    if not phrase_text:
        return jsonify({"error": "Please enter a phrase."}), 400
    if len(phrase_text) > 60:
        return jsonify({"error": "That phrase is too long."}), 400

    existing = get_all_phrases()
    if any(p["phrase"].lower() == phrase_text.lower() for p in existing):
        return jsonify({"error": "That phrase is already in the library."}), 400

    prompt = (
        f"A Mandarin-speaking English learner wants to add the phrase or expression "
        f"'{phrase_text}' to their study list. Provide:\n"
        f"1. A concise, clear meaning/definition in English (one sentence).\n"
        f"2. A natural Traditional Chinese (繁體中文) translation of that meaning.\n"
        f"3. A short two-line example dialogue (one line for speaker A, one for speaker "
        f"B) that naturally uses the exact phrase '{phrase_text}' unchanged, in its base "
        f"form - do not conjugate, inflect, or change its tense in any way.\n"
        f"Reply with ONLY a JSON object with keys 'meaning', 'meaning_zh', and 'dialogue' "
        f"(dialogue as an array of exactly two [speaker, line] pairs, speaker being 'A' "
        f"or 'B'). No markdown code fences, no other text."
    )

    text, error = ask_claude(prompt, max_tokens=400)
    if error:
        return error

    cleaned = text.strip().strip("`").strip()
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        content = json.loads(cleaned)
        meaning = content["meaning"]
        meaning_zh = content["meaning_zh"]
        dialogue = content["dialogue"]
        assert isinstance(dialogue, list) and len(dialogue) == 2
    except Exception:
        return jsonify({"error": "Couldn't generate content for that phrase - try rephrasing it."}), 502

    new_phrase = add_custom_phrase(phrase_text, meaning, meaning_zh, dialogue)

    return jsonify({"phrase": new_phrase})


@app.route("/api/phrase/explain", methods=["POST"])
def phrase_explain():
    data = request.get_json(silent=True) or {}
    phrase = get_all_phrases_by_id().get(data.get("phrase_id"))
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
    phrase = get_all_phrases_by_id().get(data.get("phrase_id"))
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
    all_phrases_by_id = get_all_phrases_by_id()

    if len(seen_ids) < 2:
        return jsonify({"error": "Not enough phrases learned yet."}), 400

    target_id = weighted_target_choice(seen_ids, get_results())
    target = all_phrases_by_id[target_id]

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

    options = [{"id": i, "phrase": all_phrases_by_id[i]["phrase"]} for i in option_ids]

    return jsonify({"sentence": sentence, "options": options})


@app.route("/api/discrimination/check", methods=["POST"])
def discrimination_check():
    data = request.get_json(silent=True) or {}
    selected_id = data.get("selected_id")

    target_id = session.pop("discrimination_target", None)
    if not target_id:
        return jsonify({"error": "No active round - start a new one."}), 400

    target = get_all_phrases_by_id()[target_id]
    correct = selected_id == target_id
    record_result(target_id, correct)

    return jsonify({
        "correct": correct,
        "correct_phrase": target["phrase"],
        "meaning": target["meaning"],
    })


if __name__ == "__main__":
    app.run(debug=True)
