# -*- coding: utf-8 -*-
"""차시 원고(짧은 명세) → lesson.json 을 만드는 틀.

모든 차시가 같은 흐름(도입–어휘 제시–정의–용례–연습–마무리)과 같은 화면 순서를 갖게 한다.
만든 뒤에는 각 차시 폴더의 lesson.json 이 기준이다(직접 고쳐도 된다. 다시 생성하면 덮어쓴다).
"""
import io, json, os, re

LANGS = ['English', '中文', '日本語', 'Tiếng Việt', 'Русский', 'العربية']
# 60차시 추천안(2026-10-09) 기준. 옛 목차(10-06)의 5~15차시 시안은 prev-1006/ 폴더로 옮겼다.
FOLD = {1: 'L01-common-01', 2: 'L02-common-02', 3: 'L03-common-03', 4: 'L04-common-04', 5: 'L05-9su01-01', 6: 'L06-9su01-01'}

def eq(*lines, size=None):
    d = {'kind': 'eq', 'lines': list(lines)}
    if size: d['size'] = size
    return d
def word(*rows): return {'kind': 'word', 'rows': [{'parts': list(r[:-1]), 'result': r[-1]} for r in rows]}   # 낱말 짜임: word(('소수', '인수', '소인수'), …)
def num(a, b, **k): return dict(kind='num', min=a, max=b, **k)
def pw(base, exp, labels=True, eqs=None):
    d = {'kind': 'power', 'base': base, 'exp': exp, 'labels': labels}
    if eqs: d['eq'] = eqs
    return d
def tree(n, eqs=None): return {'kind': 'tree', 'n': n, 'eq': eqs} if eqs else {'kind': 'tree', 'n': n}
plain = lambda t: re.sub(r'[*‘’]', '', t)
def cut(cap=None, fig=None, text=None, dir='', b=None, narr=None):
    c = {}
    if fig is not None: c['fig'] = fig
    if text is not None: c['text'] = text
    if cap: c['caption'] = cap; c['narr'] = narr or plain(cap)
    if dir: c['dir'] = dir
    if b: c['bubbles'] = [{'who': w, 'text': t} for w, t in b]
    return c
def ch(q, options, answer, fig=None, cols=None, hint=None, memo=None):
    d = {'type': 'choice', 'q': q, 'options': options, 'answer': answer if isinstance(answer, list) else [answer]}
    if fig: d['fig'] = fig
    if cols: d['cols'] = cols
    if hint: d['hint'] = hint
    if memo: d['memo'] = memo
    return d
def ox(statement, answer, fig=None, why=None):
    d = {'type': 'OX', 'q': '맞으면 O, 틀리면 X를 선택해 보세요.', 'statement': statement, 'answer': answer}
    if fig: d['fig'] = fig
    if why: d['why'] = why
    return d
def l2l(left, right, answer, q='알맞은 것끼리 연결해 보세요.'): return {'type': 'linetoline', 'q': q, 'left': left, 'right': right, 'answer': answer}
def card(front, back_text=None, cap=None, fig=None):
    back = {'fig': fig} if fig else {'text': back_text}
    if cap: back['caption'] = cap
    return (front, back)

def build(p, names):
    no = p['no']; common = no <= 4
    new, aux, pre, elem, perf = p['new'], p.get('aux', []), p.get('pre', []), p.get('elem', []), p.get('perf', [])
    kind_new = '수행 도구어' if common else '핵심 개념어'
    M = []
    # ── 도입
    s = []
    cols = []
    if pre or elem:
        cols.append({'label': '미리 확인할 말' if pre else '이미 아는 말', 'items': [{'t': w, 's': f'{n}차시에서 배운 말'} for w, n, _ in pre] + [{'t': w, 's': '초등학교에서 배운 말'} for w, _ in elem[:max(1, 3 - len(pre))]]})
    else:
        cols.append({'label': '수학 문제의 끝말', 'items': [{'t': '~하시오', 's': '무엇을 하라는 말일까요?'}]})
    cols.append({'label': '오늘 새로 익힐 말', 'hl': True, 'items': new})
    school = {'label': '학교 수업', 'items': [{'t': p['school'], 's': p['school_s']}]}
    if p.get('school_goal'): school['desc'] = p['school_goal']   # 이 단원에서 무엇을 왜 배우는지 한두 문장
    cols.append(school)
    s.append({'type': 'curation', 'q': p['intro_q'], 'cols': cols, 'note': p['intro_note'],
              'memo': '도입(큐레이션). 이 콘텐츠는 학교에서 해당 단원을 배우기 전에 보는 것임을 먼저 알린다. 이미 아는 말 → 새로 익힐 말 → 학교 수업의 흐름을 한 화면에 보여 준다. 학교 수업 칸에는 그 단원에서 무엇을 왜 배우는지 한두 문장으로 알려, 낱말과 학습 목표를 함께 확인하게 한다.'})
    for c in p.get('checks', []):
        c.setdefault('memo', '미리 확인할 말의 뜻 확인. 새로 가르치지 않는다. 틀리면 그 낱말을 익히는 차시로 안내한다.'); s.append(c)
    if pre:
        s.append({'type': 'checklist', 'q': '이 말을 알고 있나요? 잘 모르면 먼저 배우고 와요.',
                  'items': [{'t': w, 'ex': ex, 'go': f'→ {n}차시 ‘{names[n]}’ 먼저 보고 오기', 'href': f'../{FOLD[n]}/'} for w, n, ex in pre],
                  'memo': '미리 확인할 말(이 차시에 필요하지만 앞 차시에서 이미 익힌 말) 확인의 마무리. 학습 어휘로 다시 가르치지 않는다. ‘잘 몰라요’를 누르면 그 낱말을 익히는 차시로 가는 연결이 나온다. 초등에서 배운 말은 여기에 넣지 않고 다음 화면에서 바로 안내한다.'})
    for w, back in p.get('elem_cards', []):
        s.append({'type': 'card_flip', 'q': '초등학교에서 배운 말이에요. 한국어로 확인해 보세요.', 'front': {'text': w}, 'back': back, 'answerText': w,
                  'memo': '초등에서 배운 말은 앞 차시로 보내지 않는다. 학생이 이미 아는 개념을 식이나 그림으로 보여 주고 한국어 낱말과 잇는다. 번역 기능으로 모국어 낱말도 함께 볼 수 있다.'})
    if common:
        s.append({'type': 'vod', 'title': '수업 장면: 문제의 끝말', 'cuts': p['scene'], 'memo': '문제의 수학 내용은 알지만 끝말(지시어)을 몰라 멈추는 장면에서 시작한다.'})
    M.append({'name': '도입', 'screens': s})
    # ── 어휘 제시
    s = []
    cols = [{'label': '오늘 새로 익힐 말', 'hl': True, 'items': new}]
    if aux: cols.append({'label': '함께 보는 말', 'items': [{'t': w} for w in aux]})
    known = [{'t': w, 's': f'{n}차시'} for w, n, _ in pre] + [{'t': w, 's': '초등'} for w, _ in elem]
    if known and not (aux and perf): cols.append({'label': '이미 아는 말', 'items': known[:4]})
    if perf: cols.append({'label': '문제에서 쓰는 말', 'items': [{'t': v, 's': f'{n}차시' if n else ''} for v, n in perf]})
    s.append({'type': 'curation', 'noArrow': True, 'q': '오늘 만날 낱말이에요.', 'cols': cols, 'note': p.get('present_note', '이미 아는 말을 가지고 새 낱말의 뜻을 알아봐요.'),
              'memo': f'새 어휘({kind_new}), 함께 보는 말·이미 아는 말(보조·배경 개념어), 문제에서 쓰는 말(수행 도구어)을 나누어 보여 준다.'})
    if not common:
        s.append({'type': 'vod', 'title': '수업 장면: 교과서에서 만난 낱말', 'cuts': p['scene'], 'memo': '새 낱말을 수업 장면 속에서 처음 보여 준다. 이미 아는 말과 이미 아는 개념에서 출발한다는 점을 대사로 짚는다.'})
    s.append({'type': 'listen', 'q': '다음 낱말을 듣고 2번 따라 읽어 보세요.', 'items': [{'text': t, 'say': sy} if sy else {'text': t} for t, sy in p['listen']]})
    M.append({'name': '어휘 제시', 'screens': s})
    # ── 정의
    s = [{'type': 'vod', 'title': p['define_title'], 'cuts': p['define'], 'memo': '개념을 새로 가르치지 않는다. 이미 아는 말과 아는 개념을 차례로 써서 새 낱말에 이른다. 낱말에 들어 있는 한자말의 뜻(예: 최대 = 가장 큰)을 풀어 주어 한국어 낱말로 받아들이게 한다.'}]
    for front, back in p['cards']:
        s.append({'type': 'card_flip', 'q': '낱말을 클릭해 뜻을 확인해 보세요.', 'front': {'text': front}, 'back': back, 'answerText': front})
    s.append({'type': 'lang_match', 'q': '내가 아는 말과 연결해 보세요.', 'words': p['lang_words'], 'items': [{'lang': l, 'terms': t} for l, t in zip(LANGS, p['lang'])],
              'note': '나라마다 부르는 말은 달라도 뜻은 같아요.',
              'memo': '이미 아는 개념과 한국어 낱말을 대응시키는 화면. ★ 각 언어의 용어는 원어민 검수를 받아야 한다. 다른 언어는 검수자가 채운다. 원본 플랫폼에서는 학습자가 고른 언어 한 줄만 보여 주는 방식이 알맞다.'})
    M.append({'name': '정의', 'screens': s})
    # ── 용례
    s = [{'type': 'vod', 'title': '교과서 문장 속의 낱말', 'cuts': [cut(c, text=t) for t, c in p['usage']], 'memo': '용례 단계. 학교 수업에서 실제로 만나는 교과서 문장을 보여 주고, 함께 쓰이는 말(공기관계어)과 수행 도구어를 자막으로 짚는다.'},
         {'type': 'listen', 'q': '다음 문장을 듣고 2번 따라 읽어 보세요.', 'items': [{'text': t, 'say': sy} if sy else {'text': t} for t, sy in p['says']]},
         dict({'type': 'drag_drop', 'q': '보기에서 알맞은 낱말을 골라 빈칸에 넣어 보세요.'}, **p['drag'])]
    i = p['instr']; i['q'] = '문제에서 무엇을 하라고 하나요?'; i['memo'] = '지시문을 이해하는지 확인하는 문항. 답을 구하게 하지 않는다.'; s.append(i)
    M.append({'name': '용례', 'screens': s})
    # ── 연습
    s = list(p['practice'])
    s[0].setdefault('memo', '새 낱말의 뜻을 아는지 확인하는 문항. 계산 연습이 아니므로 수는 작게 둔다.')
    sp = {'type': 'step_recorde', 'q': '다음을 듣고 따라 말해 보세요.', 'sentence': p['speak'][0], 'memo': '원본의 step_recorde(듣고 따라 말하기, 녹음) 기능을 연결한다.'}
    if p['speak'][1]: sp['say'] = p['speak'][1]
    if len(p['speak']) > 2: sp['fig'] = p['speak'][2]
    s.append(sp)
    M.append({'name': '연습', 'screens': s})
    # ── 마무리
    s = [{'type': 'curation', 'noArrow': True, 'q': '오늘 새로 익힌 낱말을 정리해요.', 'cols': [{'label': lb, 'hl': True, 'items': [{'t': t, 's': sub}]} for lb, t, sub in p['summary']], 'memo': '새 어휘를 한 화면에서 다시 본다.'},
         {'type': 'curation', 'q': '이제 학교 수업에서 만나요.', 'cols': [{'label': '오늘 익힌 낱말', 'hl': True, 'items': new}, {'label': '학교 수업', 'items': [{'t': p['school'], 's': p['school_use']}]},
                                                               {'label': '그다음에 볼 콘텐츠', 'items': [{'t': names[no + 1], 's': f'{no + 1}차시'}]}],
          'note': p['outro_note'], 'memo': '마무리(큐레이션). 익힌 낱말이 학교 수업의 어디에서 쓰이는지, 그다음에 볼 콘텐츠가 무엇인지 안내한다.'}]
    M.append({'name': '마무리', 'screens': s})
    vocab = {f'새 어휘 = {kind_new} (이 차시에서 익힘)': [w + (' (충남대 핵심어)' if w in p.get('ess', []) else '') for w in new]}
    if aux: vocab['함께 처음 보는 말' + (' (수행 도구어)' if common else ' (보조·배경 개념어)')] = aux
    if pre: vocab['미리 확인할 말 (차시 처음에 아는지 확인 → 모르면 익힌 차시로 안내)'] = [f'{w} → {n}차시 ‘{names[n]}’' for w, n, _ in pre]
    if elem: vocab['초등에서 배운 말 (이 차시 안에서 배경지식으로 안내)'] = [f'{w} ({sem})' for w, sem in elem]
    if perf: vocab['수행 도구어 (문제에서 쓰는 말)'] = [f'{v} → {n}차시' if n else f'{v} (익히는 차시 없음)' for v, n in perf]
    if p.get('colloc'): vocab['공기관계어'] = p['colloc']
    keep = sorted({w for w in new + aux + [x[0] for x in pre] + [x[0] for x in elem] + p.get('keep', []) if len(w) >= 2 or w in new}, key=len, reverse=True)
    return {'code': f'L{no:02d}', 'no': no, 'title': names[no], 'grade': '중학교 1학년' if not common else '중학교 1~2학년 공통', 'standard': p['std'], 'unit': p['unit'],
            'lessonType': f'{"수행" if p.get("type") == "수행" else "개념"} 중심 차시 (10분 안팎) · 새 어휘 {len(new)}개' + (f', 미리 확인할 말 {len(pre)}개' if pre else '') + (f', 초등에서 배운 말 안내 {len(elem)}개' if elem else ''),
            'words': new, 'keep': keep, 'cast': ['아미르', '유나'], 'vocab': vocab, 'modules': M}

def write(root, L):
    d = os.path.join(root, FOLD[L['no']]); os.makedirs(d, exist_ok=True)
    io.open(os.path.join(d, 'lesson.json'), 'w', encoding='utf-8').write(json.dumps(L, ensure_ascii=False, indent=1))
    return FOLD[L['no']]
