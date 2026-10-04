"""Closed, provider-free input validation, including untrusted image containers."""
import json
from pathlib import Path
import re
import struct
from urllib.parse import urlsplit

LOCALES = ('en', 'es-419', 'zh-Hans')
SLUG = re.compile(r'[a-z0-9][a-z0-9-]{2,79}\Z')
BLOCK = re.compile(r'b-[0-9a-f]{8}\Z')
NOTE = re.compile(r'fn-[0-9a-f]{8}\Z')

def slug(value):
    if not isinstance(value, str) or not SLUG.fullmatch(value):
        raise ValueError('El nombre de la publicación no es válido.')
    return value

def locale(value):
    if value not in LOCALES: raise ValueError('El idioma no está disponible.')
    return value

def closed(obj, required, optional=()):
    if not isinstance(obj, dict) or not set(required) <= obj.keys() or obj.keys() - set(required) - set(optional):
        raise ValueError('La estructura del documento no es válida.')

def text(value):
    if not isinstance(value, str): raise ValueError('Se esperaba texto.')

def url(value):
    text(value)
    parsed = urlsplit(value)
    if any(ord(c) < 32 for c in value) or '\\' in value: raise ValueError('El enlace no es válido.')
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password:
        return
    if value.startswith('/') and not value.startswith('//') and not parsed.scheme and not parsed.netloc:
        return
    raise ValueError('Usa un enlace HTTPS o una ruta del sitio.')

def inlines(nodes, refs=None, text_only=False, depth=0):
    if not isinstance(nodes, list) or depth > 8: raise ValueError('El texto no es válido.')
    for node in nodes:
        if not isinstance(node, dict): raise ValueError('El texto no es válido.')
        kind = node.get('t')
        if kind == 'text':
            closed(node, ('t', 'v'), ('marks',)); text(node['v'])
            if not isinstance(node.get('marks', []), list) or any(x not in ('em', 'strong') for x in node.get('marks', [])):
                raise ValueError('El formato de texto no es válido.')
        elif not text_only and kind in ('link', 'lang'):
            attr = 'href' if kind == 'link' else 'lang'
            closed(node, ('t', attr, 'c'))
            if kind == 'link': url(node[attr])
            elif not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]+)*', node[attr]): raise ValueError('El idioma de la cita no es válido.')
            inlines(node['c'], refs, True, depth + 1)
        elif not text_only and kind == 'fn':
            closed(node, ('t', 'id'))
            if not NOTE.fullmatch(node['id']): raise ValueError('La nota no es válida.')
            if refs is not None: refs.add(node['id'])
        elif not text_only and kind == 'cite':
            closed(node, ('t', 'key'), ('locator',)); text(node['key'])
            if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', node['key']): raise ValueError('La fuente no es válida.')
            if 'locator' in node: text(node['locator'])
        else: raise ValueError('Este tipo de contenido no está permitido.')

def validate_doc(doc, loc):
    locale(loc); closed(doc, ('schema', 'locale', 'title', 'dek', 'blocks', 'footnotes'))
    if doc['schema'] != 'fcmo-essay-doc-v1' or doc['locale'] != loc: raise ValueError('El documento pertenece a otro idioma.')
    text(doc['title']); text(doc['dek'])
    if not isinstance(doc['blocks'], list) or not isinstance(doc['footnotes'], dict): raise ValueError('El documento no es válido.')
    ids, refs = set(), set()
    for block in doc['blocks']:
        closed(block, ('id', 'type'), ('content', 'items', 'attrs'))
        if not BLOCK.fullmatch(block['id']) or block['id'] in ids: raise ValueError('Hay párrafos duplicados o no válidos.')
        ids.add(block['id']); kind = block['type']; attrs = block.get('attrs', {})
        if kind in ('p', 'h2', 'h3', 'pullquote', 'blockquote'):
            if 'items' in block: raise ValueError('La estructura del párrafo no es válida.')
            closed(attrs, (), ('cite',) if kind == 'blockquote' else ())
            if 'cite' in attrs: text(attrs['cite'])
            inlines(block.get('content', []), refs)
        elif kind in ('ul', 'ol'):
            closed(attrs, ());
            if not isinstance(block.get('items'), list) or 'content' in block: raise ValueError('La lista no es válida.')
            for item in block['items']: inlines(item, refs)
        elif kind == 'figure':
            closed(attrs, ('fig',)); text(attrs['fig'])
            if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', attrs['fig']): raise ValueError('La figura no es válida.')
        elif kind == 'evidence':
            closed(attrs, ('class', 'confidence', 'limits'))
            if attrs['class'] not in ('A', 'B', 'C', 'D'): raise ValueError('La clase de evidencia no es válida.')
            text(attrs['confidence']); inlines(attrs['limits'], refs)
        elif kind == 'hr': closed(attrs, ())
        else: raise ValueError('Este bloque no está permitido.')
        if kind in ('figure', 'evidence', 'hr') and (block.get('content') or block.get('items')):
            raise ValueError('El bloque contiene campos no permitidos.')
    for key, value in doc['footnotes'].items():
        if not NOTE.fullmatch(key): raise ValueError('La nota no es válida.')
        inlines(value)
    if refs - doc['footnotes'].keys(): raise ValueError('Una nota al pie no tiene contenido.')
    return doc

def validate_sources(value):
    if not isinstance(value, list): raise ValueError('Las fuentes no son válidas.')
    keys = set()
    for source in value:
        closed(source, ('key', 'title', 'author', 'publisher', 'date', 'url', 'accessed'), ('locator', 'evidence_class', 'note'))
        for key, val in source.items(): text(val)
        url(source['url'])
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', source['key']) or source['key'] in keys: raise ValueError('Hay fuentes duplicadas.')
        keys.add(source['key'])
        if source.get('evidence_class', 'A') not in 'ABCD': raise ValueError('La clase de fuente no es válida.')
    return value

def validate_figures(value):
    if not isinstance(value, dict): raise ValueError('Las figuras no son válidas.')
    for key, fig in value.items():
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', key): raise ValueError('La figura no es válida.')
        closed(fig, ('file', 'width', 'height', 'credit', 'licence', 'alt', 'caption'), ('licence_url', 'source_page'))
        if not re.fullmatch(r'figures/[a-zA-Z0-9_-]+\.webp', fig['file']): raise ValueError('El archivo de figura no es válido.')
        for size in ('width', 'height'):
            if type(fig[size]) is not int or not 0 < fig[size] <= 8000: raise ValueError('La figura es demasiado grande.')
        for field in ('credit', 'licence'): text(fig[field])
        for field in ('alt', 'caption'):
            closed(fig[field], (), LOCALES)
            for val in fig[field].values(): text(val)
        for field in ('licence_url', 'source_page'):
            if field in fig: url(fig[field])
    return value

def validate_webp(data):
    if len(data) > 15 * 1024 * 1024 or len(data) < 20 or data[:4] != b'RIFF' or data[8:12] != b'WEBP':
        raise ValueError('Sube una imagen WebP de hasta 15 MB.')
    if struct.unpack('<I', data[4:8])[0] != len(data) - 8: raise ValueError('La imagen está incompleta.')
    pos, dimensions, image = 12, None, False
    while pos < len(data):
        if pos + 8 > len(data): raise ValueError('La imagen está incompleta.')
        kind, size = data[pos:pos+4], struct.unpack('<I', data[pos+4:pos+8])[0]
        chunk = data[pos+8:pos+8+size]
        if len(chunk) != size: raise ValueError('La imagen está incompleta.')
        if kind in (b'EXIF', b'XMP ', b'ICCP', b'ANIM', b'ANMF'):
            raise ValueError('La imagen conserva metadatos o animación; vuelve a exportarla.')
        if kind == b'VP8X':
            if size != 10 or chunk[0] & 0x2e: raise ValueError('La imagen conserva metadatos o animación.')
            dimensions = (1+int.from_bytes(chunk[4:7], 'little'), 1+int.from_bytes(chunk[7:10], 'little'))
        elif kind == b'VP8 ':
            if size < 10 or chunk[3:6] != b'\x9d\x01\x2a': raise ValueError('La imagen no es válida.')
            dimensions = (int.from_bytes(chunk[6:8], 'little') & 0x3fff, int.from_bytes(chunk[8:10], 'little') & 0x3fff); image = True
        elif kind == b'VP8L':
            if size < 5 or chunk[0] != 0x2f: raise ValueError('La imagen no es válida.')
            bits = int.from_bytes(chunk[1:5], 'little')
            dimensions = ((bits & 0x3fff)+1, ((bits >> 14) & 0x3fff)+1); image = True
        elif kind != b'ALPH': raise ValueError('La imagen contiene una sección no permitida.')
        pos += 8 + size + (size % 2)
    if pos != len(data) or not image or not dimensions or not all(0 < x <= 8000 for x in dimensions):
        raise ValueError('La imagen no es válida o supera 8000 píxeles.')
    return dimensions

def plain_text(doc):
    values = []
    def visit(node):
        if isinstance(node, dict):
            if node.get('t') == 'text': values.append(node['v'])
            for k in ('content', 'items', 'c'): visit(node.get(k, []))
        elif isinstance(node, list):
            for child in node: visit(child)
    for block in doc['blocks']: visit(block)
    return ' '.join(values)
