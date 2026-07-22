const API_BASE = "/api/summaries";

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function renderInlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+?)`/g, "<code>$1</code>");
}

function extractYoutubeVideoId(url) {
  const patterns = [
    /(?:v=)([0-9A-Za-z_-]{11})/,
    /youtu\.be\/([0-9A-Za-z_-]{11})/,
    /shorts\/([0-9A-Za-z_-]{11})/,
    /embed\/([0-9A-Za-z_-]{11})/,
  ];
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

function formatDate(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderSummary(summary) {
  const sourceLabel = summary.source_type === "youtube" ? "YouTube" : "PDF";
  const keyPoints = (summary.key_points || [])
    .map((point) => `<li>${renderInlineMarkdown(point)}</li>`)
    .join("");

  const videoId =
    summary.source_type === "youtube" ? extractYoutubeVideoId(summary.source_ref || "") : null;

  let chaptersHtml = "";
  if (summary.chapters && summary.chapters.length > 0) {
    const items = summary.chapters
      .map((chapter) => {
        const timeLabel = formatSeconds(chapter.start_seconds);
        const timeHtml = videoId
          ? `<button type="button" class="chapter-time" data-seconds="${chapter.start_seconds}">${timeLabel}</button>`
          : `<span class="chapter-time">${timeLabel}</span>`;
        return `
          <div class="chapter-item">
            ${timeHtml}<strong>${escapeHtml(chapter.title)}</strong>
            <p>${renderInlineMarkdown(chapter.summary)}</p>
          </div>
        `;
      })
      .join("");
    chaptersHtml = `<h3>챕터별 요약</h3>${items}`;
  }

  const textPane = `
    <div class="summary-text">
      <span class="badge">${sourceLabel}</span>
      <h2>${escapeHtml(summary.source_title)}</h2>
      <div class="one-liner">${renderInlineMarkdown(summary.one_line_summary)}</div>
      <h3>핵심 포인트</h3>
      <ul>${keyPoints}</ul>
      ${chaptersHtml}
    </div>
  `;

  if (!videoId) {
    return `<div class="summary-card">${textPane}</div>`;
  }

  return `
    <div class="summary-card with-video">
      <div class="video-pane">
        <div class="video-embed">
          <iframe
            src="https://www.youtube.com/embed/${videoId}?start=0"
            title="YouTube video player"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen
          ></iframe>
        </div>
      </div>
      ${textPane}
    </div>
  `;
}

function attachChapterHandlers(containerEl) {
  const iframe = containerEl.querySelector(".video-embed iframe");
  if (!iframe) return;
  const baseSrc = iframe.src.split("?")[0];
  containerEl.querySelectorAll(".chapter-time[data-seconds]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const seconds = Math.floor(parseFloat(btn.dataset.seconds) || 0);
      iframe.src = `${baseSrc}?start=${seconds}&autoplay=1`;
    });
  });
}

function formatSeconds(totalSeconds) {
  const seconds = Math.floor(totalSeconds || 0);
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const mm = String(m).padStart(2, "0");
  const ss = String(s).padStart(2, "0");
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

// ---------- Tabs ----------
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "history") {
      loadHistory();
    }
  });
});

document.querySelectorAll(".source-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".source-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("youtube-form").classList.toggle("hidden", btn.dataset.source !== "youtube");
    document.getElementById("pdf-form").classList.toggle("hidden", btn.dataset.source !== "pdf");
  });
});

// ---------- Create summary ----------
const createLoading = document.getElementById("create-loading");
const createError = document.getElementById("create-error");
const createResult = document.getElementById("create-result");

function setCreateState({ loading = false, error = null, result = null }) {
  createLoading.classList.toggle("hidden", !loading);
  if (error) {
    createError.textContent = error;
    createError.classList.remove("hidden");
  } else {
    createError.classList.add("hidden");
  }
  if (result) {
    createResult.innerHTML = renderSummary(result);
    attachChapterHandlers(createResult);
    createResult.classList.remove("hidden");
  } else if (!loading) {
    createResult.classList.add("hidden");
  }
}

async function handleSubmit(fetchPromise, submitButton) {
  submitButton.disabled = true;
  setCreateState({ loading: true });
  try {
    const response = await fetchPromise;
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || "요약 생성 중 오류가 발생했습니다.");
    }
    setCreateState({ loading: false, result: data });
  } catch (err) {
    setCreateState({ loading: false, error: err.message });
  } finally {
    submitButton.disabled = false;
  }
}

document.getElementById("youtube-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const url = document.getElementById("youtube-url").value.trim();
  const submitButton = e.target.querySelector("button[type=submit]");
  handleSubmit(
    fetch(`${API_BASE}/youtube`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }),
    submitButton
  );
});

document.getElementById("pdf-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const fileInput = document.getElementById("pdf-file");
  const file = fileInput.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append("file", file);
  const submitButton = e.target.querySelector("button[type=submit]");
  handleSubmit(fetch(`${API_BASE}/pdf`, { method: "POST", body: formData }), submitButton);
});

// ---------- History ----------
const historyListEl = document.getElementById("history-list");
const historyDetailEl = document.getElementById("history-detail");
let selectedSummaryId = null;

async function loadHistory() {
  historyListEl.innerHTML = `<p class="empty">불러오는 중...</p>`;
  try {
    const response = await fetch(API_BASE);
    if (!response.ok) throw new Error("히스토리를 불러오지 못했습니다.");
    const items = await response.json();
    renderHistoryList(items);
  } catch (err) {
    historyListEl.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
  }
}

function renderHistoryList(items) {
  if (!items || items.length === 0) {
    historyListEl.innerHTML = `<p class="empty">아직 생성된 요약이 없어요.</p>`;
    return;
  }

  historyListEl.innerHTML = items
    .map((item) => {
      const sourceLabel = item.source_type === "youtube" ? "YouTube" : "PDF";
      return `
        <div class="history-item ${item.id === selectedSummaryId ? "active" : ""}" data-id="${escapeHtml(item.id)}">
          <div class="item-info">
            <div class="item-title">${escapeHtml(item.source_title)}</div>
            <div class="item-meta">${sourceLabel} · ${formatDate(item.created_at)}</div>
          </div>
          <button class="delete-btn" data-id="${escapeHtml(item.id)}" title="삭제">✕</button>
        </div>
      `;
    })
    .join("");

  historyListEl.querySelectorAll(".history-item").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (e.target.closest(".delete-btn")) return;
      selectedSummaryId = el.dataset.id;
      historyListEl.querySelectorAll(".history-item").forEach((item) => {
        item.classList.toggle("active", item.dataset.id === selectedSummaryId);
      });
      loadDetail(el.dataset.id);
    });
  });

  historyListEl.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const id = btn.dataset.id;
      if (!confirm("이 요약을 삭제할까요?")) return;
      try {
        const response = await fetch(`${API_BASE}/${id}`, { method: "DELETE" });
        if (!response.ok) throw new Error("삭제에 실패했습니다.");
        if (selectedSummaryId === id) {
          selectedSummaryId = null;
          historyDetailEl.innerHTML = `<p class="empty">목록에서 항목을 선택하세요.</p>`;
        }
        loadHistory();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

async function loadDetail(id) {
  historyDetailEl.innerHTML = `<p class="empty">불러오는 중...</p>`;
  try {
    const response = await fetch(`${API_BASE}/${id}`);
    if (!response.ok) throw new Error("상세 정보를 불러오지 못했습니다.");
    const summary = await response.json();
    historyDetailEl.innerHTML = renderSummary(summary);
    attachChapterHandlers(historyDetailEl);
  } catch (err) {
    historyDetailEl.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
  }
}
