import hmac
import json
import os
import re
from datetime import date, datetime

from flask import Flask, Response, jsonify, redirect, render_template, request, send_from_directory

import config as C
import excel_store as X
import mailer
import sheet_cloud
from calc import inr, split_compensation
from pdf_builder import build_pdf

app = Flask(__name__)
STATES = json.loads((C.BASE / "static" / "states.json").read_text(encoding="utf-8"))
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{0,39}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


@app.before_request
def require_login():
    """Simple username/password prompt so that only your team can use the page (set APP_PASSWORD in .env)."""
    if not C.APP_PASSWORD:
        return None
    a = request.authorization
    if a and hmac.compare_digest(a.username or "", C.APP_USERNAME) and hmac.compare_digest(a.password or "", C.APP_PASSWORD):
        return None
    return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Smart Work Mart HR"'})


def _peek():
    try:
        return X.peek_next_id()
    except Exception:                                    # noqa: BLE001 - the page must still open if the sheet is unreachable
        return "Assigned on submit"


@app.get("/")
def index():
    return render_template("form.html", roles=C.ROLES, next_id=_peek(), split=C.SPLIT, cloud=sheet_cloud.enabled())


@app.get("/api/next-id")
def next_id():
    return jsonify(id=_peek())


def _clean(d):
    err = {}
    g = lambda k: str(d.get(k, "")).strip()          # noqa: E731
    first, last = re.sub(r"\s+", " ", g("first_name")), re.sub(r"\s+", " ", g("last_name"))
    if not NAME_RE.match(first): err["first_name"] = "Enter a valid first name (letters only)."
    if not NAME_RE.match(last): err["last_name"] = "Enter a valid last name (letters only)."
    state, district = g("state"), g("district")
    if state not in STATES: err["state"] = "Select a state."
    elif district not in STATES[state]: err["district"] = "Select a district."
    phone = re.sub(r"[\s\-]", "", g("phone")).removeprefix("+91")
    if not re.fullmatch(r"[6-9]\d{9}", phone): err["phone"] = "Enter a valid 10-digit mobile number."
    email = g("email")
    if not EMAIL_RE.match(email): err["email"] = "Enter a valid email address."
    try: dt = datetime.strptime(g("date"), "%Y-%m-%d").date()
    except ValueError: dt = None; err["date"] = "Choose the date of engagement."
    role = g("role")
    if role not in C.ROLES: err["role"] = "Select a role."
    try:
        monthly = int(re.sub(r"[,\s₹]", "", g("monthly")))
        if not 1 <= monthly <= 10_000_000: raise ValueError
    except ValueError:
        monthly = 0; err["monthly"] = "Enter the monthly gross amount in rupees."
    return err, dict(first_name=first.title() if first.islower() else first, last_name=last.title() if last.islower() else last,
                     state=state, district=district, phone=phone, email=email, date=dt, role=role, monthly=monthly)


@app.post("/api/submit")
def submit():
    err, a = _clean(request.get_json(force=True, silent=True) or {})
    if err:
        return jsonify(ok=False, errors=err), 400
    rows, _, _ = split_compensation(a["monthly"])
    try:
        assoc_id, pdf_path = X.add_record({**a, "rows": rows, "engagement_type": C.ENGAGEMENT_TYPE}, build_pdf)
    except PermissionError:
        return jsonify(ok=False, message="The Excel register is open in another program. Close Associates_Register.xlsx and press Submit again."), 409
    except sheet_cloud.CloudError as ex:
        return jsonify(ok=False, message=str(ex)), 502
    except Exception as ex:                                     # noqa: BLE001
        app.logger.exception("submit failed")
        return jsonify(ok=False, message=f"Could not save the record: {ex}"), 500
    a["assoc_id"] = assoc_id
    ok, status = mailer.send(a, pdf_path)
    saved = X.set_status(assoc_id, status)
    return jsonify(ok=True, assoc_id=assoc_id, email_sent=ok, email_status=status, excel_updated=saved,
                   pdf=pdf_path.name, name=f"{a['first_name']} {a['last_name']}", to=a["email"], next_id=_peek())


def _as_date(v):
    if isinstance(v, datetime): return v.date()
    if isinstance(v, date): return v
    return date.fromisoformat(str(v)[:10])


@app.post("/api/resend")
def resend():
    aid = (request.get_json(force=True, silent=True) or {}).get("assoc_id", "")
    try:
        r = X.get_record(aid)
    except sheet_cloud.CloudError as ex:
        return jsonify(ok=False, message=str(ex)), 502
    if not r:
        return jsonify(ok=False, message="Associate not found."), 404
    a = dict(first_name=r["First Name"], last_name=r["Last Name"], state=r["State"], district=r["District"], phone=str(r["Contact No."]),
             email=r["Email ID"], assoc_id=aid, role=r["Role"], date=_as_date(r["Date of Engagement"]))
    pdf = C.PDF_DIR / (r["PDF File"] or "")
    if not pdf.is_file():                                    # e.g. the server was restarted: rebuild the same letter
        rows, _, _ = split_compensation(int(r["Total Gross Monthly (INR)"]))
        pdf = C.PDF_DIR / f"{aid.replace('/', '-')}_{a['first_name']}_{a['last_name']}.pdf".replace(" ", "_")
        C.PDF_DIR.mkdir(parents=True, exist_ok=True)
        build_pdf(pdf, {**a, "monthly": int(r["Total Gross Monthly (INR)"])})
    ok, status = mailer.send(a, pdf)
    X.set_status(aid, status)
    return jsonify(ok=True, email_sent=ok, email_status=status)


@app.get("/download/<path:name>")
def download(name):
    return send_from_directory(C.PDF_DIR, name, as_attachment=True)


@app.get("/register")
def register():
    if sheet_cloud.enabled():                                # live Google Sheet: opens in the browser, always up to date
        return redirect(C.SHEET_URL or "https://docs.google.com/spreadsheets", 302)
    X.peek_next_id()
    return send_from_directory(C.DATA_DIR, C.EXCEL_PATH.name, as_attachment=True)


if __name__ == "__main__":
    print("\n  Smart Work Mart - Engagement Letter Generator\n  Open  http://127.0.0.1:5000  in your browser\n")
    print("  Register : " + ("LIVE GOOGLE SHEET" if sheet_cloud.enabled() else "local Excel file (data/Associates_Register.xlsx)"))
    if not C.APP_PASSWORD:
        print("  WARNING: APP_PASSWORD is empty - anyone who can open this page can send letters.")
    if not mailer.smtp_ready():
        print("  NOTE: SMTP is not configured (.env). Emails will be saved to data/outbox instead of being sent.\n")
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")), debug=False)
