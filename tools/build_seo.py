#!/usr/bin/env python3
"""도시별 검색용 페이지(city/*.html)와 sitemap.xml을 만든다.
페이지는 열릴 때 clinics.json·travel.json을 다시 읽어 최신 가격으로 바꿔 그리므로,
이 스크립트는 도시 목록이 바뀔 때만 다시 돌리면 된다.  사용: python3 tools/build_seo.py
"""
import json, html, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://usingus1.github.io/jarotrip/"
CITIES = [  # (도시, slug, 항공 도착지 이름(travel.json 노선), 공항 설명)
    ("도쿄", "tokyo", "도쿄", "나리타·하네다 공항"),
    ("후쿠오카", "fukuoka", "후쿠오카", "후쿠오카 공항(시내까지 지하철 5분)"),
    ("오사카", "osaka", "오사카", "간사이 국제공항"),
    ("나고야", "nagoya", "나고야", "주부 국제공항"),
    ("삿포로", "sapporo", "삿포로", "신치토세 공항"),
    ("히로시마", "hiroshima", "히로시마", "히로시마 공항"),
    ("교토", "kyoto", "오사카", "간사이 국제공항(교토까지 특급 약 75분)"),
    ("가고시마", "kagoshima", "가고시마", "가고시마 공항"),
]
DOSES = ["2.5", "5", "7.5", "10", "12.5", "15"]

C = json.load(open(os.path.join(ROOT, "clinics.json")))
T = json.load(open(os.path.join(ROOT, "travel.json")))
H = C["header"]
ix = {h: i for i, h in enumerate(H)}
e = lambda s: html.escape(str(s if s is not None else ""))
fmt = lambda n: f"{int(n):,}"
FX = (T.get("fx") or {}).get("jpy100krw")


def clinic_rows(city):
    rows = [r for r in C["rows"] if r[ix["도시"]] == city]
    rows.sort(key=lambda r: (r[ix["1개월 2.5mg"]] is None, r[ix["1개월 2.5mg"]] or 0))
    return rows


def table(rows):
    out = []
    for r in rows:
        p = r[ix["1개월 2.5mg"]]
        won = f" <small>≈{round(p*FX/100/10000,1)}만원</small>" if p and FX else ""
        prices = " · ".join(f"{d}mg ¥{fmt(r[ix['1개월 '+d+'mg']])}" for d in DOSES if r[ix["1개월 " + d + "mg"]])
        url = r[ix["공식 URL"]]
        out.append(f"""<article class="c"><h3>{e(r[ix['병원명']])}</h3>
<p class="big">2.5mg 1개월 {('¥'+fmt(p)+won) if p else '가격 확인 필요'}</p>
<p>{e(prices) or '용량별 가격 확인 필요'}</p>
<ul><li>한국어: {e(r[ix['한국어 지원']]) or '–'}</li><li>관광객 처방: {e(r[ix['관광객 처방']]) or '–'}</li><li>예약: {e(r[ix['예약 상황']]) or '–'}</li><li>위치: {e(r[ix['주소']]) or '–'}</li></ul>
{f'<a href="{e(url)}" rel="nofollow noopener" target="_blank">병원 공식 사이트</a>' if url else ''}</article>""")
    return "\n".join(out)


def fares(dest):
    rs = [r for r in T["rows"] if str(r[1]).endswith("→" + dest) and r[3]]
    rs.sort(key=lambda r: r[3])
    if not rs:
        return "<p>운임 수집 중이에요.</p>"
    return "<ul>" + "".join(f"<li>{e(r[1])} {e(r[2])} 편도 ₩{fmt(r[3])}~ ({e(r[5])})</li>" for r in rs[:4]) + "</ul>"


PAGE = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{city} 마운자로 병원 가격 비교 (한국어 상담) · 항공권까지 | 자로트립</title>
<meta name="description" content="{city} 마운자로 처방 병원 {n}곳의 2.5mg~15mg 용량별 가격을 원화로 비교하고, 한국→{city} 항공권 최저가와 숙소까지 한 번에. 스시자로 원정 준비, 매일 자동 갱신.">
<link rel="canonical" href="{base}city/{slug}.html">
<meta property="og:type" content="website"><meta property="og:site_name" content="자로트립">
<meta property="og:title" content="{city} 마운자로 병원 가격 비교 | 자로트립">
<meta property="og:description" content="{city} 한국어 상담 병원 {n}곳 용량별 가격 + 항공권 최저가, 매일 자동 갱신">
<meta property="og:url" content="{base}city/{slug}.html"><meta property="og:image" content="{base}icons/icon-512.png">
<link rel="icon" type="image/png" sizes="32x32" href="../icons/favicon-32.png">
<script type="application/ld+json">{ld}</script>
<style>
:root{{color-scheme:light dark;--ink:light-dark(#111,#f2f2f2);--mute:light-dark(#666,#9a9a9a);--line:light-dark(#e3e3e3,#2a2a2a);--red:#e4002b}}
body{{margin:0;word-break:keep-all;font:16px/1.6 system-ui,-apple-system,"Noto Sans KR",sans-serif;color:var(--ink);background:light-dark(#fff,#0e0e0e)}}
main{{max-width:760px;margin:0 auto;padding:16px 18px 60px}}
header a{{font-weight:800;color:var(--ink);text-decoration:none;font-size:20px}}
h1{{font-size:28px;line-height:1.25;margin:18px 0 8px;border-top:4px solid var(--ink);padding-top:14px}}
h2{{font-size:20px;margin:28px 0 8px;border-bottom:3px solid var(--ink);padding-bottom:4px}}
h3{{margin:0 0 4px;font-size:17px}} .c{{border-bottom:1px solid var(--line);padding:14px 0}}
.big{{font-size:19px;font-weight:800;margin:0}} .c p,.c ul{{margin:4px 0}} .c ul{{padding-left:18px;color:var(--mute);font-size:14px}}
.cta{{display:block;background:var(--ink);color:light-dark(#fff,#111);text-align:center;padding:14px;font-weight:800;text-decoration:none;margin:18px 0}}
.mute,small{{color:var(--mute)}} a{{color:inherit}} .note{{background:light-dark(#f4f4f4,#1a1a1a);padding:12px 14px;font-size:14px}}
nav.cities a{{display:inline-block;margin:0 10px 6px 0}}
</style></head><body><main>
<header><a href="../">자로트립</a></header>
<h1>{city} 마운자로 병원 가격 비교</h1>
<p>{city}에서 한국어로 상담되는 마운자로 처방 병원 <b id="cnt">{n}곳</b>의 용량별 가격(1개월 4펜, 약값+진찰료)을 엔화와 원화로 모았어요. 가격은 매일 아침 자동으로 다시 확인해요. <span class="mute" id="upd">기준일 {upd}</span></p>
<a class="cta" href="../?city={city_q}#plan">{city} 병원 + 항공 + 숙소 한 번에 짜기 →</a>
<h2>{city} 병원별 가격</h2>
<div id="list">{table}</div>
<h2>한국 → {city} 가는 길</h2>
<p>도착 공항: {airport}</p>
<div id="fares">{fares}</div>
<p><a href="../#travel">날짜로 항공권·배편 최저가 찾기 →</a></p>
<h2>가져올 때 알아둘 점</h2>
<div class="note"><ul>
<li>2026년 11월 12일부터 해외에서 정상 처방·구입한 의약품은 <b>본인 치료용</b>에 한해 휴대 반입할 수 있고, 마운자로 펜은 3개월 투여량(최대 12개)까지예요. 처방 관련 서류를 챙기세요.</li>
<li>반입한 약을 다른 사람에게 팔거나 넘기는 것, 대신 사다 주는 것은 약사법 위반이 될 수 있어요.</li>
<li>마운자로는 전문의약품이에요. 처방 여부와 용량은 진찰한 의사가 정하고, 냉장 보관이 필요해요.</li>
<li>가격·예약 상황은 수시로 바뀌니 예약 전에 병원에 직접 확인하세요.</li></ul></div>
<h2>다른 도시</h2>
<nav class="cities">{others}</nav>
<p class="mute"><a href="../#about">자로트립 소개</a> · <a href="../#clinics">전체 병원 목록</a></p>
</main>
<script>
(async()=>{{try{{
const CITY={city_js},DOSES={doses};
const [c,t]=await Promise.all([fetch('../clinics.json',{{cache:'no-store'}}).then(r=>r.json()),fetch('../travel.json',{{cache:'no-store'}}).then(r=>r.json())]);
const H=c.header,I=k=>H.indexOf(k),esc=s=>String(s??'').replace(/[&<>"]/g,m=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[m]),f=n=>Number(n).toLocaleString('ko-KR');
const fx=t.fx&&t.fx.jpy100krw;
const rows=c.rows.filter(r=>r[I('도시')]===CITY).sort((a,b)=>(a[I('1개월 2.5mg')]==null)-(b[I('1개월 2.5mg')]==null)||(a[I('1개월 2.5mg')]||0)-(b[I('1개월 2.5mg')]||0));
if(!rows.length)return;
document.getElementById('list').innerHTML=rows.map(r=>{{const p=r[I('1개월 2.5mg')],u=r[I('공식 URL')];
const ps=DOSES.filter(d=>r[I('1개월 '+d+'mg')]).map(d=>d+'mg ¥'+f(r[I('1개월 '+d+'mg')])).join(' · ');
return `<article class="c"><h3>${{esc(r[I('병원명')])}}</h3><p class="big">2.5mg 1개월 ${{p?'¥'+f(p)+(fx?` <small>≈${{(p*fx/100/10000).toFixed(1)}}만원</small>`:''):'가격 확인 필요'}}</p><p>${{esc(ps)||'용량별 가격 확인 필요'}}</p><ul><li>한국어: ${{esc(r[I('한국어 지원')])||'–'}}</li><li>관광객 처방: ${{esc(r[I('관광객 처방')])||'–'}}</li><li>예약: ${{esc(r[I('예약 상황')])||'–'}}</li><li>위치: ${{esc(r[I('주소')])||'–'}}</li></ul>${{u?`<a href="${{esc(u)}}" rel="nofollow noopener" target="_blank">병원 공식 사이트</a>`:''}}</article>`}}).join('');
document.getElementById('cnt').textContent=rows.length+'곳';
document.getElementById('upd').textContent='기준일 '+c.updatedAt;
}}catch(e){{}}}})();
</script>
<script>document.addEventListener('click',e=>{{const a=e.target.closest('a');if(!a||!window.goatcounter||!window.goatcounter.count)return;const h=a.getAttribute('href')||'';const p=a.classList.contains('cta')?'city/cta':/^http/.test(h)?'out/site:'+new URL(a.href).hostname:null;if(p)window.goatcounter.count({{path:p,title:p,event:true}})}},true);</script>
<script data-goatcounter="https://jarotrip.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body></html>
"""

os.makedirs(os.path.join(ROOT, "city"), exist_ok=True)
built = []
for city, slug, dest, airport in CITIES:
    rows = clinic_rows(city)
    if not rows:
        continue
    built.append((city, slug))
for city, slug, dest, airport in CITIES:
    rows = clinic_rows(city)
    if not rows:
        continue
    others = " ".join(f'<a href="{s}.html">{e(c)} 마운자로</a>' for c, s in built if s != slug)
    ld = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "자로트립", "item": BASE},
        {"@type": "ListItem", "position": 2, "name": f"{city} 마운자로 병원 가격", "item": f"{BASE}city/{slug}.html"}]}, ensure_ascii=False)
    page = PAGE.format(city=e(city), slug=slug, base=BASE, n=len(rows), upd=e(C.get("updatedAt")), table=table(rows),
                       fares=fares(dest), airport=e(airport), others=others, ld=ld,
                       city_q=html.escape(city), city_js=json.dumps(city, ensure_ascii=False), doses=json.dumps(DOSES))
    open(os.path.join(ROOT, "city", slug + ".html"), "w").write(page)

today = datetime.date.today().isoformat()
urls = [BASE] + [f"{BASE}city/{s}.html" for _, s in built]
open(os.path.join(ROOT, "sitemap.xml"), "w").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
print("built", [s for _, s in built])
