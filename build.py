"""Blog estático portátil: HTML, imágenes, RSS. Python 3.10+, sin dependencias."""
from pathlib import Path
from datetime import date
from html import escape as esc
from urllib.parse import urlsplit
import base64
import binascii
import hashlib
import json
import math
import os
import re
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
SITE = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
BASE = os.environ.get('BLOG_BASE_PATH', SITE['base_path']).rstrip('/')
SECTIONS = {'dibujos': 'Dibujos', 'escritos': 'Escritos', 'musica': 'Música'}
GALLERY_PAGE_SIZE = 8
MAX_IMAGES = 12
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_POST_IMAGE_BYTES = 15 * 1024 * 1024

def href(path=''):
    return BASE + '/' + path.lstrip('/')

def media_path(value):
    if not value:
        return ''
    if not isinstance(value, str) or '\\' in value or '..' in value.split('/'):
        raise ValueError('Ruta de archivo no válida: ' + str(value))
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or not value.startswith('assets/'):
        raise ValueError('Usa una ruta local que empiece por assets/: ' + value)
    path = ROOT / value
    if not path.is_file() or not path.resolve().is_relative_to((ROOT / 'assets').resolve()):
        raise ValueError('No se encuentra un archivo válido: ' + value)
    return href(value)

def embedded_image(value):
    if not value:
        return None
    if not isinstance(value, str) or len(value) > 17 * 1024 * 1024:
        raise ValueError('La imagen incluida supera los 12 MB.')
    match = re.fullmatch(r'data:image/(png|jpeg|webp|gif);base64,([A-Za-z0-9+/=\r\n]+)', value)
    if not match:
        raise ValueError('La imagen incluida no tiene un formato válido.')
    try:
        data = base64.b64decode(match[2].replace('\r', '').replace('\n', ''), validate=True)
    except binascii.Error as error:
        raise ValueError('La imagen incluida está incompleta o dañada.') from error
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError('Cada imagen debe ocupar entre 1 byte y 12 MB.')
    signatures = {'png': data.startswith(b'\x89PNG\r\n\x1a\n'), 'jpeg': data.startswith(b'\xff\xd8\xff'), 'gif': data.startswith((b'GIF87a', b'GIF89a')), 'webp': data.startswith(b'RIFF') and data[8:12] == b'WEBP'}
    if not signatures[match[1]]:
        raise ValueError('El contenido de la imagen no coincide con su formato.')
    extension = 'jpg' if match[1] == 'jpeg' else match[1]
    return 'media/' + hashlib.sha256(data).hexdigest()[:24] + '.' + extension, data

def post_images(p, filename):
    if 'images' in p:
        raw = p['images']
        if not isinstance(raw, list) or len(raw) > MAX_IMAGES:
            raise ValueError(f'{filename}: usa una lista de hasta {MAX_IMAGES} imágenes.')
    elif p.get('image_data') or p.get('image'):
        raw = [{'data': p.get('image_data', ''), 'path': p.get('image', ''), 'alt': p.get('image_alt', ''), 'caption': ''}]
    else:
        raw = []
    images, total = [], 0
    for i, image in enumerate(raw, 1):
        if not isinstance(image, dict):
            raise ValueError(f'{filename}: la imagen {i} no es válida.')
        alt, caption = image.get('alt', ''), image.get('caption', '')
        if not isinstance(alt, str) or not alt.strip() or not isinstance(caption, str):
            raise ValueError(f'{filename}: añade una descripción a la imagen {i}.')
        embedded = embedded_image(image.get('data', ''))
        url = href(embedded[0]) if embedded else media_path(image.get('path', ''))
        if not url:
            raise ValueError(f'{filename}: falta el archivo de la imagen {i}.')
        total += len(embedded[1]) if embedded else 0
        if total > MAX_POST_IMAGE_BYTES:
            raise ValueError(f'{filename}: las imágenes de la entrada superan los 15 MB.')
        images.append({'url': url, 'alt': alt.strip(), 'caption': caption.strip(), 'embedded': embedded})
    return images

def pretty_day(value):
    d = date.fromisoformat(value)
    months = 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split()
    return f'{d.day} de {months[d.month-1]} de {d.year}'

def load_posts():
    posts, seen = [], {}
    for path in sorted((ROOT / 'content').glob('*.json')):
        p = json.loads(path.read_text(encoding='utf-8-sig'))
        if p.get('draft', False):
            continue
        for key in ('slug', 'title', 'date', 'category'):
            if not isinstance(p.get(key), str) or not p[key].strip():
                raise ValueError(f'{path.name}: falta {key}.')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', p['slug']):
            raise ValueError(f'{path.name}: nombre de URL no válido.')
        if p['slug'] in seen:
            raise ValueError(f'URL repetida: {p["slug"]}. {seen[p["slug"]]} y {path.name} son la misma entrada. Reemplaza el archivo original; no subas una copia con (1).')
        seen[p['slug']] = path.name
        if p['category'] not in SECTIONS:
            raise ValueError(f'{path.name}: categoría no válida.')
        date.fromisoformat(p['date'])
        p.setdefault('text', '')
        if not isinstance(p['text'], str):
            raise ValueError(f'{path.name}: el texto no es válido.')
        p['images'] = post_images(p, path.name)
        if p['category'] != 'dibujos' and not p['text'].strip():
            raise ValueError(f'{path.name}: escribe el contenido de la entrada.')
        p['image_url'] = p['images'][0]['url'] if p['images'] else ''
        p['image_alt'] = p['images'][0]['alt'] if p['images'] else ''
        p['audio_url'] = media_path(p.get('audio', ''))
        excerpt = p.get('excerpt', '')
        if not isinstance(excerpt, str):
            raise ValueError(f'{path.name}: la descripción breve no es válida.')
        p['excerpt'] = excerpt or p['text'].split('\n')[0][:180]
        p['link'] = href('publicaciones/' + p['slug'] + '/')
        posts.append(p)
    return sorted(posts, key=lambda p: (p['date'], p['slug']), reverse=True)

def drill(cls='drill'):
    return f'<img class="{cls}" src="{href("assets/drill.svg")}" width="54" height="84" alt="" aria-hidden="true">'

def page(title, body, active='', description=None, canonical=''):
    links = [('Inicio', ''), ('Dibujos', 'dibujos/'), ('Escritos', 'escritos/'), ('Música', 'musica/')]
    nav = ''.join(f'<a href="{href(path)}"' + (' aria-current="page"' if active == path else '') + f'>{label}</a>' for label, path in links)
    desc = description or SITE['description']
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(SITE['title'])}</title><meta name="description" content="{esc(desc, quote=True)}"><meta name="color-scheme" content="light dark">
<link rel="canonical" href="{esc(SITE['url'] + href(canonical), quote=True)}">
<meta property="og:title" content="{esc(title, quote=True)}"><meta property="og:description" content="{esc(desc, quote=True)}"><meta property="og:type" content="website">
<link rel="icon" href="{href('assets/favicon.ico')}?v=2" sizes="16x16 32x32 48x48 64x64"><link rel="icon" type="image/png" sizes="192x192" href="{href('assets/blog-icon.png')}?v=2"><link rel="apple-touch-icon" href="{href('assets/blog-icon.png')}">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE['title'], quote=True)}" href="{href('feed.xml')}">
<link rel="stylesheet" href="{href('assets/style.css')}?v=4"><script src="{href('assets/site.js')}?v=3" defer></script></head>
<body><a class="skip" href="#contenido">Saltar al contenido</a><div class="topline" aria-hidden="true"></div>
<header class="header"><a class="brand" href="{href()}"><span class="brand-mark"><img src="{href('assets/blog-icon.jpg')}" width="50" height="50" alt=""></span><span>{esc(SITE['title'])}<small>CUADERNO PERSONAL</small></span></a><nav aria-label="Principal">{nav}</nav><button class="theme-button" id="theme" type="button" aria-label="Cambiar entre tema claro y oscuro">◐</button></header>
<main id="contenido">{body}</main><footer class="footer"><div class="footer-brand">{drill('footer-drill')}<div><strong>{esc(SITE['title'])}</strong><span>Dibujos, palabras y alguna canción.</span></div></div><div class="footer-links"><a href="{href('sobre-mi/')}">Sobre este espacio</a><a href="{href('feed.xml')}">RSS</a></div><small>© {esc(SITE['author'])} · Las obras pertenecen a su autor.</small></footer></body></html>'''

def save(path, text):
    dest = OUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(text.encode('utf-8'))

def meta(p):
    return f'<div class="meta"><span class="category">{SECTIONS[p["category"]]}</span><time datetime="{p["date"]}">{pretty_day(p["date"])}</time></div>'

def card(p):
    image = f'<a class="card-image" href="{p["link"]}"><img src="{esc(p["image_url"], quote=True)}" alt="{esc(p["image_alt"], quote=True)}" loading="lazy"></a>' if p['image_url'] else ''
    return f'<article class="entry" data-category="{p["category"]}" data-search="{esc(p["title"] + " " + p["excerpt"], quote=True)}">{image}<div class="entry-info">{meta(p)}<h3><a href="{p["link"]}">{esc(p["title"])}</a></h3><p>{esc(p["excerpt"])}</p><a class="read" href="{p["link"]}">Abrir publicación <span aria-hidden="true">↗</span></a></div></article>'

def listing(posts, category=None):
    selected = [p for p in posts if category is None or p['category'] == category]
    controls = '''<div class="tools"><div class="filters" role="group" aria-label="Filtrar publicaciones"><button type="button" data-filter="all" aria-pressed="true">Todo</button><button type="button" data-filter="dibujos" aria-pressed="false">Dibujos</button><button type="button" data-filter="escritos" aria-pressed="false">Escritos</button><button type="button" data-filter="musica" aria-pressed="false">Música</button></div><label class="search"><span class="sr-only">Buscar publicaciones</span><input id="search" type="search" placeholder="Buscar en el archivo"></label></div>''' if category is None else ''
    empty = '<div class="empty">' + drill() + '<h3>Una página por estrenar.</h3><p>Las publicaciones de esta sección aparecerán aquí.</p></div>'
    return controls + '<div class="entries">' + (''.join(card(p) for p in selected) if selected else empty) + '</div><p id="no-results" class="empty" hidden role="status">No hay publicaciones con esa búsqueda.</p>'

def gallery_url(number, category='dibujos'):
    return href(f'{category}/' if number == 1 else f'{category}/pagina/{number}/')

def pagination(number, count, category='dibujos'):
    if count <= 1:
        return ''
    pieces = [f'<a class="page-direction" href="{gallery_url(number-1, category)}" rel="prev">← Anterior</a>' if number > 1 else '<span class="page-direction disabled">← Anterior</span>']
    wanted = sorted({1, count} | set(range(max(1, number-2), min(count, number+2)+1)))
    last = 0
    for n in wanted:
        if last and n > last+1:
            pieces.append('<span class="ellipsis" aria-hidden="true">…</span>')
        pieces.append(f'<span class="page-number current" aria-current="page" aria-label="Página {n}">{n}</span>' if n == number else f'<a class="page-number" href="{gallery_url(n, category)}" aria-label="Página {n}">{n}</a>')
        last = n
    pieces.append(f'<a class="page-direction" href="{gallery_url(number+1, category)}" rel="next">Siguiente →</a>' if number < count else '<span class="page-direction disabled">Siguiente →</span>')
    return f'<nav class="pagination" aria-label="Páginas de {SECTIONS[category].lower()}">' + ''.join(pieces) + '</nav>'

def gallery_item(p, number):
    pictures = ''.join(f'<a class="gallery-image" href="{p["link"]}" aria-label="Abrir {esc(p["title"], quote=True)}, imagen {i}"><img src="{esc(im["url"], quote=True)}" alt="{esc(im["alt"], quote=True)}" loading="lazy" decoding="async"></a>' for i, im in enumerate(p['images'], 1))
    if not pictures:
        pictures = '<a class="gallery-missing" href="' + p['link'] + '">' + drill() + '<span>Ver publicación</span></a>'
    count = f'<span class="image-count">{len(p["images"]):02d} imágenes</span>' if len(p['images']) > 1 else ''
    return f'<article class="gallery-entry"><div class="gallery-heading"><span class="work-number">{number:03d}</span><div>{meta(p)}<h2><a href="{p["link"]}">{esc(p["title"])}</a></h2></div>{count}</div><div class="gallery-pictures">{pictures}</div><div class="gallery-caption"><p>{esc(p["excerpt"])}</p><a class="read" href="{p["link"]}">Ver publicación ↗</a></div></article>'

def gallery(posts, number, count):
    start = (number-1)*GALLERY_PAGE_SIZE
    selected = posts[start:start+GALLERY_PAGE_SIZE]
    intro = f'<section class="section-intro gallery-intro"><div><div class="eyebrow">01 / ARCHIVO VISUAL</div><h1>Dibujos<span class="dot">.</span></h1><p>Bocetos e ilustraciones. Baja para mirar, abre para leer.</p></div>{drill("section-drill")}</section>'
    stats = f'<div class="gallery-stats"><span>{len(posts):02d} publicaciones</span><span>Página {number} / {count}</span></div>'
    content = ''.join(gallery_item(p, len(posts)-start-i) for i, p in enumerate(selected))
    if not content:
        content = '<div class="empty">' + drill() + '<h3>Los primeros trazos van aquí.</h3></div>'
    return intro + '<div class="gallery-feed">' + stats + content + pagination(number, count) + '</div>'

def writing_item(p, number):
    paragraphs = ''.join('<p>' + esc(x).replace('\n', '<br>') + '</p>' for x in p['text'].strip().split('\n\n') if x.strip())
    pictures = ''.join(f'<figure><a class="gallery-image" href="{p["link"]}"><img src="{esc(im["url"], quote=True)}" alt="{esc(im["alt"], quote=True)}" loading="lazy"></a>' + (f'<figcaption>{esc(im["caption"])}</figcaption>' if im['caption'] else '') + '</figure>' for im in p['images'])
    return f'<article class="gallery-entry writing-entry"><div class="gallery-heading"><span class="work-number">{number:03d}</span><div>{meta(p)}<h2><a href="{p["link"]}">{esc(p["title"])}</a></h2></div></div><div class="post-images">{pictures}</div><div class="prose">{paragraphs}</div><a class="read" href="{p["link"]}">Abrir publicación ↗</a></article>'

def writings(posts, number, count):
    start = (number-1)*GALLERY_PAGE_SIZE
    selected = posts[start:start+GALLERY_PAGE_SIZE]
    intro = f'<section class="section-intro gallery-intro"><div><div class="eyebrow">02 / PALABRAS</div><h1>Escritos<span class="dot">.</span></h1><p>Pensamientos, relatos e ideas. Baja para seguir leyendo.</p></div>{drill("section-drill")}</section>'
    stats = f'<div class="gallery-stats"><span>{len(posts):02d} publicaciones</span><span>Página {number} / {count}</span></div>'
    content = ''.join(writing_item(p, len(posts)-start-i) for i, p in enumerate(selected))
    if not content:
        content = '<div class="empty">' + drill() + '<h3>Las primeras palabras van aquí.</h3></div>'
    return intro + '<div class="gallery-feed writing-feed">' + stats + content + pagination(number, count, 'escritos') + '</div>'

def adjacent(p, drawings):
    index = next(i for i, item in enumerate(drawings) if item['slug'] == p['slug'])
    older = drawings[index+1] if index+1 < len(drawings) else None
    newer = drawings[index-1] if index > 0 else None
    def link(item, label, rel):
        if item:
            return f'<a class="post-adjacent {rel}" href="{item["link"]}" rel="{rel}"><small>{label}</small><span>{esc(item["title"])}</span></a>'
        return f'<span class="post-adjacent disabled"><small>{label}</small><span>No hay más publicaciones</span></span>'
    return f'<nav class="post-navigation" aria-label="Navegar entre {SECTIONS[p["category"]].lower()}">' + link(older, '← Anterior', 'prev') + link(newer, 'Siguiente →', 'next') + '</nav>'

def article(p, posts):
    paragraphs = ''.join('<p>' + esc(x).replace('\n', '<br>') + '</p>' for x in p['text'].strip().split('\n\n') if x.strip())
    pictures = ''.join(f'<figure><img src="{esc(im["url"], quote=True)}" alt="{esc(im["alt"], quote=True)}"' + (' loading="lazy"' if i else '') + '>' + (f'<figcaption>{esc(im["caption"])}</figcaption>' if im['caption'] else '') + '</figure>' for i, im in enumerate(p['images']))
    audio = f'<div class="audio"><p>Escucha esta composición</p><audio controls preload="metadata" src="{esc(p["audio_url"], quote=True)}">Tu navegador no admite audio.</audio><a href="{esc(p["audio_url"], quote=True)}" download>Descargar audio</a></div>' if p['audio_url'] else ''
    navigation = adjacent(p, [item for item in posts if item['category'] == p['category']]) if p['category'] in ('dibujos', 'escritos') else '<div class="post-end">' + drill() + '</div>'
    return f'<article class="post{ " artwork-post" if p["category"] == "dibujos" else ""}"><a class="back" href="{href(p["category"] + "/")}">← Volver a {SECTIONS[p["category"]].lower()}</a>{meta(p)}<h1>{esc(p["title"])}</h1><p class="post-lead">{esc(p["excerpt"])}</p><div class="post-images">{pictures}</div><div class="prose">{paragraphs}</div>{audio}{navigation}</article>'

def build():
    posts = load_posts()
    drawings = [p for p in posts if p['category'] == 'dibujos']
    if OUT.exists():
        if OUT.resolve() != ROOT.resolve() / 'dist' or OUT.is_symlink():
            raise ValueError('Directorio de salida inseguro.')
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets')
    for p in posts:
        for image in p['images']:
            if image['embedded']:
                path, data = image['embedded']
                dest = OUT / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
    hero = f'''<section class="hero"><div class="hero-copy"><div class="eyebrow">DIBUJOS / PALABRAS / MÚSICA</div><h1>Un pequeño<br>archivo <em>personal.</em></h1><p>Bocetos, ideas sueltas y cosas que voy creando.</p><a class="hero-link" href="{href('dibujos/')}">Explorar los dibujos <span aria-hidden="true">↗</span></a></div><div class="hero-sign" aria-hidden="true">{drill('hero-drill')}</div></section><section class="latest" id="publicaciones"><div class="section-heading"><h2>Lo más reciente</h2><span>EL CUADERNO, SIN PRISA.</span></div>'''
    save('index.html', page('Inicio', hero + listing(posts) + '</section>'))
    count = max(1, math.ceil(len(drawings)/GALLERY_PAGE_SIZE))
    gallery_paths = []
    for number in range(1, count+1):
        path = 'dibujos/' if number == 1 else f'dibujos/pagina/{number}/'
        gallery_paths.append(path)
        save(path + 'index.html', page('Dibujos' + (f' · Página {number}' if number > 1 else ''), gallery(drawings, number, count), 'dibujos/', canonical=path))
    written = [p for p in posts if p['category'] == 'escritos']
    writing_count = max(1, math.ceil(len(written)/GALLERY_PAGE_SIZE))
    for number in range(1, writing_count+1):
        path = 'escritos/' if number == 1 else f'escritos/pagina/{number}/'
        gallery_paths.append(path)
        save(path + 'index.html', page('Escritos' + (f' · Página {number}' if number > 1 else ''), writings(written, number, writing_count), 'escritos/', canonical=path))
    intros = {'musica': ('03 / SONIDOS', 'Melodías y composiciones para escuchar un momento.')}
    for key, (label, text) in intros.items():
        body = f'<section class="section-intro"><div class="eyebrow">{label}</div><h1>{SECTIONS[key]}<span class="dot">.</span></h1><p>{text}</p></section>' + listing(posts, key)
        save(key + '/index.html', page(SECTIONS[key], body, key + '/', canonical=key + '/'))
    for p in posts:
        path = 'publicaciones/' + p['slug'] + '/'
        save(path + 'index.html', page(p['title'], article(p, posts), p['category'] + '/', p['excerpt'], path))
    save('sobre-mi/index.html', page('Sobre este espacio', '<section class="post"><div class="eyebrow">UN CUADERNO PERSONAL</div><h1>Sobre este espacio<span class="dot">.</span></h1><div class="prose"><p>Un blog personal para reunir mis bocetos, dibujos, pensamientos, música y cosas en general.</p><p>Aquí hay lugar tanto para una obra terminada como para una idea que apenas empieza.</p></div></section>', canonical='sobre-mi/'))
    save('404.html', page('Página no encontrada', f'<section class="post"><div class="eyebrow">404 / FUERA DEL ARCHIVO</div><h1>Esta página se perdió.</h1><a class="button" href="{href()}">Volver al inicio</a></section>'))
    save('.nojekyll', '')
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for tag, value in [('title', SITE['title']), ('link', SITE['url'] + href()), ('description', SITE['description']), ('language', 'es')]:
        ET.SubElement(channel, tag).text = value
    for p in posts:
        item = ET.SubElement(channel, 'item')
        for tag, value in [('title', p['title']), ('link', SITE['url'] + p['link']), ('guid', SITE['url'] + p['link']), ('description', p['excerpt'])]:
            ET.SubElement(item, tag).text = value
    save('feed.xml', '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(rss, encoding='unicode'))
    sitemap = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in ['', 'musica/', 'sobre-mi/'] + gallery_paths + ['publicaciones/' + p['slug'] + '/' for p in posts]:
        ET.SubElement(ET.SubElement(sitemap, 'url'), 'loc').text = SITE['url'] + href(path)
    save('sitemap.xml', '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(sitemap, encoding='unicode'))
    save('robots.txt', f'User-agent: *\nAllow: /\nDisallow: {href("editor/")}\nSitemap: {SITE["url"]}{href("sitemap.xml")}\n')
    print(f'Blog generado: {len(posts)} publicaciones; {len(drawings)} dibujos; {count} paginas de galeria. Salida: {OUT}')

if __name__ == '__main__':
    build()
