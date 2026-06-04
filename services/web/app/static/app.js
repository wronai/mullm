(function () {
  const sessionKey = "mullm_session_id";
  let sessionId = localStorage.getItem(sessionKey) || "";

  const els = {
    messages: document.getElementById("chat-messages"),
    input: document.getElementById("chat-input"),
    send: document.getElementById("chat-send"),
    files: document.getElementById("chat-files"),
    fileList: document.getElementById("file-list"),
    useRag: document.getElementById("use-rag"),
    createTaskOnSend: document.getElementById("create-task-on-send"),
    shellFromChat: document.getElementById("shell-from-chat"),
    taskForm: document.getElementById("task-form"),
    taskToast: document.getElementById("task-toast"),
    refreshBoard: document.getElementById("refresh-board"),
  };

  function toast(el, text, ok) {
    if (!el) return;
    el.textContent = text;
    el.className = "toast " + (ok ? "ok" : "err");
  }

  function appendMessage(role, content, meta) {
    const div = document.createElement("div");
    div.className = "msg " + role;
    div.textContent = content;
    if (meta) {
      const m = document.createElement("div");
      m.className = "meta";
      m.textContent = meta;
      div.appendChild(m);
    }
    els.messages.appendChild(div);
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  function renderHistory(history) {
    if (!els.messages || !history) return;
    els.messages.innerHTML = "";
    history.forEach((item) => {
      const meta =
        item.role === "assistant" && item.sources && item.sources.length
          ? `Źródła: ${item.sources.length}`
          : "";
      appendMessage(item.role, item.content, meta || undefined);
    });
  }

  async function ensureSession() {
    if (sessionId) return sessionId;
    const r = await fetch("/api/chat/session");
    const data = await r.json();
    sessionId = data.session_id;
    localStorage.setItem(sessionKey, sessionId);
    renderHistory(data.history || []);
    return sessionId;
  }

  async function uploadFiles() {
    const files = els.files?.files;
    if (!files || !files.length) return [];
    const fd = new FormData();
    for (const f of files) fd.append("files", f);
    const r = await fetch("/api/files/upload", { method: "POST", body: fd });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "upload failed");
    return data.items || [];
  }

  els.send?.addEventListener("click", async () => {
    const text = (els.input?.value || "").trim();
    if (!text) return;
    els.send.disabled = true;
    try {
      await ensureSession();
      const uploaded = await uploadFiles();
      if (uploaded.length && els.fileList) {
        els.fileList.textContent =
          "Pliki: " +
          uploaded.map((u) => (u.ok ? u.filename + " ✓" : u.filename + " ✗")).join(", ");
      }
      appendMessage("user", text);
      els.input.value = "";

      const body = {
        session_id: sessionId,
        message: text,
        use_rag: els.useRag?.checked !== false,
        create_task: els.createTaskOnSend?.checked === true,
        shell_command: els.shellFromChat?.value?.trim() || null,
        task_title: text.slice(0, 80),
      };
      const r = await fetch("/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "chat error");
      sessionId = data.session_id;
      localStorage.setItem(sessionKey, sessionId);
      renderHistory(data.history || []);
      if (data.task?.ok) {
        toast(els.taskToast, "Utworzono zadanie: " + data.task.task_id, true);
        refreshTables();
      }
      if (els.files) els.files.value = "";
    } catch (e) {
      appendMessage("assistant", "Błąd: " + e.message);
    } finally {
      els.send.disabled = false;
    }
  });

  els.input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      els.send?.click();
    }
  });

  els.taskForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(els.taskForm);
    const payload = {
      title: fd.get("title"),
      description: fd.get("description") || "",
      shell_command: fd.get("shell_command") || null,
      auto_assign: fd.get("auto_assign") === "on",
      priority: fd.get("priority") || "medium",
    };
    try {
      const r = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail));
      toast(els.taskToast, "Zadanie utworzone: " + data.task_id, true);
      els.taskForm.reset();
      refreshTables();
    } catch (err) {
      toast(els.taskToast, err.message, false);
    }
  });

  function rowTask(t) {
    return `<tr>
      <td title="${t.task_id}">${(t.task_id || "").slice(0, 8)}…</td>
      <td>${escapeHtml(t.title || "")}</td>
      <td class="status">${t.status || ""}</td>
      <td>${t.assigned_agent_id || "—"}</td>
      <td>${t.priority || ""}</td>
    </tr>`;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  async function refreshTables() {
    try {
      const r = await fetch("/api/board");
      const data = await r.json();
      const tasksBody = document.getElementById("tasks-body");
      if (tasksBody) {
        const tasks = data.tasks || [];
        tasksBody.innerHTML = tasks.length
          ? tasks.map(rowTask).join("")
          : '<tr><td colspan="5">Brak zadań</td></tr>';
      }
    } catch (_) {
      /* ignore */
    }
  }

  els.refreshBoard?.addEventListener("click", refreshTables);

  ensureSession().catch(() => {
    appendMessage(
      "assistant",
      "Witaj w Mullm. Napisz wiadomość, dołącz pliki (indeks RAG) lub utwórz zadanie w panelu po prawej."
    );
  });

  setInterval(refreshTables, 15000);
})();
