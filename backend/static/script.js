const MIN_PHRASES_FOR_STEP2 = 3;
const NUDGE_INTERVAL = 5;

const seenIds = [...SEEN_IDS];

// ---- Shared: progress readout + step navigation ----

const overallProgress = document.getElementById("overall-progress");
const navStep1Btn = document.getElementById("nav-step1-btn");
const navStep2Btn = document.getElementById("nav-step2-btn");
const step1 = document.getElementById("step1");
const step2 = document.getElementById("step2");
const step2Nudge = document.getElementById("step2-nudge");
const step2NudgeText = document.getElementById("step2-nudge-text");
const step2NudgeGoBtn = document.getElementById("step2-nudge-go-btn");
const step2NudgeDismissBtn = document.getElementById("step2-nudge-dismiss-btn");

const segNotStarted = document.getElementById("seg-not-started");
const segSeen = document.getElementById("seg-seen");
const segPracticing = document.getElementById("seg-practicing");
const segMastered = document.getElementById("seg-mastered");
const countNotStarted = document.getElementById("count-not-started");
const countSeen = document.getElementById("count-seen");
const countPracticing = document.getElementById("count-practicing");
const countMastered = document.getElementById("count-mastered");

let step2Started = false;

function updateProgress() {
    const remaining = PHRASES.length - seenIds.length;
    overallProgress.textContent =
        `${seenIds.length} of ${PHRASES.length} phrases learned · ${remaining} remaining`;

    if (seenIds.length >= MIN_PHRASES_FOR_STEP2) {
        navStep2Btn.disabled = false;
    }
}

function renderProgressTracker(summary) {
    const pct = (n) => (summary.total === 0 ? 0 : (n / summary.total) * 100);

    segNotStarted.style.width = `${pct(summary.not_started)}%`;
    segSeen.style.width = `${pct(summary.seen_untested)}%`;
    segPracticing.style.width = `${pct(summary.practicing)}%`;
    segMastered.style.width = `${pct(summary.mastered)}%`;

    countNotStarted.textContent = summary.not_started;
    countSeen.textContent = summary.seen_untested;
    countPracticing.textContent = summary.practicing;
    countMastered.textContent = summary.mastered;
}

async function refreshProgressTracker() {
    const response = await fetch("/api/progress/summary");
    const data = await response.json();
    renderProgressTracker(data);
}

renderProgressTracker(PROGRESS_SUMMARY);

function maybeShowStep2Nudge() {
    if (seenIds.length < MIN_PHRASES_FOR_STEP2) return;
    if (seenIds.length % NUDGE_INTERVAL !== 0) return;

    step2NudgeText.textContent =
        `You've learned ${seenIds.length} phrases — want to practice them in Step 2?`;
    step2Nudge.classList.remove("hidden");
}

function showStep(step) {
    step1.classList.toggle("hidden", step !== 1);
    step2.classList.toggle("hidden", step !== 2);
    navStep1Btn.classList.toggle("active", step === 1);
    navStep2Btn.classList.toggle("active", step === 2);
    step2Nudge.classList.add("hidden");

    if (step === 2 && !step2Started) {
        step2Started = true;
        startNewRound();
    }
}

navStep1Btn.addEventListener("click", () => showStep(1));
navStep2Btn.addEventListener("click", () => showStep(2));
step2NudgeGoBtn.addEventListener("click", () => showStep(2));
step2NudgeDismissBtn.addEventListener("click", () => step2Nudge.classList.add("hidden"));

// ---- Step 1: learn phrases in random order ----

const dialogueBox = document.getElementById("dialogue-box");
const guessForm = document.getElementById("guess-form");
const guessLabel = document.getElementById("guess-label");
const guessInput = document.getElementById("guess");
const reveal = document.getElementById("reveal");
const guessText = document.getElementById("your-guess-text");
const revealExplanation = document.getElementById("reveal-explanation");
const step1Controls = document.getElementById("step1-controls");
const nextPhraseBtn = document.getElementById("next-phrase-btn");
const allLearned = document.getElementById("all-learned");

const showZhBtn = document.getElementById("show-zh-btn");
const showExplainBtn = document.getElementById("show-explain-btn");
const showExampleBtn = document.getElementById("show-example-btn");
const revealZh = document.getElementById("reveal-zh");
const explainResult = document.getElementById("explain-result");
const exampleResult = document.getElementById("example-result");

let currentPhrase = null;

function pickRandomUnseenPhrase() {
    const unseen = PHRASES.filter((p) => !seenIds.includes(p.id));
    if (unseen.length === 0) return null;
    return unseen[Math.floor(Math.random() * unseen.length)];
}

function highlightPhrase(line, phrase) {
    const regex = new RegExp(`(${phrase})`, "i");
    return line.replace(regex, "<mark>$1</mark>");
}

function renderPhrase(phrase) {
    currentPhrase = phrase;

    if (!phrase) {
        dialogueBox.classList.add("hidden");
        guessForm.classList.add("hidden");
        reveal.classList.add("hidden");
        step1Controls.classList.add("hidden");
        allLearned.classList.remove("hidden");
        return;
    }

    allLearned.classList.add("hidden");
    dialogueBox.classList.remove("hidden");
    guessForm.classList.remove("hidden");

    dialogueBox.innerHTML = "";
    phrase.dialogue.forEach(([speaker, line]) => {
        const p = document.createElement("p");
        p.innerHTML = `<span class="speaker">${speaker}:</span> ${highlightPhrase(line, phrase.phrase)}`;
        dialogueBox.appendChild(p);
    });

    guessLabel.textContent = `What do you think "${phrase.phrase}" means here? (English or 繁體中文)`;
    guessInput.value = "";
    guessInput.disabled = false;
    guessForm.querySelector("button").disabled = false;

    reveal.classList.add("hidden");
    step1Controls.classList.add("hidden");

    revealZh.classList.add("hidden");
    explainResult.classList.add("hidden");
    exampleResult.classList.add("hidden");
}

function highlightExact(text, phrase) {
    return escapeHtml(text).replace(new RegExp(`(${phrase})`, "i"), "<mark>$1</mark>");
}

showZhBtn.addEventListener("click", () => {
    revealZh.textContent = currentPhrase.meaning_zh;
    revealZh.classList.remove("hidden");
});

showExplainBtn.addEventListener("click", async () => {
    explainResult.textContent = "Loading...";
    explainResult.classList.remove("hidden");

    const response = await fetch("/api/phrase/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phrase_id: currentPhrase.id }),
    });
    const data = await response.json();

    explainResult.textContent = data.error
        ? "Sorry, something went wrong: " + data.error
        : data.explanation;
});

showExampleBtn.addEventListener("click", async () => {
    exampleResult.textContent = "Loading...";
    exampleResult.classList.remove("hidden");

    const response = await fetch("/api/phrase/example", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phrase_id: currentPhrase.id }),
    });
    const data = await response.json();

    exampleResult.innerHTML = data.error
        ? "Sorry, something went wrong: " + data.error
        : highlightExact(data.example, currentPhrase.phrase);
});

async function markPhraseSeen(phraseId) {
    const response = await fetch("/api/progress/seen", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phrase_id: phraseId }),
    });
    const data = await response.json();
    if (data.seen_ids) {
        seenIds.length = 0;
        seenIds.push(...data.seen_ids);
    }
}

guessForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const phrase = currentPhrase;

    guessText.textContent = guessInput.value;
    revealExplanation.innerHTML = `<strong>Phrasal verb:</strong> "${phrase.phrase}" — ${phrase.meaning}.`;
    reveal.classList.remove("hidden");
    guessInput.disabled = true;
    guessForm.querySelector("button").disabled = true;

    await markPhraseSeen(phrase.id);
    updateProgress();
    maybeShowStep2Nudge();
    refreshProgressTracker();

    step1Controls.classList.remove("hidden");
});

nextPhraseBtn.addEventListener("click", () => {
    renderPhrase(pickRandomUnseenPhrase());
});

updateProgress();
renderPhrase(pickRandomUnseenPhrase());
showStep(1);

// ---- Add a new phrase to the library ----

const addPhraseForm = document.getElementById("add-phrase-form");
const newPhraseInput = document.getElementById("new-phrase-input");
const addPhraseError = document.getElementById("add-phrase-error");

addPhraseForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const phraseText = newPhraseInput.value.trim();
    if (!phraseText) return;

    addPhraseError.classList.add("hidden");
    const submitBtn = addPhraseForm.querySelector("button");
    submitBtn.disabled = true;
    submitBtn.textContent = "Adding...";

    const response = await fetch("/api/phrases/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phrase: phraseText }),
    });
    const data = await response.json();

    submitBtn.disabled = false;
    submitBtn.textContent = "Add phrase";

    if (data.error) {
        addPhraseError.textContent = data.error;
        addPhraseError.classList.remove("hidden");
        return;
    }

    PHRASES.push(data.phrase);
    updateProgress();
    refreshProgressTracker();
    newPhraseInput.value = "";

    showStep(1);
    renderPhrase(data.phrase);
});

// ---- Step 2: match a scenario sentence to a learned phrase ----

const discSentence = document.getElementById("discrimination-sentence");
const discOptions = document.getElementById("discrimination-options");
const discFeedback = document.getElementById("discrimination-feedback");
const newRoundBtn = document.getElementById("new-round-btn");

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function renderHighlightedSentence(text) {
    return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<mark>$1</mark>");
}

async function startNewRound() {
    discFeedback.classList.add("hidden");
    newRoundBtn.classList.add("hidden");
    discOptions.innerHTML = "";
    discSentence.textContent = "Loading a new scenario...";

    const response = await fetch("/api/discrimination/new", { method: "POST" });
    const data = await response.json();

    if (data.error) {
        discSentence.textContent = "Sorry, something went wrong: " + data.error;
        return;
    }

    discSentence.innerHTML = renderHighlightedSentence(data.sentence);
    data.options.forEach((option) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "option-btn";
        btn.textContent = option.phrase;
        btn.addEventListener("click", () => selectOption(option.id));
        discOptions.appendChild(btn);
    });
}

async function selectOption(selectedId) {
    document.querySelectorAll(".option-btn").forEach((btn) => (btn.disabled = true));

    const response = await fetch("/api/discrimination/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selected_id: selectedId }),
    });
    const data = await response.json();

    if (data.error) {
        discFeedback.textContent = "Sorry, something went wrong: " + data.error;
        discFeedback.className = "feedback-incorrect";
    } else if (data.correct) {
        discFeedback.textContent = `Correct! "${data.correct_phrase}" — ${data.meaning}.`;
        discFeedback.className = "feedback-correct";
    } else {
        discFeedback.textContent = `Not quite. The answer was "${data.correct_phrase}" — ${data.meaning}.`;
        discFeedback.className = "feedback-incorrect";
    }

    discFeedback.classList.remove("hidden");
    newRoundBtn.classList.remove("hidden");
    refreshProgressTracker();
}

newRoundBtn.addEventListener("click", startNewRound);
