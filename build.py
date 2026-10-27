"""Genera un blog HTML portátil. Solo requiere Python 3.10 o posterior."""
from pathlib import Path
from datetime import date
from html import escape as esc
from urllib.parse import urlsplit
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
import base64
import binascii
import hashlib

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
SITE = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
BASE = os.environ.get('BLOG_BASE_PATH', SITE['base_path']).rstrip('/')
SECTIONS = {'dibujos': 'Dibujos', 'escritos': 'Escritos', 'musica': 'Música'}

def href(path=''):
    return BASE + '/' + path.lstrip('/')

def media_path(value):
    """Solo medios locales: el blog no depende de servicios de terceros."""
    if not value:
        return ''
    if not isinstance(value, str) or '\\' in value or '..' in value.split('/'):
        raise ValueError('Ruta de archivo no válida: ' + str(value))
    if urlsplit(value).scheme or urlsplit(value).netloc or not value.startswith('assets/'):
        raise ValueError('Usa una ruta local que empiece por assets/: ' + value)
    if not (ROOT / value).is_file():
        raise ValueError('No se encuentra el archivo: ' + value)
    return href(value)

def embedded_image(value):
    if not value:
        return None
    if not isinstance(value, str) or len(value) > 17 * 1024 * 1024:
        raise ValueError('La imagen incluida supera el tamaño permitido (12 MB).')
    match = re.fullmatch(r'data:image/(png|jpeg|webp|gif);base64,([A-Za-z0-9+/=\r\n]+)', value)
    if not match:
        raise ValueError('La imagen incluida no tiene un formato válido.')
    try:
        data = base64.b64decode(match[2].replace('\r', '').replace('\n', ''), validate=True)
    except binascii.Error as error:
        raise ValueError('La imagen incluida está incompleta o dañada.') from error
    if not data or len(data) > 12 * 1024 * 1024:
        raise ValueError('La imagen debe ocupar entre 1 byte y 12 MB.')
    valid = {
        'png': data.startswith(b'\x89PNG\r\n\x1a\n'),
        'jpeg': data.startswith(b'\xff\xd8\xff'),
        'gif': data.startswith((b'GIF87a', b'GIF89a')),
        'webp': data.startswith(b'RIFF') and data[8:12] == b'WEBP',
    }
    if not valid[match[1]]:
        raise ValueError('El contenido de la imagen no coincide con su formato.')
    extension = 'jpg' if match[1] == 'jpeg' else match[1]
    path = 'media/' + hashlib.sha256(data).hexdigest()[:24] + '.' + extension
    return path, data

def pretty_day(value):
    d = date.fromisoformat(value)
    months = 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split()
    return f'{d.day} de {months[d.month-1]} de {d.year}'

def load_posts():
    posts = []
    seen = set()
    for path in sorted((ROOT / 'content').glob('*.json')):
        p = json.loads(path.read_text(encoding='utf-8-sig'))
        if p.get('draft', False):
            continue
        for key in ('slug', 'title', 'date', 'category', 'text'):
            if not isinstance(p.get(key), str) or not p[key].strip():
                raise ValueError(f'{path.name}: falta {key}')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', p['slug']):
            raise ValueError(f'{path.name}: nombre de URL no válido')
        if p['slug'] in seen:
            raise ValueError('URL repetida: ' + p['slug'])
        seen.add(p['slug'])
        if p['category'] not in SECTIONS:
            raise ValueError(f'{path.name}: categoría no válida')
        date.fromisoformat(p['date'])
        p['embedded_image'] = embedded_image(p.get('image_data', ''))
        p['image_url'] = href(p['embedded_image'][0]) if p['embedded_image'] else media_path(p.get('image', ''))
        p['audio_url'] = media_path(p.get('audio', ''))
        if p['image_url'] and not p.get('image_alt', '').strip():
            raise ValueError(f'{path.name}: añade una descripción de la imagen')
        p['excerpt'] = p.get('excerpt') or p['text'].split('\n')[0][:180]
        p['link'] = href('publicaciones/' + p['slug'] + '/')
        posts.append(p)
    return sorted(posts, key=lambda p: (p['date'], p['slug']), reverse=True)

def page(title, body, active='', description=None, canonical=''):
    links = [('Inicio', ''), ('Dibujos', 'dibujos/'), ('Escritos', 'escritos/'), ('Música', 'musica/')]
    nav = ''.join(f'<a href="{esc(href(path), quote=True)}"' + (' aria-current="page"' if active == path else '') + f'>{label}</a>' for label, path in links)
    desc = description or SITE['description']
    canonical_tag = f'<link rel="canonical" href="{esc(SITE["url"] + href(canonical), quote=True)}">'
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(SITE['title'])}</title><meta name="description" content="{esc(desc, quote=True)}">
<meta name="color-scheme" content="light dark">{canonical_tag}
<meta property="og:title" content="{esc(title, quote=True)}"><meta property="og:description" content="{esc(desc, quote=True)}"><meta property="og:type" content="website">
<link rel="icon" type="image/svg+xml" href="{href('assets/favicon.svg')}">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE['title'], quote=True)}" href="{href('feed.xml')}">
<link rel="stylesheet" href="{href('assets/style.css')}"><script src="{href('assets/site.js')}" defer></script></head>
<body><a class="skip" href="#contenido">Saltar al contenido</a>
<header class="header"><a class="brand" href="{href()}"><span class="brand-mark" aria-hidden="true">b.</span><span>{esc(SITE['title'])}<small>un cuaderno personal</small></span></a>
<nav aria-label="Principal">{nav}</nav><button class="theme-button" id="theme" type="button" aria-label="Cambiar entre tema claro y oscuro">◐</button></header>
<main id="contenido">{body}</main>
<footer class="footer"><div><strong>{esc(SITE['title'])}</strong><span>Dibujos, palabras y alguna canción.</span></div><div><a href="{href('sobre-mi/')}">Sobre este espacio</a><a href="{href('feed.xml')}">RSS</a></div><small>© {esc(SITE['author'])} · Las obras pertenecen a su autor.</small></footer></body></html>'''

def save(path, text):
    dest = OUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding='utf-8')

def card(p):
    image = f'<a class="card-image" href="{esc(p["link"], quote=True)}"><img src="{esc(p["image_url"], quote=True)}" alt="{esc(p.get("image_alt", ""), quote=True)}" loading="lazy"></a>' if p['image_url'] else ''
    return f'''<article class="entry" data-category="{p['category']}" data-search="{esc(p['title'] + ' ' + p['excerpt'], quote=True)}">{image}<div class="entry-info"><div class="meta"><span class="category">{SECTIONS[p['category']]}</span><time datetime="{p['date']}">{pretty_day(p['date'])}</time></div><h3><a href="{p['link']}">{esc(p['title'])}</a></h3><p>{esc(p['excerpt'])}</p><a class="read" href="{p['link']}">Abrir publicación <span aria-hidden="true">↗</span></a></div></article>'''

def listing(posts, category=None):
    selected = [p for p in posts if category is None or p['category'] == category]
    controls = '''<div class="tools"><div class="filters" role="group" aria-label="Filtrar publicaciones"><button type="button" data-filter="all" aria-pressed="true">Todo</button><button type="button" data-filter="dibujos" aria-pressed="false">Dibujos</button><button type="button" data-filter="escritos" aria-pressed="false">Escritos</button><button type="button" data-filter="musica" aria-pressed="false">Música</button></div><label class="search"><span class="sr-only">Buscar publicaciones</span><input id="search" type="search" placeholder="Buscar en el cuaderno…"></label></div>''' if category is None else ''
    empty = '<div class="empty"><span aria-hidden="true">✳</span><h3>Una página por estrenar.</h3><p>Las nuevas publicaciones de esta sección aparecerán aquí.</p></div>'
    cards = ''.join(card(p) for p in selected) if selected else empty
    return controls + f'<div class="entries">{cards}</div><p id="no-results" class="empty" hidden role="status">No hay publicaciones con esa búsqueda.</p>'

def article(p):
    paragraphs = ''.join('<p>' + esc(x).replace('\n', '<br>') + '</p>' for x in p['text'].strip().split('\n\n') if x.strip())
    image = f'<figure><img src="{esc(p["image_url"], quote=True)}" alt="{esc(p.get("image_alt", ""), quote=True)}"><figcaption>{esc(p.get("image_alt", ""))}</figcaption></figure>' if p['image_url'] else ''
    audio = f'<div class="audio"><p>Escucha esta composición</p><audio controls preload="metadata" src="{esc(p["audio_url"], quote=True)}">Tu navegador no admite audio.</audio><a href="{esc(p["audio_url"], quote=True)}" download>Descargar audio</a></div>' if p['audio_url'] else ''
    return f'''<article class="post"><a class="back" href="{href(p['category'] + '/')}">← Volver a {SECTIONS[p['category']].lower()}</a><div class="meta"><span class="category">{SECTIONS[p['category']]}</span><time datetime="{p['date']}">{pretty_day(p['date'])}</time></div><h1>{esc(p['title'])}</h1><p class="post-lead">{esc(p['excerpt'])}</p>{image}<div class="prose">{paragraphs}</div>{audio}<div class="post-end">✳</div></article>'''

def build():
    posts = load_posts()
    # Solo se limpia el directorio de salida fijo dentro de este proyecto.
    if OUT.exists():
        if OUT.resolve() != ROOT.resolve() / 'dist' or OUT.is_symlink():
            raise ValueError('Directorio de salida inseguro')
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / 'assets', OUT / 'assets')
    for p in posts:
        if p['embedded_image']:
            path, data = p['embedded_image']
            dest = OUT / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    hero = '''<section class="hero"><div class="eyebrow"><span></span> ARCHIVO PERSONAL / EN CONSTRUCCIÓN</div><h1>Cosas que dibujo.<br>Ideas que <em>se quedan.</em></h1><div class="hero-bottom"><p>Un lugar para los trazos, los pensamientos<br class="desktop-break"> y la música que aparece entre ellos.</p><a href="#publicaciones">Explorar el cuaderno <span aria-hidden="true">↓</span></a></div><span class="hero-star" aria-hidden="true">✳</span></section><section class="latest" id="publicaciones"><div class="section-heading"><h2>Entre páginas</h2><span>El archivo, sin prisa.</span></div>'''
    save('index.html', page('Inicio', hero + listing(posts) + '</section>'))
    intros = {'dibujos': 'Bocetos, trazos y dibujos terminados. Un espacio para mirar con calma.', 'escritos': 'Pensamientos, relatos e ideas que encontraron palabras.', 'musica': 'Melodías y composiciones para escuchar un momento.'}
    for key, label in SECTIONS.items():
        body = f'<section class="section-intro"><div class="eyebrow">DEL CUADERNO</div><h1>{label}<span class="dot">.</span></h1><p>{intros[key]}</p></section>' + listing(posts, key)
        save(key + '/index.html', page(label, body, key + '/', canonical=key + '/'))
    for p in posts:
        path = 'publicaciones/' + p['slug'] + '/'
        save(path + 'index.html', page(p['title'], article(p), p['category'] + '/', p['excerpt'], path))
    save('sobre-mi/index.html', page('Sobre este espacio', '<section class="post"><div class="eyebrow">UN PEQUEÑO RINCÓN EN INTERNET</div><h1>Sobre este espacio<span class="dot">.</span></h1><div class="prose"><p>Un cuaderno personal para reunir dibujos, pensamientos y música. Aquí hay lugar tanto para una obra terminada como para una idea que apenas empieza.</p><p>Este sitio está hecho con archivos propios. Sus páginas y sus obras pueden conservarse y trasladarse a otro alojamiento.</p></div></section>', canonical='sobre-mi/'))
    save('404.html', page('Página no encontrada', f'<section class="post"><div class="eyebrow">404</div><h1>Esta página se perdió.</h1><p>Puede que el enlace haya cambiado.</p><a class="button" href="{href()}">Volver al cuaderno</a></section>'))
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
    for path in ['', 'dibujos/', 'escritos/', 'musica/', 'sobre-mi/'] + ['publicaciones/' + p['slug'] + '/' for p in posts]:
        ET.SubElement(ET.SubElement(sitemap, 'url'), 'loc').text = SITE['url'] + href(path)
    save('sitemap.xml', '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(sitemap, encoding='unicode'))
    save('robots.txt', f'User-agent: *\nAllow: /\nDisallow: {href("editor/")}\nSitemap: {SITE["url"]}{href("sitemap.xml")}\n')
    print(f'Blog generado: {len(posts)} publicaciones. Salida: {OUT}')

if __name__ == '__main__':
    build()
