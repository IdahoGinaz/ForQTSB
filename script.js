const API_URL = "https://forqtsb.onrender.com/upload";
const HEALTH_URL = "https://forqtsb.onrender.com/";

const fileInput = document.getElementById("fileInput");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const diagPre = document.getElementById("diagPre");

// Check if backend is awake
async function checkBackendReady() {
  statusEl.textContent = "Checking server status…";
  try {
    const res = await fetch(HEALTH_URL);
    const data = await res.json();
    if (data.status === "ok") {
      statusEl.textContent = "Server is ready. You can upload a file.";
      fileInput.disabled = false;
    } else {
      statusEl.textContent = "Server responded but not ready.";
    }
  } catch (err) {
    statusEl.textContent = "Waking up the server… please wait";
    setTimeout(checkBackendReady, 5000); // retry after 5s
  }
}

checkBackendReady();
fileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) {
    statusEl.textContent = "No file selected.";
    return;
  }

  statusEl.textContent = `Selected: ${file.name}`;
  resultEl.textContent = "";
  diagPre.textContent = "";

  const formData = new FormData();
  formData.append("file", file);

  const start = performance.now();

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      body: formData,
    });

    const elapsed = (performance.now() - start) | 0;

    let data = null;
    try {
      data = await res.json();
    } catch (jsonErr) {
      statusEl.textContent = `Server error (${res.status}): invalid JSON`;
      diagPre.textContent = `Raw response: ${await res.text()}`;
      return;
    }

    statusEl.textContent = `Response in ${elapsed} ms (HTTP ${res.status})`;

    if (data.error) {
      resultEl.textContent = `Error: ${data.error}${data.message ? " — " + data.message : ""}`;
      diagPre.textContent = JSON.stringify(data, null, 2);
      return;
    }

    if (data.found) {
      resultEl.textContent = `VO₂ max: ${data.vo2} (raw: ${data.raw})`;
    } else {
      resultEl.textContent = data.message || "VO₂ max not found";
    }

    diagPre.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    statusEl.textContent = "Upload failed.";
    resultEl.textContent = err.message;
    diagPre.textContent = String(err);
  }
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").catch(() => {});
}

