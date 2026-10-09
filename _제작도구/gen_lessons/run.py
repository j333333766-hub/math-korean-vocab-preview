# -*- coding: utf-8 -*-
"""차시 원고 → 각 차시 폴더의 lesson.json 생성.

60차시 추천안(2026-10-09) 기준: 공통 1~4차시(l01_07.py의 앞 4개)와 5~6차시(k05_06.py)만 만든다.
l01_07.py의 5~7차시와 l08_15.py는 옛 목차(10-06) 원고로, prev-1006/ 시안의 출처이며 새 차시를 쓸 때 참고한다.

    python _제작도구/gen_lessons/run.py        (그다음 python _제작도구/build.py --all)

주의: 다시 실행하면 해당 차시의 lesson.json 을 덮어쓴다. lesson.json 을 직접 고친 차시는 원고에도 같은 내용을 반영한다.
"""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lib, l01_07, k05_06
ROOT = os.path.dirname(os.path.dirname(HERE))
syl = json.load(io.open(os.path.join(ROOT, 'syllabus.json'), encoding='utf-8'))
names = {d['no']: d['name'] for d in syl['lessons']}; by = {d['no']: d for d in syl['lessons']}
cfg_p = os.path.join(ROOT, 'lessons.json'); cfg = json.load(io.open(cfg_p, encoding='utf-8'))
for p in [x for x in l01_07.L if x['no'] <= 4] + k05_06.L:
    d = by[p['no']]
    # 원고와 목차(syllabus.json)가 어긋나지 않는지 확인
    assert p['new'] == d['new'] or p['no'] <= 4, (p['no'], p['new'], d['new'])
    if p['no'] > 4:
        assert set(p.get('aux', [])) == set(d['aux']), (p['no'], p.get('aux'), d['aux'])
        assert {(w, n) for w, n, _ in p.get('pre', [])} <= {(w, s) for w, s in d['review'] if isinstance(s, int)}, (p['no'], 'pre')
        assert {w for w, _ in p.get('elem', [])} <= {w for w, s in d['review'] if not isinstance(s, int)}, (p['no'], 'elem')
    L = lib.build(p, names); folder = lib.write(ROOT, L)
    cfg['built'][names[p['no']]] = {'folder': folder}
    print(p['no'], names[p['no']], '→', folder, sum(len(m['screens']) for m in L['modules']), '화면')
io.open(cfg_p, 'w', encoding='utf-8').write(json.dumps(cfg, ensure_ascii=False, indent=2))
