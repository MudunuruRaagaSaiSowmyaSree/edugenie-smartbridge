// ---------- HISTORY ----------
const HISTORY_KEY = "edugenie-history";

function saveToHistory(feature, input, output) {
  const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  history.unshift({
    feature,
    input,
    output,
    timestamp: new Date().toLocaleString(),
  });
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 50))); // keep last 50
}

function renderHistory() {
  const history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  const listEl = document.getElementById("history-list");

  if (history.length === 0) {
    listEl.innerHTML = '<p class="text-gray-400 dark:text-gray-500 italic">No history yet. Try out a feature and it will show up here!</p>';
    return;
  }

  listEl.innerHTML = history
    .map(
      (entry) => `
      <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
        <div class="flex justify-between items-center mb-1">
          <span class="text-xs font-bold uppercase text-indigo-500 dark:text-indigo-300">${entry.feature}</span>
          <span class="text-xs text-gray-400">${entry.timestamp}</span>
        </div>
        <p class="text-sm font-semibold mb-1">${entry.input}</p>
        <p class="text-sm text-gray-600 dark:text-gray-300 truncate">${entry.output}</p>
      </div>`
    )
    .join("");
}

document.getElementById("clear-history").addEventListener("click", () => {
  localStorage.removeItem(HISTORY_KEY);
  renderHistory();
});

// ---------- FLASHCARDS ----------
document.getElementById("flashcard-submit").addEventListener("click", async () => {
  const topic = document.getElementById("flashcard-topic").value.trim();
  const num_cards = parseInt(document.getElementById("flashcard-count").value, 10);
  const resultBox = document.getElementById("flashcard-result");

  if (!topic) {
    resultBox.innerHTML = '<p class="text-red-500 col-span-2">Please enter a topic first.</p>';
    return;
  }

  resultBox.innerHTML = '<p class="text-indigo-500 italic col-span-2">Generating flashcards...</p>';
  try {
    const data = await callApi("/flashcards/generate", { topic, num_cards });

    if (data.error) {
      resultBox.innerHTML = `<p class="text-red-500 col-span-2">Error: ${data.error}</p>`;
      return;
    }

    resultBox.innerHTML = data.flashcards
      .map(
        (card, i) => `
        <div class="flashcard-flip h-40 cursor-pointer" data-flipped="false">
          <div class="flashcard-inner relative w-full h-full transition-transform duration-500" style="transform-style: preserve-3d;">
            <div class="flashcard-front absolute w-full h-full flex items-center justify-center text-center p-4 bg-indigo-50 dark:bg-indigo-900 border border-indigo-200 dark:border-indigo-700 rounded-lg font-semibold" style="backface-visibility: hidden;">
              ${card.front}
            </div>
            <div class="flashcard-back absolute w-full h-full flex items-center justify-center text-center p-4 bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-lg text-sm" style="backface-visibility: hidden; transform: rotateY(180deg);">
              ${card.back}
            </div>
          </div>
        </div>`
      )
      .join("");

    saveToHistory("Flashcards", topic, `${data.flashcards.length} flashcards generated`);

    // Attach flip listeners
    document.querySelectorAll(".flashcard-flip").forEach((card) => {
      card.addEventListener("click", () => {
        const inner = card.querySelector(".flashcard-inner");
        const isFlipped = card.dataset.flipped === "true";
        inner.style.transform = isFlipped ? "rotateY(0deg)" : "rotateY(180deg)";
        card.dataset.flipped = isFlipped ? "false" : "true";
      });
    });
  } catch (err) {
    resultBox.innerHTML = `<p class="text-red-500 col-span-2">${friendlyErrorMessage(err)}</p>`;
  }
});

// ---------- DARK MODE ----------
const darkModeToggle = document.getElementById("dark-mode-toggle");

// Check saved preference on load
if (localStorage.getItem("edugenie-dark-mode") === "true") {
  document.documentElement.classList.add("dark");
  darkModeToggle.textContent = "☀️ Light Mode";
}

darkModeToggle.addEventListener("click", () => {
  const isDark = document.documentElement.classList.toggle("dark");
  darkModeToggle.textContent = isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
  localStorage.setItem("edugenie-dark-mode", isDark);
});

const API_BASE = "https://edugenie-3r88.onrender.com/api";

// ---------- TAB SWITCHING ----------
const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.tab;

    // Update button styles
    tabButtons.forEach((b) => {
      b.classList.remove("bg-indigo-500", "text-white");
      b.classList.add("bg-gray-200", "text-gray-700");
    });
    btn.classList.remove("bg-gray-200", "text-gray-700");
    btn.classList.add("bg-indigo-500", "text-white");

    // Show matching content, hide the rest
    tabContents.forEach((section) => {
      section.classList.toggle("hidden", section.id !== target);
    });

    if (target === "history") {
      renderHistory();
    }
  });
});

// ---------- HELPER: fetch wrapper ----------
async function callApi(endpoint, payload) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  let data = {};
  try {
    data = await response.json();
  } catch (_) {
    // no JSON body
  }

  if (!response.ok) {
    const err = new Error(data.detail || `Request failed (${response.status})`);
    err.status = response.status;
    throw err;
  }

  return data;
}

function friendlyErrorMessage(err) {
  if (err && err.status === 429) {
    return "⏳ Daily AI quota reached. Please try again later (or use a paid Gemini API key).";
  }
  if (err && err.status === 502) {
    return "Error: the AI service failed to respond. Please try again.";
  }
  return "Error: could not reach EduGenie backend.";
}

// ---------- Q&A ----------
document.getElementById("qa-submit").addEventListener("click", async () => {
  const question = document.getElementById("qa-input").value.trim();
  const resultBox = document.getElementById("qa-result");

  if (!question) {
    resultBox.textContent = "Please type a question first.";
    return;
  }

  resultBox.textContent = "Thinking...";
  try {
    const data = await callApi("/ask", { question });
    resultBox.textContent = data.response;
    saveToHistory("Q&A", question, data.response);
  } catch (err) {
    resultBox.textContent = friendlyErrorMessage(err);
  }
});

// ---------- QUIZ ----------
document.getElementById("quiz-submit").addEventListener("click", async () => {
  const topic = document.getElementById("quiz-topic").value.trim();
  const num_questions = parseInt(document.getElementById("quiz-count").value, 10);
  const difficulty = document.getElementById("quiz-difficulty").value;
  const resultBox = document.getElementById("quiz-result");

  if (!topic) {
    resultBox.textContent = "Please enter a topic first.";
    return;
  }

  resultBox.innerHTML = '<p class="text-indigo-500 italic">Generating quiz...</p>';
  try {
    const data = await callApi("/quiz/generate", { topic, num_questions, difficulty });

    if (data.error) {
      resultBox.textContent = "Error: " + data.error;
      return;
    }

    resultBox.innerHTML = data.questions
      .map(
        (q, i) => `
        <div class="mb-5 pb-4 border-b border-gray-200 last:border-b-0">
          <p class="font-semibold mb-2">${i + 1}. ${q.question}</p>
          <ul class="pl-5 mb-2 space-y-1">
            ${Object.entries(q.options)
              .map(
                ([letter, text]) => `
                <li class="${letter === q.correct_answer ? "text-green-600 font-semibold" : ""}">
                  ${letter}. ${text}
                </li>`
              )
              .join("")}
          </ul>
          <p class="text-sm text-gray-500"><strong>Explanation:</strong> ${q.explanation}</p>
        </div>`
      )
      .join("");

    saveToHistory("Quiz", topic, `${data.questions.length} questions generated`);
  } catch (err) {
    resultBox.textContent = friendlyErrorMessage(err);
  }
});

// ---------- SUMMARIZE ----------
document.getElementById("summarize-submit").addEventListener("click", async () => {
  const text = document.getElementById("summarize-input").value.trim();
  const length = document.getElementById("summarize-length").value;
  const resultBox = document.getElementById("summarize-result");

  if (!text) {
    resultBox.textContent = "Please paste some text first.";
    return;
  }

  resultBox.textContent = "Summarizing...";
  try {
    const data = await callApi("/summarize/text", { text, length });
    resultBox.textContent = data.summary;
    saveToHistory("Summarize", text.slice(0, 60) + "...", data.summary);
  } catch (err) {
    resultBox.textContent = friendlyErrorMessage(err);
  }
});

// ---------- LEARNING PATH ----------
document.getElementById("lp-submit").addEventListener("click", async () => {
  const topic = document.getElementById("lp-topic").value.trim();
  const current_level = document.getElementById("lp-level").value;
  const resultBox = document.getElementById("lp-result");

  if (!topic) {
    resultBox.textContent = "Please enter a topic first.";
    return;
  }

  resultBox.innerHTML = '<p class="text-indigo-500 italic">Generating learning path...</p>';
  try {
    const data = await callApi("/learning-path/generate", { topic, current_level });

    if (data.error) {
      resultBox.textContent = "Error: " + data.error;
      return;
    }

    resultBox.innerHTML = data.path
      .map(
        (stage) => `
        <div class="mb-5">
          <h3 class="font-bold text-indigo-700 mb-1">${stage.stage}</h3>
          <ul class="list-disc pl-5 mb-2 space-y-1">
            ${stage.subtopics.map((s) => `<li>${s}</li>`).join("")}
          </ul>
          <p class="text-sm text-gray-500"><strong>Recommendation:</strong> ${stage.recommendation}</p>
        </div>`
      )
      .join("");

    saveToHistory("Learning Path", topic, `${data.path.length} stages generated`);
  } catch (err) {
    resultBox.textContent = friendlyErrorMessage(err);
  }
});
