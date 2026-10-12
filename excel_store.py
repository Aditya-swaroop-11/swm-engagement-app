"""Excel register (one row per associate) + safe, sequential Associate ID allocation."""
import json
import re
import threading
from datetime import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import sheet_cloud
from config import COUNTER_PATH, DATA_DIR, EXCEL_PATH, ID_PREFIX, ID_START, PDF_DIR

LOCK = threading.Lock()
SHEET = "Associates"
COLUMNS = [
    ("Sr. No.", 7), ("Associate ID", 22), ("Date of Engagement", 17), ("First Name", 16), ("Last Name", 16),
    ("Full Name", 24), ("Contact No.", 14), ("Email ID", 30), ("State", 20), ("District", 20),
    ("Work Location", 28), ("Role", 22), ("Engagement Type", 24),
    ("Total Gross Monthly (INR)", 16), ("Base Retainer - Monthly", 16), ("Operational & Field Logistics - Monthly", 18),
    ("Performance Deliverable - Monthly", 18), ("Total Gross Yearly (INR)", 16), ("Base Retainer - Yearly", 16),
    ("Operational & Field Logistics - Yearly", 18), ("Performance Deliverable - Yearly", 18),
    ("Submitted On", 20), ("Email Status", 30), ("PDF File", 40),
]
MONEY_COLS = range(14, 22)
ID_COL, STATUS_COL = 2, 23


def _ensure():
    DATA_DIR.mkdir(parents=True, exist_ok=True); PDF_DIR.mkdir(parents=True, exist_ok=True)
    if EXCEL_PATH.exists():
        return
    wb = Workbook(); ws = wb.active; ws.title = SHEET
    thin = Side(style="thin", color="000000")
    for i, (name, width) in enumerate(COLUMNS, 1):
        c = ws.cell(row=1, column=i, value=name)
        c.font = Font(bold=True, color="F5B50A", name="Calibri", size=11)
        c.fill = PatternFill("solid", fgColor="000000")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = Border(bottom=thin)
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.row_dimensions[1].height = 46
    ws.freeze_panes = "C2"
    wb.save(EXCEL_PATH)


def _seq(assoc_id):
    m = re.search(r"(\d+)$", str(assoc_id or ""))
    return int(m.group(1)) if m else 0


def _last_seq():
    last = ID_START - 1
    try:
        last = max(last, int(json.loads(COUNTER_PATH.read_text()).get("last", 0)))
    except Exception:
        pass
    if EXCEL_PATH.exists():
        wb = load_workbook(EXCEL_PATH, read_only=True)
        for row in wb[SHEET].iter_rows(min_row=2, min_col=ID_COL, max_col=ID_COL, values_only=True):
            last = max(last, _seq(row[0]))
        wb.close()
    return last


def _cloud_fields(rec):
    comp = rec["rows"]
    names = [c[0] for c in COLUMNS]
    vals = [None, None, rec["date"].isoformat(), rec["first_name"], rec["last_name"], f"{rec['first_name']} {rec['last_name']}",
            rec["phone"], rec["email"], rec["state"], rec["district"], f"{rec['district']}, {rec['state']}",
            rec["role"], rec["engagement_type"], rec["monthly"], comp[0][1], comp[1][1], comp[2][1],
            rec["monthly"] * 12, comp[0][2], comp[1][2], comp[2][2], datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "Pending", ""]
    return {k: v for k, v in zip(names, vals) if v is not None}


def peek_next_id():
    if sheet_cloud.enabled():
        return sheet_cloud.call("peek")["assoc_id"]
    with LOCK:
        _ensure()
        return f"{ID_PREFIX}{_last_seq() + 1}"


def add_record(rec, build_pdf_fn):
    """Allocates the next ID, builds the PDF, appends the Excel row. Returns (assoc_id, pdf_path).
    Nothing is consumed (no ID, no row) if the PDF or the Excel save fails."""
    if sheet_cloud.enabled():
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        fields = _cloud_fields(rec)
        assoc_id = sheet_cloud.call("add", fields=fields)["assoc_id"]      # row is created + ID assigned atomically in the sheet
        rec = {**rec, "assoc_id": assoc_id}
        pdf_name = f"{assoc_id.replace('/', '-')}_{rec['first_name']}_{rec['last_name']}.pdf".replace(" ", "_")
        pdf_path = PDF_DIR / pdf_name
        try:
            build_pdf_fn(pdf_path, rec)
            sheet_cloud.call("status", assoc_id=assoc_id, status="Pending", pdf=pdf_name)
        except Exception as ex:                                              # noqa: BLE001
            try: sheet_cloud.call("status", assoc_id=assoc_id, status=f"FAILED - PDF error: {ex}"[:150])
            except Exception: pass                                           # noqa: BLE001
            raise
        return assoc_id, pdf_path
    with LOCK:
        _ensure()
        seq = _last_seq() + 1
        assoc_id = f"{ID_PREFIX}{seq}"
        rec = {**rec, "assoc_id": assoc_id}
        pdf_name = f"{assoc_id.replace('/', '-')}_{rec['first_name']}_{rec['last_name']}.pdf".replace(" ", "_")
        pdf_path = PDF_DIR / pdf_name
        build_pdf_fn(pdf_path, rec)

        wb = load_workbook(EXCEL_PATH); ws = wb[SHEET]
        n = ws.max_row  # header is row 1 -> Sr. No. = existing data rows + 1
        comp = rec["rows"]
        vals = [n, assoc_id, rec["date"], rec["first_name"], rec["last_name"], f"{rec['first_name']} {rec['last_name']}",
                rec["phone"], rec["email"], rec["state"], rec["district"], f"{rec['district']}, {rec['state']}",
                rec["role"], rec["engagement_type"], rec["monthly"], comp[0][1], comp[1][1], comp[2][1],
                rec["monthly"] * 12, comp[0][2], comp[1][2], comp[2][2],
                datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "Pending", pdf_name]
        ws.append(vals)
        r = ws.max_row
        thin = Side(style="thin", color="D0D0D0")
        for c in range(1, len(COLUMNS) + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = Border(top=thin, bottom=thin, left=thin, right=thin)
            cell.alignment = Alignment(vertical="center", horizontal="left" if c in (4, 5, 6, 8, 9, 10, 11, 12, 13, 24) else "center")
            if c in MONEY_COLS:
                cell.number_format = '"₹"#,##0'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            if r % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="FFF7DB")
        ws.cell(row=r, column=3).number_format = "DD-MMM-YYYY"
        ws.cell(row=r, column=7).number_format = "@"
        wb.save(EXCEL_PATH)          # raises PermissionError if the file is open in Excel
        COUNTER_PATH.write_text(json.dumps({"last": seq}))
        return assoc_id, pdf_path


def set_status(assoc_id, status):
    if sheet_cloud.enabled():
        try:
            sheet_cloud.call("status", assoc_id=assoc_id, status=status); return True
        except sheet_cloud.CloudError:
            return False
    with LOCK:
        for _ in range(2):
            try:
                wb = load_workbook(EXCEL_PATH); ws = wb[SHEET]
                for row in ws.iter_rows(min_row=2, min_col=ID_COL, max_col=ID_COL):
                    if row[0].value == assoc_id:
                        ws.cell(row=row[0].row, column=STATUS_COL, value=status)
                        break
                wb.save(EXCEL_PATH)
                return True
            except PermissionError:
                continue
        return False


def get_record(assoc_id):
    if sheet_cloud.enabled():
        return sheet_cloud.call("get", assoc_id=assoc_id).get("record")
    with LOCK:
        wb = load_workbook(EXCEL_PATH, read_only=True)
        for row in wb[SHEET].iter_rows(min_row=2, values_only=True):
            if row[ID_COL - 1] == assoc_id:
                wb.close()
                return dict(zip([c[0] for c in COLUMNS], row))
        wb.close()
    return None
