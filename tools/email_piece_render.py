"""Render the closed, published essay document as HTML and plain-text email."""
import json
import re
from urllib.parse import urljoin, urlsplit

from tools.email_render import EMAIL_COPY, PAPER_NAME, RenderedEmail, email_escape as e

COPY = {
    'en': ('By', 'Read on the web', 'Notes', 'Sources'),
    'es-419': ('Por', 'Leer en la web', 'Notas', 'Fuentes'),
    'zh-Hans': ('作者', '在线阅读', '注释', '来源'),
}
PREFIX = {'en': '', 'es-419': 'es/', 'zh-Hans': 'zh/'}


def safe_url(value, site_url):
    if not isinstance(value, str) or re.search(r'[\s\\{}]', value):
        raise ValueError('invalid_piece_link')
    if value.startswith('/') and not value.startswith('//'):
        value = urljoin(site_url + '/', value)
    parts = urlsplit(value)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        raise ValueError('invalid_piece_link')
    return value


def piece_url(piece, locale, site_url):
    if locale not in PREFIX or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', piece.get('slug', '')):
        raise ValueError('invalid_piece_slug_or_locale')
    return safe_url(site_url.rstrip('/') + '/' + PREFIX[locale] + 'cartas/' + piece['slug'] + '/', site_url)


def render(piece, *, locale, site_url, postal_address, preferences_url=None, unsubscribe_url=None):
    if locale not in COPY or piece.get('schema') != 'fcmo-piece-v1' or piece.get('kind') not in ('letter', 'essay', 'note'):
        raise ValueError('invalid_email_piece')
    if piece.get('status') != 'published': raise ValueError('piece_not_published')
    if 'fcmo group' in json.dumps(piece, ensure_ascii=False).casefold():
        raise ValueError('forbidden_email_brand')
    if not postal_address.strip(): raise ValueError('postal_address_required')
    doc = piece.get('docs', {}).get(locale, {})
    if (doc.get('schema') != 'fcmo-essay-doc-v1' or doc.get('locale') != locale
        or set(doc) != {'schema', 'locale', 'title', 'dek', 'blocks', 'footnotes'}
        or not isinstance(doc['title'], str) or not doc['title'].strip()
        or not isinstance(doc['dek'], str) or not isinstance(doc['blocks'], list) or not doc['blocks']
        or not isinstance(doc['footnotes'], dict)):
        raise ValueError('invalid_piece_document')
    authors = piece.get('authors', [])
    if not authors or any(not isinstance(a.get('name'), str) or not a['name'].strip() for a in authors):
        raise ValueError('piece_byline_required')
    byline = ', '.join(a['name'] for a in authors)
    by, read, notes_label, sources_label = COPY[locale]
    web = piece_url(piece, locale, site_url)
    sources = {s['key']: s for s in piece.get('sources', [])}
    if len(sources) != len(piece.get('sources', [])): raise ValueError('duplicate_piece_source')
    numbers, reference_count = {}, {}

    def inline(nodes):
        if not isinstance(nodes, list): raise ValueError('invalid_piece_inline')
        html, text = [], []
        for node in nodes:
            if not isinstance(node, dict): raise ValueError('invalid_piece_inline')
            kind = node.get('t')
            if kind == 'text':
                if set(node) - {'t', 'v', 'marks'} or not isinstance(node.get('v'), str):
                    raise ValueError('invalid_piece_text')
                value = e(node['v']); marks = node.get('marks', [])
                if not isinstance(marks, list) or any(m not in ('em', 'strong') for m in marks):
                    raise ValueError('invalid_piece_marks')
                for mark in marks: value = f'<{mark}>{value}</{mark}>'
                html.append(value); text.append(node['v'])
            elif kind in ('link', 'lang'):
                fields = {'t', 'href', 'c'} if kind == 'link' else {'t', 'lang', 'c'}
                if set(node) != fields: raise ValueError('invalid_piece_inline')
                child, plain = inline(node['c'])
                if kind == 'link':
                    url = safe_url(node['href'], site_url)
                    html.append(f'<a href="{e(url)}" style="color:#a9340e">{child}</a>')
                    text.append(f'{plain} ({url})')
                else:
                    if node['lang'] not in COPY: raise ValueError('invalid_quote_locale')
                    html.append(f'<span lang="{node["lang"]}" translate="no">{child}</span>'); text.append(plain)
            elif kind == 'fn':
                fid = node.get('id', '')
                if set(node) != {'t', 'id'} or not re.fullmatch(r'fn-[0-9a-f]{8}', fid) or fid not in doc['footnotes']:
                    raise ValueError('missing_or_invalid_piece_endnote')
                number = numbers.setdefault(fid, len(numbers) + 1)
                reference_count[fid] = reference_count.get(fid, 0) + 1
                ref = f'note-reference-{number}-{reference_count[fid]}'
                html.append(f'<sup id="{ref}"><a href="#endnote-{number}">{number}</a></sup>')
                text.append(f'[{number}]')
            elif kind == 'cite':
                if set(node) - {'t', 'key', 'locator'} or node.get('key') not in sources:
                    raise ValueError('missing_piece_citation_source')
                source = sources[node['key']]; url = safe_url(source['url'], site_url)
                label = source['title'] + (', ' + node['locator'] if node.get('locator') else '')
                html.append(f'<cite><a href="{e(url)}" style="color:#a9340e">{e(label)}</a></cite>')
                text.append(f'{label} ({url})')
            else: raise ValueError('unsupported_piece_inline')
        return ''.join(html), ''.join(text)

    body, plain_body, block_ids = [], [], set()
    for block in doc['blocks']:
        bid = block.get('id', '')
        if (not re.fullmatch(r'b-[0-9a-f]{8}', bid) or bid in block_ids
            or set(block) - {'id', 'type', 'content', 'items', 'attrs'}):
            raise ValueError('invalid_piece_block')
        block_ids.add(bid); kind = block.get('type')
        attrs = block.get('attrs', {})
        if not isinstance(attrs, dict) or set(attrs) - {'fig', 'cite', 'class', 'confidence', 'limits'}:
            raise ValueError('invalid_piece_block_attributes')
        if kind in ('p', 'h2', 'h3', 'blockquote', 'pullquote'):
            html, plain = inline(block['content'])
            tag = 'blockquote' if kind == 'pullquote' else kind
            style = 'margin:0 0 18px;font:18px/1.6 Georgia,serif'
            if kind in ('h2', 'h3'): style = 'margin:24px 0 12px;font:700 24px/1.2 Arial,sans-serif'
            if attrs.get('cite'):
                cite, cite_plain = inline([{'t': 'cite', 'key': attrs['cite']}])
                html += cite; plain += '\n' + cite_plain
            body.append(f'<{tag} style="{style}">{html}</{tag}>'); plain_body.append(plain)
        elif kind in ('ul', 'ol'):
            rows = [inline(item) for item in block['items']]
            body.append(f'<{kind} style="font:18px/1.6 Georgia,serif">' + ''.join(f'<li>{h}</li>' for h, _ in rows) + f'</{kind}>')
            plain_body.append('\n'.join(f'{n}. {t}' if kind == 'ol' else f'• {t}' for n, (_, t) in enumerate(rows, 1)))
        elif kind == 'hr': body.append('<hr style="border:0;border-top:1px solid #c9c2b6">')
        elif kind == 'evidence':
            if attrs.get('class') not in ('A', 'B', 'C', 'D') or not isinstance(attrs.get('confidence'), str):
                raise ValueError('invalid_piece_evidence')
            html, plain = inline(attrs['limits']); label = attrs['class'] + ' · ' + attrs['confidence']
            body.append(f'<aside style="padding:16px;background:#f2efe8;font:16px/1.5 Arial,sans-serif"><strong>{e(label)}</strong><p>{html}</p></aside>')
            plain_body.append(label + '\n' + plain)
        elif kind == 'figure':
            fig = piece.get('figures', {}).get(attrs.get('fig'), {})
            file = fig.get('file', '')
            if (not re.fullmatch(r'figures/[A-Za-z0-9-]+\.webp', file) or not fig.get('credit') or not fig.get('licence')
                or not fig.get('caption', {}).get(locale) or not fig.get('alt', {}).get(locale)):
                raise ValueError('invalid_piece_figure_or_credit')
            caption, alt = fig['caption'][locale], fig['alt'][locale]
            credit = fig['credit'] + ' · ' + fig['licence']
            src = safe_url(site_url.rstrip('/') + '/editorial/pieces/' + piece['slug'] + '/' + file, site_url)
            body.append(f'<figure style="margin:24px 0"><img src="{e(src)}" alt="{e(alt)}" style="display:block;width:100%;max-width:100%;height:auto"><figcaption style="font:13px/1.5 Arial,sans-serif">{e(caption)} · {e(credit)}</figcaption></figure>')
            plain_body.append(alt + '\n' + caption + '\n' + credit + '\n' + src)
        else: raise ValueError('unsupported_piece_block')
    notes, plain_notes = [], []
    # Notes may themselves refer to other notes; numbering follows first use.
    index = 0
    while index < len(numbers):
        fid = list(numbers)[index]; number = numbers[fid]
        html, plain = inline(doc['footnotes'][fid])
        notes.append(f'<li id="endnote-{number}">{html} <a href="#note-reference-{number}-1">↩</a></li>')
        plain_notes.append(f'[{number}] {plain}'); index += 1
    if set(numbers) != set(doc['footnotes']): raise ValueError('unreferenced_piece_endnote')
    if notes:
        body.append(f'<h2 style="font:700 24px Arial,sans-serif">{notes_label}</h2><ol style="font:15px/1.6 Georgia,serif">' + ''.join(notes) + '</ol>')
        plain_body.append(notes_label + '\n' + '\n'.join(plain_notes))
    if sources:
        rows = [(safe_url(s['url'], site_url), s['title'], s.get('author', '')) for s in sources.values()]
        body.append(f'<h2 style="font:700 24px Arial,sans-serif">{sources_label}</h2><ul>' + ''.join(
            f'<li><a href="{e(url)}">{e(title)}</a> {e(author)}</li>' for url, title, author in rows) + '</ul>')
        plain_body.append(sources_label + '\n' + '\n'.join(f'{title} · {author}: {url}' for url, title, author in rows))
    lang, _, _, _, prefs, unsub, *_ = EMAIL_COPY[locale]
    unsubscribe_url = unsubscribe_url or web
    preferences_url = preferences_url or unsubscribe_url
    # Only caller-controlled provider tokens are allowed to remain template syntax.
    def footer_url(value):
        if value in ('{{ unsubscribe_url }}', '{{ unsubscribe }}', '{{ UnsubscribeURL }}', '{{ UnsubscribeURL }}?manage=true'):
            return value
        return e(safe_url(value, site_url))
    title, dek = doc['title'], doc['dek']
    subject = PAPER_NAME + ': ' + title.replace('\r', ' ').replace('\n', ' ')
    subject = subject.replace('{{', '{\u200b{').replace('}}', '}\u200b}')
    html = f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{e(subject)}</title></head>
<body style="margin:0;background:#f2efe8;color:#0a0a0a;overflow-wrap:anywhere"><div style="display:none;max-height:0;overflow:hidden;opacity:0">{e(dek)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:28px 12px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;background:#fbf9f4">
<tr><td style="padding:28px;border-bottom:3px solid #0a0a0a"><p style="margin:0;color:#a9340e;font:700 12px Arial,sans-serif;letter-spacing:.14em">fCMO · {e(PAPER_NAME)}</p><h1 style="font:700 36px/1.1 Arial,sans-serif">{e(title)}</h1><p style="font:18px/1.6 Georgia,serif">{e(dek)}</p><p style="font:14px Arial,sans-serif">{by} {e(byline)}</p></td></tr>
<tr><td style="padding:28px">{''.join(body)}<p><a href="{e(web)}" style="color:#a9340e;font:700 16px Arial,sans-serif">{read} →</a></p></td></tr>
<tr><td style="padding:20px 28px;background:#f2efe8;color:#5e5a53;font:12px/1.5 Arial,sans-serif"><strong>{e(PAPER_NAME)}</strong><p>{e(postal_address)}</p><a href="{footer_url(preferences_url)}">{prefs}</a> · <a href="{footer_url(unsubscribe_url)}">{unsub}</a></td></tr>
</table></td></tr></table></body></html>'''
    text = f'{PAPER_NAME}\n{title}\n{dek}\n{by} {byline}\n\n' + '\n\n'.join(plain_body)
    text += f'\n\n{read}: {web}\n{postal_address}\n{prefs}: {preferences_url}\n{unsub}: {unsubscribe_url}\n'
    return RenderedEmail(subject, dek[:140], html, text)
