# -*- coding: utf-8 -*-
"""차시 하나만 따로 볼 수 있는 단독 배포본을 만든다.

    python _제작도구/publish_single.py                (기본: 6차시 소인수분해 → ../소인수분해 차시 단독 배포)
    python _제작도구/publish_single.py <차시 폴더> <배포 폴더>

먼저 build.py 로 차시의 index.html 을 만든 뒤 실행한다. 배포 폴더는 별도 git 저장소
(j333333766-hub/math-korean-vocab-sample)이며, 이 스크립트는 파일만 만들고 commit·push 는 하지 않는다.
전체 시안과 다른 점: 🏠 홈 단추를 빼고, 다른 차시로 가는 연결은 전체 시안 주소로 바꾼다.
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
MAIN = 'https://j333333766-hub.github.io/math-korean-vocab-preview/'
folder = sys.argv[1] if len(sys.argv) > 1 else 'L06-9su01-01'
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(ROOT), '소인수분해 차시 단독 배포')

html = io.open(os.path.join(ROOT, folder, 'index.html'), encoding='utf-8').read()
home = '<a class="homebtn notranslate" href="../">🏠 홈</a>'
assert home in html, '홈 단추를 찾지 못했습니다(template.html 이 바뀌었는지 확인).'
html = html.replace(home, '')
html, n = re.subn(r'"href": "\.\./([^"]+)"', lambda m: f'"href": "{MAIN}{m.group(1)}"', html)
os.makedirs(out, exist_ok=True)
io.open(os.path.join(out, 'index.html'), 'w', encoding='utf-8', newline='').write(html)
io.open(os.path.join(out, '.nojekyll'), 'w').write('')
print(f'{folder} → {out} (다른 차시 연결 {n}곳을 전체 시안 주소로 바꿈)')
