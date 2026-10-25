// If the page is served by the backend (http://127.0.0.1:8000), "" means same origin.
// If you open index.html directly from disk, fall back to the local backend URL.
const API_URL = location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

const form = document.getElementById("form");
const messageBox = document.getElementById("message");
const submitBtn = document.getElementById("submit");
const errorEl = document.getElementById("error");
const resultEl = document.getElementById("result");

// Escape text before putting it in innerHTML (the AI summary is untrusted).
function esc(value) {
  const div = document.createElement("div");
  div.textContent = String(value);
  return div.innerHTML;
}

function row(label, value) {
  return `<div><dt>${esc(label)}</dt><dd>${value}</dd></div>`;
}

function renderRejected(data) {
  resultEl.className = "card rejected";
  const tokens = data.token_metadata
    ? `<p class="muted">Tokens used: ${esc(data.token_metadata.total_tokens)}</p>`
    : "";
  resultEl.innerHTML = `
    <h2>Rejected <span class="badge badge-rejected">blocked</span></h2>
    <p>${esc(data.rejection_reason)}</p>
    ${tokens}`;
}

function renderAccepted(data) {
  const r = data.result;
  const p = r.priority_parameters;
  const t = r.token_metadata;
  resultEl.className = "card";
  resultEl.innerHTML = `
    <h2>Accepted <span class="badge badge-accepted">forwarded downstream</span></h2>
    <p>${esc(r.summary)}</p>
    <dl>
      ${row("Intent", esc(r.intent.replace(/_/g, " ")))}
      ${row("Risk", `<span class="badge badge-${esc(r.risk_profile)}" style="margin-left:0">${esc(r.risk_profile)}</span>`)}
      ${row("Priority", `${esc(p.priority)} (1 = most urgent)`)}
      ${row("Response target", `${esc(p.sla_hours)} h`)}
      ${row("Human review", p.requires_human_review ? "Required" : "Not required")}
      ${row("Confidence", `${Math.round(r.confidence * 100)}%`)}
    </dl>
    <h3>Token metadata</h3>
    <dl>
      ${row("Input", esc(t.input_tokens))}
      ${row("Output", esc(t.output_tokens))}
      ${row("Total", esc(t.total_tokens))}
    </dl>
    <details>
      <summary>Raw JSON</summary>
      <pre>${esc(JSON.stringify(r, null, 2))}</pre>
    </details>`;
}

function showError(text) {
  errorEl.textContent = text;
  errorEl.hidden = false;
}

messageBox.addEventListener("input", () => {
  submitBtn.disabled = messageBox.value.trim().length < 3;
});

document.querySelectorAll(".sample").forEach((btn) => {
  btn.addEventListener("click", () => {
    messageBox.value = btn.textContent;
    submitBtn.disabled = false;
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.hidden = true;
  resultEl.hidden = true;
  submitBtn.disabled = true;
  submitBtn.textContent = "Checking...";

  try {
    const res = await fetch(`${API_URL}/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: messageBox.value }),
    });

    if (res.status === 422) {
      showError("Invalid input: message must be 3-2000 characters.");
    } else if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      showError(body.detail || `Server error (${res.status})`);
    } else {
      const data = await res.json();
      data.accepted ? renderAccepted(data) : renderRejected(data);
      resultEl.hidden = false;
    }
  } catch (err) {
    showError("Cannot reach the backend. Is it running on http://127.0.0.1:8000 ?");
  } finally {
    submitBtn.textContent = "Submit";
    submitBtn.disabled = messageBox.value.trim().length < 3;
  }
});
