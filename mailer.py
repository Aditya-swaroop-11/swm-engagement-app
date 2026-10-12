"""Builds and sends the 'Official Letter of Engagement' email (PDF attached)."""
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from html import escape as e
from pathlib import Path

import config as C


def smtp_ready():
    return bool(C.SMTP_HOST and C.SMTP_PASSWORD)


def _long(d):
    return f"{d.day} {d.strftime('%B %Y')}"


def build_message(a, pdf_path):
    """a: first_name,last_name,state,district,phone,email,assoc_id,date,role"""
    full = f"{a['first_name']} {a['last_name']}".strip()
    loc = f"{a['district']}, {a['state']}"
    accept = (f"mailto:{C.SENDER_EMAIL}?subject=" + f"Engagement Agreement Accepted - {full} ({a['assoc_id']})".replace(" ", "%20")
              + "&body=" + f"I, {full} (Associate ID: {a['assoc_id']}), accept the Engagement Agreement.".replace(" ", "%20"))
    rows = [("Associate Name:", full), ("Associate ID:", a["assoc_id"]), ("Engagement Type:", C.ENGAGEMENT_TYPE),
            ("Location:", loc), ("Contact Number:", a["phone"]), ("Email Address:", a["email"]),
            ("Date of Engagement:", a["date"].strftime("%d-%m-%Y"))]
    tr = "".join(f'<tr><td style="padding:5px 18px 5px 0;font-weight:bold;color:#3a4560;white-space:nowrap">{e(k)}</td>'
                 f'<td style="padding:5px 0;font-weight:bold;color:#111">{e(v)}</td></tr>' for k, v in rows)
    html = f"""<!doctype html><html><body style="margin:0;padding:0;background:#ffffff;font-family:Segoe UI,Arial,sans-serif;color:#3a4560">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:680px"><tr><td>
<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:#1a237e;padding:14px 16px 12px 16px">
<div style="font-size:28px;font-weight:800;color:#ffffff;letter-spacing:.3px">SMART WORK MART</div>
<div style="font-size:15px;color:#ffffff;margin-top:6px">Your Search Ends Here</div></td></tr></table>
<div style="padding:18px 6px 0 6px">
<div style="font-size:24px;font-weight:bold;color:#1a237e;margin-bottom:10px">Dear {e(a['first_name'])},</div>
<p style="font-size:16px;line-height:1.6;margin:0 0 18px 0">We are pleased to offer you engagement as an Independent <b>{e(a['role'])}</b> at <b>Smart Work Mart</b>.
Your Engagement is effective from <b>{_long(a['date'])}</b>.</p>
<p style="font-size:16px;line-height:1.6;margin:0 0 18px 0">Please find your detailed Engagement Agreement <b>PDF attached</b> with this email. Review the terms and conditions carefully.</p>
<table cellpadding="0" cellspacing="0" style="font-size:15px;margin:6px 0 10px 0">{tr}</table>
<div style="font-size:18px;font-weight:bold;color:#1a237e;margin:14px 0 18px 0">ACTION REQUIRED TO CONFIRM YOUR ENGAGEMENT</div>
<p style="font-size:16px;margin:0 0 16px 0">Complete your Documentations - <a href="{e(C.ONBOARDING_FORM_URL)}" style="background:#1a237e;color:#ffffff;font-weight:bold;text-decoration:none;padding:4px 8px">COMPLETE ONBOARDING FORM</a></p>
<p style="margin:0 0 20px 0"><a href="{e(accept)}" style="display:inline-block;background:#F5B50A;color:#000000;font-weight:bold;text-decoration:none;padding:12px 22px;border-radius:5px;font-size:15px">I ACCEPT THE ENGAGEMENT AGREEMENT</a></p>
<p style="font-size:14px;line-height:1.5;margin:0 0 22px 0">* Clicking "I ACCEPT THE ENGAGEMENT AGREEMENT" will automatically send an official acceptance email to our HR Department.</p>
<div style="font-size:14px;line-height:1.55;color:#222"><b>Smart Work Mart HR Department</b><br>57, 13th Cross, Baldwins Road, Koramangala, Bengaluru, Karnataka, India<br>
Email: <a href="mailto:HR@smartworkmart.com" style="color:#1a237e">HR@smartworkmart.com</a> | Website: <a href="https://www.smartworkmart.com" style="color:#1a237e">www.smartworkmart.com</a></div>
</div></td></tr></table></body></html>"""
    text = (f"Dear {a['first_name']},\n\nWe are pleased to offer you engagement as an Independent {a['role']} at Smart Work Mart. "
            f"Your Engagement is effective from {_long(a['date'])}.\n\nPlease find your detailed Engagement Agreement PDF attached with this email. "
            "Review the terms and conditions carefully.\n\n" + "\n".join(f"{k} {v}" for k, v in rows) +
            f"\n\nACTION REQUIRED TO CONFIRM YOUR ENGAGEMENT\nComplete your Documentations - COMPLETE ONBOARDING FORM: {C.ONBOARDING_FORM_URL}\n"
            f"I ACCEPT THE ENGAGEMENT AGREEMENT: {accept}\n\n* Clicking \"I ACCEPT THE ENGAGEMENT AGREEMENT\" will automatically send an official acceptance email to our HR Department.\n\n"
            "Smart Work Mart HR Department\n57, 13th Cross, Baldwins Road, Koramangala, Bengaluru, Karnataka, India\nEmail: HR@smartworkmart.com | Website: www.smartworkmart.com\n")
    m = EmailMessage()
    m["Subject"] = f"Official Letter of Engagement - {a['first_name']}"
    m["From"] = formataddr((C.SENDER_NAME, C.SENDER_EMAIL))
    m["To"] = a["email"]
    m["Date"] = formatdate(localtime=True)
    m["Message-ID"] = make_msgid(domain="smartworkmart.com")
    m.set_content(text)
    m.add_alternative(html, subtype="html")
    m.add_attachment(Path(pdf_path).read_bytes(), maintype="application", subtype="pdf",
                     filename=f"{a['first_name']}_{a['last_name']}_Engagement_Agreement.pdf".replace(" ", "_"))
    return m


def send(a, pdf_path):
    """Returns (ok: bool, status_text: str)."""
    msg = build_message(a, pdf_path)
    if not smtp_ready():
        C.OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        f = C.OUTBOX_DIR / f"{a['assoc_id'].replace('/', '-')}.eml"
        f.write_bytes(bytes(msg))
        return False, f"NOT SENT - SMTP not configured (saved as {f.name})"
    try:
        if C.SMTP_SECURITY == "ssl":
            with smtplib.SMTP_SSL(C.SMTP_HOST, C.SMTP_PORT, context=ssl.create_default_context(), timeout=40) as s:
                s.login(C.SMTP_USER, C.SMTP_PASSWORD); s.send_message(msg)
        else:
            with smtplib.SMTP(C.SMTP_HOST, C.SMTP_PORT, timeout=40) as s:
                s.starttls(context=ssl.create_default_context()); s.login(C.SMTP_USER, C.SMTP_PASSWORD); s.send_message(msg)
        return True, "Sent"
    except Exception as ex:                      # noqa: BLE001 - report any SMTP problem to the operator
        return False, f"NOT SENT - {type(ex).__name__}: {ex}"[:200]
