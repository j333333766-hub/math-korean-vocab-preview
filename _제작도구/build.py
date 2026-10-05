# -*- coding: utf-8 -*-
"""차시 원고(lesson.json) → 웹콘텐츠 시안(index.html) + 제작팀 전달 자료

사용법:  python build.py "..\\평행선의 동위각과 엇각"
만드는 것:
  index.html                         브라우저로 여는 시안 (파일 하나)
  제작용/영상 대본.md                 영상 자리의 컷별 대사·자막·내레이션·연출
  제작용/화면 목록.md                 모듈·화면별 유형, 지시문, 정답, 메모
  제작용/모듈 데이터(원본 형식)/sco_0N/mega_quiz_data.json   원본 사이트의 데이터 형식에 맞춘 파일
"""
import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
plain = lambda t: re.sub(r'\*\*', '', str(t or '')).replace('\n', ' ')

def answer_text(sc):
    t = sc['type']
    if sc.get('answerText'): return sc['answerText']
    if t in ('drag_drop',): return ', '.join(sc['options'][i] for i in sc['answer'])
    if t == 'choice': return ', '.join(plain(sc['options'][i]) for i in sc['answer'])
    if t == 'OX': return sc['answer']
    if t == 'linetoline': return ' / '.join(f"{plain(l)} → {plain(sc['right'][a])}" for l, a in zip(sc['left'], sc['answer']))
    if t == 'input': return ' 또는 '.join(sc['answer'])
    if t in ('listen',): return sc['text']
    if t == 'step_recorde': return plain(sc['sentence'])
    return ''

def to_origin(sc):
    """원본 mega_quiz_data.json의 항목 형식으로 옮긴다(그림 이름은 제작 때 정한다)."""
    t = sc['type']
    base = {"data_type": t, "data_jung_dap": "", "data_audsrc": "", "data_is_auto_play": "true", "data_trynum": "", "data_point": "",
            "data_load_stroge_name": "", "data_guide": "false", "data_guide_points": "", "question": plain(sc.get('q', '')),
            "sub_question": "", "selection": "", "img": "", "object": [], "basket_name": "", "drop": "", "character": "false", "commentary": ""}
    if t == 'motion': base['object'] = [{"txt": w} for w in sc['words']]; base['character'] = 'true'
    elif t == 'card_flip':
        base['data_jung_dap'] = sc.get('answerText', '')
        back = sc['back']
        base['object'] = [{"txt": plain(back.get('caption') or back.get('text')) if not back.get('fig') else "card(그림)"}]
        base['custom'] = 'i_t' if sc['front'].get('fig') else ('t_t' if not back.get('fig') else '')
    elif t == 'listen': base.update(data_jung_dap=sc['text'], object=[{"txt": sc['text']}], data_guide='true', double='true')
    elif t == 'drag_drop':
        base['data_jung_dap'] = ','.join(str(i + 1) for i in sc['answer']); base['object'] = [{"txt": o} for o in sc['options']]
        base['drop'] = re.sub(r'\{\d\}', ',drop,', plain(sc['sentence'])).strip(','); base['data_guide'] = 'true'
    elif t == 'choice':
        base['data_jung_dap'] = ','.join(str(i + 1) for i in sc['answer']); base['object'] = [{"txt": plain(o)} for o in sc['options']]; base['data_guide'] = 'true'
    elif t == 'OX': base['data_jung_dap'] = '1' if sc['answer'] == 'O' else '2'; base['sub_question'] = plain(sc['statement'])
    elif t == 'linetoline':
        base['data_jung_dap'] = ','.join(f"{i + 1}@{'abcdefg'[a]}" for i, a in enumerate(sc['answer']))
        base['object'] = [{"txt": plain(x)} for x in sc['left'] + sc['right']]; base['custom'] = 'horizontal'
    elif t == 'input': base['data_jung_dap'] = sc['answer'][0]; base['selection'] = 'input_txt'; base['sub_question'] = plain(sc.get('sentence', ''))
    elif t == 'step_recorde': base['data_jung_dap'] = plain(sc['sentence']); base['custom'] = 'STT'
    elif t == 'ocr': base['data_jung_dap'] = sc['word']; base['object'] = [{"txt": "<type=blank>"}]
    return base

def main(folder):
    folder = os.path.abspath(folder)
    L = json.load(io.open(os.path.join(folder, 'lesson.json'), encoding='utf-8'))
    n_screens = 0
    for m in L['modules']:
        for sc in m['screens']:
            n_screens += 1
            a = answer_text(sc)
            if a and not sc.get('answerText'): sc['answerText'] = a
    tpl = io.open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
    html = tpl.replace('__TITLE__', L['title']).replace('/*__LESSON__*/null', json.dumps(L, ensure_ascii=False))
    io.open(os.path.join(folder, 'index.html'), 'w', encoding='utf-8').write(html)

    out = os.path.join(folder, '제작용'); os.makedirs(out, exist_ok=True)
    # 영상 대본
    s = [f"# 영상 대본 — {L['title']}", '', f"{L['grade']} · {L['standard']}", '',
         f"등장인물: {', '.join(L['cast'])} (임시 이름과 임시 그림. 실제 캐릭터로 바꾼다.)", '',
         '낱말 앞뒤의 `**`는 화면에서 색으로 강조할 말이다. 그림은 시안(index.html)의 같은 컷을 본다.', '']
    nv = 0
    for mi, m in enumerate(L['modules'], 1):
        for si, sc in enumerate(m['screens'], 1):
            if sc['type'] != 'vod': continue
            nv += 1
            s += [f"## 영상 {nv}. {sc.get('title', '')}", '', f"위치: {mi}. {m['name']} · 화면 {si}", '']
            if sc.get('memo'): s += [f"메모: {sc['memo']}", '']
            s += ['| 컷 | 화면 | 대사 | 자막 | 내레이션 | 연출 |', '|---:|---|---|---|---|---|']
            for ci, c in enumerate(sc['cuts'], 1):
                scr = '제목 화면' if c.get('title') else ('그림(시안 참조)' if c.get('fig') is not None else '')
                talk = '<br>'.join(f"{L['cast'][b['who']]}: {b['text']}" for b in c.get('bubbles', []))
                s.append(f"| {ci} | {scr} | {talk} | {c.get('caption', '')} | {c.get('narr', '')} | {c.get('dir', '')} |")
            s.append('')
    io.open(os.path.join(out, '영상 대본.md'), 'w', encoding='utf-8').write('\n'.join(s))
    # 화면 목록
    s = [f"# 화면 목록 — {L['title']}", '', f"모듈 {len(L['modules'])}개, 화면 {n_screens}개, 영상 {nv}개", '',
         '| 모듈 | 화면 | 원본 유형 | 지시문 | 정답 | 메모 |', '|---|---:|---|---|---|---|']
    for mi, m in enumerate(L['modules'], 1):
        for si, sc in enumerate(m['screens'], 1):
            q = plain(sc.get('q', '')) or (sc.get('title', '') if sc['type'] == 'vod' else '')
            s.append(f"| {mi}. {m['name']} | {si} | {sc['type']} | {q} | {plain(sc.get('answerText', ''))} | {sc.get('memo', '')} |")
    io.open(os.path.join(out, '화면 목록.md'), 'w', encoding='utf-8').write('\n'.join(s) + '\n')
    # 원본 형식 데이터
    for mi, m in enumerate(L['modules'], 1):
        d = os.path.join(out, '모듈 데이터(원본 형식)', f'sco_{mi:02d}'); os.makedirs(d, exist_ok=True)
        quiz = [to_origin(sc) for sc in m['screens']]
        if mi == 1: quiz[0]['intro'] = 'true'
        if mi == len(L['modules']): quiz[-1]['outro'] = 'true'
        io.open(os.path.join(d, 'mega_quiz_data.json'), 'w', encoding='utf-8').write(json.dumps({"quiz": quiz}, ensure_ascii=False, indent=4))
    print(f"{L['title']}: 모듈 {len(L['modules'])}, 화면 {n_screens}, 영상 {nv}")
    print([ (m['name'], len(m['screens'])) for m in L['modules'] ])

if __name__ == '__main__':
    main(sys.argv[1])
