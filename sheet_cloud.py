"""Talks to the Google Apps Script web app that sits on the client's Google Sheet."""
import json
import urllib.request

import config as C


class CloudError(Exception):
    pass


def enabled():
    return bool(C.SHEET_WEBHOOK_URL)


def call(action, **payload):
    body = json.dumps({"key": C.SHEET_SECRET, "action": action, "prefix": C.ID_PREFIX, "start": C.ID_START, **payload}).encode()
    req = urllib.request.Request(C.SHEET_WEBHOOK_URL, data=body, headers={"Content-Type": "text/plain;charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:          # Apps Script answers via a 302 redirect; urllib follows it
            data = json.loads(r.read().decode("utf-8"))
    except Exception as ex:                                          # noqa: BLE001
        raise CloudError(f"Could not reach the Google Sheet ({type(ex).__name__}). Check SHEET_WEBHOOK_URL and the deployment.") from ex
    if not data.get("ok"):
        raise CloudError(f"Google Sheet refused the request: {data.get('error', 'unknown error')}")
    return data
