"""Smoke-test the deployed browser-local SprintBoard showcase."""
import json, re, time, urllib.error, urllib.request
BASE="https://sprintboard-live-olabs123.onrender.com"
def fetch(path):
    req=urllib.request.Request(BASE+path,headers={"User-Agent":"SprintBoard-CI-Smoke/1.0"})
    with urllib.request.urlopen(req,timeout=25) as r:
        return r.status,r.read(2000000).decode("utf-8",errors="replace"),r.headers
def main():
    for attempt in range(8):
        try:
            status,html,headers=fetch("/")
            assert status==200
            break
        except Exception as exc:
            print(f"Attempt {attempt+1}: {exc}")
            if attempt==7: raise
            time.sleep(7)
    assert "SprintBoard" in html
    scripts=re.findall(r'<script[^>]+src="([^"]+)"',html)
    assert scripts, "No bundled JavaScript script in static HTML"
    asset=scripts[0]
    asset_status,js,_=fetch(asset)
    assert asset_status==200
    assert "public-demo" in js or "Interactive portfolio demo" in js, "Expected demo-mode browser bundle"
    assert "sprintboard_public_demo_tasks_v1" in js, "Expected browser-local data store"
    assert "Interactive portfolio demo" in js, "Expected visible no-backend disclosure"
    assert "Local browser demo" in js
    print("SPRINTBOARD_SMOKE="+json.dumps({"result":"passed","homepage_status":status,"bundle_status":asset_status,"demo_mode":True,"local_only_storage":True,"url":BASE}))
if __name__=="__main__":main()
