/**
 * Smart Work Mart - live "Excel" register on Google Sheets.
 * Paste this whole file into Extensions > Apps Script of the Google Sheet, change SECRET, then Deploy > New deployment > Web app.
 */
const SECRET = 'CHANGE-THIS-TO-A-LONG-RANDOM-TEXT';   // must be identical to SHEET_SECRET in the app's .env
const SHEET_NAME = 'Associates';
const HEADERS = ['Sr. No.', 'Associate ID', 'Date of Engagement', 'First Name', 'Last Name', 'Full Name', 'Contact No.', 'Email ID',
  'State', 'District', 'Work Location', 'Role', 'Engagement Type', 'Total Gross Monthly (INR)', 'Base Retainer - Monthly',
  'Operational & Field Logistics - Monthly', 'Performance Deliverable - Monthly', 'Total Gross Yearly (INR)', 'Base Retainer - Yearly',
  'Operational & Field Logistics - Yearly', 'Performance Deliverable - Yearly', 'Submitted On', 'Email Status', 'PDF File'];
const MONEY = [14, 15, 16, 17, 18, 19, 20, 21];

function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function sheet_() {
  const ss = SpreadsheetApp.getActive();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    const h = sh.getRange(1, 1, 1, HEADERS.length);
    h.setValues([HEADERS]).setFontWeight('bold').setFontColor('#F5B50A').setBackground('#000000')
      .setHorizontalAlignment('center').setVerticalAlignment('middle').setWrap(true);
    sh.setRowHeight(1, 46);
    sh.setFrozenRows(1);
    sh.setFrozenColumns(2);
    const widths = [60, 170, 120, 110, 110, 160, 110, 220, 150, 150, 200, 160, 180, 120, 120, 130, 130, 120, 120, 130, 130, 150, 260, 330];
    widths.forEach(function (w, i) { sh.setColumnWidth(i + 1, w); });
    const first = ss.getSheets()[0];
    if (first.getName() === 'Sheet1' && first.getLastRow() === 0) ss.deleteSheet(first);
  }
  return sh;
}

function seqOf_(id) {
  const m = String(id || '').match(/(\d+)$/);
  return m ? parseInt(m[1], 10) : 0;
}

function lastSeq_(sh, start) {
  let last = start - 1;
  const n = sh.getLastRow();
  if (n > 1) {
    sh.getRange(2, 2, n - 1, 1).getValues().forEach(function (r) { last = Math.max(last, seqOf_(r[0])); });
  }
  return last;
}

function findRow_(sh, id) {
  const n = sh.getLastRow();
  if (n < 2) return 0;
  const ids = sh.getRange(2, 2, n - 1, 1).getValues();
  for (let i = 0; i < ids.length; i++) if (ids[i][0] === id) return i + 2;
  return 0;
}

function doPost(e) {
  let d;
  try { d = JSON.parse(e.postData.contents); } catch (err) { return out_({ ok: false, error: 'bad request' }); }
  if (!SECRET || d.key !== SECRET) return out_({ ok: false, error: 'unauthorized' });
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const sh = sheet_();
    const start = parseInt(d.start, 10) || 1;
    const prefix = String(d.prefix || '');

    if (d.action === 'peek') {
      return out_({ ok: true, assoc_id: prefix + (lastSeq_(sh, start) + 1) });
    }

    if (d.action === 'add') {
      const f = d.fields || {};
      const id = prefix + (lastSeq_(sh, start) + 1);
      const r = sh.getLastRow() + 1;
      const row = HEADERS.map(function (h) {
        if (h === 'Sr. No.') return r - 1;
        if (h === 'Associate ID') return id;
        if (h === 'Date of Engagement') { const p = String(f[h]).split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
        return f[h] === undefined ? '' : f[h];
      });
      sh.getRange(r, 7).setNumberFormat('@');                 // keep phone numbers as text
      sh.getRange(r, 1, 1, HEADERS.length).setValues([row]);
      sh.getRange(r, 3).setNumberFormat('dd-mmm-yyyy');
      MONEY.forEach(function (c) { sh.getRange(r, c).setNumberFormat('"₹"#,##0'); });
      if (r % 2 === 0) sh.getRange(r, 1, 1, HEADERS.length).setBackground('#FFF7DB');
      return out_({ ok: true, assoc_id: id, row: r });
    }

    if (d.action === 'status') {
      const r = findRow_(sh, d.assoc_id);
      if (!r) return out_({ ok: false, error: 'associate not found' });
      sh.getRange(r, HEADERS.indexOf('Email Status') + 1).setValue(d.status);
      if (d.pdf) sh.getRange(r, HEADERS.indexOf('PDF File') + 1).setValue(d.pdf);
      return out_({ ok: true });
    }

    if (d.action === 'get') {
      const r = findRow_(sh, d.assoc_id);
      if (!r) return out_({ ok: false, error: 'associate not found' });
      const vals = sh.getRange(r, 1, 1, HEADERS.length).getValues()[0];
      const rec = {};
      HEADERS.forEach(function (h, i) {
        let v = vals[i];
        if (h === 'Date of Engagement' && v instanceof Date) v = Utilities.formatDate(v, Session.getScriptTimeZone(), 'yyyy-MM-dd');
        rec[h] = v;
      });
      return out_({ ok: true, record: rec });
    }

    return out_({ ok: false, error: 'unknown action' });
  } catch (err) {
    return out_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

function doGet() {   // opening the URL in a browser only shows that the service is alive
  return out_({ ok: true, service: 'Smart Work Mart register' });
}
