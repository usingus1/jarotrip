"""자로트립 현황을 터미널에 출력한다 (live.html 과 같은 숫자). 사용: python3 tools/stats.py"""
import json, urllib.request, urllib.parse, datetime as dt
from concurrent.futures import ThreadPoolExecutor
GC = "https://jarotrip.goatcounter.com/counter/"
SB = "https://imuajiqktrnhinqfrnva.supabase.co/rest/v1/rpc/live_count"
SBK = "sb_publishable_yUje1cM2a__SiwUXh0RsGA_AfCBZLPg"
PG = {"main": "첫 화면", "home": "홈", "plan": "여행 짜기", "clinics": "병원 목록", "travel": "가는 길", "board": "커뮤니티", "log": "변경 기록", "about": "안내"}
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
day = lambda back=0: (now - dt.timedelta(days=back)).date().isoformat()
num = lambda s: int("".join(c for c in str(s or "0") if c.isdigit()) or 0)
def cnt(path, s, e):
    e = (dt.date.fromisoformat(e) + dt.timedelta(days=1)).isoformat()  # GoatCounter end 는 그날을 포함하지 않는다
    url = GC + urllib.parse.quote(path, safe="") + ".json?" + urllib.parse.urlencode({"start": s, "end": e})
    try:
        with urllib.request.urlopen(url, timeout=20) as r: j = json.load(r)
        return num(j.get("count_unique")), num(j.get("count"))
    except urllib.error.HTTPError as x:
        if x.code == 404: return 0, 0
        raise
def live():
    req = urllib.request.Request(SB, data=b"{}", method="POST", headers={"apikey": SBK, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r: return json.load(r)
P = [("오늘", day(), day()), ("어제", day(1), day(1)), ("최근 7일", day(6), day()), ("최근 30일", day(29), day())]
jobs = [(p, l, s, e) for l, s, e in P for p in ("TOTAL", "out/flight-trip", "out/stay-trip")]
with ThreadPoolExecutor(8) as ex:
    lv = ex.submit(live)
    res = dict(zip([(p, l) for p, l, _, _ in jobs], ex.map(lambda j: cnt(j[0], j[2], j[3]), jobs)))
    l = lv.result()
print(f"[{now:%m/%d %H:%M} 기준]")
pages = " · ".join(f"{PG.get(k, k)} {v}" for k, v in sorted((l.get('pages') or {}).items(), key=lambda x: -x[1]))
print(f"지금 접속 중: {l.get('now', 0)}명" + (f" ({pages})" if pages else ""))
t = res[("TOTAL", "오늘")]
print(f"오늘 방문자: {t[0]:,}명 (화면 조회 {t[1]:,}회)")
print("\n구분 | 방문자 | 항공권 클릭 | 숙소 클릭 | 트립닷컴 이동 인원 | 비율")
for lab, _, _ in P:
    v = res[("TOTAL", lab)][0]; f = res[("out/flight-trip", lab)]; h = res[("out/stay-trip", lab)]
    people = f[0] + h[0]
    print(f"{lab} | {v:,} | {f[1]} | {h[1]} | {people} | {people / v * 100:.1f}%" if v else f"{lab} | 0 | {f[1]} | {h[1]} | {people} | –")
