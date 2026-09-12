import { useState, useEffect } from 'react'

const API = "http://localhost:8000";

export default function App() {
  const [s, setS] = useState({ appliances: [], total_load: 0, capacity: 800, remaining: 800 });
  const [error, setError] = useState("");
  const [form, setForm] = useState({ name: "", wattage: "", priority: "" });

  const refresh = () =>
    fetch(`${API}/status`)
      .then(r => r.json())
      .then(setS)
      .catch(() => setError("Could not reach the backend. Is it running on port 8000?"));

  useEffect(() => { refresh(); }, []);

  const call = async (url, opts) => {
    setError("");
    try {
      const res = await fetch(url, opts);
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Request failed");
      } else {
        setS(data);
      }
    } catch (err) {
      setError("Could not reach the backend. Is it running on port 8000?");
    } finally {
      // Always resync with server truth, even if the mutation response
      // didn't include the full status shape.
      refresh();
    }
  };

  const toggle = (a) =>
    call(`${API}/appliances/${a.id}/state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: a.state === "running" ? "off" : "on" }),
    });

  const del = (a) => {
    if (window.confirm(`Delete ${a.name}?`)) {
      call(`${API}/appliances/${a.id}`, { method: "DELETE" });
    }
  };

  const create = (e) => {
    e.preventDefault();

    const wattage = Number(form.wattage);
    const priority = Number(form.priority);

    if (!form.name.trim() || !wattage || !priority) {
      setError("Name, watts, and priority are all required.");
      return;
    }

    call(`${API}/appliances`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: form.name, wattage, priority }),
    });

    setForm({ name: "", wattage: "", priority: "" });
  };

  return (
    <div>
      <h1>Inverter Load Manager</h1>
      <p>{s.total_load}W / {s.capacity}W used ({s.remaining}W free)</p>
      {error && <p style={{ color: "red" }}>{error}</p>}

      <form onSubmit={create}>
        <input
          placeholder="Name"
          required
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
        />
        <input
          placeholder="Watts"
          type="number"
          required
          value={form.wattage}
          onChange={e => setForm({ ...form, wattage: e.target.value })}
        />
        <input
          placeholder="Priority"
          type="number"
          required
          value={form.priority}
          onChange={e => setForm({ ...form, priority: e.target.value })}
        />
        <button type="submit">Add</button>
      </form>

      {s.appliances.length === 0 ? (
        <p>No appliances registered yet.</p>
      ) : (
        <table border="1">
          <thead>
            <tr>
              <th>Name</th>
              <th>Watts</th>
              <th>Priority</th>
              <th>State</th>
              <th></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {s.appliances.map(a => (
              <tr key={a.id}>
                <td>{a.name}</td>
                <td>{a.wattage}</td>
                <td>{a.priority}</td>
                <td>{a.state.toUpperCase()}</td>
                <td>
                  <button onClick={() => toggle(a)}>
                    {a.state === "running" ? "Turn OFF" : "Turn ON"}
                  </button>
                </td>
                <td><button onClick={() => del(a)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}