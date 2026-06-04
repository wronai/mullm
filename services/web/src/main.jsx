import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  Bot,
  CheckCircle2,
  Play,
  Plus,
  RefreshCw,
  TerminalSquare,
} from "lucide-react";
import "./styles.css";

const ORCHESTRATOR_URL = envUrl(
  ["REACT_APP_API_URL", "VITE_API_URL"],
  "http://localhost:8001"
);
const PROJECTOR_URL = envUrl(
  ["REACT_APP_PROJECTOR_URL", "VITE_PROJECTOR_URL"],
  "http://localhost:8002"
);

function envUrl(keys, fallback) {
  return keys.map((key) => import.meta.env[key]).find(Boolean) || fallback;
}

async function fetchJson(url, unavailableMessage) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(unavailableMessage || (await response.text()));
  return await response.json();
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await response.text());
  return await response.json();
}

function taskMetrics(tasks) {
  return {
    active: tasks.filter((task) =>
      ["assigned", "running", "pending"].includes(task.status)
    ).length,
    completed: tasks.filter((task) => task.status === "completed").length,
    failed: tasks.filter((task) => task.status === "failed").length,
  };
}

function App() {
  const [tasks, setTasks] = useState([]);
  const [agents, setAgents] = useState([]);
  const [feed, setFeed] = useState([]);
  const [title, setTitle] = useState("Review staging pipeline");
  const [command, setCommand] = useState("pwd");
  const [agentId, setAgentId] = useState("shell-agent-1");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const metrics = useMemo(() => taskMetrics(tasks), [tasks]);

  async function refresh() {
    setError("");
    const [taskData, agentData, feedData] = await Promise.all([
      fetchJson(`${PROJECTOR_URL}/projections/tasks`, "Projection API is not available"),
      fetchJson(`${PROJECTOR_URL}/projections/agents`, "Projection API is not available"),
      fetchJson(`${PROJECTOR_URL}/projections/feed?limit=20`, "Projection API is not available"),
    ]);
    setTasks(taskData.items || []);
    setAgents(agentData.items || []);
    setFeed(feedData.items || []);
  }

  async function createTask(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const created = await postJson(`${ORCHESTRATOR_URL}/api/commands/tasks`, {
        title,
        priority: "medium",
        execution_mode: "semi_auto",
        required_capabilities: ["shell"],
      });
      await postJson(`${ORCHESTRATOR_URL}/api/commands/tasks/assign`, {
        task_id: created.result.aggregate_id,
        agent_id: agentId,
        command,
      });
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
      <Sidebar />
      <section className="workspace">
        <Topbar onRefresh={refresh} />
        {error && <div className="notice">{error}</div>}
        <Metrics metrics={metrics} />
        <section className="split">
          <TaskForm
            agentId={agentId}
            busy={busy}
            command={command}
            onAgentChange={setAgentId}
            onCommandChange={setCommand}
            onSubmit={createTask}
            onTitleChange={setTitle}
            title={title}
          />
          <TaskBoard tasks={tasks} />
        </section>
        <section className="split lower">
          <AgentsPanel agents={agents} />
          <FeedPanel feed={feed} />
        </section>
      </section>
    </main>
  );
}

function Sidebar() {
  return (
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
  );
}

function Topbar({ onRefresh }) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Control plane</p>
        <h1>Operational queue</h1>
      </div>
      <button
        className="iconButton"
        onClick={() => onRefresh()}
        aria-label="Refresh projections"
        title="Refresh projections"
      >
        <RefreshCw size={18} />
      </button>
    </header>
  );
}

function Metrics({ metrics }) {
  return (
    <section className="metrics" aria-label="Task metrics">
      <Metric value={metrics.active} label="Active" />
      <Metric value={metrics.completed} label="Completed" />
      <Metric value={metrics.failed} label="Failed" />
    </section>
  );
}

function Metric({ value, label }) {
  return (
    <div>
      <span>{value}</span>
      <p>{label}</p>
    </div>
  );
}

function TaskForm({
  agentId,
  busy,
  command,
  onAgentChange,
  onCommandChange,
  onSubmit,
  onTitleChange,
  title,
}) {
  return (
    <form className="toolPanel" onSubmit={onSubmit}>
      <div className="panelTitle">
        <Plus size={18} />
        <h2>Create shell task</h2>
      </div>
      <label>
        Task title
        <input value={title} onChange={(event) => onTitleChange(event.target.value)} />
      </label>
      <label>
        Agent
        <input value={agentId} onChange={(event) => onAgentChange(event.target.value)} />
      </label>
      <label>
        Shell command
        <input value={command} onChange={(event) => onCommandChange(event.target.value)} />
      </label>
      <button className="primaryButton" type="submit" disabled={busy}>
        <Play size={16} />
        {busy ? "Dispatching" : "Dispatch"}
      </button>
    </form>
  );
}

function TaskBoard({ tasks }) {
  return (
    <section className="listPanel" id="tasks">
      <div className="panelTitle">
        <CheckCircle2 size={18} />
        <h2>Task board</h2>
      </div>
      <div className="table">
        {tasks.map((task) => (
          <TaskRow task={task} key={task.task_id} />
        ))}
        {tasks.length === 0 && <p className="empty">No projected tasks yet.</p>}
      </div>
    </section>
  );
}

function TaskRow({ task }) {
  return (
    <article className="row">
      <strong>{task.title}</strong>
      <span>{task.assigned_agent_id || "unassigned"}</span>
      <mark data-status={task.status}>{task.status}</mark>
    </article>
  );
}

function AgentsPanel({ agents }) {
  return (
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
  );
}

function FeedPanel({ feed }) {
  return (
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
  );
}

createRoot(document.getElementById("root")).render(<App />);
