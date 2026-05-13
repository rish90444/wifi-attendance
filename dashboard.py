"""
dashboard.py — Flask admin web UI on localhost:47832
All HTML templates are inline (Jinja2 render_template_string).
"""
import functools
import logging

from flask import (
    Flask,
    render_template_string,
    request,
    redirect,
    url_for,
    session,
    flash,
)

import config
import db

log = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# ─────────────────────────────────────────────
# Auth helper
# ─────────────────────────────────────────────

def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# HTML base template
# ─────────────────────────────────────────────

BASE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WiFi Attendance — S.P. Timber Industries</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f6fa; color: #1a1a2e; min-height: 100vh; }
  header { background: #1a1a2e; color: #fff; padding: 14px 32px;
           display: flex; align-items: center; justify-content: space-between; }
  header h1 { font-size: 1.1rem; font-weight: 600; letter-spacing: .5px; }
  header a { color: #aab; text-decoration: none; font-size: .85rem; }
  header a:hover { color: #fff; }
  main { max-width: 1100px; margin: 32px auto; padding: 0 20px; }
  section { background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08);
            margin-bottom: 28px; padding: 24px 28px; }
  section h2 { font-size: 1rem; font-weight: 600; margin-bottom: 16px;
               padding-bottom: 10px; border-bottom: 1px solid #eee; }
  table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  th { text-align: left; padding: 8px 12px; background: #f8f9fb;
       font-weight: 600; color: #555; border-bottom: 2px solid #e8e8e8; }
  td { padding: 9px 12px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr.unknown-row td { background: #fffbe6; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 20px;
           font-size: .78rem; font-weight: 600; }
  .badge-present { background: #d4f8e8; color: #1a7a4a; }
  .badge-absent  { background: #f0f0f0; color: #666; }
  .badge-checkin  { background: #d4f8e8; color: #1a7a4a; }
  .badge-checkout { background: #ffe0e0; color: #c0392b; }
  .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%;
         margin-right: 5px; vertical-align: middle; }
  .dot-green { background: #27ae60; }
  .dot-grey  { background: #bbb; }
  .btn { display: inline-block; padding: 5px 14px; border-radius: 6px; border: none;
         cursor: pointer; font-size: .85rem; font-weight: 500; text-decoration: none; }
  .btn-primary { background: #2563eb; color: #fff; }
  .btn-primary:hover { background: #1d4ed8; }
  .btn-danger  { background: #ef4444; color: #fff; }
  .btn-danger:hover  { background: #dc2626; }
  .btn-secondary { background: #e5e7eb; color: #374151; }
  .btn-secondary:hover { background: #d1d5db; }
  .flash { padding: 10px 16px; border-radius: 6px; margin-bottom: 18px;
           font-size: .9rem; }
  .flash-success { background: #d4f8e8; color: #1a7a4a; }
  .flash-error   { background: #ffe0e0; color: #c0392b; }
  /* Inline register form */
  .reg-form { display: none; margin-top: 10px; }
  .reg-form input { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 5px;
                    font-size: .88rem; margin-right: 6px; }
  /* Login page */
  .login-wrap { display: flex; align-items: center; justify-content: center;
                min-height: 80vh; }
  .login-box { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,.1);
               padding: 40px 44px; width: 360px; }
  .login-box h2 { margin-bottom: 24px; font-size: 1.2rem; }
  .login-box label { display: block; font-size: .85rem; font-weight: 500;
                     margin-bottom: 6px; color: #555; }
  .login-box input[type=password] { width: 100%; padding: 9px 12px; border: 1px solid #d1d5db;
                                    border-radius: 6px; font-size: .95rem; margin-bottom: 18px; }
  .login-box button { width: 100%; padding: 10px; background: #2563eb; color: #fff;
                      border: none; border-radius: 6px; font-size: 1rem;
                      cursor: pointer; font-weight: 600; }
  .login-box button:hover { background: #1d4ed8; }
  .empty { color: #aaa; font-size: .9rem; padding: 12px 0; }
</style>
</head>
<body>
{% if session.get('authenticated') %}
<header>
  <h1>📶 WiFi Attendance &nbsp;—&nbsp; S.P. Timber Industries</h1>
  <a href="{{ url_for('logout') }}">Log out</a>
</header>
{% endif %}
<main>
  {% for msg, cat in get_flashed_messages(with_categories=True) %}
    <div class="flash flash-{{ cat }}">{{ msg }}</div>
  {% endfor %}
  {% block content %}{% endblock %}
</main>
<script>
function toggleRegForm(mac) {
  var form = document.getElementById('reg-' + mac);
  form.style.display = form.style.display === 'block' ? 'none' : 'block';
}
</script>
</body>
</html>
"""

LOGIN_HTML = BASE_HTML.replace(
    "{% block content %}{% endblock %}",
    """
<div class="login-wrap">
  <div class="login-box">
    <h2>🔒 Admin Login</h2>
    {% for msg, cat in get_flashed_messages(with_categories=True) %}
      <div class="flash flash-{{ cat }}" style="margin-bottom:14px;">{{ msg }}</div>
    {% endfor %}
    <form method="POST" action="{{ url_for('login') }}">
      <label>Password</label>
      <input type="password" name="password" autofocus required>
      <button type="submit">Sign In</button>
    </form>
  </div>
</div>
""")

DASHBOARD_HTML = BASE_HTML.replace(
    "{% block content %}{% endblock %}",
    """
<!-- Section 1: Unknown Devices -->
<section>
  <h2>⚠️ Unknown Devices
    <span style="font-weight:400;font-size:.85rem;color:#888;margin-left:8px;">
      (seen on network, not yet registered)
    </span>
  </h2>
  {% if unknown_devices %}
  <table>
    <thead>
      <tr><th>MAC Address</th><th>First Seen</th><th>Last Seen</th><th>Times Seen</th><th>Action</th></tr>
    </thead>
    <tbody>
    {% for dev in unknown_devices %}
    <tr class="unknown-row">
      <td><code>{{ dev.mac_address }}</code></td>
      <td>{{ dev.first_seen }}</td>
      <td>{{ dev.last_seen }}</td>
      <td>{{ dev.times_seen }}</td>
      <td>
        <button class="btn btn-primary" onclick="toggleRegForm('{{ dev.mac_address }}')">Register</button>
        <div class="reg-form" id="reg-{{ dev.mac_address }}">
          <form method="POST" action="{{ url_for('register_device') }}" style="display:inline;">
            <input type="hidden" name="mac_address" value="{{ dev.mac_address }}">
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="text" name="role" placeholder="Role (e.g. Warehouse)">
            <button type="submit" class="btn btn-primary">Save</button>
          </form>
        </div>
      </td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
    <p class="empty">No unknown devices detected yet. Ask employees to connect to the office WiFi.</p>
  {% endif %}
</section>

<!-- Section 2: Registered Employees -->
<section>
  <h2>👥 Registered Employees</h2>
  {% if employees %}
  <table>
    <thead>
      <tr><th>Name</th><th>Role</th><th>MAC Address</th><th>Status</th><th>Actions</th></tr>
    </thead>
    <tbody>
    {% for emp in employees %}
    <tr>
      <td><strong>{{ emp.name }}</strong></td>
      <td>{{ emp.role or '—' }}</td>
      <td><code>{{ emp.mac_address }}</code></td>
      <td>
        {% if emp.mac_address in present_macs %}
          <span class="dot dot-green"></span><span class="badge badge-present">Present</span>
        {% else %}
          <span class="dot dot-grey"></span><span class="badge badge-absent">Absent</span>
        {% endif %}
      </td>
      <td>
        <button class="btn btn-secondary" onclick="toggleRegForm('edit-{{ emp.id }}')">Edit</button>
        {% if emp.is_active %}
        <form method="POST" action="{{ url_for('disable_employee') }}" style="display:inline;"
              onsubmit="return confirm('Disable {{ emp.name }}?')">
          <input type="hidden" name="employee_id" value="{{ emp.id }}">
          <button type="submit" class="btn btn-danger">Disable</button>
        </form>
        {% else %}
        <span style="color:#aaa;font-size:.82rem;">(disabled)</span>
        {% endif %}
        <div class="reg-form" id="reg-edit-{{ emp.id }}">
          <form method="POST" action="{{ url_for('edit_employee') }}" style="display:inline;">
            <input type="hidden" name="employee_id" value="{{ emp.id }}">
            <input type="text" name="name" value="{{ emp.name }}" required>
            <input type="text" name="role" value="{{ emp.role }}">
            <button type="submit" class="btn btn-primary">Save</button>
          </form>
        </div>
      </td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
    <p class="empty">No employees registered yet.</p>
  {% endif %}
</section>

<!-- Section 3: Today's Attendance Log -->
<section>
  <h2>📋 Today's Attendance Log</h2>
  {% if today_log %}
  <table>
    <thead><tr><th>Time</th><th>Employee</th><th>Event</th></tr></thead>
    <tbody>
    {% for entry in today_log %}
    <tr>
      <td>{{ entry.timestamp[11:16] if entry.timestamp|length > 10 else entry.timestamp }}</td>
      <td>{{ entry.name }}</td>
      <td>
        {% if entry.event_type == 'checkin' %}
          <span class="badge badge-checkin">✅ Check-in</span>
        {% else %}
          <span class="badge badge-checkout">🔴 Check-out</span>
        {% endif %}
      </td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
    <p class="empty">No events recorded today yet.</p>
  {% endif %}
</section>
""")


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == config.DASHBOARD_PASSWORD:
            session["authenticated"] = True
            log.info("Admin login successful")
            return redirect(url_for("index"))
        else:
            log.warning("Failed admin login attempt")
            flash("Incorrect password.", "error")
    return render_template_string(LOGIN_HTML)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    import scanner  # import here to avoid circular at module load
    employees    = db.get_employees()
    unknown      = db.get_unknown_devices()
    today_log    = db.get_today_log()
    present_macs = scanner.currently_present

    return render_template_string(
        DASHBOARD_HTML,
        employees=employees,
        unknown_devices=unknown,
        today_log=today_log,
        present_macs=present_macs,
    )


@app.route("/register", methods=["POST"])
@login_required
def register_device():
    mac  = request.form.get("mac_address", "").strip().lower()
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "").strip()
    if not mac or not name:
        flash("MAC address and name are required.", "error")
        return redirect(url_for("index"))
    try:
        db.register_device(mac, name, role)
        flash(f"✅ {name} registered successfully.", "success")
    except Exception as e:
        log.error("register_device error: %s", e)
        flash("Could not register device. Check logs.", "error")
    return redirect(url_for("index"))


@app.route("/employee/edit", methods=["POST"])
@login_required
def edit_employee():
    employee_id = request.form.get("employee_id")
    name        = request.form.get("name", "").strip()
    role        = request.form.get("role", "").strip()
    if not employee_id or not name:
        flash("Employee ID and name are required.", "error")
        return redirect(url_for("index"))
    try:
        db.edit_employee(int(employee_id), name, role)
        flash(f"✅ {name} updated.", "success")
    except Exception as e:
        log.error("edit_employee error: %s", e)
        flash("Could not update employee.", "error")
    return redirect(url_for("index"))


@app.route("/employee/disable", methods=["POST"])
@login_required
def disable_employee():
    employee_id = request.form.get("employee_id")
    if not employee_id:
        flash("Employee ID required.", "error")
        return redirect(url_for("index"))
    try:
        db.disable_employee(int(employee_id))
        flash("Employee disabled.", "success")
    except Exception as e:
        log.error("disable_employee error: %s", e)
        flash("Could not disable employee.", "error")
    return redirect(url_for("index"))
