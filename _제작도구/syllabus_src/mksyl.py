# -*- coding: utf-8 -*-
"""60차시 추천안(rows60.json) → 웹콘텐츠 시안의 syllabus.json.

추천안의 칸을 시안의 어휘 구분으로 옮기는 규칙
  필수어휘 + 관련 학습어휘  → 새 어휘(new). 앞 차시에서 이미 익힌 말이면 앞에서 배운 말(review)로.
  선수학습 어휘            → 앞 차시에서 익힌 말이면 앞에서 배운 말, 초등 낱말이면 초등에서 배운 말,
                            둘 다 아니면(익히는 차시가 없는 말) 처음 나오는 차시의 함께 보는 말(aux).
  비고의 '차시 안에서 함께 안내' → 함께 보는 말(aux).
"""
import io, json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1]
old = json.load(io.open(os.path.join(ROOT, 'syllabus.json'), encoding='utf-8'))
src = json.load(io.open(os.path.join(here, 'rows60.json'), encoding='utf-8'))
rows, P = src['rows'], src['P']
sp = lambda s: [w.strip() for w in s.split(',') if w.strip()]

ELEM = dict(old['elem'])
for l in old['lessons']:
    for w, s in l['review']:
        if not isinstance(s, int): ELEM.setdefault(w, s)
ELEM.update({'소수(小數)': '초3-1', '삼각형': '초등', '곱셈': '초3-1', '분수': '초3-1'})

U = {'중1': ['Ⅰ. 수와 연산', 'Ⅱ. 문자와 식', 'Ⅲ. 좌표평면과 그래프', 'Ⅳ. 도형의 기초', 'Ⅴ. 도형의 성질', 'Ⅵ. 통계'],
     '중2': ['Ⅰ. 수와 식', 'Ⅱ. 부등식과 연립방정식', 'Ⅲ. 일차함수', 'Ⅳ. 삼각형과 사각형의 성질', 'Ⅴ. 도형의 닮음과 피타고라스 정리', 'Ⅵ. 경우의 수와 확률']}
# 차시: (단원 번호, 천재 소단원 번호들, 성취기준들, 수행 도구어들)
META = {
 5: (1, [1], ['01-01'], '구분하다'), 6: (1, [1], ['01-01'], '나타내다'), 7: (1, [2], ['01-02'], '구하다'), 8: (1, [2], ['01-02'], '구하다'),
 9: (1, [3], ['01-03'], '구분하다'), 10: (1, [3], ['01-03'], '구분하다'), 11: (1, [3], ['01-04'], '비교하다'), 12: (1, [4, 5, 6], ['01-05'], '계산하다'), 13: (1, [7], ['01-05'], '계산하다'),
 14: (2, [2], ['02-02'], '말하다'), 15: (2, [2], ['02-02'], '고르다'), 16: (2, [3], ['02-02'], '간단히 하다'), 17: (2, [4], ['02-03'], '풀다'), 18: (2, [4, 5], ['02-03', '02-04'], '풀다'),
 19: (3, [1], ['02-05'], '나타내다'), 20: (3, [1], ['02-05'], '나타내다'), 21: (3, [2], ['02-06'], '해석하다,나타내다'), 22: (3, [3], ['02-07'], '나타내다'), 23: (3, [4], ['02-07'], '나타내다'),
 24: (4, [1], ['03-01'], '나타내다'), 25: (4, [2], ['03-01'], '구하다'), 26: (4, [3], ['03-01'], '찾다,말하다'), 27: (4, [4], ['03-02'], '구하다,설명하다'),
 28: (4, [6], ['03-04'], '찾다'), 29: (4, [5, 6], ['03-03', '03-04'], '작도하다,설명하다'),
 30: (5, [1, 2], ['03-05'], '구하다'), 31: (5, [3], ['03-06'], '구하다'), 32: (5, [4], ['03-07'], '고르다,말하다'), 33: (5, [4, 5, 6, 7], ['03-07', '03-08'], '그리다,구하다'),
 34: (6, [1], ['04-01'], '구하다'), 35: (6, [2], ['04-02'], '나타내다,완성하다'), 36: (6, [3, 4], ['04-02', '04-03'], '해석하다'),
 37: (1, [1], ['01-06'], '구분하다'), 38: (1, [1, 2], ['01-06'], '나타내다'), 39: (1, [3, 4], ['02-08', '02-10'], '간단히 하다'), 40: (1, [5, 6], ['02-09', '02-10'], '간단히 하다'),
 41: (2, [1, 2], ['02-11'], '나타내다'), 42: (2, [3], ['02-12'], '풀다'), 43: (2, [4], ['02-13'], '나타내다,찾다'), 44: (2, [5], ['02-13'], '풀다'),
 45: (3, [1], ['02-14'], '구하다'), 46: (3, [2], ['02-15'], '그리다'), 47: (3, [3], ['02-16'], '구하다'), 48: (3, [3, 4], ['02-16'], '구하다'), 49: (3, [5, 6, 7], ['02-17', '02-18'], '구하다'),
 50: (4, [1], ['03-09'], '구하다,증명하다'), 51: (4, [1], ['03-09'], '증명하다,설명하다'), 52: (4, [2], ['03-10'], '구하다'), 53: (4, [3], ['03-10'], '구하다'), 54: (4, [4, 5, 6], ['03-11'], '구하다,설명하다'),
 55: (5, [1], ['03-12'], '찾다,구하다'), 56: (5, [2], ['03-13'], '찾다,설명하다'), 57: (5, [3, 4], ['03-14'], '구하다'), 58: (5, [5], ['03-15'], '구하다'),
 59: (6, [1], ['04-05'], '구하다'), 60: (6, [2, 3, 4], ['04-06'], '구하다'),
}
AUX = {39: ['곱셈의 교환법칙', '곱셈의 결합법칙'], 41: ['좌변', '우변'], 48: ['일치'], 52: ['외접'], 53: ['내접', '접점', '접한다', '각의 이등분선']}
PRE = {44: ['대입'], 47: ['대입']}   # 비고의 '함께 안내' 가운데 앞 차시에서 이미 나온 말
COMMON = [
 (['구하다(구하시오)', '계산하다(계산하시오)', '풀다(푸시오)'], ['간단히 하다', '모두', '각각', '값', '다음 식', '정리하다', '~일 때', '해', '단']),
 (['나타내다(나타내시오)', '써넣다(써넣으시오)', '그리다(그리시오)'], ['완성하다', '작도하다', '~을 이용하여', '기호', '빈칸', '표', '알맞은', '좌표평면 위에']),
 (['고르다(고르시오)', '찾다(찾으시오)', '구분하다(구분하시오)'], ['비교하다', '다음 중', '보기', '옳은 것', '옳지 않은 것', '대소', '큰 것', '작은 것']),
 (['설명하다(설명하시오)', '말하다(말하시오)', '까닭(이유)'], ['~이므로', '~이기 때문에']),
]
PF = {}
for i, (nw, ax) in enumerate(COMMON, 1):
    for w in nw + ax: PF[w.split('(')[0]] = (i, w)

L = []; learned = {}
for r in rows:
    no, grade, _, sub, name, a, b, c = r[:8]
    if grade == '공통':
        nw, ax = COMMON[no - 1]
        L.append(dict(no=no, grade='공통', unit='공통(수행 중심)', sub='중1·중2 전 단원', std='', name=name, type='수행 중심', perf='', perfs=[], new=nw, elemNew={}, aux=ax, review=[], stds=[], secs=[]))
        continue
    u, secs, stds, pf = META[no]
    words = sp(a) + sp(b); new = []; review = []; aux = []
    for w in words:
        if w in learned: review.append([w, learned[w]])
        else: new.append(w)
    for w in sp(c) + PRE.get(no, []):
        if w in words: continue
        if w in learned: review.append([w, learned[w]])
        elif w in ELEM: review.append([w, ELEM[w]])
        else: aux.append(w)
    aux += [w for w in AUX.get(no, []) if w not in learned]
    for w in new + aux: learned[w] = no
    stds = ['[9수%s]' % s for s in stds]
    perfs = [[w, PF[w][0], PF[w][1]] if w in PF else [w, None, None] for w in pf.split(',')]
    L.append(dict(no=no, grade=grade, unit=U[grade][u - 1], sub=sub, std=', '.join(stds), name=name, type='수행 중심' if no == 44 else '개념 중심',
                  perf=pf.split(',')[0], perfs=perfs, new=new, elemNew={w: ELEM[w] for w in new if w in ELEM}, aux=aux, review=review, stds=stds, secs=secs, must=sp(a)))

# 점검
ess = set(old['ess']); newset = set(w for d in L for w in d['new'])
assert not ess - newset, ess - newset
codes = {s['code'] for s in old['stds']}
for d in L:
    for s in d['stds']: assert s in codes, (d['no'], s)
    for w, s in d['review']:
        if isinstance(s, int): assert s < d['no'], (d['no'], w, s)
    if d['grade'] != '공통':
        t = [x for x in old['toc'] if x['grade'] == d['grade'] and x['unit'] == d['unit']]; assert t, d['unit']
        assert set(d['secs']) <= {x['n'] for x in t[0]['secs']}, (d['no'], d['secs'])
used = {s for d in L for s in d['stds']}
print('차시 없는 성취기준:', sorted(codes - used))
for t in old['toc']:
    miss = [f"{x['n']}. {x['title']}" for x in t['secs'] if not any(d['grade'] == t['grade'] and d['unit'] == t['unit'] and x['n'] in d['secs'] for d in L)]
    if miss: print('차시 없는 소단원:', t['grade'], t['unit'], miss)
print('새 어휘', sum(len(d['new']) for d in L if d['grade'] != '공통'), '/ 함께 보는 말', sum(len(d['aux']) for d in L if d['grade'] != '공통'))
print('새 어휘 4개 이상:', [(d['no'], d['new']) for d in L if d['grade'] != '공통' and len(d['new']) > 3])
print('새 어휘 없는 차시:', [d['no'] for d in L if not d['new']])
for d in L[4:12]: print(d['no'], d['name'], '| new', d['new'], '| aux', d['aux'], '| rev', d['review'])
old['lessons'] = L
old['title'] = '중학교 수학 한국어 어휘 콘텐츠 · 60차시 어휘 위계 (추천안 2026-10-09)'
io.open(os.path.join(ROOT, 'syllabus.json'), 'w', encoding='utf-8').write(json.dumps(old, ensure_ascii=False, indent=1))
