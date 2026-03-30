from http.server import BaseHTTPRequestHandler
import requests, json

URL = "https://samagra.gov.in/Services/CommonWebApi.svc/GetDetailsBySamagra"

HEADERS = {
    "User-Agent": "okhttp/3.12.1",
    "Content-Type": "application/json; charset=UTF-8",
    "Authorization": "Basic c2FtYWdyYUFwaTpzYW1hZ3JhQDEyMw==",
}

def fetch(payload):
    try:
        r = requests.post(URL, headers=HEADERS, json=payload, timeout=4)
        if r.status_code != 200:
            return None
        return r.json().get("d", {})
    except:
        return None

def smart_get(obj, keys):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys:
                return v
            res = smart_get(v, keys)
            if res:
                return res
    elif isinstance(obj, list):
        for i in obj:
            res = smart_get(i, keys)
            if res:
                return res
    return None

def get_user_ids(mobile):
    res = fetch({"samagraID": "0", "MobileNo": mobile})
    if not res:
        return []

    items = res if isinstance(res, list) else [res]

    for it in items:
        uid = smart_get(it, ["UserID", "samagraID", "MemberID"])
        if uid:
            return [str(uid)]

    return []

def get_full(uid):
    res = fetch({"samagraID": uid})
    if not res:
        return None

    photo = smart_get(res, ["Photo"])

    return {
        "uid": uid,
        "name": smart_get(res, ["MemberNameE"]),
        "mobile": smart_get(res, ["MobileNo"]),
        "photo_url": f"data:image/jpeg;base64,{photo}" if photo else None
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs

        try:
            q = parse_qs(urlparse(self.path).query)
            mobile = q.get("mobile", [None])[0]

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            if not mobile:
                self.wfile.write(json.dumps({"status": False}).encode())
                return

            uids = get_user_ids(mobile)

            if not uids:
                self.wfile.write(json.dumps({"status": False}).encode())
                return

            data = get_full(uids[0])

            self.wfile.write(json.dumps({
                "status": True,
                "data": data
            }).encode())

        except Exception as e:
            self.wfile.write(json.dumps({
                "status": False,
                "error": str(e)
            }).encode())
