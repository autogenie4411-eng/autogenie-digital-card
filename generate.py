from pathlib import Path
import re, html, urllib.parse, shutil
from PIL import Image, ImageDraw, ImageFont, ImageOps

BASE = Path(__file__).resolve().parent
SALES = BASE / 'sales_profiles'
CARDS = BASE / 'cards'
OG = BASE / 'og'
TEMPLATE = BASE / 'index.html'
BASE_URL = 'https://sales.agautoplan.com'
COMPANY_DEFAULT = '주식회사 오토지니'

OG_W, OG_H = 1200, 600
OG_BG = '#2B57D9'
OG_BG_IMAGE = BASE / 'images' / 'bg.png'


def parse_profile(path: Path):
    data = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        data[key.strip()] = value.strip()
    return data


def find_font(size, bold=False):
    candidates = [
        r'C:\\Windows\\Fonts\\malgunbd.ttf' if bold else r'C:\\Windows\\Fonts\\malgun.ttf',
        r'C:\\Windows\\Fonts\\NanumGothicBold.ttf' if bold else r'C:\\Windows\\Fonts\\NanumGothic.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc' if bold else '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc' if bold else '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def resolve_photo(folder: Path, data, name):
    raw = data.get('photo', '').strip()
    if raw:
        # try absolute-from-project path first
        candidate = BASE / raw.removeprefix('./')
        if candidate.exists():
            return candidate
        # then same folder basename
        candidate = folder / Path(raw).name
        if candidate.exists():
            return candidate
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        p = folder / f'{name}{ext}'
        if p.exists():
            return p
    for pattern in ('*.png', '*.jpg', '*.jpeg', '*.webp'):
        items = list(folder.glob(pattern))
        if items:
            return items[0]
    return None


def make_og(photo_path, name, department, position, company, out_path):
    # 디지털 명함 상단에서 사용하는 자동차 배경을 OG 이미지에도 동일하게 사용합니다.
    # 원본 비율을 유지한 채 1200x600 영역을 꽉 채우도록 중앙 크롭합니다.
    if OG_BG_IMAGE.exists():
        bg = Image.open(OG_BG_IMAGE).convert('RGB')
        canvas = ImageOps.fit(
            bg,
            (OG_W, OG_H),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    else:
        canvas = Image.new('RGB', (OG_W, OG_H), OG_BG)

    draw = ImageDraw.Draw(canvas)

    # 카톡 축소 시에도 잘 보이도록 큰 글씨 + Bold
    font_name = find_font(82, True)
    font_position = find_font(48, True)
    font_company = find_font(40, True)

    photo_size = 310
    px = 80
    py = (OG_H - photo_size) // 2

    if photo_path and photo_path.exists():
        profile = Image.open(photo_path).convert('RGB')
        profile = ImageOps.fit(profile, (photo_size, photo_size), Image.Resampling.LANCZOS, centering=(0.5, 0.43))
        mask = Image.new('L', (photo_size, photo_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, photo_size - 1, photo_size - 1), fill=255)

        ring_size = photo_size + 16
        ring = Image.new('RGB', (ring_size, ring_size), '#FFFFFF')
        ring_mask = Image.new('L', (ring_size, ring_size), 0)
        ImageDraw.Draw(ring_mask).ellipse((0, 0, ring_size - 1, ring_size - 1), fill=255)
        canvas.paste(ring, (px - 8, py - 8), ring_mask)
        canvas.paste(profile, (px, py), mask)

    tx = 455
    draw.text((tx, 120), name, font=font_name, fill='#FFFFFF')
    draw.text((tx, 265), f'{department} | {position}', font=font_position, fill='#FFFFFF')
    draw.text((tx, 360), company, font=font_company, fill='#FFFFFF')
    canvas.save(out_path, quality=96)


def replace_id_text(source, element_id, value):
    pattern = rf'(<[^>]+id=["\']{re.escape(element_id)}["\'][^>]*>)(.*?)(</[^>]+>)'
    return re.sub(pattern, lambda m: m.group(1) + value + m.group(3), source, count=1, flags=re.S)



def format_phone_display(value: str) -> str:
    digits = re.sub(r'\D', '', value or '')

    if len(digits) == 11 and digits.startswith('01'):
        return f'{digits[:3]}-{digits[3:7]}-{digits[7:]}'
    if len(digits) == 10 and digits.startswith('01'):
        return f'{digits[:3]}-{digits[3:6]}-{digits[6:]}'

    return value or ''

def build_card(template, folder, photo, data):
    name = data.get('name', folder.name).strip()
    phone = data.get('phone', '').strip()
    phone_clean = re.sub(r'\D', '', phone)
    email = data.get('email', '').strip()
    kakao_chat_url = data.get('kakaoChatUrl', '').strip()
    department = data.get('department', '').strip()
    position = data.get('position', '').strip()
    company = data.get('company', COMPANY_DEFAULT).strip() or COMPANY_DEFAULT
    site_name = data.get('siteName', f'{name} {position} | 오토지니').strip()
    phone_clean = ''.join(c for c in phone if c.isdigit() or c == '+')

    enc_name = urllib.parse.quote(name)
    enc_photo = urllib.parse.quote(photo.name)
    # 직원별 링크 파일과 공유 URL에는 한글 이름을 그대로 표시한다.
    # 실제 HTTP 요청 시 브라우저가 필요한 경우 자동으로 URL 인코딩한다.
    page_url = f'{BASE_URL}/cards/{name}/'
    og_url = f'{BASE_URL}/og/{urllib.parse.quote(name + "_og.png")}'

    s = template
    s = re.sub(r'<title>.*?</title>', f'<title>{html.escape(site_name)}</title>', s, count=1, flags=re.S)
    s = re.sub(r'<meta property="og:title"[^>]*>', f'<meta property="og:title" content="{html.escape(site_name)}">', s, count=1)
    s = re.sub(r'<meta property="og:image"[^>]*>', f'<meta property="og:image" content="{html.escape(og_url)}">', s, count=1)
    s = re.sub(r'<meta property="og:image:alt"[^>]*>', f'<meta property="og:image:alt" content="오토지니 {html.escape(name)} 디지털 명함">', s, count=1)

    # og:url이 없으면 추가
    if 'property="og:url"' not in s:
        s = s.replace('<meta property="og:type" content="website">', f'<meta property="og:type" content="website">\n  <meta property="og:url" content="{html.escape(page_url)}">')
    else:
        s = re.sub(r'<meta property="og:url"[^>]*>', f'<meta property="og:url" content="{html.escape(page_url)}">', s, count=1)

    # Kakao가 이미지 규격을 명확히 알 수 있게 추가
    if 'og:image:width' not in s:
        s = s.replace(f'<meta property="og:image" content="{html.escape(og_url)}">', f'<meta property="og:image" content="{html.escape(og_url)}">\n  <meta property="og:image:width" content="1200">\n  <meta property="og:image:height" content="600">')

    s = re.sub(r'<body\b[^>]*>', f'<body class="page-enter" data-static-card="true" data-profile-name="{html.escape(name)}" data-kakao-chat-url="{html.escape(kakao_chat_url)}">', s, count=1, flags=re.I)
    s = s.replace('href="./style.css"', 'href="../../style.css?v=20260930-entry5"')
    s = re.sub(r'src="(?:\./|\.\./\.\./)script\.js(?:\?v=[^"]*)?"', 'src="../../script.js?v=20260930-entry5"', s)

    s = s.replace('href="./style.css?v=20260930-entry5"', 'href="../../style.css?v=20260930-entry5"')
    s = s.replace('src="./script.js?v=20260930-entry5"', 'src="../../script.js?v=20260930-entry5"')

    s = s.replace('href="./favicon/autogenie-navy-48.png"', 'href="../../favicon/autogenie-navy-48.png"')
    s = s.replace('href="./favicon/autogenie-navy-180.png"', 'href="../../favicon/autogenie-navy-180.png"')
    s = s.replace('href="./favicon/autogenie-navy-16.png"', 'href="../../favicon/autogenie-navy-16.png"')
    s = s.replace('href="./favicon/autogenie-navy-32.png"', 'href="../../favicon/autogenie-navy-32.png"')

    # 회사소개 연결과 스타일 경로를 직원별 명함 위치에 맞춥니다.
    s = re.sub(r'href="(?:\./|\.\./\.\./)style\.css(?:\?v=[^"]*)?"', 'href="../../style.css?v=20261007-advisor-intro2"', s, count=1)
    s = s.replace('href="./company/index.html?from=main"', 'href="../../company/index.html?card=' + enc_name + '"')

    # profile image
    s = re.sub(
        r'(<img class="avatar" id="profilePhoto" )src="[^"]*" alt="[^"]*">',
        rf'\1src="../../sales_profiles/{enc_name}/{enc_photo}" alt="{html.escape(name)} 프로필 사진">',
        s,
        count=1
    )

    s = replace_id_text(s, 'profileName', html.escape(name))
    s = re.sub(r'<p class="position" id="profilePosition">.*?</p>', f'<p class="position" id="profilePosition">{html.escape(department)} <span class="divider">|</span> {html.escape(position)}</p>', s, count=1, flags=re.S)
    s = replace_id_text(s, 'profileCompany', html.escape(company))
    s = replace_id_text(s, 'phoneText', html.escape(format_phone_display(phone)))
    s = replace_id_text(s, 'emailText', html.escape(email))
    s = replace_id_text(s, 'affiliationText', html.escape(department))

    # 선택 입력: intro1, intro2... 가 있는 직원만 담당자 소개 섹션을 생성합니다.
    intro_paragraphs = []
    for i in range(1, 10):
        value = data.get(f'intro{i}', '').strip()
        if value:
            intro_paragraphs.append(value)

    if intro_paragraphs:
        intro_html = ['''
      <section class="advisor-intro" aria-labelledby="advisorIntroTitle">
        <div class="advisor-intro__heading">
          <h2 id="advisorIntroTitle">담당자 소개</h2>
        </div>
        <div class="advisor-intro__body">
''']
        for idx, paragraph in enumerate(intro_paragraphs):
            class_name = ' class="advisor-intro__hello"' if idx == 0 else ''
            intro_html.append(f'          <p{class_name}>{html.escape(paragraph)}</p>\n')
        intro_html.append('        </div>\n      </section>\n')
        intro_html = ''.join(intro_html)

        # 상담 버튼 바로 아래, 담당자 정보 위에 삽입합니다.
        s = s.replace(
            '    <section class="content">\n      <section class="info-section">',
            '    <section class="content">\n' + intro_html + '      <section class="info-section">',
            1
        )

    if phone_clean:
        s = re.sub(r'(<a class="contact-card contact-card--call" id="callLink" href=")[^"]*(")', rf'\1tel:{phone_clean}\2', s, count=1)
        s = re.sub(r'(<a class="contact-card contact-card--sms" id="smsLink" href=")[^"]*(")', rf'\1sms:{phone_clean}\2', s, count=1)
        s = re.sub(r'(<a id="phoneText" href=")[^"]*(")', rf'\1tel:{phone_clean}\2', s, count=1)
    else:
        # phone is optional: remove phone-only controls from generated static card.
        s = re.sub(r'\s*<a class="contact-card contact-card--call" id="callLink".*?</a>', '', s, count=1, flags=re.S)
        s = re.sub(r'\s*<a class="contact-card contact-card--sms" id="smsLink".*?</a>', '', s, count=1, flags=re.S)
        s = re.sub(
            r'\s*<div>\s*<dt>연락처</dt>\s*<dd><a id="phoneText".*?</a></dd>\s*</div>',
            '',
            s,
            count=1,
            flags=re.S
        )

    s = re.sub(r'(<a id="emailText" href=")[^"]*(")', rf'\1mailto:{html.escape(email)}\2', s, count=1)

    return s, page_url


def main():
    CARDS.mkdir(exist_ok=True)
    OG.mkdir(exist_ok=True)

    # 기존 자동생성 카드만 재생성
    for child in CARDS.iterdir():
        if child.is_dir():
            shutil.rmtree(child)

    template = TEMPLATE.read_text(encoding='utf-8')
    links = []

    for folder in sorted(SALES.iterdir(), key=lambda p: p.name):
        if not folder.is_dir():
            continue
        txt = folder / 'profile.txt'
        if not txt.exists():
            continue

        data = parse_profile(txt)
        name = data.get('name', folder.name).strip()
        photo = resolve_photo(folder, data, name)
        if not photo:
            print(f'[SKIP] {name}: photo not found')
            continue

        department = data.get('department', '').strip()
        position = data.get('position', '').strip()
        company = data.get('company', COMPANY_DEFAULT).strip() or COMPANY_DEFAULT

        make_og(photo, name, department, position, company, OG / f'{name}_og.png')
        card_html, page_url = build_card(template, folder, photo, data)
        card_dir = CARDS / name
        card_dir.mkdir(parents=True, exist_ok=True)
        (card_dir / 'index.html').write_text(card_html, encoding='utf-8')
        links.append((name, page_url))
        print(f'[DONE] {name} -> {page_url}')

    link_text = '직원별 디지털 명함 링크\n\n'
    for name, url in links:
        link_text += f'{name}\n{url}\n\n'
    (BASE / '직원별_링크.txt').write_text(link_text, encoding='utf-8')
    print(f'Completed: {len(links)} profile(s)')

if __name__ == '__main__':
    main()
