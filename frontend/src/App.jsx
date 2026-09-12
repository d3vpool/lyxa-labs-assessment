import { useState, useEffect } from 'react'

const API = "http://localhost:8000";

export default function App() {
  const [s, setS] = useState({ appliances: [], total_load: 0, capacity: 800, remaining: 800});
  const [error, setError] = useState("")
  const [form, setForm] = useState({
    name: "",
    wattage: "",
    priority: ""
  });

  const refresh = () => fetch(`${API}/status`).then(r => r.json()).then(setS);
  useEffect(() => { refresh();}, []);

  const call = async(URL, opts) => {
    setError("");
    const res = await fetch(URL, opts);
    const data = await res.json();
    if (!res.ok) setError(data.detail);
    else setS(data)

  }

  const toggle = (a) => 
    call(`${API}/appliances/${a.id}/state`,{
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({action: a.state === "running" ? "off":"on"}),
    });

    const del = (a) => {
      if (window.confirm(`Delete ${a.name}?`)) call(`${API}/appliances/${a.id}`, {method: "DELETE"});
    };

    const create = (e) => {
      e.preventDefault();
      call(`${API}/appliances`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name: form.name, wattage: +form.wattage, priority: +form.priority}),
      });
      setForm({name: "", wattage: "", priority: ""});
    };


    return (
      <div>
        <h1>Inverter Load Manager</h1>
        <p>{s.total_load}W / {s.capacity}W used ({s.remaining}W free)</p>
        {error && <p style={{color: "red"}}>{error}</p>}

        <form onSubmit={create}>
          <input placeholder='Name' required value={form.name} onChange={e => setForm({...form, name: e.target.value})}/>
          <input placeholder='Watts' type='number' required value={form.wattage} onChange={e => setForm({...form, wattage: e.target.value})}/>
          <input placeholder='Name' type='number' required value={form.priority} onChange={e => setForm({...form, priority: e.target.value})}/>
          <button type="submit">Add</button>
        </form>

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
                <td><button onClick={() => toggle(a)}>{a.state === "running"?"Turn OFF":"Turn ON"}</button></td>
                <td><button onClick={() => del(a)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>


    );
}