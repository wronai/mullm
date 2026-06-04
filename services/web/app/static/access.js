(function () {
  const $ = (id) => document.getElementById(id);
  let state = null;

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

  function renderAgentResourceMatrix() {
    const wrap = $("wrap-agent-resource");
    if (!wrap || !state) return;
    const resources = state.resources || [];
    const agents = state.agents || [];
    const matrix = state.agent_resource || {};
    let html =
      '<table class="matrix-table"><thead><tr><th class="corner row-head">Zasób \\ Agent</th>';
    agents.forEach((a) => {
      html += `<th title="${escapeHtml(a.id)}">${escapeHtml(a.title || a.id)}</th>`;
    });
    html += "</tr></thead><tbody>";
    resources.forEach((r) => {
      html += `<tr><td class="row-head" title="${escapeHtml(r.id)}">${escapeHtml(r.title || r.id)}</td>`;
      agents.forEach((a) => {
        const checked = matrix[r.id]?.[a.id] !== false;
        html += `<td><input type="checkbox" data-matrix="ar" data-row="${escapeHtml(r.id)}" data-col="${escapeHtml(a.id)}" ${checked ? "checked" : ""} /></td>`;
      });
      html += "</tr>";
    });
    html += "</tbody></table>";
    wrap.innerHTML = html;
    wrap.querySelectorAll('input[data-matrix="ar"]').forEach((cb) => {
      cb.addEventListener("change", () => {
        if (!state.agent_resource[cb.dataset.row]) state.agent_resource[cb.dataset.row] = {};
        state.agent_resource[cb.dataset.row][cb.dataset.col] = cb.checked;
      });
    });
  }

  function renderHumanAgentMatrix() {
    const wrap = $("wrap-human-agent");
    if (!wrap || !state) return;
    const agents = state.agents || [];
    const humans = state.humans || [];
    const matrix = state.human_agent || {};
    let html =
      '<table class="matrix-table"><thead><tr><th class="corner row-head">Agent \\ Human</th>';
    humans.forEach((h) => {
      html += `<th title="${escapeHtml(h.id)}">${escapeHtml(h.title || h.id)}</th>`;
    });
    html += "</tr></thead><tbody>";
    agents.forEach((a) => {
      html += `<tr><td class="row-head" title="${escapeHtml(a.id)}">${escapeHtml(a.title || a.id)}</td>`;
      humans.forEach((h) => {
        const checked = matrix[a.id]?.[h.id] !== false;
        html += `<td><input type="checkbox" data-matrix="ha" data-row="${escapeHtml(a.id)}" data-col="${escapeHtml(h.id)}" ${checked ? "checked" : ""} /></td>`;
      });
      html += "</tr>";
    });
    html += "</tbody></table>";
    wrap.innerHTML = html;
    wrap.querySelectorAll('input[data-matrix="ha"]').forEach((cb) => {
      cb.addEventListener("change", () => {
        if (!state.human_agent[cb.dataset.row]) state.human_agent[cb.dataset.row] = {};
        state.human_agent[cb.dataset.row][cb.dataset.col] = cb.checked;
      });
    });
  }

  function renderAll() {
    renderAgentResourceMatrix();
    renderHumanAgentMatrix();
  }

  async function load() {
    state = await api("/api/access/matrix");
    renderAll();
    const diag = await api("/api/access/diagnose/file-list");
    const el = $("diag-file-list");
    if (el) {
      el.textContent = [
        "uses_shell_agent: " + diag.uses_shell_agent,
        "uses_host_filesystem_directly: " + diag.uses_host_filesystem_directly,
        "",
        "Źródła danych:",
        ...(diag.data_sources || []).map((s) => "  • " + s),
        "",
        "Filtr user:",
        "  " + diag.user_scope_filter,
        "",
        "Shell agent:",
        "  " + diag.shell_agent_role,
        "",
        "Typowe nieporozumienie:",
        "  " + diag.typical_wrong_expectation,
      ].join("\n");
    }
  }

  async function save() {
    const res = await api("/api/access/matrix", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    });
    state = res.state || state;
    toast("Zapisano macierze ACL", true);
  }

  async function resetAll() {
    const res = await api("/api/access/matrix/reset", { method: "POST" });
    state = res.state;
    renderAll();
    toast("Przywrócono: wszystkie checkboxy włączone", true);
  }

  $("btn-save")?.addEventListener("click", () => save().catch((e) => toast(e.message, false)));
  $("btn-reset")?.addEventListener("click", () => resetAll().catch((e) => toast(e.message, false)));
  $("btn-add-human")?.addEventListener("click", () => {
    const id = ($("new-human-id")?.value || "").trim();
    const title = ($("new-human-title")?.value || "").trim() || id;
    if (!id) {
      toast("Podaj id human (np. human@serwer2)", false);
      return;
    }
    if (!state.humans.some((h) => h.id === id)) {
      state.humans.push({ id, title });
      state.agents.forEach((a) => {
        if (!state.human_agent[a.id]) state.human_agent[a.id] = {};
        state.human_agent[a.id][id] = true;
      });
    }
    renderHumanAgentMatrix();
    toast("Dodano kolumnę: " + id, true);
    if ($("new-human-id")) $("new-human-id").value = "";
    if ($("new-human-title")) $("new-human-title").value = "";
  });

  load().catch((e) => toast(e.message, false));
})();
