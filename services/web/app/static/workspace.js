(function () {
  const SESSION_KEY = "mullm_workspace_session";
  let sessionId = localStorage.getItem(SESSION_KEY) || "";
  let currentDraft = null; // tylko podgląd API /tasks/draft
  let selectedTaskId = null;
  let ticketView = "active";
  let cachedTasks = [];
  let pendingClarify = null;
  let artifactSummaries = [];
  const artifactFullCache = new Map();
  let selectedArtifactId = null;
  let artifactPreviewTab = "text";

  const $ = (id) => document.getElementById(id);

  function ticketWebUrl(id) {
    return `/t/${id}`;
  }
  function ticketUri(id) {
    return `mullm://ticket/${id}`;
  }

  function toast(text, ok) {
    const el = $("toast");
    if (!el) return;
    el.textContent = text;
    el.className = "toast-bar show " + (ok ? "ok" : "err");
    setTimeout(() => el.classList.remove("show"), 4000);
  }

  async function api(path, opts) {
    const r = await fetch(path, opts);
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      const detail = data.detail || data.error || r.statusText;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
  }

  async function ensureSession() {
    if (sessionId) return sessionId;
    const data = await api("/api/chat/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    sessionId = data.session_id;
    localStorage.setItem(SESSION_KEY, sessionId);
    return sessionId;
  }

  async function loadTickets() {
    const data = await api(
      `/api/tickets?session_id=${encodeURIComponent(sessionId)}&view=${ticketView}`
    );
    cachedTasks = data.items || [];
    return cachedTasks;
  }

  async function refreshWorkspace() {
    await ensureSession();
    const state = await api(`/api/workspace/state?session_id=${encodeURIComponent(sessionId)}`);
    renderContext(state.context);
    currentDraft = state.draft || null;
    renderSessionEvents(state.events);
    renderChat(state.history);
    syncArtifacts(state.artifacts || [], null);
    await loadTickets();
    renderTasks(filterTasks(cachedTasks));
    renderFileChips(state.board?.resources || [], state.context);
    if (selectedTaskId) {
      const t = cachedTasks.find((x) => x.task_id === selectedTaskId);
      if (t) renderTicketDetail(t);
      else loadTicketDetail(selectedTaskId).catch(() => renderTicketDetail(null));
    }
    return state;
  }

  function filterTasks(tasks) {
    const q = ($("ticket-search")?.value || "").trim().toLowerCase();
    if (!q) return tasks;
    return tasks.filter(
      (t) =>
        (t.title || "").toLowerCase().includes(q) ||
        (t.task_id || "").toLowerCase().includes(q) ||
        (t.status_label || "").toLowerCase().includes(q)
    );
  }

  async function loadTicketDetail(taskId) {
    const t = await api(
      `/api/tickets/${encodeURIComponent(taskId)}?session_id=${encodeURIComponent(sessionId)}`
    );
    renderTicketDetail(t);
    return t;
  }

  function selectTicket(taskId, pushHistory = true) {
    selectedTaskId = taskId;
    if (pushHistory) {
      history.pushState({ ticket: taskId }, "", ticketWebUrl(taskId));
    }
    renderTasks(filterTasks(cachedTasks));
    const t = cachedTasks.find((x) => x.task_id === taskId);
    if (t) {
      renderTicketDetail(t);
      api("/api/tickets/" + encodeURIComponent(taskId) + "/link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      }).catch(() => {});
    } else {
      loadTicketDetail(taskId).catch(() => toast("Ticket nie znaleziony", false));
    }
  }

  function renderTicketDetail(t) {
    const el = $("ticket-detail");
    if (!el) return;
    if (!t) {
      el.className = "ticket-detail empty";
      el.innerHTML =
        '<p class="muted">Wybierz ticket z listy.</p><p class="muted small">URL: <code>/t/&lt;id&gt;</code></p>';
      return;
    }
    const sk = t.status_key || (t.status || "pending").toLowerCase();
    const stClass = sk === "archived" ? "st-archived" : `st-${sk}`;
    const color = t.status_color || "#8b9bb4";
    el.className = "ticket-detail";
    el.innerHTML = `
      <div class="draft-head"><span class="status-dot ${stClass}"></span>
        <span class="status-pill" style="background:${escapeHtml(color)}">${escapeHtml(t.status_label || t.status)}</span>
      </div>
      <div class="td-title">${escapeHtml(t.title || t.task_id)}</div>
      <div class="td-row"><strong>ID</strong> <code>${escapeHtml(t.task_id)}</code></div>
      <div class="td-row"><strong>URL</strong> <a href="${escapeHtml(t.web_url || ticketWebUrl(t.task_id))}">${escapeHtml(t.web_url || ticketWebUrl(t.task_id))}</a></div>
      <div class="td-row"><strong>URI</strong> <code id="ticket-uri-text">${escapeHtml(t.uri || ticketUri(t.task_id))}</code></div>
      <div class="td-row">Agent: ${escapeHtml(t.assigned_agent_id || "—")} · ${escapeHtml(t.priority || "")}</div>
      <div class="td-row">Tryb: ${escapeHtml(t.execution_mode || "—")}</div>
      <div class="td-actions">
        ${sk === "pending" ? '<button type="button" class="btn success btn-sm" id="btn-confirm-ticket">Uruchom</button>' : ""}
        <button type="button" class="btn ghost btn-sm" id="btn-copy-uri">Kopiuj URI</button>
        <button type="button" class="btn ghost btn-sm" id="btn-copy-url">Kopiuj URL</button>
        ${sk !== "archived" ? '<button type="button" class="btn ghost btn-sm" id="btn-archive-ticket">Archiwizuj</button>' : ""}
      </div>
    `;
    $("btn-copy-uri")?.addEventListener("click", () =>
      copyText(t.uri || ticketUri(t.task_id), "URI")
    );
    $("btn-copy-url")?.addEventListener("click", () =>
      copyText(location.origin + (t.web_url || ticketWebUrl(t.task_id)), "URL")
    );
    $("btn-confirm-ticket")?.addEventListener("click", () =>
      confirmTicket(t.task_id).catch((e) => toast(e.message, false))
    );
    $("btn-archive-ticket")?.addEventListener("click", () => archiveTicket(t.task_id));
  }

  async function confirmTicket(taskId) {
    await ensureSession();
    await api(`/api/tickets/${encodeURIComponent(taskId)}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
    toast("Ticket uruchomiony", true);
    await refreshWorkspace();
  }

  async function archiveTicket(taskId) {
    await api(`/api/tickets/${encodeURIComponent(taskId)}/archive`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
    toast("Przeniesiono do archiwum", true);
    await refreshWorkspace();
  }

  function initRouting() {
    const deep = window.__DEEP_LINK_TICKET__;
    const m = location.pathname.match(/^\/t\/([0-9a-f-]+)$/i);
    const id = deep || (m && m[1]) || new URLSearchParams(location.search).get("ticket");
    if (id) selectTicket(id, false);
    window.addEventListener("popstate", () => {
      const m2 = location.pathname.match(/^\/t\/([0-9a-f-]+)$/i);
      if (m2) selectTicket(m2[1], false);
      else {
        selectedTaskId = null;
        renderTicketDetail(null);
        renderTasks(filterTasks(cachedTasks));
      }
    });
  }

  function renderContext(ctx) {
    if (!ctx) return;
    if ($("ctx-ticket")) $("ctx-ticket").value = ctx.ticket_id || "";
    if ($("ctx-project")) $("ctx-project").value = ctx.project || "";
    if ($("ctx-branch")) $("ctx-branch").value = ctx.branch || "";
    if ($("ctx-agent")) $("ctx-agent").value = ctx.agent_id || "";
    const uris = $("ctx-uris");
    if (uris) {
      uris.innerHTML = (ctx.uris || [])
        .map((u) => `<li>${escapeHtml(u)}</li>`)
        .join("") || "<li>—</li>";
    }
    const files = $("ctx-files");
    if (files) {
      const names = ctx.file_names || [];
      files.innerHTML =
        names.map((n) => `<li>${escapeHtml(n)}</li>`).join("") || "<li>—</li>";
    }
  }

  function renderDraft(draft) {
    currentDraft = draft;
  }

  function renderClarify(clarify) {
    pendingClarify = clarify;
    const panel = $("clarify-panel");
    const form = $("clarify-form");
    const hint = $("clarify-hint");
    if (!panel || !form) return;
    if (!clarify || !clarify.form) {
      panel.hidden = true;
      form.innerHTML = "";
      return;
    }
    panel.hidden = false;
    if (hint) hint.textContent = clarify.hint || "Uzupełnij pola:";
    const fields = clarify.form.fields || [];
    form.innerHTML = fields
      .map((f) => {
        const req = f.required ? " *" : "";
        const opts =
          f.type === "select" && f.options
            ? `<select name="${escapeHtml(f.name)}">${(f.options || [])
                .map((o) => `<option value="${escapeHtml(o)}">${escapeHtml(o)}</option>`)
                .join("")}</select>`
            : `<input name="${escapeHtml(f.name)}" type="${f.type === "number" ? "number" : "text"}" />`;
        return `<label>${escapeHtml(f.label || f.name)}${req}${opts}</label>`;
      })
      .join("");
    panel.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function collectClarifyValues() {
    const form = $("clarify-form");
    if (!form) return {};
    const fd = new FormData(form);
    const out = {};
    for (const [k, v] of fd.entries()) {
      if (String(v).trim()) out[k] = v;
    }
    return out;
  }

  function renderSessionEvents(events) {
    const el = $("session-events");
    if (!el) return;
    el.innerHTML = (events || [])
      .slice()
      .reverse()
      .map(
        (e) =>
          `<div class="ev"><span class="ev-type">${escapeHtml(e.type)}</span> — ${escapeHtml(e.summary || "")}</div>`
      )
      .join("") || '<div class="ev">Brak zdarzeń sesji</div>';
  }


  let lastHistoryLen = -1;

  function formatChatContent(content) {
    if (!content) return "";
    return String(content)
      .replace(/^\[([A-Z_]+[^\]]*)\]\n\n/gm, "⚠ $1\n\n")
      .trim();
  }

  function renderChat(history) {
    const box = $("chat-messages");
    if (!box) return;
    const items = history || [];
    if (items.length === lastHistoryLen && items.length > 0) return;
    lastHistoryLen = items.length;
    box.innerHTML = "";
    items.forEach((item) => {
      const meta = item.sources?.length
        ? `Źródła RAG: ${item.sources.length}`
        : item.incident
          ? `Incydent: ${item.incident}`
          : "";
      appendMsgTo(
        box,
        item.role,
        formatChatContent(item.content),
        meta,
        false,
        item.content || "",
        item.routing
      );
    });
    if (!items.length) {
      appendMsgTo(
        box,
        "system",
        "Napisz czego potrzebujesz — AI utworzy ticket i uruchomi go (domyślnie).\n\n• lista plików · run ls -la\n• Zaznacz „Czekaj na potwierdzenie”, aby ticket został tylko w kolejce (◎ → Uruchom)",
        "",
        false
      );
    }
    box.scrollTop = box.scrollHeight;
  }

  function appendMsg(role, content, meta) {
    const box = $("chat-messages");
    appendMsgTo(box, role, content, meta, true, content || "");
  }

  function cacheArtifactFull(art) {
    if (art?.artifact_id) artifactFullCache.set(art.artifact_id, art);
  }

  function syncArtifacts(summaries, newestFull) {
    artifactSummaries = summaries || [];
    if (newestFull) cacheArtifactFull(newestFull);
    renderArtifactList();
    if (newestFull?.artifact_id) {
      selectArtifact(newestFull.artifact_id, { auto: true });
      return;
    }
    if (
      selectedArtifactId &&
      artifactSummaries.some((a) => a.artifact_id === selectedArtifactId)
    ) {
      selectArtifact(selectedArtifactId, { auto: false });
      return;
    }
    if (artifactSummaries.length) {
      selectArtifact(artifactSummaries[artifactSummaries.length - 1].artifact_id, {
        auto: false,
      });
    } else {
      clearArtifactPreview();
    }
  }

  function clearArtifactPreview() {
    selectedArtifactId = null;
    const title = $("artifact-preview-title");
    const body = $("artifact-preview-body");
    if (title) title.textContent = "Podgląd";
    if (body) {
      body.textContent =
        "Wybierz artefakt z listy lub wyślij polecenie generujące wynik.";
      body.classList.add("muted");
    }
    $("artifact-tab-text")?.setAttribute("disabled", "disabled");
    $("artifact-tab-json")?.setAttribute("disabled", "disabled");
    $("artifact-download")?.setAttribute("disabled", "disabled");
    $("artifact-tab-text")?.classList.remove("active");
    $("artifact-tab-json")?.classList.remove("active");
  }

  function renderArtifactList() {
    const list = $("artifact-list");
    if (!list) return;
    if (!artifactSummaries.length) {
      list.innerHTML =
        '<li class="artifact-empty muted">Brak artefaktów — np. „lista plików usera”</li>';
      return;
    }
    list.innerHTML = artifactSummaries
      .map((a) => {
        const active = a.artifact_id === selectedArtifactId ? " active" : "";
        const when = a.created_at ? new Date(a.created_at).toLocaleString() : "";
        return `<li class="artifact-item${active}" data-id="${escapeHtml(a.artifact_id)}">
          <span class="art-title">${escapeHtml(a.title || a.filename || a.kind || "?")}</span>
          <span class="art-meta">${escapeHtml(a.kind || "")}${a.list_scope ? " · " + escapeHtml(a.list_scope) : ""}${when ? " · " + escapeHtml(when) : ""}</span>
        </li>`;
      })
      .join("");
    list.querySelectorAll(".artifact-item").forEach((el) => {
      el.addEventListener("click", () => {
        selectArtifact(el.dataset.id, { auto: false }).catch((e) => toast(e.message, false));
      });
    });
  }

  async function selectArtifact(id, { auto = false } = {}) {
    if (!id) return;
    selectedArtifactId = id;
    renderArtifactList();
    const body = $("artifact-preview-body");
    if (body && auto) {
      body.textContent = "Ładowanie podglądu…";
      body.classList.remove("muted");
    }
    let art = artifactFullCache.get(id);
    if (!art?.text && !art?.json) {
      await ensureSession();
      art = await api(
        `/api/workspace/artifacts/${encodeURIComponent(id)}?session_id=${encodeURIComponent(sessionId)}`
      );
      cacheArtifactFull(art);
    }
    showArtifactPreview(art);
    if (auto && $("rail-artifacts")) {
      $("rail-artifacts").scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  function showArtifactPreview(art) {
    if (!art) return;
    const title = $("artifact-preview-title");
    const body = $("artifact-preview-body");
    const tabText = $("artifact-tab-text");
    const tabJson = $("artifact-tab-json");
    const dl = $("artifact-download");
    if (title) title.textContent = art.title || art.filename || art.kind || "Artefakt";
    const hasText = Boolean(art.text);
    const hasJson = Boolean(art.json);
    if (tabText) {
      tabText.disabled = !hasText;
      tabText.classList.toggle("active", artifactPreviewTab === "text" && hasText);
    }
    if (tabJson) {
      tabJson.disabled = !hasJson;
      tabJson.classList.toggle("active", artifactPreviewTab === "json" && hasJson);
    }
    if (dl) dl.disabled = !hasText && !hasJson;
    if (!hasText && hasJson) artifactPreviewTab = "json";
    if (hasText && artifactPreviewTab !== "json") artifactPreviewTab = "text";
    if (body) {
      body.classList.remove("muted");
      if (artifactPreviewTab === "json" && hasJson) {
        body.textContent = JSON.stringify(art.json, null, 2);
      } else if (hasText) {
        body.textContent = art.text;
      } else {
        body.textContent = "(brak treści podglądu)";
        body.classList.add("muted");
      }
    }
    if (dl) {
      dl.onclick = () => downloadArtifact(art);
    }
  }

  function downloadArtifact(art) {
    if (!art) return;
    let blob;
    let name = art.filename || "mullm-artifact.txt";
    if (artifactPreviewTab === "json" && art.json) {
      blob = new Blob([JSON.stringify(art.json, null, 2)], { type: "application/json" });
      name = name.replace(/\.txt$/i, ".json");
    } else {
      blob = new Blob([art.text || ""], {
        type: art.mime || "text/plain;charset=utf-8",
      });
    }
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
    toast("Pobrano " + name, true);
  }

  function msgRoleLabel(role) {
    if (role === "user") return "Ty";
    if (role === "assistant") return "AI";
    return role;
  }

  function formatRouteBadge(routing) {
    if (!routing?.route) return "";
    const pct = Math.round((routing.confidence || 0) * 100);
    const codes = (routing.reason_codes || []).slice(0, 3).join(", ");
    const ms = routing.timing_ms != null ? `${routing.timing_ms}ms` : "";
    return [routing.route, `${pct}%`, codes, ms].filter(Boolean).join(" · ");
  }

  function appendRouteBadge(div, routing) {
    if (!routing?.route) return;
    const badge = document.createElement("div");
    badge.className = "msg-route-badge";
    badge.title = JSON.stringify(routing, null, 2);
    badge.textContent = formatRouteBadge(routing);
    div.appendChild(badge);
  }

  function appendMsgTo(box, role, content, meta, scroll, rawContent, routing) {
    const div = document.createElement("div");
    div.className =
      "msg " + (role === "user" ? "user" : role === "system" ? "system" : "assistant");
    const raw = String(rawContent ?? content ?? "");

    if (role === "user" || role === "assistant") {
      const head = document.createElement("div");
      head.className = "msg-head";
      const label = document.createElement("span");
      label.className = "msg-role";
      label.textContent = msgRoleLabel(role);
      const copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "btn ghost btn-sm msg-copy";
      copyBtn.title = `Kopiuj wiadomość (${msgRoleLabel(role)})`;
      copyBtn.textContent = "⎘";
      copyBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        copyText(raw, msgRoleLabel(role)).catch((err) => toast(err.message, false));
      });
      head.appendChild(label);
      head.appendChild(copyBtn);
      div.appendChild(head);
    }

    const body = document.createElement("div");
    body.className = "msg-body";
    body.textContent = content || "";
    div.appendChild(body);
    if (meta) {
      const m = document.createElement("div");
      m.className = "msg-meta";
      m.textContent = meta;
      div.appendChild(m);
    }
    if (role === "assistant" && routing) appendRouteBadge(div, routing);
    box.appendChild(div);
    if (scroll) box.scrollTop = box.scrollHeight;
  }

  function renderTasks(tasks) {
    const list = $("task-list");
    if (!list) return;
    const items = tasks || [];
    list.innerHTML = items
      .map((t) => {
        const active = t.task_id === selectedTaskId ? " active" : "";
        const sk = t.status_key || "pending";
        const stClass = sk === "archived" ? "st-archived" : `st-${sk}`;
        const color = t.status_color || "#8b9bb4";
        return `<div class="task-item ${stClass}${active}" data-id="${escapeHtml(t.task_id)}" role="button" tabindex="0">
          <div class="t-title"><span class="status-dot ${stClass}"></span>${escapeHtml(t.title || t.task_id?.slice(0, 8))}</div>
          <div class="t-meta"><span class="status-pill" style="background:${escapeHtml(color)}">${escapeHtml(t.status_label || t.status || "?")}</span></div>
        </div>`;
      })
      .join("") || '<div class="rail-empty">Brak ticketów w tym widoku</div>';
    list.querySelectorAll(".task-item").forEach((el) => {
      el.addEventListener("click", () => {
        selectTicket(el.dataset.id);
      });
    });
  }

  function renderFileChips(resources, ctx) {
    const el = $("file-chips");
    if (!el) return;
    const chips = [];
    (ctx?.file_names || []).forEach((n) => {
      chips.push(`<span class="file-chip">📎 ${escapeHtml(n)}</span>`);
    });
    (resources || []).slice(0, 8).forEach((r) => {
      chips.push(
        `<span class="file-chip" title="${escapeHtml(r.uri || "")}">${escapeHtml(r.name || r.resource_id?.slice(0, 8))} <small>${escapeHtml(r.status || "")}</small></span>`
      );
    });
    el.innerHTML = chips.join("") || '<span style="color:var(--muted)">Brak plików</span>';
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  async function saveContextFromForm() {
    await ensureSession();
    await api("/api/context/attach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        ticket_id: $("ctx-ticket")?.value || null,
        project: $("ctx-project")?.value || null,
        branch: $("ctx-branch")?.value || null,
        agent_id: $("ctx-agent")?.value || null,
      }),
    });
    await refreshWorkspace();
    toast("Kontekst zapisany", true);
  }

  async function syncContextNote(note) {
    await ensureSession();
    await api("/api/context/attach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, note }),
    });
  }

  async function uploadFiles(fileList) {
    if (!fileList || !fileList.length) return [];
    await ensureSession();
    const fd = new FormData();
    fd.append("session_id", sessionId);
    for (const f of fileList) fd.append("files", f);
    const data = await api("/api/files/upload", { method: "POST", body: fd });
    await refreshWorkspace();
    return data.items || [];
  }

  async function sendChat(fromClarifyOnly) {
    const formValues = fromClarifyOnly ? collectClarifyValues() : null;
    const text = ($("chat-input")?.value || "").trim();
    if (!text && !formValues) return;
    $("chat-send").disabled = true;
    try {
      await ensureSession();
      const files = $("chat-files")?.files;
      if (files?.length) await uploadFiles(files);
      if (text) appendMsg("user", text);
      else appendMsg("user", Object.entries(formValues || {}).map(([k, v]) => `${k}: ${v}`).join(", "));
      $("chat-input").value = "";
      const payload = {
        session_id: sessionId,
        message: text,
        mode: $("chat-mode")?.value || "discuss",
        use_rag: true,
        wait_for_confirmation: !!$("wait-for-confirmation")?.checked,
      };
      if (formValues && Object.keys(formValues).length) payload.form_values = formValues;
      const data = await api("/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      lastHistoryLen = -1;
      renderChat(data.history);
      if (data.artifact) cacheArtifactFull(data.artifact);
      syncArtifacts(data.artifacts || [], data.artifact || null);
      if (data.intent === "file_list" && data.artifact?.list_scope) {
        toast(`Lista plików · zakres: ${data.artifact.list_scope}`, true);
      }
      renderClarify(data.clarify);
      if (!data.clarify) pendingClarify = null;
      renderContext(data.context);
      renderSessionEvents(data.events);
      if (data.routing) {
        toast(`Trasa: ${formatRouteBadge(data.routing)}`, true);
      }
      if (data.task?.ok) {
        document.body.classList.add("tickets-open");
        toast("Ticket: " + (data.task.task_id || "?"), true);
        if (data.task.task_id) selectTicket(data.task.task_id);
      }
      await refreshWorkspace();
    } catch (e) {
      appendMsg("system", "Błąd: " + e.message);
      toast(e.message, false);
    } finally {
      $("chat-send").disabled = false;
      if ($("chat-files")) $("chat-files").value = "";
    }
  }

  async function createFromDraft(run) {
    await ensureSession();
    if (!currentDraft) {
      const text = ($("chat-input")?.value || "").trim();
      if (text) {
        const drafted = await api("/api/tasks/draft", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, message: text }),
        });
        currentDraft = drafted.draft || null;
        renderDraft(currentDraft);
      }
    }
    if (!currentDraft) {
      toast("Brak draftu — wyślij wiadomość w trybie „Dyskusja + draft”", false);
      return;
    }
    const data = await api(run ? "/api/tasks/create-and-run" : "/api/tasks/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, draft: currentDraft }),
    });
    if (!data.ok && !data.task_id) {
      toast(data.error || "Nie udało się utworzyć ticketu", false);
      return;
    }
    const tid = data.task_id || data.result?.aggregate_id;
    toast(
      run
        ? `Uruchomiono ticket ${tid} (shell → agent)`
        : `Ticket ${tid} w kolejce (status: pending — bez shell agent nic nie wykona)`,
      true
    );
    lastHistoryLen = -1;
    currentDraft = null;
    $("draft-panel").style.display = "none";
    await refreshWorkspace();
    if (tid) selectTicket(tid);
  }

  function openTicketDialogFromDraft() {
    const dialog = $("task-dialog");
    const form = $("task-form");
    if (!dialog || !form) return;
    const d = currentDraft || {};
    const input = ($("chat-input")?.value || "").trim();
    form.title.value = d.title || input.slice(0, 80) || "";
    form.description.value = d.description || input || "";
    form.shell_command.value = d.shell_command || "";
    if (form.priority && d.priority) form.priority.value = d.priority;
    dialog.showModal();
  }

  $("chat-send")?.addEventListener("click", () => sendChat(false));
  $("clarify-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    sendChat(true);
  });
  $("btn-toggle-tickets")?.addEventListener("click", () => {
    document.body.classList.toggle("tickets-open");
  });
  $("chat-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChat();
    }
  });

  document.querySelectorAll(".view-tabs .tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".view-tabs .tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      ticketView = tab.dataset.view || "active";
      refreshWorkspace().catch((e) => toast(e.message, false));
    });
  });
  $("ticket-search")?.addEventListener("input", () => renderTasks(filterTasks(cachedTasks)));

  async function copyText(text, label) {
    try {
      await navigator.clipboard.writeText(text);
      toast(`Skopiowano ${label} (${text.length} znaków)`, true);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      toast(`Skopiowano ${label} (fallback)`, true);
    }
  }

  function buildChatTextFromDom() {
    const box = $("chat-messages");
    const lines = ["# Mullm — okno czatu", ""];
    if (sessionId) lines.push(`session_id: ${sessionId}`, "");
    box?.querySelectorAll(".msg").forEach((msg) => {
      let role = "assistant";
      if (msg.classList.contains("user")) role = "user";
      if (msg.classList.contains("system")) role = "system";
      const body = msg.querySelector(".msg-body")?.textContent?.trim() || "";
      if (!body) return;
      const label = role === "user" ? "Ty" : role === "assistant" ? "AI" : role;
      lines.push(`## ${label}`, body, "");
    });
    return lines.join("\n").trim() + "\n";
  }

  async function copyChatToClipboard() {
    await ensureSession();
    try {
      const data = await api(
        `/api/workspace/chat/export?session_id=${encodeURIComponent(sessionId)}`
      );
      await copyText(data.text || "", "cały chat");
    } catch {
      await copyText(buildChatTextFromDom(), "cały chat (widok)");
    }
  }

  async function copyChatViewToClipboard() {
    await copyText(buildChatTextFromDom(), "widok czatu");
  }

  async function copyLogsToClipboard() {
    await ensureSession();
    const data = await api(
      `/api/workspace/logs/export?session_id=${encodeURIComponent(sessionId)}&limit=40`
    );
    await copyText(data.text || JSON.stringify(data, null, 2), "logi");
  }

  function bindCopyChatButtons() {
    const handlerFull = () => copyChatToClipboard().catch((e) => toast(e.message, false));
    const handlerView = () => copyChatViewToClipboard().catch((e) => toast(e.message, false));
    ["btn-copy-chat", "btn-copy-chat-inline"].forEach((id) => {
      $(id)?.addEventListener("click", handlerFull);
    });
    ["btn-copy-chat-view", "btn-copy-chat-view-inline"].forEach((id) => {
      $(id)?.addEventListener("click", handlerView);
    });
  }
  bindCopyChatButtons();
  $("btn-copy-logs")?.addEventListener("click", () =>
    copyLogsToClipboard().catch((e) => toast(e.message, false))
  );
  $("btn-refresh")?.addEventListener("click", () => refreshWorkspace().catch((e) => toast(e.message, false)));
  $("btn-artifacts-refresh")?.addEventListener("click", () =>
    refreshWorkspace().catch((e) => toast(e.message, false))
  );
  $("artifact-tab-text")?.addEventListener("click", () => {
    if ($("artifact-tab-text")?.disabled) return;
    artifactPreviewTab = "text";
    const art = selectedArtifactId && artifactFullCache.get(selectedArtifactId);
    if (art) showArtifactPreview(art);
  });
  $("artifact-tab-json")?.addEventListener("click", () => {
    if ($("artifact-tab-json")?.disabled) return;
    artifactPreviewTab = "json";
    const art = selectedArtifactId && artifactFullCache.get(selectedArtifactId);
    if (art) showArtifactPreview(art);
  });

  $("btn-save-note")?.addEventListener("click", async () => {
    const note = ($("ctx-note")?.value || "").trim();
    if (!note) return;
    await syncContextNote(note);
    $("ctx-note").value = "";
    await refreshWorkspace();
    toast("Notatka dodana", true);
  });

  ["ctx-ticket", "ctx-project", "ctx-branch"].forEach((id) => {
    $(id)?.addEventListener("change", () => saveContextFromForm().catch(() => {}));
  });

  const dialog = $("task-dialog");
  $("form-close")?.addEventListener("click", () => dialog?.close());

  async function submitTaskForm() {
    const form = $("task-form");
    const fd = new FormData(form);
    await ensureSession();
    const wait = fd.get("wait_for_confirmation") === "on";
    const body = {
      session_id: sessionId,
      title: fd.get("title"),
      description: fd.get("description") || "",
      shell_command: fd.get("shell_command") || null,
      wait_for_confirmation: wait,
      priority: fd.get("priority") || "medium",
      ticket_id: $("ctx-ticket")?.value || null,
    };
    await api("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    dialog?.close();
    form.reset();
    toast("Zadanie zapisane", true);
    await refreshWorkspace();
  }

  $("task-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    submitTaskForm().catch((err) => toast(err.message, false));
  });

  $("btn-attach-file")?.addEventListener("click", () => $("chat-files")?.click());
  $("chat-files")?.addEventListener("change", async (e) => {
    try {
      const items = await uploadFiles(e.target.files);
      toast(`Wgrano ${items.filter((i) => i.ok).length} plik(ów)`, true);
    } catch (err) {
      toast(err.message, false);
    }
  });

  const dz = $("dropzone");
  if (dz) {
    dz.addEventListener("dragover", (e) => {
      e.preventDefault();
      dz.classList.add("dragover");
    });
    dz.addEventListener("dragleave", () => dz.classList.remove("dragover"));
    dz.addEventListener("drop", async (e) => {
      e.preventDefault();
      dz.classList.remove("dragover");
      try {
        await uploadFiles(e.dataTransfer.files);
        toast("Pliki dodane do kontekstu", true);
      } catch (err) {
        toast(err.message, false);
      }
    });
    dz.addEventListener("click", () => $("chat-files")?.click());
  }

  document.body.classList.add("tickets-open");
  refreshWorkspace()
    .then(() => initRouting())
    .catch((e) => toast(e.message, false));
  setInterval(() => refreshWorkspace().catch(() => {}), 15000);
})();
