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
def mg(*rows): return {'kind': 'mg', 'rows': list(rows)}   # 낱말 이야기 모션그래픽(줄을 차례로 띄운다). 줄 종류는 template 의 figMg 참고
def num(a, b, **k): return dict(kind='num', min=a, max=b, **k)
def pw(base, exp, labels=True, eqs=None):
    d = {'kind': 'power', 'base': base, 'exp': exp, 'labels': labels}
    if eqs: d['eq'] = eqs
    return d
def tree(n, eqs=None): return {'kind': 'tree', 'n': n, 'eq': eqs} if eqs else {'kind': 'tree', 'n': n}
plain = lambda t: re.sub(r'[*‘’]', '', t)
def ask(q, options=None, answer=0, ok=None, fig=None, text=None, replies=None, hint=None):
    """영상 컷 안의 참여 활동. 자막이 나오기 전에 멈추고 묻는다. options 가 없으면 O·X, answer=None 이면 정답 없이 고르기만 한다(replies 로 대답).
    fig·text 는 답하기 전에 보여 줄 그림·글(답이 보이지 않게 가린 것). 답하면 컷의 원래 그림·자막이 나온다."""
    d = {'q': q, 'options': options or ['O', 'X'], 'answer': answer}
    if not options: d['ox'] = True
    for k, v in (('ok', ok), ('fig', fig), ('text', text), ('replies', replies), ('hint', hint)):
        if v is not None: d[k] = v
    return d
def cut(cap=None, fig=None, text=None, dir='', b=None, narr=None, ask=None):
    c = {}
    if fig is not None: c['fig'] = fig
    if text is not None: c['text'] = text
    if cap: c['caption'] = cap; c['narr'] = narr or plain(cap)
    if dir: c['dir'] = dir
    if b: c['bubbles'] = [dict({'who': x[0], 'text': x[1]}, **({'after': True} if len(x) > 2 else {})) for x in b]   # (누구, 말) 또는 (누구, 말, True): 참여 활동에 답한 뒤에 나오는 말
    if ask: c['ask'] = ask
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

OPENERS = {'도입': ('🧭', '오늘 무엇을 익힐지 살펴봐요', False), '어휘 제시': ('👀', '오늘의 낱말을 만나요', True), '정의': ('💡', '아는 것에 한국어 이름을 붙여요', False),
           '용례': ('💬', '대화 속에서 낱말을 만나요', False), '연습': ('✏️', '낱말을 고르고, 쓰고, 말해 봐요', False), '마무리': ('🎒', '오늘 익힌 낱말을 점검해요', True)}

def build(p, names):
    no = p['no']; common = no <= 4
    new, aux, pre, elem, perf = p['new'], p.get('aux', []), p.get('pre', []), p.get('elem', []), p.get('perf', [])
    kind_new = '수행 도구어' if common else '핵심 개념어'
    # flow1011: 2026-10-11 회의에서 정한 단계별 역할. 정의 = 영상 + 리마인드(뜻 카드), 용례 = 충남대 자료의 용례 소개,
    # 쓰고 말하는 활동은 모두 연습 단계, 마무리 = ‘점검해 봐요’ 한 화면. 문제에서 쓰는 말(수행 도구어)은 개념어 차시에서 다루지 않는다.
    flow = p.get('flow1011')
    M = []
    # 낱말 미리 보기: 낱말을 누르면 뜻·예·교과서 문장이 작은 창으로 나온다. 정리 화면(summary)과 용례(usage)에서 가져오고, p['preview'] 로 고치거나 더한다.
    def pv(w, cheer=False):
        d = {}
        for t, eg, df in p.get('summary', []):
            if t == w: d = {'def': df, 'eg': eg}
        sents = [' '.join(t.split()) for t, _ in p.get('usage', []) if isinstance(t, str)]
        hit = [t for t in sents if '**' + w in t] or [t for t in sents if w in t.replace('*', '')]
        if d and hit: d['sent'] = hit[0]
        d.update(p.get('preview', {}).get(w, {}))
        if cheer and p.get('cheer', {}).get(w): d['cheer'] = p['cheer'][w]   # 낱말을 누르면 뜨는 응원하는 말(학습 동기)
        r = {'t': w, 'pv': d} if d else {'t': w}
        if flow and w in p.get('ess', []): r['core'] = True   # 핵심 학습 어휘(충남대 필수 어휘)는 색을 달리해 강조한다
        return r
    def pv_pre(w, n, ex):   # 미리 확인할 말: 앞 차시에서 익힌 뜻을 그대로 보여 준다
        df, _, eg = ex.partition(' 예: ')
        d = {'def': df.rstrip('.'), 'tip': f'{n}차시에서 익힌 말이에요.'}
        if eg: d['eg'] = eg
        d.update(p.get('preview', {}).get(w, {}))
        return {'t': w, 's': f'{n}차시에서 배운 말', 'pv': d}
    tap = p.get('intro_preview')   # 도입 화면에서도 낱말·단원 이름을 눌러 미리 보기
    # ── 도입
    s = []
    cols = []
    if pre or elem:
        cols.append({'label': '미리 확인할 말' if pre else '이미 아는 말', 'items': [pv_pre(w, n, ex) if tap else {'t': w, 's': f'{n}차시에서 배운 말'} for w, n, ex in pre] + [{'t': w, 's': '초등학교에서 배운 말'} for w, _ in elem[:max(1, 3 - len(pre))]]})
    else:
        cols.append({'label': '수학 문제의 끝말', 'items': [{'t': '~하시오', 's': '무엇을 하라는 말일까요?'}]})
    cols.append({'label': '오늘 새로 익힐 말', 'hl': True, 'items': [pv(w) for w in new] if tap else new})
    school = {'label': '학교 수업', 'items': [{'t': p['school'], 's': p['school_s']}]}
    if p.get('school_goal') and tap: school['items'][0]['pv'] = {'info': p['school_goal'], 'tip': ''}   # 눌러야 보인다
    elif p.get('school_goal'): school['desc'] = p['school_goal']   # 이 단원에서 무엇을 하고 오늘 낱말이 어디에 쓰이는지 한두 문장(낱말 쪽에서 말한다)
    cols.append(school)
    s.append({'type': 'curation', 'q': p['intro_q'], 'cols': cols, 'note': p['intro_note'] + (chr(10) + '낱말이나 단원 이름을 누르면 미리 볼 수 있어요.' if tap else ''),
              'memo': '도입(큐레이션). 이 콘텐츠는 학교에서 해당 단원을 배우기 전에 보는 것임을 먼저 알린다. 이미 아는 말 → 새로 익힐 말 → 학교 수업의 흐름을 한 화면에 보여 준다. 학교 수업 칸에는 그 단원에서 무엇을 하는지, 오늘 낱말이 어디에서 쓰이는지를 한두 문장으로 알린다(교과 내용을 설명하지 않고 낱말 쪽에서 말한다). 낱말과 단원 이름은 눌렀을 때만 뜻·예·안내가 작은 창으로 나온다(선택 활동).'})
    for c in ([] if flow else p.get('checks', [])):
        c.setdefault('memo', '미리 확인할 말의 뜻 확인. 새로 가르치지 않는다. 틀리면 그 낱말을 익히는 차시로 안내한다.'); s.append(c)
    if pre and flow:   # 갈림길: ‘알아요’ → 바로 어휘 제시로, ‘잘 몰라요’ → 다음 화면(뜻 확인)으로. 화면 번호(yesJump·noJump)는 아래에서 단계 표지를 넣은 뒤에 붙인다
        s.append({'type': 'checklist', 'q': '이 말을 알고 있나요?', 'fork': True, 'allOk': '좋아요! 바로 시작해요.', 'someNo': '괜찮아요. 뜻을 한 번 확인하고 가요.',
                  'items': [{'t': w, 'ex': ex} for w, n, ex in pre], 'note': '‘알아요’를 누르면 바로 오늘의 낱말로 가요. ‘잘 몰라요’를 누르면 뜻을 한 번 확인하고 가요.',
                  'memo': '선수학습 낱말 확인(2026-10-11 회의: 알아요/잘 몰라요). ‘알아요’를 고르면 다음 화면(뜻 확인)을 건너뛰고 어휘 제시 단계로 바로 넘어간다. ‘잘 몰라요’를 고르면 다음 화면으로 넘어가 뜻을 한 번 확인한다. 학습 어휘로 다시 가르치지 않는다.'})
        for c in p.get('checks', []):
            c.setdefault('memo', '‘잘 몰라요’를 고른 학생만 보는 화면. 미리 확인할 말의 뜻과 예를 보여 주고 낱말을 고르게 한다. 새로 가르치지 않는다. 그래도 모르면 그 낱말을 익히는 차시로 안내한다.'); s.append(c)
    elif pre:
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
    cols = [{'label': '오늘 새로 익힐 말', 'hl': True, 'items': [pv(w, cheer=True) for w in new]}]
    if aux: cols.append({'label': '함께 보는 말', 'items': [pv(w) for w in aux]})
    can_tap = any('pv' in it for c in cols for it in c['items'])
    known = [{'t': w, 's': f'{n}차시'} for w, n, _ in pre] + [{'t': w, 's': '초등'} for w, _ in elem]
    if known and not (aux and perf): cols.append({'label': '이미 아는 말', 'items': known[:4]})
    if perf: cols.append({'label': '문제에서 쓰는 말', 'items': [{'t': v, 's': f'{n}차시' if n else ''} for v, n in perf]})
    s.append({'type': 'curation', 'noArrow': True, 'q': '오늘 만날 낱말이에요.', 'cols': cols, 'note': p.get('present_note', '이미 아는 말을 가지고 새 낱말의 뜻을 알아봐요.') + (chr(10) + '궁금한 낱말을 누르면 뜻과 예를 미리 볼 수 있어요.' if can_tap else '') + (' ★ 색이 다른 낱말은 꼭 알아야 하는 핵심 낱말이에요.' if flow and p.get('ess') else ''),
              'memo': f'새 어휘({kind_new}), 함께 보는 말·이미 아는 말(보조·배경 개념어), 문제에서 쓰는 말(수행 도구어)을 나누어 보여 준다.' + (' 낱말을 누르면 뜻·예·교과서 문장을 작은 창으로 미리 볼 수 있다(선택 활동, 보지 않아도 뒤에서 모두 배운다).' if can_tap else '')})
    if not common:
        s.append({'type': 'vod', 'title': '수업 장면: 교과서에서 만난 낱말', 'cuts': p['scene'], 'memo': '새 낱말을 수업 장면 속에서 처음 보여 준다. 이미 아는 말과 이미 아는 개념에서 출발한다는 점을 대사로 짚는다.'})
    if flow:   # 어휘 제시에서는 듣기만 한다(따라 말하기·쓰기는 연습 단계)
        s.append({'type': 'listen', 'q': '낱말을 눌러 소리를 들어 보세요.', 'tip': '🔊를 누르면 낱말을 읽어 줘요. 쓰고 말하는 것은 ‘연습’에서 해요.', 'items': [{'text': t, 'say': sy} if sy else {'text': t} for t, sy in p['listen']],
                  'memo': '어휘 제시 단계에서는 낱말의 모양과 소리만 만난다. 따라 읽기·쓰기는 넣지 않는다(쓰고 말하는 활동은 연습 단계에서만 — 2026-10-11 회의).'})
    elif p.get('type_listen'):   # 듣고 쓰기: 따라 읽기 대신 ▶로 듣고 낱말을 쳐 넣는다(낱말은 보여 준다 — 처음 만나는 단계라 보고 쓰기)
        s.append({'type': 'listen', 'mode': 'type', 'q': '낱말을 듣고, 보면서 따라 써 보세요.', 'items': [dict({'text': t, 'answer': t}, **({'say': sy} if sy else {})) for t, sy in p['listen']],
                  'memo': '듣고 쓰기(낱말). ▶를 누르면 발음이 나오고, 학생은 낱말을 보면서 자판으로 쳐 넣는다. 맞게 쓰면 ✓가 생긴다. 틀렸다는 표시는 하지 않는다. 원본 유형에 맞는 것이 없으면 input(직접 써넣기) 유형에 듣기 단추를 붙여 구현한다.'})
    else:
        s.append({'type': 'listen', 'q': '다음 낱말을 듣고 2번 따라 읽어 보세요.', 'items': [{'text': t, 'say': sy} if sy else {'text': t} for t, sy in p['listen']]})
    M.append({'name': '어휘 제시', 'screens': s})
    # ── 정의
    s = [{'type': 'vod', 'title': p['define_title'], 'cuts': p['define'], 'memo': p.get('define_memo', '개념을 새로 가르치지 않는다. 이미 아는 말과 아는 개념을 차례로 써서 새 낱말에 이른다. 낱말에 들어 있는 한자말의 뜻(예: 최대 = 가장 큰)을 풀어 주어 한국어 낱말로 받아들이게 한다.')}]
    for front, back in p['cards']:
        s.append({'type': 'card_flip', 'q': '낱말을 클릭해 뜻을 확인해 보세요.', 'front': {'text': front}, 'back': back, 'answerText': front})
    s.append({'type': 'lang_match', 'q': '내 나라 말을 고르고, 뜻이 같은 말끼리 연결해 보세요.' if p.get('active') else '내가 아는 말과 연결해 보세요.', 'words': p['lang_words'], 'items': [{'lang': l, 'terms': t} for l, t in zip(LANGS, p['lang'])],
              'note': '나라마다 부르는 말은 달라도 뜻은 같아요.', **({'pick': True} if p.get('active') else {}),
              'memo': '이미 아는 개념과 한국어 낱말을 대응시키는 화면. ★ 각 언어의 용어는 원어민 검수를 받아야 한다. 다른 언어는 검수자가 채운다. 원본 플랫폼에서는 학습자가 고른 언어 한 줄만 보여 주는 방식이 알맞다.'})
    M.append({'name': '정의', 'screens': s})
    # ── 용례
    def blanked(t, sy):   # 문장 속의 오늘 낱말(가장 긴 것)을 빈칸으로 바꾼다
        w = next((w for w in sorted(new + aux, key=len, reverse=True) if w in t), None)
        d = {'text': t.replace(w, '{0}', 1), 'answer': w, 'say': sy or t} if w else {'text': t, 'answer': t}
        return d
    if p.get('type_listen'):
        say_screen = {'type': 'listen', 'mode': 'type', 'q': '문장을 듣고, 빈칸에 들어갈 낱말을 써 보세요.', 'items': [blanked(t, sy) for t, sy in p['says']],
                      'memo': '듣고 쓰기(문장). ▶를 누르면 문장 전체가 나오고, 학생은 빈칸에 들어갈 오늘의 낱말만 쳐 넣는다(받아쓰기). 수식이나 문장 전체를 치게 하지 않는다.'}
    else:
        say_screen = {'type': 'listen', 'q': '다음 문장을 듣고 2번 따라 읽어 보세요.', 'items': [{'text': t, 'say': sy} if sy else {'text': t} for t, sy in p['says']]}
    s = [{'type': 'vod', 'title': '교과서 문장 속의 낱말', 'cuts': [cut(c, text=t, ask=a) for (t, c), a in zip(p['usage'], p.get('usage_ask') or [None] * len(p['usage']))],
          'memo': '용례 단계. 학교 수업에서 실제로 만나는 교과서 문장을 보여 주고, 함께 쓰이는 말(공기관계어)과 수행 도구어를 자막으로 짚는다.' + (' 문장마다 먼저 학생이 O·X로 낱말을 알맞게 썼는지 고르고, 그다음에 자막이 나온다(읽고 넘기지 않게).' if p.get('usage_ask') else '')},
         say_screen,
         dict({'type': 'drag_drop', 'q': '보기에서 알맞은 낱말을 골라 빈칸에 넣어 보세요.'}, **p['drag'])]
    if flow and p.get('talk'):   # 용례 = 두 인물의 대화. 대사가 하나씩 나오고, 그 안에 용례가 녹아 있다. 낱말 사이의 관계가 이야기로 드러난다. 끝에 잘못 쓴 문장 찾기
        t = p['talk']
        s = [{'type': 'talk', 'q': t['q'], 'board': t.get('board', '칠판'), 'end': t.get('end'), 'lines': [dict({'who': who, 'text': text}, **extra) for who, text, extra in t['lines']],
              'memo': '용례 단계(사용자 의견 2026-10-11). 두 인물의 대화로 용례를 만난다. 맥락(상황)이 있고, 대사가 하나씩 나오며, 용례 문장이 대사 안에 자연스럽게 들어 있다. 색이 다른 말풍선이 용례이고, 충남대 학습어휘 자료의 용례 문장을 그대로 쓴다. 한 차시의 학습 어휘들이 서로 어떻게 이어지는지가 이야기 순서로 드러나게 한다. 왼쪽 칠판에는 지금 말하는 식이 보인다. 말풍선을 누르면 읽어 준다. 학생이 쓰거나 말하는 활동은 넣지 않는다(연습 단계에서 한다). 실제 제작에서는 인물이 말하는 애니메이션(영상)으로 만들어도 된다.'}]
        for sp in p.get('spots', []):
            sp = dict(sp); sp['type'] = 'spot'
            sp.setdefault('memo', '잘못 쓴 문장 찾기. 인물이 말한 문장 가운데 오늘의 낱말을 잘못 쓴 문장을 찾아 누른다. 누르면 줄이 그어지고 바른 문장이 나온다. 수학 내용이 틀린 문장이 아니라 낱말을 바꿔 쓴 문장만 넣는다(계산하거나 구하게 하지 않는다). 점수를 매기지 않는다.')
            s.append(sp)
    elif flow:   # 용례 = 사례를 보여 주는 것. 충남대 학습어휘 자료의 용례를 그대로 소개하고, 활동은 넣지 않는다
        s = [{'type': 'vod', 'title': '용례: 문장 속의 낱말', 'cuts': [cut(c, text=t) for t, c in p['usage']],
              'memo': '용례 단계. 충남대 학습어휘 자료(학습어휘추출 엑셀)의 용례를 그대로 소개한다. 낱말마다 용례 한 문장. 자막으로는 함께 쓰이는 말(공기관계어)만 짚는다. 수학 문제 풀이는 넣지 않고, 학생이 쓰거나 말하는 활동도 넣지 않는다(연습 단계에서 한다).'}]
    else:
        i = p['instr']; i['q'] = '문제에서 무엇을 하라고 하나요?'; i['memo'] = '지시문을 이해하는지 확인하는 문항. 답을 구하게 하지 않는다.'; s.append(i)
    M.append({'name': '용례', 'screens': s})
    # ── 연습
    s = list(p['practice'])
    s[0].setdefault('memo', '새 낱말의 뜻을 아는지 확인하는 문항. 계산 연습이 아니므로 수는 작게 둔다.')
    sp = {'type': 'step_recorde', 'q': '다음을 듣고 따라 말해 보세요.', 'sentence': p['speak'][0], 'memo': '원본의 step_recorde(듣고 따라 말하기, 녹음) 기능을 연결한다.'}
    if p['speak'][1]: sp['say'] = p['speak'][1]
    if len(p['speak']) > 2: sp['fig'] = p['speak'][2]
    if flow: sp = None   # 연습 화면은 원고(p['practice'])에 차례대로 모두 적는다: 낱말 고르기 → 듣고 쓰기 → 손글씨 → 말하기 → 받아쓰기
    elif p.get('write_final'):   # 따라 말하기 대신 듣고 쓰기(받아쓰기): [(문장, 읽는 법, 빈칸 낱말)]
        sp = {'type': 'listen', 'mode': 'type', 'q': '문장을 듣고, 빈칸에 들어갈 낱말을 써 보세요.',
              'items': [{'text': t.replace(w, '{0}', 1), 'answer': w, 'say': sy or t} for t, sy, w in p['write_final']],
              'memo': '연습의 마무리. 듣고 쓰기(받아쓰기). ▶를 누르면 문장 전체가 나오고, 학생은 빈칸에 들어갈 오늘의 낱말을 낱말을 보지 않고 쳐 넣는다. 오늘의 낱말을 모두 한 번씩 쓴다. 맞게 쓰면 ✓가 생긴다.'}
    if sp: s.append(sp)
    M.append({'name': '연습', 'screens': s})
    # ── 마무리
    s = [{'type': 'curation', 'noArrow': True, 'q': '오늘 새로 익힌 낱말을 정리해요.', 'cols': [{'label': lb, 'hl': True, 'items': [{'t': t, 's': sub}]} for lb, t, sub in p['summary']], 'memo': '새 어휘를 한 화면에서 다시 본다.'},
         {'type': 'curation', 'q': '이제 학교 수업에서 만나요.', 'cols': [{'label': '오늘 익힌 낱말', 'hl': True, 'items': new}, {'label': '학교 수업', 'items': [{'t': p['school'], 's': p['school_use']}]},
                                                               {'label': '그다음에 볼 콘텐츠', 'items': [{'t': names[no + 1], 's': f'{no + 1}차시'}]}],
          'note': p['outro_note'], 'memo': '마무리(큐레이션). 익힌 낱말이 학교 수업의 어디에서 쓰이는지, 그다음에 볼 콘텐츠가 무엇인지 안내한다.'}]
    if p.get('active'):   # 참여형 마무리: 정리 화면은 낱말 넣기로, 그 뒤에 스스로 점검(모르면 낱말 이야기로 돌아가기)을 넣는다
        off = 1 if p.get('openers') else 0
        s[0] = {'type': 'recall', 'q': '뜻과 예를 보고, 알맞은 낱말을 넣어 보세요.', 'items': [{'t': t, 'eg': eg, 'def': df} for t, eg, df in p['summary']],
                'memo': '마무리 정리. 낱말을 다시 읽어 주지 않고, 뜻과 예가 적힌 카드에 학생이 낱말을 넣으면서 정리한다. 낱말을 누른 다음 카드를 누른다(끌어넣기로 만들어도 된다).'}
        s.insert(1, {'type': 'checklist', 'q': '오늘 익힌 낱말을 스스로 점검해 봐요.', 'yes': '알아요', 'no': '다시 볼래요', 'allOk': '모두 익혔어요! 이제 학교 수업에서 만나요.', 'someNo': '‘낱말 이야기’를 한 번 더 보고 와도 좋아요.',
                     'items': [{'t': t, 'ex': df, 'go': '→ ‘' + t + '’ 낱말 이야기 다시 보기', 'jump': [2, off, p.get('story_cut', {}).get(t, 0)]} for t, eg, df in p['summary']],
                     'memo': '스스로 점검. ‘다시 볼래요’를 누르면 정의 단계의 낱말 이야기 가운데 그 낱말이 시작되는 컷으로 돌아가는 연결이 나온다. 점수를 매기지 않는다.'})
        s[2]['cols'][0]['items'] = [pv(w) for w in new]
        s[2]['note'] = p['outro_note'] + chr(10) + '낱말을 누르면 뜻과 예를 다시 볼 수 있어요.'
    if flow:   # 마무리 = ‘점검해 봐요’ 한 화면. 문제 풀이 없이 오늘 익힌 낱말을 뜻·예와 함께 다시 보고 스스로 점검한다
        s = [{'type': 'checklist', 'q': '점검해 봐요. 오늘 익힌 낱말을 알고 있나요?', 'yes': '알아요', 'no': '다시 볼래요', 'allOk': '모두 익혔어요! 이제 학교 수업에서 만나요.', 'someNo': '‘낱말 이야기’를 한 번 더 보고 와도 좋아요.',
              'items': [{'t': t, 'ex': df + chr(10) + '예: ' + eg, 'go': '→ ‘' + t + '’ 낱말 이야기 다시 보기', 'jump': [2, 1 if p.get('openers') else 0, p.get('story_cut', {}).get(t, 0)]} for t, eg, df in p['summary']],
              'note': p['outro_note'],
              'memo': '마무리는 이 한 화면이다(2026-10-11 회의: ‘점검해 봐요’ 한 페이지 또는 짧은 정리 영상 하나). 오늘 익힌 낱말을 뜻·예와 함께 요약해 보여 주고 스스로 점검한다. 문제를 풀게 하지 않고 점수도 매기지 않는다. ‘다시 볼래요’를 누르면 정의 단계의 낱말 이야기에서 그 낱말이 시작되는 컷으로 돌아간다.'}]
    M.append({'name': '마무리', 'screens': s})
    vocab = {f'새 어휘 = {kind_new} (이 차시에서 익힘)': [w + (' (충남대 핵심어)' if w in p.get('ess', []) else '') for w in new]}
    if aux: vocab['함께 처음 보는 말' + (' (수행 도구어)' if common else ' (보조·배경 개념어)')] = aux
    if pre: vocab['미리 확인할 말 (차시 처음에 아는지 확인 → 모르면 익힌 차시로 안내)'] = [f'{w} → {n}차시 ‘{names[n]}’' for w, n, _ in pre]
    if elem: vocab['초등에서 배운 말 (이 차시 안에서 배경지식으로 안내)'] = [f'{w} ({sem})' for w, sem in elem]
    if perf: vocab['수행 도구어 (문제에서 쓰는 말)'] = [f'{v} → {n}차시' if n else f'{v} (익히는 차시 없음)' for v, n in perf]
    if p.get('colloc'): vocab['공기관계어'] = p['colloc']
    keep = sorted({w for w in new + aux + [x[0] for x in pre] + [x[0] for x in elem] + p.get('keep', []) if len(w) >= 2 or w in new}, key=len, reverse=True)
    # 단계 표지(모션그래픽): p['openers'] 가 참이면 여섯 단계의 맨 앞에 하나씩 넣는다.
    if p.get('openers'):
        for m in M:
            icon, subt, chips = OPENERS[m['name']]
            o = {'type': 'opener', 'name': m['name'], 'icon': icon, 'sub': subt,
                 'memo': '단계 표지(모션그래픽). 3~4초 길이. 위쪽 길에서 여섯 단계 가운데 지금 어디인지 보여 주고, 단계 이름과 이 단계에서 할 일이 차례로 나타난다. 시안에서는 자동으로 넘어가지 않고 ▶를 눌러 넘긴다.'}
            if chips: o['chips'] = new
            if chips and flow and m['name'] == '어휘 제시':   # 어휘 제시 첫 화면: 핵심 낱말은 색을 달리하고, 낱말을 누르면 응원하는 말이 뜬다
                o['core'] = [w for w in new if w in p.get('ess', [])]
                if p.get('cheer'): o['cheer'] = p['cheer']
                o['memo'] += ' 핵심 학습 어휘(★)는 다른 낱말과 색을 달리해 강조한다. 낱말을 누르면 그 낱말을 익히고 싶게 하는 짧은 말(학습 동기)이 작은 창으로 뜬다. 뜻을 설명하는 말은 넣지 않는다.'
            m['screens'].insert(0, o)
    for i, sc in enumerate(M[0]['screens']):   # 도입의 갈림길 화면에 넘어갈 곳을 붙인다
        if sc.pop('fork', None):
            sc['yesJump'] = [1, 0]
            if i + 1 < len(M[0]['screens']): sc['noJump'] = [0, i + 1]
    chat = None
    if p.get('chat_url'):   # 질문하기 챗봇: 차시의 낱말 풀이를 기본 자료로 함께 보낸다
        gl = [f'{t}: {df} (예: {eg})' for t, eg, df in p.get('summary', [])] + [f'{w}: {ex} ({n}차시에서 익힌 말)' for w, n, ex in pre]
        gl += [f'{w}: {d.get("def", "")}' for w, d in p.get('preview', {}).items() if d.get('def')] + ['교과서 문장: ' + ' '.join(t.replace('*', '').split()) for t, _ in p.get('usage', []) if isinstance(t, str)]
        chat = {'url': p['chat_url'], 'words': chr(10).join(gl)}
    return {'chat': chat, 'code': f'L{no:02d}', 'no': no, 'title': names[no], 'grade': '중학교 1학년' if not common else '중학교 1~2학년 공통', 'standard': p['std'], 'unit': p['unit'],
            'lessonType': f'{"수행" if p.get("type") == "수행" else "개념"} 중심 차시 (10분 안팎) · 새 어휘 {len(new)}개' + (f', 미리 확인할 말 {len(pre)}개' if pre else '') + (f', 초등에서 배운 말 안내 {len(elem)}개' if elem else ''),
            'words': new, 'keep': keep, 'cast': ['아미르', '유나'], 'vocab': vocab, 'modules': M}

def write(root, L):
    d = os.path.join(root, FOLD[L['no']]); os.makedirs(d, exist_ok=True)
    io.open(os.path.join(d, 'lesson.json'), 'w', encoding='utf-8').write(json.dumps(L, ensure_ascii=False, indent=1))
    return FOLD[L['no']]
