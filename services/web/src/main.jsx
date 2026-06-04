import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, Bot, CheckCircle2, Play, Plus, RefreshCw, TerminalSquare } from "lucide-react";
import "./styles.css";

const ORCHESTRATOR_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || "http://localhost:8001";
const PROJECTOR_URL = import.meta.env.REACT_APP_PROJECTOR_URL || import.meta.env.VITE_PROJECTOR_URL || "http://localhost:8002";

function App() {
  const [tasks, setTasks] = useState([]);
  const [agents, setAgents] = useState([]);
  const [feed, setFeed] = useState([]);
  const [title, setTitle] = useState("Review staging pipeline");
  const [command, setCommand] = useState("pwd");
  const [agentId, setAgentId] = useState("shell-agent-1");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const metrics = useMemo(() => {
    const active = tasks.filter((task) => ["assigned", "running", "pending"].includes(task.status)).length;
    const completed = tasks.filter((task) => task.status === "completed").length;
    const failed = tasks.filter((task) => task.status === "failed").length;
    return { active, completed, failed };
  }, [tasks]);

  async function refresh() {
    setError("");
    const [taskResponse, agentResponse, feedResponse] = await Promise.all([
      fetch(`${PROJECTOR_URL}/projections/tasks`),
      fetch(`${PROJECTOR_URL}/projections/agents`),
      fetch(`${PROJECTOR_URL}/projections/feed?limit=20`),
    ]);
    if (!taskResponse.ok || !agentResponse.ok || !feedResponse.ok) {
      throw new Error("Projection API is not available");
    }
    setTasks((await taskResponse.json()).items || []);
    setAgents((await agentResponse.json()).items || []);
    setFeed((await feedResponse.json()).items || []);
  }

  async function createTask(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const createResponse = await fetch(`${ORCHESTRATOR_URL}/api/commands/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          priority: "medium",
          execution_mode: "semi_auto",
          required_capabilities: ["shell"],
        }),
      });
      if (!createResponse.ok) {
        throw new Error(await createResponse.text());
      }
      const created = await createResponse.json();
      const taskId = created.result.aggregate_id;

      const assignResponse = await fetch(`${ORCHESTRATOR_URL}/api/commands/tasks/assign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId, agent_id: agentId, command }),
      });
      if (!assignResponse.ok) {
        throw new Error(await assignResponse.text());
      }
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
    const timer = setInterval(() => refresh().catch((err) => setError(err.message)), 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <TerminalSquare size={24} />
          <span>mullm</span>
        </div>
        <nav>
          <a className="active" href="#tasks"><Activity size={18} />Tasks</a>
          <a href="#agents"><Bot size={18} />Agents</a>
          <a href="#feed"><RefreshCw size={18} />Feed</a>
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Control plane</p>
            <h1>Operational queue</h1>
          </div>
          <button className="iconButton" onClick={() => refresh()} aria-label="Refresh projections" title="Refresh projections">
            <RefreshCw size={18} />
          </button>
        </header>

        {error && <div className="notice">{error}</div>}

        <section className="metrics" aria-label="Task metrics">
          <div>
            <span>{metrics.active}</span>
            <p>Active</p>
          </div>
          <div>
            <span>{metrics.completed}</span>
            <p>Completed</p>
          </div>
          <div>
            <span>{metrics.failed}</span>
            <p>Failed</p>
          </div>
        </section>

        <section className="split">
          <form className="toolPanel" onSubmit={createTask}>
            <div className="panelTitle">
              <Plus size={18} />
              <h2>Create shell task</h2>
            </div>
            <label>
              Task title
              <input value={title} onChange={(event) => setTitle(event.target.value)} />
            </label>
            <label>
              Agent
              <input value={agentId} onChange={(event) => setAgentId(event.target.value)} />
            </label>
            <label>
              Shell command
              <input value={command} onChange={(event) => setCommand(event.target.value)} />
            </label>
            <button className="primaryButton" type="submit" disabled={busy}>
              <Play size={16} />
              {busy ? "Dispatching" : "Dispatch"}
            </button>
          </form>

          <section className="listPanel" id="tasks">
            <div className="panelTitle">
              <CheckCircle2 size={18} />
              <h2>Task board</h2>
            </div>
            <div className="table">
              {tasks.map((task) => (
                <article className="row" key={task.task_id}>
                  <strong>{task.title}</strong>
                  <span>{task.assigned_agent_id || "unassigned"}</span>
                  <mark data-status={task.status}>{task.status}</mark>
                </article>
              ))}
              {tasks.length === 0 && <p className="empty">No projected tasks yet.</p>}
            </div>
          </section>
        </section>

        <section className="split lower">
          <section className="listPanel" id="agents">
            <div className="panelTitle">
              <Bot size={18} />
              <h2>Agents</h2>
            </div>
            {agents.map((agent) => (
              <article className="row" key={agent.agent_id}>
                <strong>{agent.agent_id}</strong>
                <span>{agent.agent_type}</span>
                <mark data-status={agent.status}>{agent.status}</mark>
              </article>
            ))}
            {agents.length === 0 && <p className="empty">No registered agents yet.</p>}
          </section>

          <section className="listPanel" id="feed">
            <div className="panelTitle">
              <Activity size={18} />
              <h2>Operational feed</h2>
            </div>
            {feed.map((item) => (
              <article className="feedItem" key={item.event_id}>
                <strong>{item.title || item.event_type}</strong>
                <span>{item.summary || item.aggregate_id}</span>
              </article>
            ))}
            {feed.length === 0 && <p className="empty">No events projected yet.</p>}
          </section>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
