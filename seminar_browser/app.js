const state = {
  data: null,
  tab: "overview",
  query: "",
  tool: "",
  useCase: "",
  year: "",
  angle: "",
  latestOnly: false,
  hideShort: false,
  sort: "date",
  visibleLimit: 80,
};

const els = {};
let latestIds = new Set();
let toolMap = new Map();
let useCaseMap = new Map();

function $(selector) {
  return document.querySelector(selector);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function compact(value, max = 180) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

function queryTokens() {
  return state.query
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
}

function lectureText(video) {
  const lecture = video.lecture || {};
  return [
    lecture.title,
    lecture.module?.name,
    lecture.type,
    lecture.difficulty,
    lecture.audience,
    lecture.recommendedUse,
    video.review?.status,
    video.review?.priority,
    ...(video.review?.reasons || []),
    ...(lecture.outcomes || []),
    ...(lecture.deliverables || []),
    ...(lecture.features || []),
    ...(lecture.procedure || []),
    ...(lecture.casePoints || []),
    ...(lecture.nonToolPoints || []),
  ].join(" ");
}

function highlight(text, tokens = queryTokens()) {
  let safe = escapeHtml(text);
  if (!tokens.length) return safe;
  const pattern = tokens.map(escapeRegExp).join("|");
  if (!pattern) return safe;
  return safe.replace(new RegExp(`(${pattern})`, "gi"), "<mark>$1</mark>");
}

function scoreVideo(video, tokens) {
  if (!tokens.length) return 0;
  const title = video.title.toLowerCase();
  const summary = video.summary.toLowerCase();
  const toolNames = video.toolNames.join(" ").toLowerCase();
  const useNames = video.useCaseNames.join(" ").toLowerCase();
  const lecture = lectureText(video).toLowerCase();
  const search = video.searchText.toLowerCase();
  let score = 0;
  for (const token of tokens) {
    if (title.includes(token)) score += 90;
    if (lecture.includes(token)) score += 42;
    if (summary.includes(token)) score += 30;
    if (toolNames.includes(token)) score += 25;
    if (useNames.includes(token)) score += 18;
    const firstHit = search.indexOf(token);
    if (firstHit >= 0) score += 8 + Math.max(0, 10 - Math.floor(firstHit / 800));
  }
  return score;
}

function videoHasAllTokens(video, tokens) {
  if (!tokens.length) return true;
  const haystack = [
    video.title,
    video.summary,
    video.toolNames.join(" "),
    video.useCaseNames.join(" "),
    lectureText(video),
    video.searchText,
  ]
    .join(" ")
    .toLowerCase();
  return tokens.every((token) => haystack.includes(token));
}

function transcriptHref(path) {
  return `../${path}`;
}

function initElements() {
  Object.assign(els, {
    generatedMeta: $("#generatedMeta"),
    stats: $("#stats"),
    searchInput: $("#searchInput"),
    sortSelect: $("#sortSelect"),
    yearSelect: $("#yearSelect"),
    latestOnly: $("#latestOnly"),
    hideShort: $("#hideShort"),
    resetButton: $("#resetButton"),
    toolFilter: $("#toolFilter"),
    useCaseFilter: $("#useCaseFilter"),
    angleList: $("#angleList"),
    activeSummary: $("#activeSummary"),
    selectedTags: $("#selectedTags"),
    overviewPanel: $("#overviewPanel"),
    resultCount: $("#resultCount"),
    videoList: $("#videoList"),
    lectureCount: $("#lectureCount"),
    lectureTags: $("#lectureTags"),
    lectureStats: $("#lectureStats"),
    lectureList: $("#lectureList"),
    catalogCount: $("#catalogCount"),
    catalogPanel: $("#catalogPanel"),
    reviewCount: $("#reviewCount"),
    reviewPanel: $("#reviewPanel"),
    toolCards: $("#toolCards"),
    revisionGroups: $("#revisionGroups"),
    qualityPanel: $("#qualityPanel"),
    detailDialog: $("#detailDialog"),
    detailContent: $("#detailContent"),
    loadError: $("#loadError"),
  });

  els.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value;
    state.visibleLimit = 80;
    render();
  });
  els.sortSelect.addEventListener("change", (event) => {
    state.sort = event.target.value;
    renderVideos();
  });
  els.yearSelect.addEventListener("change", (event) => {
    state.year = event.target.value;
    state.visibleLimit = 80;
    render();
  });
  els.latestOnly.addEventListener("change", (event) => {
    state.latestOnly = event.target.checked;
    state.visibleLimit = 80;
    render();
  });
  els.hideShort.addEventListener("change", (event) => {
    state.hideShort = event.target.checked;
    state.visibleLimit = 80;
    render();
  });
  els.resetButton.addEventListener("click", resetFilters);
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchTab(tab.dataset.tab));
  });
  els.detailDialog.addEventListener("click", (event) => {
    if (event.target === els.detailDialog) els.detailDialog.close();
  });
}

async function loadData() {
  try {
    const response = await fetch("./data/seminar-data.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
  } catch (error) {
    console.error(error);
    els.loadError.hidden = false;
    return;
  }

  latestIds = new Set();
  state.data.revisionGroups.forEach((group) => latestIds.add(group.latest.id));
  state.data.tools.forEach((tool) => {
    if (tool.latestVideo) latestIds.add(tool.latestVideo.id);
  });
  toolMap = new Map(state.data.tools.map((tool) => [tool.id, tool]));
  useCaseMap = new Map(state.data.useCases.map((useCase) => [useCase.id, useCase]));
  renderStatic();
  render();
}

function renderStatic() {
  const { channel, generatedAt, videos, tools } = state.data;
  const latest = videos[0];
  const fullCount = videos.filter((video) => video.transcriptChars > 0).length;
  const shortCount = videos.filter((video) => video.transcriptChars < 800).length;
  els.generatedMeta.textContent = `${generatedAt}生成 / ${channel.videoCount}本 / 最新 ${latest.date}`;
  $("#channelLink").href = channel.url;

  els.stats.innerHTML = [
    stat("対象動画", `${channel.videoCount}本`, "現行公開動画"),
    stat("文字起こし", `${fullCount}本`, "全件取得済み"),
    stat("ツール分類", `${tools.length}件`, "主分類で560本を整理"),
    stat("最新版候補", `${latestIds.size}本`, "ツール・重複テーマの優先動画"),
    stat("短文要確認", `${shortCount}本`, "800字未満"),
  ].join("");

  const years = [...new Set(videos.map((video) => video.year))].sort().reverse();
  els.yearSelect.innerHTML = `<option value="">全年</option>${years
    .map((year) => `<option value="${year}">${year}</option>`)
    .join("")}`;

  renderAngleFilters();
  renderToolFilters();
  renderUseCaseFilters();
  renderOverview();
  renderReview();
  renderTools();
  renderLatest();
  renderQuality();
}

function stat(label, value, note) {
  return `
    <article class="stat-card">
      <div class="stat-label">${escapeHtml(label)}</div>
      <div class="stat-value">${escapeHtml(value)}</div>
      <div class="small">${escapeHtml(note)}</div>
    </article>
  `;
}

function renderAngleFilters() {
  const allButton = `
    <button class="angle-button active" data-angle="">
      <span>すべて</span><span class="count-pill">${state.data.videos.length}</span>
    </button>
  `;
  const buttons = state.data.seminarAngles
    .map((angle, index) => {
      const count = state.data.videos.filter((video) => angle.tools.includes(video.primaryTool)).length;
      return `
        <button class="angle-button" data-angle="${index}">
          <span>${escapeHtml(angle.title)}</span><span class="count-pill">${count}</span>
        </button>
      `;
    })
    .join("");
  els.angleList.innerHTML = allButton + buttons;
  els.angleList.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.angle = button.dataset.angle;
      state.visibleLimit = 80;
      render();
    });
  });
}

function renderToolFilters() {
  const buttons = [
    `<button class="filter-button active" data-tool=""><span>すべて</span><span class="count-pill">${state.data.videos.length}</span></button>`,
    ...state.data.tools.map(
      (tool) => `
        <button class="filter-button" data-tool="${tool.id}">
          <span>${escapeHtml(tool.name)}</span><span class="count-pill">${tool.videoCount}</span>
        </button>
      `,
    ),
  ].join("");
  els.toolFilter.innerHTML = buttons;
  els.toolFilter.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.tool = button.dataset.tool;
      state.visibleLimit = 80;
      render();
    });
  });
}

function renderUseCaseFilters() {
  const buttons = [
    `<button class="filter-button active" data-use-case=""><span>すべて</span><span class="count-pill">${state.data.videos.length}</span></button>`,
    ...state.data.useCases.map(
      (useCase) => `
        <button class="filter-button" data-use-case="${useCase.id}">
          <span>${escapeHtml(useCase.name)}</span><span class="count-pill">${useCase.videoCount}</span>
        </button>
      `,
    ),
  ].join("");
  els.useCaseFilter.innerHTML = buttons;
  els.useCaseFilter.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.useCase = button.dataset.useCase;
      state.visibleLimit = 80;
      render();
    });
  });
}

function updateFilterButtons() {
  els.toolFilter.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tool === state.tool);
  });
  els.useCaseFilter.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.dataset.useCase === state.useCase);
  });
  els.angleList.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("active", button.dataset.angle === state.angle);
  });
}

function resetFilters() {
  Object.assign(state, {
    query: "",
    tool: "",
    useCase: "",
    year: "",
    angle: "",
    latestOnly: false,
    hideShort: false,
    sort: "date",
    visibleLimit: 80,
  });
  els.searchInput.value = "";
  els.yearSelect.value = "";
  els.latestOnly.checked = false;
  els.hideShort.checked = false;
  els.sortSelect.value = "date";
  render();
}

function switchTab(tabName) {
  state.tab = tabName;
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === tabName);
  });
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === `${tabName}View`);
  });
}

function filteredVideos() {
  const tokens = queryTokens();
  const angle = state.angle ? state.data.seminarAngles[Number(state.angle)] : null;
  let rows = state.data.videos.map((video) => ({ ...video, _score: scoreVideo(video, tokens) }));

  rows = rows.filter((video) => {
    if (state.query && !videoHasAllTokens(video, tokens)) return false;
    if (state.tool && video.primaryTool !== state.tool) return false;
    if (state.useCase && !video.useCases.includes(state.useCase)) return false;
    if (state.year && video.year !== state.year) return false;
    if (angle && !angle.tools.includes(video.primaryTool)) return false;
    if (state.latestOnly && !latestIds.has(video.id)) return false;
    if (state.hideShort && video.transcriptChars < 800) return false;
    return true;
  });

  rows.sort((a, b) => {
    if (state.sort === "relevance" && tokens.length) {
      return b._score - a._score || b.date.localeCompare(a.date);
    }
    if (state.sort === "length") {
      return b.transcriptChars - a.transcriptChars || b.date.localeCompare(a.date);
    }
    return b.date.localeCompare(a.date);
  });
  return rows;
}

function render() {
  updateFilterButtons();
  renderActiveSummary();
  renderSelectedTags();
  renderVideos();
  renderLectures();
  renderCatalog();
  renderReview();
}

function renderActiveSummary() {
  const lines = [];
  if (state.angle) {
    const angle = state.data.seminarAngles[Number(state.angle)];
    lines.push(`<strong>${escapeHtml(angle.title)}</strong>: ${escapeHtml(angle.pitch)} 対象: ${escapeHtml(angle.target)}`);
  }
  if (state.tool) {
    const tool = toolMap.get(state.tool);
    lines.push(`<strong>${escapeHtml(tool.name)}</strong>: ${escapeHtml(tool.capabilities[0])}`);
  }
  if (state.useCase) {
    const useCase = useCaseMap.get(state.useCase);
    lines.push(`<strong>${escapeHtml(useCase.name)}</strong>の観点で絞り込み中`);
  }
  if (state.query) lines.push(`検索語: <strong>${escapeHtml(state.query)}</strong>`);
  els.activeSummary.innerHTML = lines.length
    ? lines.join("<br />")
    : "ツール名だけでなく、実際の業務用途、手順、事例の観点で横断検索できます。";
}

function renderSelectedTags() {
  const tags = [];
  if (state.angle) tags.push(state.data.seminarAngles[Number(state.angle)].title);
  if (state.tool) tags.push(toolMap.get(state.tool).name);
  if (state.useCase) tags.push(useCaseMap.get(state.useCase).name);
  if (state.year) tags.push(`${state.year}年`);
  if (state.latestOnly) tags.push("最新版候補");
  if (state.hideShort) tags.push("短文除外");
  els.selectedTags.innerHTML = tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
}

function renderVideos() {
  if (!state.data) return;
  const rows = filteredVideos();
  els.resultCount.textContent = `${rows.length}本ヒット / ${state.data.videos.length}本`;
  const visible = rows.slice(0, state.visibleLimit);
  els.videoList.innerHTML = visible.map(videoCard).join("");

  if (!rows.length) {
    els.videoList.innerHTML = `<div class="empty">条件に合う動画がありません。検索語やフィルタを調整してください。</div>`;
    return;
  }
  if (rows.length > state.visibleLimit) {
    const button = document.createElement("button");
    button.className = "button ghost";
    button.textContent = `さらに表示 (${rows.length - state.visibleLimit}本)`;
    button.addEventListener("click", () => {
      state.visibleLimit += 80;
      renderVideos();
    });
    els.videoList.appendChild(button);
  }

  els.videoList.querySelectorAll("[data-detail-id]").forEach((button) => {
    button.addEventListener("click", () => openDetail(button.dataset.detailId));
  });
}

function renderOverview() {
  const data = state.data;
  const quality = data.transcriptQuality || {};
  const reviewSummary = data.reviewSummary || {};
  const topModules = data.lectureModules
    .slice(0, 8)
    .map(
      (module) => `
        <article class="overview-item">
          <div>
            <h4>${escapeHtml(module.name)}</h4>
            <p>${escapeHtml((module.topTools || []).map((tool) => `${tool.name} ${tool.count}本`).join(" / "))}</p>
          </div>
          <strong>${module.videoCount}本 <span>${module.ratio}%</span></strong>
        </article>
      `,
    )
    .join("");
  const topTools = data.tools
    .slice(0, 10)
    .map(
      (tool) => `
        <button class="overview-tool" data-set-tool="${tool.id}">
          <span>${escapeHtml(tool.name)}</span>
          <strong>${tool.videoCount}本</strong>
        </button>
      `,
    )
    .join("");
  const sourceText = (quality.sourceCounts || [])
    .map((source) => `${source.name}: ${source.count}本`)
    .join(" / ");
  const lengthRows = (quality.lengthBuckets || [])
    .map(
      (bucket) => `
        <div class="ratio-row">
          <span>${escapeHtml(bucket.name)}</span>
          <strong>${bucket.count}本</strong>
        </div>
      `,
    )
    .join("");
  const featureRows = (data.featureCatalog || [])
    .slice(0, 8)
    .map(
      (item) => `
        <li>
          <span>${escapeHtml(item.name)}</span>
          <strong>${item.count}本</strong>
        </li>
      `,
    )
    .join("");
  const shortVideos = (quality.shortVideos || [])
    .slice(0, 5)
    .map(
      (video) => `
        <a class="mini-video" href="${video.url}" target="_blank" rel="noreferrer">
          ${escapeHtml(video.date)} ${video.transcriptChars.toLocaleString()}字 ${escapeHtml(compact(video.title, 78))}
        </a>
      `,
    )
    .join("");

  els.overviewPanel.innerHTML = `
    <section class="overview-hero">
      <div>
        <p class="eyebrow">Channel map</p>
        <h3>560本から、Google Workspace講義に使える論点を横断整理</h3>
        <p>動画本文・講義候補・機能候補・成果物候補を同じ検索対象にしているため、ツール名だけでなく「在庫管理」「議事録」「権限」「内製化」のような業務テーマでも探せます。</p>
      </div>
      <div class="overview-score">
        <strong>${quality.withTranscript || data.videos.length}</strong>
        <span>文字起こしあり / ${data.videos.length}本</span>
      </div>
    </section>

    <section class="overview-grid">
      ${stat("講義モジュール", `${data.lectureModules.length}分類`, "全動画を講義テーマで整理")}
      ${stat("機能カタログ", `${(data.featureCatalog || []).length}項目`, "扱える機能・操作を抽出")}
      ${stat("平均文字数", `${(quality.avgChars || 0).toLocaleString()}字`, `中央値 ${(quality.medianChars || 0).toLocaleString()}字`)}
      ${stat("字幕ソース", sourceText || "unknown", "YouTube字幕由来")}
      ${stat("精査済み", `${reviewSummary.reviewed || 0}本`, `未精査 ${reviewSummary.unreviewed ?? data.videos.length}本`)}
    </section>

    <section class="handoff-guide">
      <div class="handoff-head">
        <p class="eyebrow">For review</p>
        <h3>共有された人は、まずここを見れば判断できます</h3>
      </div>
      <div class="handoff-grid">
        <article>
          <h4>見る順番</h4>
          <ol>
            <li>全体マップで、チャンネルのテーマ比率を確認</li>
            <li>精査状況で、未精査/精査優先の本数を確認</li>
            <li>講義候補で、どの講義を作れそうか確認</li>
            <li>機能カタログで、具体的な機能・成果物を確認</li>
            <li>必要な動画だけ詳細/Markdown全文/YouTubeで確認</li>
          </ol>
        </article>
        <article>
          <h4>このURLで分かること</h4>
          <ul>
            <li>560本の中で、どのツール・論点が多いか</li>
            <li>各動画を講義化するなら何を扱えるか</li>
            <li>スプレッドシート、AppSheet、AI、会議、DXなどの具体テーマ</li>
            <li>最新版を優先すべき重複テーマ</li>
          </ul>
        </article>
        <article>
          <h4>注意点</h4>
          <ul>
            <li>文字起こしはYouTube字幕由来で、人手校正済みではありません</li>
            <li>講義候補は機械抽出なので、精査済みになるまで最終採用しないでください</li>
            <li>短文・告知寄り動画は品質確認タブで分けて見てください</li>
            <li>社外共有前の最終資料化には、別途講義構成への落とし込みが必要です</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="overview-columns">
      <article class="overview-card">
        <h3>多い講義テーマ</h3>
        <div class="overview-list">${topModules}</div>
      </article>
      <article class="overview-card">
        <h3>主なツール分類</h3>
        <div class="overview-tool-list">${topTools}</div>
      </article>
    </section>

    <section class="overview-columns">
      <article class="overview-card">
        <h3>よく出る機能・論点</h3>
        <ul class="feature-rank">${featureRows}</ul>
      </article>
      <article class="overview-card">
        <h3>文字起こし品質</h3>
        <p class="quality-note">${escapeHtml(quality.note || "")}</p>
        <div class="ratio-table">${lengthRows}</div>
        <div class="mini-video-list">${shortVideos}</div>
      </article>
    </section>
  `;

  els.overviewPanel.querySelectorAll("[data-set-tool]").forEach((button) => {
    button.addEventListener("click", () => {
      state.tool = button.dataset.setTool;
      state.visibleLimit = 80;
      switchTab("videos");
      render();
    });
  });
}

function countBy(rows, getter) {
  const counter = new Map();
  rows.forEach((row) => {
    const key = getter(row);
    if (!key) return;
    counter.set(key, (counter.get(key) || 0) + 1);
  });
  return [...counter.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "ja"));
}

function lectureStat(title, entries, total) {
  const rows = entries
    .slice(0, 8)
    .map(([name, count]) => {
      const ratio = total ? Math.round((count / total) * 1000) / 10 : 0;
      return `
        <div class="ratio-row">
          <span>${escapeHtml(name)}</span>
          <strong>${count}本 / ${ratio}%</strong>
        </div>
      `;
    })
    .join("");
  return `
    <article class="lecture-stat-card">
      <h4>${escapeHtml(title)}</h4>
      ${rows || `<div class="small">該当なし</div>`}
    </article>
  `;
}

function renderList(items, emptyText = "該当なし") {
  if (!items || !items.length) return `<div class="empty-inline">${escapeHtml(emptyText)}</div>`;
  return `<ul class="bullet-list">${items.map((item) => `<li>${highlight(item)}</li>`).join("")}</ul>`;
}

function renderLectures() {
  if (!state.data) return;
  const rows = filteredVideos();
  els.lectureCount.textContent = `${rows.length}件 / 全${state.data.videos.length}本`;
  els.lectureTags.innerHTML = els.selectedTags.innerHTML;

  els.lectureStats.innerHTML = [
    lectureStat("講義モジュール比率", countBy(rows, (video) => video.lecture?.module?.name), rows.length),
    lectureStat("講義タイプ比率", countBy(rows, (video) => video.lecture?.type), rows.length),
    lectureStat("対象者比率", countBy(rows, (video) => video.lecture?.audience), rows.length),
  ].join("");

  const visible = rows.slice(0, state.visibleLimit);
  els.lectureList.innerHTML = visible.map(lectureCard).join("");

  if (!rows.length) {
    els.lectureList.innerHTML = `<div class="empty">条件に合う講義候補がありません。</div>`;
    return;
  }
  if (rows.length > state.visibleLimit) {
    const button = document.createElement("button");
    button.className = "button ghost";
    button.textContent = `さらに表示 (${rows.length - state.visibleLimit}件)`;
    button.addEventListener("click", () => {
      state.visibleLimit += 80;
      render();
    });
    els.lectureList.appendChild(button);
  }
  els.lectureList.querySelectorAll("[data-detail-id]").forEach((button) => {
    button.addEventListener("click", () => openDetail(button.dataset.detailId));
  });
}

function lectureCard(video) {
  const lecture = video.lecture || {};
  const tags = [
    `<span class="tag tool">${escapeHtml(video.primaryToolName)}</span>`,
    `<span class="tag">${escapeHtml(lecture.module?.name || "")}</span>`,
    `<span class="tag use">${escapeHtml(lecture.type || "")}</span>`,
    `<span class="tag">${escapeHtml(lecture.difficulty || "")}</span>`,
  ];
  if (video.review) tags.push(reviewStatusTag(video.review));
  return `
    <article class="lecture-card">
      <div class="lecture-card-head">
        <div>
          <div class="video-meta">
            <span>${escapeHtml(video.date)}</span>
            <span>${video.transcriptChars.toLocaleString()}字</span>
            <span>${escapeHtml(lecture.recommendedUse || "")}</span>
          </div>
          <h4>${highlight(lecture.title || video.title)}</h4>
          <a class="video-title-link source-title" href="${video.url}" target="_blank" rel="noreferrer">${highlight(video.title)}</a>
        </div>
        <button class="detail-button" data-detail-id="${video.id}">動画詳細</button>
      </div>
      <div class="tag-row">${tags.join("")}</div>
      <div class="lecture-grid">
        <section>
          <h5>作る/見せる成果物</h5>
          ${renderList(lecture.deliverables)}
        </section>
        <section>
          <h5>扱う機能・操作</h5>
          ${renderList(lecture.features)}
        </section>
        <section>
          <h5>進め方</h5>
          ${renderList(lecture.procedure)}
        </section>
        <section>
          <h5>事例・ツール外論点</h5>
          ${renderList([...(lecture.casePoints || []), ...(lecture.nonToolPoints || [])], "補足論点なし")}
        </section>
      </div>
    </article>
  `;
}

function buildFeatureRows(rows) {
  const map = new Map();
  rows.forEach((video) => {
    (video.lecture?.features || []).forEach((feature) => {
      if (!map.has(feature)) {
        map.set(feature, { name: feature, count: 0, tools: new Map(), videos: [] });
      }
      const item = map.get(feature);
      item.count += 1;
      item.tools.set(video.primaryToolName, (item.tools.get(video.primaryToolName) || 0) + 1);
      if (item.videos.length < 8) item.videos.push(video);
    });
  });
  return [...map.values()]
    .map((item) => ({
      ...item,
      tools: [...item.tools.entries()].sort((a, b) => b[1] - a[1]),
    }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, "ja"));
}

function renderCatalog() {
  if (!state.data) return;
  const videos = filteredVideos();
  const rows = buildFeatureRows(videos);
  els.catalogCount.textContent = `${rows.length}項目 / 対象${videos.length}本`;
  if (!rows.length) {
    els.catalogPanel.innerHTML = `<div class="empty">条件に合う機能項目がありません。</div>`;
    return;
  }
  els.catalogPanel.innerHTML = rows.map((item) => catalogCard(item, videos.length)).join("");
  els.catalogPanel.querySelectorAll("[data-detail-id]").forEach((button) => {
    button.addEventListener("click", () => openDetail(button.dataset.detailId));
  });
}

function catalogCard(item, total) {
  const ratio = total ? Math.round((item.count / total) * 1000) / 10 : 0;
  const tools = item.tools
    .slice(0, 5)
    .map(([name, count]) => `<span class="tag tool">${escapeHtml(name)} ${count}</span>`)
    .join("");
  const videos = item.videos
    .map(
      (video) => `
        <li>
          <button class="text-button" data-detail-id="${video.id}">${escapeHtml(video.date)} ${escapeHtml(compact(video.title, 86))}</button>
        </li>
      `,
    )
    .join("");
  return `
    <article class="catalog-card">
      <div class="catalog-card-head">
        <div>
          <h4>${highlight(item.name)}</h4>
          <div class="tag-row">${tools}</div>
        </div>
        <div class="tool-count">${item.count}<span>本</span><small>${ratio}%</small></div>
      </div>
      <ul class="older-list">${videos}</ul>
    </article>
  `;
}

function reviewStatusTag(review) {
  if (!review) return "";
  const className = review.status === "精査済み" ? "review-done" : review.priority === "高" ? "review-high" : review.priority === "中" ? "review-mid" : "review-low";
  return `<span class="tag ${className}">${escapeHtml(review.status)} / ${escapeHtml(review.priority)}</span>`;
}

function renderReview() {
  if (!state.data) return;
  const summary = state.data.reviewSummary || {};
  const rows = filteredVideos()
    .filter((video) => video.review)
    .sort((a, b) => (b.review.priorityScore || 0) - (a.review.priorityScore || 0) || b.date.localeCompare(a.date));
  els.reviewCount.textContent = `精査済み ${summary.reviewed || 0}本 / 未精査 ${summary.unreviewed || rows.length}本`;

  const statusRows = (summary.statusCounts || [])
    .map(
      (item) => `
        <div class="ratio-row">
          <span>${escapeHtml(item.name)}</span>
          <strong>${item.count}本</strong>
        </div>
      `,
    )
    .join("");
  const priorityRows = (summary.priorityCounts || [])
    .map(
      (item) => `
        <div class="ratio-row">
          <span>${escapeHtml(item.name)}</span>
          <strong>${item.count}本</strong>
        </div>
      `,
    )
    .join("");
  const visible = rows.slice(0, state.visibleLimit);
  const queue = visible.map(reviewCard).join("");

  els.reviewPanel.innerHTML = `
    <section class="review-warning">
      <h4>現在の状態</h4>
      <p>${escapeHtml(summary.note || "自動整理済みです。")}</p>
      <div class="review-stats">
        ${stat("精査済み", `${summary.reviewed || 0}本`, "手動確認済み")}
        ${stat("未精査", `${summary.unreviewed ?? rows.length}本`, "自動整理のみ")}
        ${stat("精査優先", `${summary.highPriority || 0}本`, "主教材/最新版/短文など")}
        ${stat("字幕要確認", `${summary.needsQualityCheck || 0}本`, "短文・低密度")}
      </div>
    </section>
    <section class="overview-columns">
      <article class="overview-card">
        <h3>ステータス別</h3>
        <div class="ratio-table">${statusRows}</div>
      </article>
      <article class="overview-card">
        <h3>優先度別</h3>
        <div class="ratio-table">${priorityRows}</div>
      </article>
    </section>
    <section>
      <div class="results-head">
        <div>
          <h3>精査キュー</h3>
          <p>${rows.length}本表示対象。優先度順に表示しています。</p>
        </div>
      </div>
      <div class="review-list">${queue || `<div class="empty">該当するレビュー対象がありません。</div>`}</div>
    </section>
  `;

  if (rows.length > state.visibleLimit) {
    const button = document.createElement("button");
    button.className = "button ghost";
    button.textContent = `さらに表示 (${rows.length - state.visibleLimit}本)`;
    button.addEventListener("click", () => {
      state.visibleLimit += 80;
      render();
    });
    els.reviewPanel.querySelector(".review-list").appendChild(button);
  }

  els.reviewPanel.querySelectorAll("[data-detail-id]").forEach((button) => {
    button.addEventListener("click", () => openDetail(button.dataset.detailId));
  });
}

function reviewCard(video) {
  const review = video.review || {};
  const reasons = (review.reasons || [])
    .map((reason) => `<span class="tag">${escapeHtml(reason)}</span>`)
    .join("");
  return `
    <article class="review-card">
      <div class="review-card-head">
        <div>
          <div class="video-meta">
            <span>${escapeHtml(video.date)}</span>
            <span>${escapeHtml(video.primaryToolName)}</span>
            <span>${video.transcriptChars.toLocaleString()}字</span>
            <span>${video.charsPerMinute || "-"}字/分</span>
          </div>
          <h4>${highlight(video.title)}</h4>
          <div class="tag-row">${reviewStatusTag(review)}<span class="tag">スコア ${review.priorityScore || 0}</span></div>
        </div>
        <button class="detail-button" data-detail-id="${video.id}">詳細</button>
      </div>
      <p class="video-summary">${escapeHtml(review.nextAction || "")}</p>
      <div class="tag-row">${reasons}</div>
    </article>
  `;
}

function videoCard(video) {
  const tags = [
    `<span class="tag tool">${escapeHtml(video.primaryToolName)}</span>`,
    ...video.useCaseNames.slice(0, 3).map((name) => `<span class="tag use">${escapeHtml(name)}</span>`),
  ];
  if (latestIds.has(video.id)) tags.push(`<span class="tag">最新版候補</span>`);
  if (video.review) tags.push(reviewStatusTag(video.review));
  return `
    <article class="video-card">
      <div>
        <div class="video-meta">
          <span>${escapeHtml(video.date)}</span>
          <span>${escapeHtml(video.duration || "")}</span>
          <span>${video.transcriptChars.toLocaleString()}字</span>
          <span>ID: ${escapeHtml(video.id)}</span>
        </div>
        <h4><a class="video-title-link" href="${video.url}" target="_blank" rel="noreferrer">${highlight(video.title)}</a></h4>
        <div class="tag-row">${tags.join("")}</div>
        <p class="video-summary">${highlight(video.summary)}</p>
        <div class="snippet-list">${renderSnippets(video)}</div>
      </div>
      <div class="video-actions">
        <a class="action-link primary" href="${video.url}" target="_blank" rel="noreferrer">YouTube</a>
        <button class="detail-button" data-detail-id="${video.id}">詳細</button>
        <a class="action-link" href="${transcriptHref(video.mdFile)}" target="_blank" rel="noreferrer">Markdown</a>
        <a class="action-link" href="${transcriptHref(video.txtFile)}" target="_blank" rel="noreferrer">TXT</a>
      </div>
    </article>
  `;
}

function renderSnippets(video) {
  const tokens = queryTokens();
  let snippets = video.snippets || [];
  if (tokens.length) {
    const text = video.searchText || "";
    const lower = text.toLowerCase();
    const found = [];
    for (const token of tokens) {
      const index = lower.indexOf(token);
      if (index >= 0) {
        const start = Math.max(0, index - 90);
        const end = Math.min(text.length, index + token.length + 220);
        found.push(compact(text.slice(start, end), 260));
      }
      if (found.length >= 2) break;
    }
    if (found.length) snippets = found;
  }
  return snippets
    .slice(0, 2)
    .map((snippet) => `<div class="snippet">${highlight(snippet)}</div>`)
    .join("");
}

function renderTools() {
  els.toolCards.innerHTML = state.data.tools.map(toolCard).join("");
  els.toolCards.querySelectorAll("[data-set-tool]").forEach((button) => {
    button.addEventListener("click", () => {
      state.tool = button.dataset.setTool;
      switchTab("videos");
      render();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });
}

function toolCard(tool) {
  const useCases = (tool.topUseCases || [])
    .slice(0, 3)
    .map((useCase) => `<span class="tag use">${escapeHtml(useCase.name)} ${useCase.count}</span>`)
    .join("");
  const videos = (tool.topVideos || [])
    .slice(0, 4)
    .map(
      (video) => `
        <a class="mini-video" href="${video.url}" target="_blank" rel="noreferrer">
          ${escapeHtml(video.date)} ${escapeHtml(compact(video.title, 76))}
        </a>
      `,
    )
    .join("");
  return `
    <article class="tool-card">
      <div class="tool-card-head">
        <div>
          <h4>${escapeHtml(tool.name)}</h4>
          <p class="card-sub">関連 ${tool.relatedCount}本 / 主分類 ${tool.videoCount}本</p>
        </div>
        <div class="tool-count">${tool.videoCount}</div>
      </div>
      <ul class="capability-list">
        ${tool.capabilities.map((capability) => `<li>${escapeHtml(capability)}</li>`).join("")}
      </ul>
      <div class="tag-row">${useCases}</div>
      <div class="mini-video-list">${videos}</div>
      <button class="detail-button" data-set-tool="${tool.id}">このツールで絞り込む</button>
    </article>
  `;
}

function renderLatest() {
  els.revisionGroups.innerHTML = state.data.revisionGroups
    .map((group) => {
      const older = group.older
        .map(
          (video) => `
          <li>
            <a href="${video.url}" target="_blank" rel="noreferrer">
              ${escapeHtml(video.date)} ${escapeHtml(compact(video.title, 92))}
            </a>
          </li>
        `,
        )
        .join("");
      return `
        <article class="revision-card">
          <div class="revision-layout">
            <div>
              <h4>${escapeHtml(group.name)} <span class="tag">${group.count}本</span></h4>
              <p class="video-summary">${escapeHtml(group.note)}</p>
              <div class="latest-box">
                <div class="small">最新優先</div>
                <a class="video-title-link" href="${group.latest.url}" target="_blank" rel="noreferrer">
                  ${escapeHtml(group.latest.date)} ${escapeHtml(group.latest.title)}
                </a>
              </div>
            </div>
            <div>
              <div class="small">過去動画</div>
              <ul class="older-list">${older}</ul>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderQuality() {
  const videos = state.data.videos;
  const quality = state.data.transcriptQuality || {};
  const short = quality.shortVideos || videos.filter((video) => video.transcriptChars < 800).sort((a, b) => a.transcriptChars - b.transcriptChars);
  const lowDensity = quality.lowDensityVideos || [];
  const latest = videos[0];
  const oldest = videos[videos.length - 1];
  const lengthBuckets = (quality.lengthBuckets || [])
    .map(
      (bucket) => `
        <div class="ratio-row">
          <span>${escapeHtml(bucket.name)}</span>
          <strong>${bucket.count}本</strong>
        </div>
      `,
    )
    .join("");
  const densityBuckets = (quality.densityBuckets || [])
    .map(
      (bucket) => `
        <div class="ratio-row">
          <span>${escapeHtml(bucket.name)}</span>
          <strong>${bucket.count}本</strong>
        </div>
      `,
    )
    .join("");
  const shortList = short
    .filter((video) => video.transcriptChars < 2000)
    .map(
      (video) => `
      <article class="quality-card">
        <div class="video-meta"><span>${escapeHtml(video.date)}</span><span>${video.transcriptChars.toLocaleString()}字</span><span>${video.charsPerMinute || "-"}字/分</span><span>${escapeHtml(video.id)}</span></div>
        <a class="video-title-link" href="${video.url}" target="_blank" rel="noreferrer">${escapeHtml(video.title)}</a>
      </article>
    `,
    )
    .join("");
  const lowDensityList = lowDensity
    .map(
      (video) => `
      <article class="quality-card">
        <div class="video-meta"><span>${escapeHtml(video.date)}</span><span>${video.transcriptChars.toLocaleString()}字</span><span>${video.charsPerMinute || "-"}字/分</span><span>${escapeHtml(video.duration || "")}</span></div>
        <a class="video-title-link" href="${video.url}" target="_blank" rel="noreferrer">${escapeHtml(video.title)}</a>
      </article>
    `,
    )
    .join("");
  const sourceCounts = (quality.sourceCounts || [])
    .map((source) => `${source.name}: ${source.count}本`)
    .join(" / ");

  els.qualityPanel.innerHTML = `
    <div class="quality-grid">
      ${stat("対象動画", `${videos.length}本`, `${oldest.date} - ${latest.date}`)}
      ${stat("文字起こしあり", `${quality.withTranscript || videos.length}本`, sourceCounts || "字幕由来")}
      ${stat("平均文字数", `${(quality.avgChars || 0).toLocaleString()}字`, `中央値 ${(quality.medianChars || 0).toLocaleString()}字`)}
      ${stat("平均密度", `${quality.avgCharsPerMinute || 0}字/分`, "動画時間あたり")}
    </div>
    <p class="quality-note">${escapeHtml(quality.note || "文字起こし品質を確認します。")} 短いものは告知動画・プレゼント動画などで、セミナー教材としては優先度が低い可能性があります。</p>
    <div class="quality-columns">
      <article class="overview-card">
        <h3>文字数分布</h3>
        <div class="ratio-table">${lengthBuckets}</div>
      </article>
      <article class="overview-card">
        <h3>文字密度分布</h3>
        <div class="ratio-table">${densityBuckets}</div>
      </article>
    </div>
    <div class="quality-columns">
      <article>
        <h3>短文・告知寄り候補</h3>
        <div class="short-list">${shortList || `<div class="empty">2,000字未満の文字起こしはありません。</div>`}</div>
      </article>
      <article>
        <h3>文字密度が低い候補</h3>
        <div class="short-list">${lowDensityList || `<div class="empty">低密度候補はありません。</div>`}</div>
      </article>
    </div>
  `;
}

function openDetail(videoId) {
  const video = state.data.videos.find((item) => item.id === videoId);
  if (!video) return;
  const lecture = video.lecture || {};
  const review = video.review || {};
  const relatedTools = video.toolNames.map((name) => `<span class="tag tool">${escapeHtml(name)}</span>`).join("");
  const useCases = video.useCaseNames.map((name) => `<span class="tag use">${escapeHtml(name)}</span>`).join("");
  els.detailContent.innerHTML = `
    <div class="detail-inner">
      <div class="detail-head">
        <div>
          <div class="video-meta">
            <span>${escapeHtml(video.date)}</span>
            <span>${escapeHtml(video.duration || "")}</span>
            <span>${video.transcriptChars.toLocaleString()}字</span>
            <span>${video.charsPerMinute || "-"}字/分</span>
            <span>${escapeHtml(video.transcriptSource || "unknown")}</span>
            <span>${escapeHtml(video.id)}</span>
          </div>
          <h3>${escapeHtml(video.title)}</h3>
        </div>
        <button class="close-button" aria-label="閉じる" data-close-dialog>×</button>
      </div>
      <div class="detail-grid">
        <div>
          <p class="video-summary">${escapeHtml(video.summary)}</p>
          <div class="tag-row">${relatedTools}${useCases}${latestIds.has(video.id) ? `<span class="tag">最新版候補</span>` : ""}</div>
          <section class="detail-lecture">
            <div class="section-title">講義候補</div>
            <h4>${escapeHtml(lecture.title || "")}</h4>
            <div class="tag-row">
              <span class="tag">${escapeHtml(lecture.module?.name || "")}</span>
              <span class="tag use">${escapeHtml(lecture.type || "")}</span>
              <span class="tag">${escapeHtml(lecture.difficulty || "")}</span>
              <span class="tag">${escapeHtml(lecture.audience || "")}</span>
            </div>
            <div class="detail-lecture-grid">
              <div>
                <h5>成果物</h5>
                ${renderList(lecture.deliverables)}
              </div>
              <div>
                <h5>機能・操作</h5>
                ${renderList(lecture.features)}
              </div>
              <div>
                <h5>進め方</h5>
                ${renderList(lecture.procedure)}
              </div>
              <div>
                <h5>注意点/事例</h5>
                ${renderList([...(lecture.casePoints || []), ...(lecture.nonToolPoints || [])], "補足論点なし")}
              </div>
            </div>
          </section>
          <section class="detail-review">
            <div class="section-title">精査状況</div>
            <div class="tag-row">
              ${reviewStatusTag(review)}
              <span class="tag">スコア ${review.priorityScore || 0}</span>
              <span class="tag">${escapeHtml(review.confidence || "未精査")}</span>
            </div>
            <p class="review-note">文字起こしはYouTube字幕由来です。精査済みのみ、全文確認と要約補完を反映しています。</p>
            <p class="video-summary">${escapeHtml(review.nextAction || "")}</p>
            ${renderList(review.reasons || [], "理由なし")}
            ${review.finalSummary ? `<h5>精査済み要約</h5><p class="video-summary">${escapeHtml(review.finalSummary)}</p>` : ""}
            ${review.verifiedPoints?.length ? `<h5>確認済みポイント</h5>${renderList(review.verifiedPoints)}` : ""}
            ${review.corrections?.length ? `<h5>自動整理からの修正点</h5>${renderList(review.corrections)}` : ""}
          </section>
          <div class="snippet-list">${renderSnippets(video)}</div>
          <h4>文字起こしプレビュー</h4>
          <div class="transcript-preview">${highlight(video.searchText)}</div>
        </div>
        <div class="video-actions">
          <a class="action-link primary" href="${video.url}" target="_blank" rel="noreferrer">YouTubeで開く</a>
          <a class="action-link" href="${transcriptHref(video.mdFile)}" target="_blank" rel="noreferrer">Markdown全文</a>
          <a class="action-link" href="${transcriptHref(video.txtFile)}" target="_blank" rel="noreferrer">TXT全文</a>
          <button class="detail-button" data-copy-title>タイトルをコピー</button>
        </div>
      </div>
    </div>
  `;
  els.detailContent.querySelector("[data-close-dialog]").addEventListener("click", () => els.detailDialog.close());
  els.detailContent.querySelector("[data-copy-title]").addEventListener("click", async () => {
    await navigator.clipboard.writeText(`${video.date} ${video.title} ${video.url}`);
  });
  els.detailDialog.showModal();
}

initElements();
loadData();
