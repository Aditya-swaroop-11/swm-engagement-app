"""Builds the 4-page Letter of Contractual Engagement (same wording/layout as the company template)."""
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

from calc import inr, split_compensation
from config import BASE, ENGAGEMENT_TYPE

F = BASE / "fonts"
pdfmetrics.registerFont(TTFont("Body", str(F / "Carlito-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Body-Bold", str(F / "Carlito-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Body-Italic", str(F / "Carlito-Italic.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-Bold")

TXT = colors.HexColor("#4f5b78")
HEAD = colors.HexColor("#3a4560")
YELLOW = colors.HexColor("#F5B50A")
BLACK = colors.HexColor("#0b0b0b")
LINE = colors.HexColor("#d9dde6")
W, H = A4
LM = RM = 44
CW = W - LM - RM

body = ParagraphStyle("body", fontName="Body", fontSize=8.6, leading=11, textColor=TXT)
small = ParagraphStyle("small", parent=body, fontSize=8.1, leading=10.3)
bullet = ParagraphStyle("bullet", parent=body, fontSize=8.6, leading=11, leftIndent=9, bulletIndent=0, spaceAfter=2.5)
kt = ParagraphStyle("kt", parent=small, fontSize=7.6, leading=9.2, leftIndent=9, bulletIndent=0, spaceAfter=1.6)
h = ParagraphStyle("h", parent=body, fontName="Body-Bold", fontSize=9.4, leading=12, textColor=HEAD, spaceBefore=9, spaceAfter=3)
sh = ParagraphStyle("sh", parent=body, fontName="Body-Bold", fontSize=8.9, textColor=HEAD, spaceBefore=6, spaceAfter=2)
right = ParagraphStyle("right", parent=body, alignment=TA_RIGHT, fontSize=9.4, leading=11.6)


def _img(rel, width):
    from PIL import Image as PI
    w, h_ = PI.open(BASE / rel).size
    return Image(str(BASE / rel), width=width, height=width * h_ / w)


def P(t, s=body):
    return Paragraph(t, s)


def B(t, s=bullet):
    return Paragraph(t, s, bulletText="•")


def fmt_long(d):          # 7 October 2026
    return f"{d.day} {d.strftime('%B %Y')}"


def build_pdf(path, a):
    """a: dict with first_name, last_name, state, district, phone, email, assoc_id, date (datetime.date), role, monthly"""
    rows, mt, yt = split_compensation(a["monthly"])
    full = f"{a['first_name']} {a['last_name']}".strip()
    location = f"{a['district']}, {a['state']}"
    e = escape

    def footer(c, doc):
        c.saveState()
        c.setFont("Body", 8.2); c.setFillColor(colors.HexColor("#7b869f"))
        if doc.page > 1:
            c.drawString(LM, 28, "Smart Work Mart • Private & Confidential")
        c.drawRightString(W - RM, 28, f"Page {doc.page}")
        c.restoreState()

    doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=36, bottomMargin=44,
                          title=f"Letter of Contractual Engagement - {full}", author="Smart Work Mart")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(LM, 44, CW, H - 80, 0, 0, 0, 0)], onPage=footer)])
    s = []

    # ---------- header ----------
    logo = _img("static/logo.png", 120)
    addr = [P("<b>Smart Work Mart</b>", right),
            P("57 13th Cross, Baldwins Road, Koramangala, Bengaluru, India.", right),
            P("Email: Hr@smartworkmart.com", ParagraphStyle("r2", parent=right, fontSize=8.6)),
            P("Website: www.smartworkmart.com", ParagraphStyle("r3", parent=right, fontSize=8.6))]
    t = Table([[logo, addr]], colWidths=[130, CW - 130])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("LINEBELOW", (0, 0), (-1, 0), 1.6, BLACK),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    s += [t, Spacer(1, 7)]

    left = [P("<b>To,</b>", small), P(f"<b>{e(full)}</b>", small),
            P(f"<b>Address</b>: {e(location)}", small),
            P(f"<b>Contact No</b>: {e(a['phone'])}", small), P(f"<b>Email</b>: {e(a['email'])}", small)]
    rt = [P(f"<b>Associate ID:</b> {e(a['assoc_id'])}", ParagraphStyle("x", parent=small, alignment=TA_RIGHT)),
          P(f"<b>Date of Engagement:</b> {fmt_long(a['date'])}", ParagraphStyle("y", parent=small, alignment=TA_RIGHT))]
    t = Table([[left, rt]], colWidths=[CW * .55, CW * .45])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    s += [t, Spacer(1, 7)]

    lab = Table([[P('<font color="#F5B50A"><b>LETTER OF CONTRACTUAL ENGAGEMENT</b></font>',
                    ParagraphStyle("lab", parent=small, fontSize=7.4, leading=9))]], colWidths=[196])
    lab.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BLACK), ("ROUNDEDCORNERS", [4, 4, 4, 4]),
                             ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5), ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    lab.hAlign = "LEFT"
    s += [lab, Spacer(1, 6), P(f"<b>Dear {e(a['first_name'])},</b>", small), Spacer(1, 2),
          P(f"We are pleased to offer you engagement as an Independent <b>{e(a['role'])}</b> at Smart Work Mart. "
            "Smart Work Mart operates as a premier B2B marketplace connecting buyers and sellers, enabling local merchants, "
            "shopkeepers, and manufacturers to list and sell their products digitally across leading E-commerce ecosystems.", small),
          Spacer(1, 7)]

    lbl = ParagraphStyle("lbl", parent=body, fontName="Body-Bold", fontSize=9.4, textColor=HEAD)
    val = ParagraphStyle("val", parent=body, fontName="Body-Bold", fontSize=9.4, textColor=colors.HexColor("#1a1f2e"))
    info = Table([[P("Company Name:", lbl), P("Smart Work Mart", val)],
                  [P("Date of Engagement:", lbl), P(fmt_long(a["date"]), val)],
                  [P("Work Location:", lbl), P(e(location), val)],
                  [P("Engagement Type:", lbl), P(ENGAGEMENT_TYPE, val)]], colWidths=[130, CW - 130])
    info.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f6fa")),
                              ("BOX", (0, 0), (-1, -1), .6, LINE), ("LINEBEFORE", (0, 0), (0, -1), 3, YELLOW),
                              ("TOPPADDING", (0, 0), (-1, -1), 3.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
                              ("LEFTPADDING", (0, 0), (-1, -1), 12)]))
    s += [info, P("ROLES &amp; KEY RESPONSIBILITIES", h)]
    for t in [
        "<b>Daily Field Visits &amp; Merchant Sourcing:</b> Conducting daily physical store visits during field operational hours (recommended between 10:00 AM and 07:00 PM) to identify, pitch, and source prospective shopkeepers, sellers, and manufacturers across assigned territories for Smart Work Mart.",
        "<b>Platform Briefing &amp; Seller Guidance:</b> Explaining platform benefits, B2B marketplace features, pricing catalog, and digital expansion models clearly to local retail and wholesale merchants.",
        "<b>Merchant Onboarding &amp; Digital Cataloging:</b> Coordinating document collection, collecting GST/KYC details, creating seller profiles, and completing the formal onboarding process onto partner E-commerce ecosystems.",
        "<b>Store Verification &amp; Deliverable Tracking:</b> Executing real-time store visit logs, capturing geo-tagged store photos, updating genuine merchant contact details, and logging task completion data on the designated enterprise application (Jibble) purely for deliverable verification."]:
        s.append(B(t))

    # ---------- compensation ----------
    s.append(P("COMPENSATION &amp; FEE STRUCTURE (ANNEXURE A)", h))
    hs = ParagraphStyle("th", parent=body, fontName="Body-Bold", fontSize=8, textColor=colors.white)
    cell = ParagraphStyle("td", parent=body, fontSize=9.6)
    data = [[P("COMPONENT NAME", ParagraphStyle("th1", parent=hs, fontSize=9)), P("MONTHLY POTENTIAL (INR)", hs), P("YEARLY POTENTIAL (INR)", ParagraphStyle("thr", parent=hs, alignment=TA_RIGHT))]]
    for n, m, y in rows:
        data.append([P(e(n), cell), P(f"₹ {inr(m)}", cell), P(f"₹ {inr(y)}", ParagraphStyle("tdr", parent=cell, alignment=TA_RIGHT))])
    tot = ParagraphStyle("tot", parent=cell, fontName="Body-Bold", fontSize=10, textColor=colors.HexColor("#1a1f2e"))
    data.append([P("Total Gross Potential Earning", tot), P(f"₹ {inr(mt)}", tot), P(f"₹ {inr(yt)}", ParagraphStyle("totr", parent=tot, alignment=TA_RIGHT))])
    ct = Table(data, colWidths=[CW * .55, CW * .25, CW * .20])
    ct.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLACK), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                            ("LEFTPADDING", (0, 0), (0, -1), 12), ("RIGHTPADDING", (-1, 0), (-1, -1), 4),
                            ("LINEBELOW", (0, 1), (-1, -3), .5, LINE), ("LINEABOVE", (0, -1), (-1, -1), 1.2, colors.HexColor("#b9c0d0")),
                            ("LINEBELOW", (0, -1), (-1, -1), .5, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    s += [ct, Spacer(1, 8), P("<b>KEY TERMS OF ENGAGEMENT &amp; EVALUATION:</b>", ParagraphStyle("k", parent=small, fontSize=7.8, textColor=HEAD, spaceAfter=3))]
    for t in [
        "Operational Availability Window: The Associate shall have full autonomy over their daily work schedule. However, for client coordination and store accessibility, recommended field operational hours are between 10:00 AM and 07:00 PM. Operational logging via the enterprise application (Jibble) shall be required purely for task completion tracking and deliverable verification, and not as attendance control.",
        "No Separate Conveyance / Petrol Claim: All personal field expenses, fuel, conveyance, and operational costs incurred during market visits are strictly bundled within the deliverable-linked fee matrix. The Company shall not entertain any separate petrol bills, travel reimbursements, or extra claims under any circumstances.",
        "Service Discontinuation &amp; Exit Notice: Either party may discontinue this engagement by providing a written notice of 7 days. In cases of zero-performance, fake reporting, or misconduct, the Company reserves the right to cancel/discontinue the engagement immediately without notice.",
        "Service Discontinuations &amp; Exit Handover: Since this is an Independent Associate engagement, the Associate may discontinue services at any time by providing a simple 7-day prior written notification via email/app. To ensure smooth account closure, the Associate must submit all pending merchant onboarding logs, complete EOD reports, and hand over active field leads. Final deliverable payout verification shall be completed post data audit.",
        "If the Associate abruptly abandons market operations, fails to submit pending data handovers, or exits without providing the 7-day prior notification, the Company reserves the legal right to adjust unverified deliverables and operational damages against any unpaid accrued fees during final account settlement.",
        "In the event of unannounced service abandonment without data handover, or instances of gross misconduct/data fabrication, the Company reserves the legal right to set off proved operational losses, unverified leads, or damages against any accrued deliverable fees. Any remaining balance post-audit reconciliation shall be remitted during final account settlement."]:
        s.append(B(t, kt))

    # ---------- page 2 ----------
    s += [PageBreak(), P("IMPORTANT DELIVERABLE ACCRUAL DISCLAIMER:", h),
          P("The Gross Monthly Potential Earning of ₹27,000 represents the maximum achievable fee mapped strictly against the completion of daily assigned onboarding deliverables. All fee components accrue on a Daily Qualified Deliverable / Piece-Rate Basis. On operational calendar dates where verified output units or physical visits are zero or below the minimum threshold, the accrued daily fee for that specific date shall be ₹0.00. No retainer pay or allowance shall accumulate for non-productive or zero-deliverable days.".replace("₹27,000", f"₹{inr(mt)}")),
          Spacer(1, 10), P("PAYOUT DISBURSEMENT TERMS (45-DAY CYCLE):", h),
          P("The accrued fee/payout for deliverables executed by the Associate shall be verified, audited, and disbursed upon completion of a mandatory 45-day cycle from their respective official date of Engagement (e.g., payout for work executed will be processed on the 45th calendar day from the official Date of Engagement). All payouts remain strictly subject to verified Jibble App task completion logs, physical store check-ins, and merchant onboarding back-check audits."),
          P("Digital Authorization Pass, PVC Printing &amp; Expense Protocol:", sh),
          P("The Company issues a Digital Authorization Pass solely for merchant verification and security identification during field interactions. The Associate is advised to carry this Authorization Pass during merchant pitching to establish authentic platform credentials.."),
          Spacer(1, 4),
          P("Reimbursement Terms: The Company shall provide a one-time operational expense reimbursement of ₹100 (Rupees One Hundred Only) towards the local printing of the Authorization Pass and lanyard, which shall be credited with the first payout. To claim this operational expense, the Associate must submit a confirmation email along with a clear photo proof of the printed Pass to hr@smartworkmart.com. Processing of this ₹100 expense claim is strictly subject to email submission and verification."),
          ]
    for ttl, txt in [
        ("1. Proof of Daily Work Submission Clause (Daily Reporting Mandate)", "\"The Associate acknowledges that field performance validation relies solely on same-day, real-time logging via the Jibble App and daily End-of-Day (EOD) activity reports submitted before 08:00 PM. Retrospective or back-dated claims of field work without concurrent GPS logs and uploaded merchant photos shall be considered invalid and non-billable (₹0 payout).\""),
        ("2. Zero Unsanctioned Expenses / No Cash Collection Disclaimer", "\"The Associate is strictly prohibited from collecting cash, personal payments, or registration fees from merchants on behalf of the Company unless explicitly authorized in writing. The Company accepts no financial liability for unauthorized cash transactions or personal agreements made by the Associate with third parties or merchants.\""),
        ("3. Non-Exclusive / Independent Contractor Status &amp; No Third-Party Liability", "\"The Associate explicitly agrees that they operate as an independent service provider and are free to engage in other non-conflicting gigs, provided it does not breach non-compete terms. The Associate is solely responsible for their personal safety, vehicle maintenance, third-party liabilities, and compliance with local traffic laws during field movements. The Company shall not be liable for any personal injury, road accidents, or third-party damages incurred during field activity.\""),
        ("4. Direct Discontinuation for Fraud / Fake Onboarding (Zero Notice)", "Submitting false GPS locations, using mock-location software, uploading fake shop pictures, entering incorrect merchant contact numbers, or uploading forged KYC documents shall be classified as Gross Professional Fraud and Breach of Trust. In such events, the Company reserves the absolute legal right to cancel the engagement immediately without notice, forfeit all payouts pending damage audit, set off proved losses/fraud damages from accrued fees, and initiate appropriate civil/criminal legal proceedings under the Information Technology Act and applicable criminal laws."),
        ("5. Finality of Company QC Audit &amp; Deliverable Decision", "All onboarding entries are subject to mandatory telephonic and physical ground audits by the Company's Quality Control (QC) team. The decision of the Company's QC team regarding the validity, quality, and eligibility of an onboarded merchant profile shall be final, binding, and conclusive for fee calculation purposes.")]:
        s += [P(ttl, sh), P(txt)]

    # ---------- page 3 ----------
    s += [PageBreak(), P("FIELD READINESS &amp; PREREQUISITE SERVICE STANDARDS", h),
          P("To execute assigned field deliverables effectively, the Associate shall independently maintain the following operational prerequisites:"), Spacer(1, 4)]
    for t in [
        "Vehicle &amp; Regulatory Compliance: Active possession of a registered two-wheeler with a valid driving license, valid vehicle insurance, and operational fuel, ensuring full compliance with local traffic regulations.",
        "Mobile &amp; Connectivity Equipment: Active possession of a functional smartphone equipped with 4G/5G data, working GPS hardware, and adequate daily battery backup (power bank/charger) necessary for real-time deliverable logging.",
        "Service Collaterals &amp; Field Kit: Carrying essential sales collaterals including merchant agreement notebooks, writing tools, product rate cards, and digital catalogues required for merchant onboardings.",
        "Authorized Field Pass Compliance: Displaying the issued Digital Authorization Pass (printed locally on a PVC card with lanyard) during merchant interactions solely for market identification and security verification. Non-display of the pass during field pitching constitutes a breach of operational code."]:
        s.append(B(t))
    s.append(P("FIELD TASK LOGGING &amp; LOCATION AUDIT PROTOCOL (JIBBLE APP)", h))
    for t in [
        "Real-Time Verification: All operational activity logs, store interactions, merchant onboarding details, and daily field movements must be recorded live through the designated enterprise application (Jibble App).",
        "Task-Based Logging Rule: Generic time tracking without active task context is strictly prohibited. The Associate must execute a separate \"Store Visit - Start\" upon arriving at a shopkeeper's premises, capture real-time store coordinates, log merchant contact details, and execute a \"Store Visit - End\" upon departure."]:
        s.append(B(t))
    s.append(P("DELIVERABLE-LINKED FEE ACCRUAL &amp; BENCHMARK GUIDELINES", h))
    for t in [
        "<b>1.</b>The Gross Monthly Potential Earning is structured around an estimated benchmark of 15 to 20 verified physical merchant interactions daily. Associates operating independently are free to manage their daily market routing; however, achieving or exceeding this recommended benchmark optimizes merchant onboarding potential, conversion rates, and daily fee accrual.",
        "<b>2.</b>Fee accrual is purely unit-linked and calculated strictly on verified, completed deliverables (e.g., successful merchant onboardings/verified visits accompanied by authentic geo-tagged logs on the Jibble platform). The Associate earns a pre-agreed fee per unit of verified deliverable executed, independent of fixed hours or shift duration.",
        "<b>3.</b>Since this engagement is strictly output-based, fee accumulation corresponds directly to verified work submitted. On operational days where zero qualified deliverables or verified market visits are logged, the accrued fee for that specific date shall naturally reflect ₹0.00. No base retainer or idle-time compensation accumulates for zero-deliverable execution."]:
        s += [P(t), Spacer(1, 5)]
    s += [P("<b>4.ZERO EARNINGS CLAUSE FOR NON-PERFORMANCE / IDLE TIME:</b>", sh),
          B("If the Associate logs into the system but executes zero verified merchant visits, zero onboardings, or fails to submit daily geotagged proof of work on the Jibble App, no deliverable fee shall accrue for such dates (₹0.00 Payout). On days with zero verified output, the daily accrued fee naturally reflects NIL (₹0), without any base retainer or idle-time compensation."),
          B("<b>GEO-AUDIT CONSENT &amp; DATA VERIFICATION RIGHTS</b>"),
          B("Deliverable Audit Verification: \"The Associate agrees to share location data via the Jibble App strictly during active merchant check-ins solely to establish proof of execution for deliverable audits."),
          B("Data Authenticity &amp; Fraud Prevention: \"Utilizing mock-location applications, GPS spoofers, virtual emulators, or tampered APKs constitutes Gross Fraud, resulting in immediate account deactivation, forfeiture of unverified accrued fees, and potential legal action under the Information Technology Act and applicable criminal laws."),
          B("Back-Check Verification: \"The Company reserves the right to audit logged merchant entries via telephonic calls and physical ground spot-checks. Falsified shop names, dummy phone numbers, or fraudulent KYC uploads constitute commercial fraud and shall result in instant account deactivation without notice.")]

    # ---------- page 4 ----------
    s += [PageBreak(), P("MERCHANT RETENTION, ACCREDITATION &amp; CLAWBACK RECOVERY", h),
          B("Valid Merchant Onboarding: A merchant onboarding is deemed valid only when the merchant profile is fully KYC-verified, product listings are approved, and the merchant account remains operational on the designated E-commerce platform."),
          B("Clawback Policy: If an onboarded seller profile is identified as fraudulent, repeatedly unresponsive, or delisted within 30 days of registration due to misrepresentation, any fee/incentive credited against such registration shall be subject to immediate clawback and deducted from the subsequent payout cycle"),
          P("CONTRACT FOR SERVICE &amp; INDEPENDENT CONTRACTOR DECLARATION", h),
          B("Contract for Service: \"This engagement is strictly a 'Contract for Service' under the Indian Contract Act, 1872, and does NOT constitute an employer-employee (master-servant) relationship. The Associate is engaged as an Independent Piece-Rate Associate. Traditional monthly payroll guarantees, statutory employee benefit acts, and labour wage rigidities do not apply to this task-linked engagement."),
          B("Immediate Engagement Deactivation for Breach: \"The Company reserves the absolute right to deactivate the engagement with immediate effect without notice or compensation in instances of data fabrication, commercial fraud, prolonged operational inactivity, client misconduct, or violation of non-disclosure terms."),
          P("CONFIDENTIALITY &amp; DATA PROTECTION", h),
          B("Proprietary Data: The Associate shall not disclose, copy, transfer, or commercialize any merchant phone numbers, catalogs, pricing structures, or buyer-seller database acquired during engagement."),
          B("Non-Diverting of Merchants During Engagement: \"During the active engagement term, the Associate shall not divert onboarded merchants or company proprietary data to any competing B2B platform."),
          P("GOVERNING LAW &amp; ARBITRATION", h),
          P("This Agreement shall be governed by and construed in accordance with the Laws of India. Any legal disputes, claims, or proceedings arising out of or in connection with this contract shall be subject to the exclusive jurisdiction of the competent Courts/Authorities situated in Bengaluru, Karnataka, or the competent authority having direct territorial jurisdiction over the actual work location."),
          Spacer(1, 26)]

    stamp = _img("static/stamp.png", 64); stamp.hAlign = "LEFT"
    lcol = [P("<b>Issued on Behalf of Company:</b>", small), P("<b>Smart Work Mart</b>", small),
            P("57 13th Cross, Baldwins Road, Koramangala, Bengaluru, India.", small),
            P("Email: Hr@smartworkmart.com", small), P("Website: www.smartworkmart.com", small), Spacer(1, 12), stamp]
    rcol = [P("<b>Associate Acceptance:</b>", small),
            P("I accept the terms and conditions outlined in this engagement agreement and agree that my daily payout is strictly tied to verified Jibble App activity and completed deliverables.", ParagraphStyle("acc", parent=small, fontSize=7.8, textColor=colors.HexColor("#6b7690"))),
            Spacer(1, 6), P(f"<b>Associate Signature:</b> {e(a['first_name'])}", small),
            P(f"<b>Date:</b> {fmt_long(a['date'])}", small)]
    t = Table([[lcol, rcol]], colWidths=[CW * .56, CW * .44])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    s.append(KeepTogether([t, Spacer(1, 40)]))
    bl = _img("static/logo.png", 110); bl.hAlign = "RIGHT"
    s.append(bl)

    doc.build(s)
    return path
