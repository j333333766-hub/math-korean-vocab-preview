# -*- coding: utf-8 -*-
"""홈 화면(60차시 어휘 위계도) 만들기.

syllabus.json  차시별 새 어휘·함께 보는 낱말·이미 배운 어휘(처음 나온 곳)
lessons.json   title, lead, built(차시명 → 시안 폴더)
"""
import html, io, json, os

CSS = """
body{font-family:"Pretendard","Noto Sans KR","Malgun Gothic",sans-serif;background:#eef5fb;color:#1d2433;margin:0;padding:28px 16px 80px;scroll-behavior:smooth}
html{scroll-behavior:smooth}
main{max-width:1180px;margin:0 auto}h1{font-size:25px;margin:0 0 6px}p.lead{line-height:1.7;color:#4b5563;margin:0 0 10px;font-size:14.5px}
.legend{display:flex;flex-wrap:wrap;gap:8px 16px;background:#fff;border:1.5px solid #1b1b1b;border-radius:12px;padding:10px 14px;font-size:13.5px;margin:10px 0 6px;align-items:center}
.stat{display:inline-block;background:#fff;border:1.5px solid #1b1b1b;border-radius:99px;padding:3px 12px;font-weight:700;margin:6px 6px 0 0;font-size:13.5px}
h2{font-size:17px;margin:26px 0 8px;padding:5px 12px;background:#2a1a00;color:#fff;border-radius:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px}
.card{break-inside:avoid;background:#fff;border:2px solid #1b1b1b;border-radius:14px;padding:11px 13px;position:relative;scroll-margin-top:16px}
.card:target{outline:5px solid #f6b21a;background:#fffbe8}
.no{display:inline-block;background:#2f6fe4;color:#fff;border-radius:8px;padding:1px 9px;font-weight:800;font-size:14px}
.card h3{display:inline;font-size:16.5px;margin:0 0 0 6px}.sub{font-size:12px;color:#6b7280;margin:3px 0 7px}
.row{display:flex;gap:6px;align-items:flex-start;margin-top:5px;font-size:13px}.lab{flex:0 0 88px;font-weight:800;font-size:12px;padding-top:3px}
.lab.b{color:#1e4fb3}.lab.n{color:#0c7d66}.lab.r{color:#6b7280}.lab.a{color:#8a5a00}
.chips{display:flex;flex-wrap:wrap;gap:4px}
.w{border-radius:99px;padding:2px 9px;font-weight:800;border:1.5px solid #19b394;background:#e3f8f1;color:#0a5c4b;font-size:13.5px}
.x{border-radius:99px;padding:2px 9px;border:1.5px dashed #c9a24a;background:#fff8e1;color:#6b4b00;font-size:12.5px;font-weight:700}
a.r{border-radius:99px;padding:2px 9px;border:1.5px solid #2f6fe4;background:#eef4ff;color:#1e4fb3;text-decoration:none;font-size:12.5px;font-weight:700}
a.r:hover{background:#2f6fe4;color:#fff}a.r small,.e small,.w small{opacity:.75;font-weight:600}
.e{border-radius:99px;padding:2px 9px;border:1.5px solid #c3c9d4;background:#f4f6f9;color:#4b5563;font-size:12.5px;font-weight:700}
.stat.map{background:#2f6fe4;color:#fff;text-decoration:none;font-size:15px;padding:6px 16px}.none{color:#b45309;font-weight:700;font-size:12.5px}
.go{position:absolute;right:11px;top:10px;background:#19b394;color:#fff;border-radius:99px;padding:2px 11px;font-size:12px;font-weight:800;text-decoration:none}
.go.old{background:#9aa3b2}.todo{position:absolute;right:11px;top:10px;color:#9aa3b2;font-size:12px;font-weight:700}
.tp{font-size:11.5px;color:#6b7280;margin-left:6px}
footer{margin-top:30px;font-size:13px;color:#6b7280;line-height:1.7}
"""

def build_home(root):
    syl = json.load(io.open(os.path.join(root, 'syllabus.json'), encoding='utf-8'))
    cfg = json.load(io.open(os.path.join(root, 'lessons.json'), encoding='utf-8'))
    built = cfg.get('built', {}); ess = set(syl['ess']); L = syl['lessons']; e = html.escape
    star = lambda x: e(x) + ('★' if x in ess else '')
    out = []; prev = None; done = 0
    for d in L:
        unit = d['unit'] if d['grade'] == '공통' else d['grade'] + ' ' + d['unit']
        if unit != prev:
            if prev is not None: out.append('</div>')
            out.append(f'<h2>{e(unit)}</h2><div class="grid">'); prev = unit
        b = built.get(d['name']); link = ''
        if b and os.path.exists(os.path.join(root, b['folder'], 'index.html')):
            done += 1; link = f'<a class="go{" old" if b.get("old") else ""}" href="{b["folder"]}/">{"옛 형식 시안" if b.get("old") else "시안 열기"} ▶</a>'
        else: link = '<span class="todo">준비 중</span>'
        en = d.get('elemNew', {})
        new = ''.join(f'<span class="w">{star(x)}{" <small>" + e(en[x]) + "</small>" if x in en else ""}</span>' for x in d['new']) or '<span class="none">새 어휘 없음 (이미 배운 말만 확인)</span>'
        aux = ''.join(f'<span class="x">{e(x)}</span>' for x in d['aux'])
        rev = ''; el = ''
        for x, s in d['review']:
            if isinstance(s, int): rev += f'<a class="r" href="#L{s}" title="{s}차시 {e(L[s - 1]["name"])}">{star(x)} <small>← {s}차시</small></a>'
            else: el += f'<span class="e">{star(x)} <small>{e(s)}</small></span>'
        h = f'<div class="card" id="L{d["no"]}"><span class="no">{d["no"]}</span><h3>{e(d["name"])}</h3><span class="tp">{e(d["type"])}</span>{link}'
        h += f'<div class="sub">먼저 보고 배우는 소단원: {e(d["sub"])} {e(d["std"])}</div>'
        h += f'<div class="row"><div class="lab n">{"새 표현" if d["grade"] == "공통" else "새 어휘"}</div><div class="chips">{new}</div></div>'
        if aux: h += f'<div class="row"><div class="lab a">함께 보는 말</div><div class="chips">{aux}</div></div>'
        if rev: h += f'<div class="row"><div class="lab b">앞에서 배운 말</div><div class="chips">{rev}</div></div>'
        if el: h += f'<div class="row"><div class="lab r">초등에서 배운 말</div><div class="chips">{el}</div></div>'
        out.append(h + '</div>')
    out.append('</div>')
    page = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(cfg['title'])}</title><style>{CSS}</style></head>
<body><main>
<h1>{e(cfg['title'])}</h1>
<p class="lead">{e(cfg['lead'])}</p>
<div class="legend"><b>보는 법</b>
<span><span class="w">새 어휘</span> 이 차시에서 처음 익히는 낱말 (★ 충남대 핵심어)</span>
<span><span class="w">새 어휘 <small>초5-1</small></span> 초등에서 배운 말이지만 뒤 단원에 꼭 필요해서 다시 익히는 낱말</span>
<span><span class="x">함께 보는 말</span> 새 어휘와 같이 처음 나오는 낱말</span>
<span><a class="r" href="#">앞에서 배운 말 <small>← n차시</small></a> 뜻만 확인. 모르면 그 낱말을 익히는 차시로 안내 (누르면 이동)</span>
<span><span class="e">초등에서 배운 말 <small>초5-1</small></span> 앞 차시로 보내지 않고 이 차시 안에서 배경지식으로 안내</span></div>
<a class="stat map" href="vocab-map.html">🗺 학습 어휘 지도 (마인드맵 · 위계 흐름) ▶</a><a class="stat map" href="vocab-map.html#std">📋 성취기준별 차시 ▶</a><a class="stat map" href="vocab-map.html#sec">📖 교과서 소단원별 차시 ▶</a><br>
<span class="stat">전체 {len(L)}차시</span><span class="stat">시안 {done}차시</span><span class="stat">새 어휘 {sum(len(d['new']) for d in L if d['grade'] != '공통')}개</span>
{''.join(out)}
<footer>{e(cfg.get('foot', ''))}</footer>
</main></body></html>
"""
    io.open(os.path.join(root, 'index.html'), 'w', encoding='utf-8').write(page)
    print(f'홈 화면(위계도): {len(L)}차시, 시안 {done}차시')
    # 어휘 지도(마인드맵·위계 흐름)
    data = dict(lessons=L, ess=syl['ess'], toc=syl['toc'], stds=syl['stds'], built={k: v['folder'] for k, v in built.items() if os.path.exists(os.path.join(root, v['folder'], 'index.html'))})
    t = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'map_template.html'), encoding='utf-8').read()
    io.open(os.path.join(root, 'vocab-map.html'), 'w', encoding='utf-8').write(t.replace('/*DATA*/', json.dumps(data, ensure_ascii=False).replace('</', '<\/')))
    print('어휘 지도: vocab-map.html')

if __name__ == '__main__':
    build_home(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
