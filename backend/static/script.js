// ---- Step 1: learn phrases one at a time ----

const step1 = document.getElementById("step1");
const phraseProgress = document.getElementById("phrase-progress");
const dialogueBox = document.getElementById("dialogue-box");
const guessForm = document.getElementById("guess-form");
const guessLabel = document.getElementById("guess-label");
const guessInput = document.getElementById("guess");
const reveal = document.getElementById("reveal");
const guessText = document.getElementById("your-guess-text");
const revealExplanation = document.getElementById("reveal-explanation");
const step1Controls = document.getElementById("step1-controls");
const nextPhraseBtn = document.getElementById("next-phrase-btn");
const toStep2Btn = document.getElementById("to-step2-btn");

const MIN_PHRASES_FOR_STEP2 = 3;

let currentIndex = 0;
const seenIds = [];

function renderPhrase(index) {
    const phrase = PHRASES[index];

    phraseProgress.textContent = `Phrase ${index + 1} of ${PHRASES.length}`;
    dialogueBox.innerHTML = "";
    phrase.dialogue.forEach(([speaker, line]) => {
        const p = document.createElement("p");
        p.innerHTML = `<span class="speaker">${speaker}:</span> ${line}`;
        dialogueBox.appendChild(p);
    });

    guessLabel.textContent = `What do you think "${phrase.phrase}" means here? (English or 繁體中文)`;
    guessInput.value = "";
    guessInput.disabled = false;
    guessForm.querySelector("button").disabled = false;

    reveal.classList.add("hidden");
    step1Controls.classList.add("hidden");
    toStep2Btn.classList.add("hidden");

    nextPhraseBtn.disabled = index >= PHRASES.length - 1;
    nextPhraseBtn.textContent =
        index >= PHRASES.length - 1 ? "No more phrases" : "Next phrase";
}

guessForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const phrase = PHRASES[currentIndex];

    guessText.textContent = guessInput.value;
    revealExplanation.innerHTML = `<strong>Phrasal verb:</strong> "${phrase.phrase}" — ${phrase.meaning}.`;
    reveal.classList.remove("hidden");
    guessInput.disabled = true;
    guessForm.querySelector("button").disabled = true;

    if (!seenIds.includes(phrase.id)) {
        seenIds.push(phrase.id);
    }

    step1Controls.classList.remove("hidden");
    if (seenIds.length >= MIN_PHRASES_FOR_STEP2) {
        toStep2Btn.classList.remove("hidden");
    }
});

nextPhraseBtn.addEventListener("click", () => {
    if (currentIndex < PHRASES.length - 1) {
        currentIndex += 1;
        renderPhrase(currentIndex);
    }
});

toStep2Btn.addEventListener("click", () => {
    step1.classList.add("hidden");
    document.getElementById("step2").classList.remove("hidden");
    startNewRound();
});

renderPhrase(currentIndex);

// ---- Step 2: match a scenario sentence to a learned phrase ----

const step2 = document.getElementById("step2");
const discSentence = document.getElementById("discrimination-sentence");
const discOptions = document.getElementById("discrimination-options");
const discFeedback = document.getElementById("discrimination-feedback");
const newRoundBtn = document.getElementById("new-round-btn");

async function startNewRound() {
    discFeedback.classList.add("hidden");
    newRoundBtn.classList.add("hidden");
    discOptions.innerHTML = "";
    discSentence.textContent = "Loading a new scenario...";

    const response = await fetch("/api/discrimination/new", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seen_ids: seenIds }),
    });
    const data = await response.json();

    if (data.error) {
        discSentence.textContent = "Sorry, something went wrong: " + data.error;
        return;
    }

    discSentence.textContent = data.sentence;
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
}

newRoundBtn.addEventListener("click", startNewRound);
