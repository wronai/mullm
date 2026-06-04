(function () {
  const SESSION_KEY = "mullm_workspace_session";
  const WR_KEY = "mullm_workroom_id";
  let workroomId = localStorage.getItem(WR_KEY) || "";
  let userSessionId = localStorage.getItem(SESSION_KEY) || "";

  const $ = (id) => document.getElementById(id);

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
    if (!r.ok) throw new Error(data.detail || data.error || r.statusText);
    return data;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  async function ensureWorkroom() {
    if (workroomId) {
      try {
        await api(`/api/agent-workroom/${workroomId}`);
        return workroomId;
      } catch {
        workroomId = "";
      }
    }
    const data = await api("/api/agent-workroom/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_session_id: userSessionId || null }),
    });
    workroomId = data.workroom_id;
    localStorage.setItem(WR_KEY, workroomId);
    renderCatalog(data.catalog);
    return workroomId;
  }

  function renderCatalog(cat) {
    if (!cat) return;
    const agents = $("agent-list");
    if (agents) {
      agents.innerHTML = (cat.agents || [])
        .map(
          (a) =>
            `<li><strong>${escapeHtml(a.id)}</strong> — ${escapeHtml(a.title)}<br><span class="muted">${escapeHtml(a.role)}</span></li>`
        )
        .join("");
    }
    const areas = $("area-list");
    if (areas) {
      areas.innerHTML = (cat.areas || [])
        .slice(0, 12)
        .map(
          (a) =>
            `<li><code>${escapeHtml(a.area_id)}</code> — ${escapeHtml(a.title || "")}<br><span class="muted">${escapeHtml((a.labels || []).join(", "))}</span></li>`
        )
        .join("");
    }
    const groups = $("group-list");
    if (groups && cat.groups) {
      groups.innerHTML = cat.groups
        .map(
          (g) =>
            `<li><strong>${escapeHtml(g.group_id)}</strong>: ${escapeHtml((g.labels || []).join(", "))}</li>`
        )
        .join("");
    }
  }

  async function loadAreas() {
    try {
      const data = await api("/api/resource-areas");
      renderCatalog({ areas: data.areas, groups: data.groups, agents: [] });
    } catch {
      /* ignore */
    }
  }

  function renderThread(thread) {
    const box = $("agent-thread");
    if (!box) return;
    box.innerHTML = (thread || [])
      .map((m) => {
        const st = m.status || "info";
        return `<div class="agent-bubble ${escapeHtml(st)}">
          <div class="who">${escapeHtml(m.role || m.agent_id)}</div>
          ${escapeHtml(m.text || "")}
        </div>`;
      })
      .join("") || '<p class="muted">Uruchom zespół agentów powyżej.</p>';
    box.scrollTop = box.scrollHeight;
  }

  function renderLedger(ledger) {
    const box = $("ledger");
    if (!box) return;
    box.innerHTML = (ledger || [])
      .map((e) => {
        const stClass =
          e.status === "ok"
            ? "st-ok"
            : e.status === "running"
              ? "st-running"
              : e.status === "blocked" || e.status === "denied"
                ? "st-blocked"
                : "";
        return `<div class="ledger-row">
          <span class="kind">${escapeHtml(e.kind)}</span>
          <span class="${stClass}">${escapeHtml(e.agent_id)}</span>
          <span>${escapeHtml(e.summary)}</span>
        </div>`;
      })
      .join("");
  }

  function renderState(data) {
    renderThread(data.agent_thread);
    renderLedger(data.ledger);
    const sum = $("result-summary");
    if (sum) sum.textContent = data.result_summary || "—";
  }

  async function runAgents() {
    const text = ($("wr-input")?.value || "").trim();
    if (!text) return;
    $("wr-run").disabled = true;
    try {
      await ensureWorkroom();
      const data = await api(`/api/agent-workroom/${workroomId}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          wait_for_confirmation: !!$("wr-wait-confirm")?.checked,
        }),
      });
      renderState(data);
      toast("Zespół agentów zakończył plan", true);
    } catch (e) {
      toast(e.message, false);
    } finally {
      $("wr-run").disabled = false;
    }
  }

  async function refresh() {
    userSessionId = localStorage.getItem(SESSION_KEY) || "";
    const el = $("wr-user-session");
    if (el) el.textContent = userSessionId || "(brak — otwórz / i wyślij wiadomość)";
    await loadAreas();
    if (workroomId) {
      try {
        const data = await api(`/api/agent-workroom/${workroomId}`);
        renderState(data);
      } catch {
        await ensureWorkroom();
      }
    } else {
      await ensureWorkroom();
    }
  }

  $("wr-run")?.addEventListener("click", () => runAgents());
  $("wr-input")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      runAgents();
    }
  });
  $("btn-refresh")?.addEventListener("click", () => refresh().catch((e) => toast(e.message, false)));

  refresh().catch((e) => toast(e.message, false));
})();
