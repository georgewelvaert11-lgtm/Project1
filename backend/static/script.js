const form = document.getElementById("guess-form");
const guessInput = document.getElementById("guess");
const reveal = document.getElementById("reveal");
const guessText = document.getElementById("your-guess-text");

form.addEventListener("submit", (event) => {
    event.preventDefault();
    guessText.textContent = guessInput.value;
    reveal.classList.remove("hidden");
    guessInput.disabled = true;
    form.querySelector("button").disabled = true;
});
