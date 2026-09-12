import sqlite3
from datetime import datetime, timezone

CAPACITY_WATTS = 800  # max limit


class ApplianceNotFound(Exception):
    pass


class CapacityRejected(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _total_load(conn):
    row = conn.execute(
        "SELECT COALESCE(SUM(wattage), 0) AS total FROM appliances WHERE state = 'running'"
    ).fetchone()
    return row["total"]


def _log(conn, appliance_id, appliance_name, action, reason):
    conn.execute(
        "INSERT INTO event_log (timestamp, appliance_id, appliance_name, action, reason) "
        "VALUES (?, ?, ?, ?, ?)",
        (_now(), appliance_id, appliance_name, action, reason),
    )


def _get_appliance(conn, appliance_id):
    row = conn.execute(
        "SELECT * FROM appliances WHERE id = ?", (appliance_id,)
    ).fetchone()
    if row is None:
        raise ApplianceNotFound(f"No appliance with id {appliance_id}")
    return row


def _auto_restore(conn, trigger_reason):
    shed = conn.execute(
        "SELECT * FROM appliances WHERE state = 'shed' ORDER BY priority ASC, id ASC"
    ).fetchall()

    current_load = _total_load(conn)

    for appliance in shed:
        if current_load + appliance["wattage"] <= CAPACITY_WATTS:
            conn.execute(
                "UPDATE appliances SET state = 'running' WHERE id = ?",
                (appliance["id"],),
            )
            current_load += appliance["wattage"]
            _log(
                conn,
                appliance["id"],
                appliance["name"],
                "restored",
                f"{appliance['name']} restored ({trigger_reason})",
            )


def get_status(conn):
    appliances = conn.execute(
        "SELECT * FROM appliances ORDER BY priority ASC, id ASC"
    ).fetchall()

    total = _total_load(conn)

    return {
        "appliances": [dict(a) for a in appliances],
        "total_load": total,
        "capacity": CAPACITY_WATTS,
        "remaining": CAPACITY_WATTS - total,
    }


def register_appliance(conn, name, wattage, priority):
    cursor = conn.execute(
        "INSERT INTO appliances (name, wattage, priority, state) VALUES (?, ?, ?, 'off')",
        (name, wattage, priority),
    )
    appliance_id = cursor.lastrowid
    _log(conn, appliance_id, name, "registered", f"{name} registered ({wattage}W, priority {priority})")
    return appliance_id


def delete_appliance(conn, appliance_id):
    appliance = _get_appliance(conn, appliance_id)
    was_running = appliance["state"] == "running"

    conn.execute("DELETE FROM appliances WHERE id = ?", (appliance_id,))
    _log(conn, appliance_id, appliance["name"], "deleted", f"{appliance['name']} deleted")

    if was_running:
        _auto_restore(conn, f"capacity freed by deleting {appliance['name']}")


def turn_on(conn, appliance_id):
    appliance = _get_appliance(conn, appliance_id)

    if appliance["state"] == "running":
        return

    current_load = _total_load(conn)
    projected = current_load + appliance["wattage"]

    if projected <= CAPACITY_WATTS:
        conn.execute("UPDATE appliances SET state = 'running' WHERE id = ?", (appliance_id,))
        _log(conn, appliance_id, appliance["name"], "on", f"{appliance['name']} turned ON")
        return

    candidates = conn.execute(
        "SELECT * FROM appliances WHERE state = 'running' AND priority > ? "
        "ORDER BY priority DESC, id ASC",
        (appliance["priority"],),
    ).fetchall()

    freed = 0
    to_shed = []
    for c in candidates:
        if current_load - freed + appliance["wattage"] <= CAPACITY_WATTS:
            break
        freed += c["wattage"]
        to_shed.append(c)

    if current_load - freed + appliance["wattage"] > CAPACITY_WATTS:
        raise CapacityRejected(
            f"Cannot turn on {appliance['name']} ({appliance['wattage']}W): "
            f"only {CAPACITY_WATTS - (current_load - freed)}W would be available "
            f"even after shedding all lower-priority appliances."
        )

    for c in to_shed:
        conn.execute("UPDATE appliances SET state = 'shed' WHERE id = ?", (c["id"],))
        _log(conn, c["id"], c["name"], "shed", f"{c['name']} shed to make room for {appliance['name']}")

    conn.execute("UPDATE appliances SET state = 'running' WHERE id = ?", (appliance_id,))
    _log(conn, appliance_id, appliance["name"], "on", f"{appliance['name']} turned ON")


def turn_off(conn, appliance_id):
    appliance = _get_appliance(conn, appliance_id)

    if appliance["state"] == "off":
        return

    if appliance["state"] == "shed":
        conn.execute("UPDATE appliances SET state = 'off' WHERE id = ?", (appliance_id,))
        _log(conn, appliance_id, appliance["name"], "off", f"{appliance['name']} turned OFF (was waiting, cancelled)")
        return

    conn.execute("UPDATE appliances SET state = 'off' WHERE id = ?", (appliance_id,))
    _log(conn, appliance_id, appliance["name"], "off", f"{appliance['name']} turned OFF")
    _auto_restore(conn, f"capacity freed by turning off {appliance['name']}")