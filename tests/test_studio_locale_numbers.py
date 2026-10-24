"""Numbers compare by value across locales; quotations are translated, not frozen."""
import copy
import unittest

from studio.translation import RULES, TranslationError, number_values, validate_translation
from studio.server.checks import checks


def doc(loc, *blocks, title='Titulo', dek='Una nota'):
    return {'schema': 'fcmo-essay-doc-v1', 'locale': loc, 'title': title, 'dek': dek, 'footnotes': {},
            'blocks': [{'id': 'b-0000000%d' % i, 'type': kind, 'content': [{'t': 'text', 'v': text}]}
                       for i, (kind, text) in enumerate(blocks)]}


def passes(src_loc, src, dst_loc, dst):
    try:
        validate_translation(doc(src_loc, ('p', src)), doc(dst_loc, ('p', dst)), dst_loc)
        return True
    except TranslationError:
        return False


class NumberValueTests(unittest.TestCase):
    def test_thousands_in_every_locale(self):
        self.assertTrue(passes('es-419', 'Cuesta 4,200 dólares en total.', 'en', 'It costs $4,200 in total.'))
        self.assertTrue(passes('es-419', 'Cuesta 4,200 dólares en total.', 'zh-Hans', '总共花费4,200美元。'))
        self.assertTrue(passes('es-419', 'Cuesta 4,200 dólares en total.', 'zh-Hans', '总共花费4200美元。'))
        self.assertTrue(passes('es-419', 'Cuesta 4200 dólares en total.', 'en', 'It costs $4,200 in total.'))
        self.assertTrue(passes('es-419', 'Cuesta 1,234,567 dólares.', 'en', 'It costs 1,234,567 dollars.'))

    def test_argentine_style(self):
        self.assertTrue(passes('es-419', 'Cuesta 4.200 pesos, el 3,5 % más.', 'en', 'It costs 4,200 pesos, 3.5% more.'))

    def test_target_locale_forms(self):
        self.assertFalse(passes('es-419', 'Cuesta 4,200 dólares.', 'en', 'It costs 4.200 dollars.'))
        self.assertTrue(passes('es-419', 'Cuesta 4,200 dólares.', 'en', 'It costs 4,200 dollars.'))
        self.assertFalse(passes('es-419', 'Subió 3,5 %.', 'en', 'It rose 3,5%.'))
        self.assertTrue(passes('es-419', 'Subió 3,5 %.', 'en', 'It rose 3.5%.'))
        self.assertFalse(passes('es-419', 'Cuesta 4,200 dólares.', 'zh-Hans', '花费4.200美元。'))

    def test_chinese_magnitude(self):
        self.assertTrue(passes('es-419', 'Son 42,000 personas.', 'zh-Hans', '共有4.2万人。'))

    def test_real_changes_still_fail(self):
        self.assertFalse(passes('es-419', 'Cuesta 4,200 dólares.', 'en', 'It costs $4,300.'))
        self.assertFalse(passes('es-419', 'Subió 37 %.', 'en', 'It rose 73%.'))
        self.assertFalse(passes('es-419', 'Subió 3,5 %.', 'en', 'It rose 35%.'))
        self.assertFalse(passes('es-419', 'Cuesta 4.200 pesos.', 'en', 'It costs 4.2 pesos.'))

    def test_times_and_years_keep_working(self):
        self.assertTrue(passes('es-419', 'A las 22:00 de 2026.', 'en', 'At 22:00 in 2026.'))
        self.assertFalse(passes('es-419', 'A las 22:00 de 2026.', 'en', 'At 21:00 in 2026.'))

    def test_values(self):
        self.assertEqual(number_values('4,200'), number_values('4.200'))
        self.assertEqual(number_values('0,25'), number_values('0.25'))
        self.assertNotEqual(number_values('0,250'), number_values('250'))


class TokenCheckTests(unittest.TestCase):
    def tokens(self, src, dst):
        from types import SimpleNamespace
        docs = {'es-419': doc('es-419', ('p', src)), 'en': doc('en', ('p', dst)), 'zh-Hans': doc('zh-Hans', ('p', dst))}
        states = {l: {'state': 'ready'} for l in docs}
        payload = {'piece': {'source_locale': 'es-419'}, 'docs': docs, 'sources': [], 'figures': {},
                   'provenance': {l: {'origin': 'human'} for l in docs}}
        store = SimpleNamespace(payload=lambda v: payload, piece=lambda v: {'author': 'x', 'locale_states': states})
        preview = SimpleNamespace(privacy=lambda v: True)
        return {r['id']: r['ok'] for r in checks(store, preview, 'x') if r['id'].startswith('tokens-')}

    def test_grouping_difference_passes(self):
        self.assertEqual(self.tokens('Son 4200 dólares.', 'It is $4,200.'), {'tokens-es-419': True, 'tokens-en': True, 'tokens-zh-Hans': True})
        self.assertTrue(self.tokens('Son 4,200 dólares.', '4200美元')['tokens-zh-Hans'])
        self.assertTrue(self.tokens('Son 4.200 y 3,5 %.', '4,200 and 3.5%')['tokens-en'])

    def test_real_change_fails(self):
        self.assertFalse(self.tokens('Son 4,200 dólares.', '$4,300')['tokens-en'])
        self.assertFalse(self.tokens('Subió 37 %.', '73%')['tokens-en'])


class QuotationTests(unittest.TestCase):
    def test_prompt_translates_quotations(self):
        self.assertIn('Translate quotations faithfully', RULES)
        self.assertNotIn('Keep proper names and quotations EXACT', RULES)

    def test_translated_blockquote_passes(self):
        src = doc('es-419', ('blockquote', '«No es culpa de nadie: 37 % de Amazon Web Services»'))
        dst = doc('en', ('blockquote', '“Nobody is to blame: 37% of Amazon Web Services”'))
        validate_translation(src, dst, 'en')

    def test_inline_quotation_translated_passes(self):
        validate_translation(doc('es-419', ('p', 'Dijo «el futuro llega» ayer.')), doc('en', ('p', 'She said “the future is coming” yesterday.')), 'en')

    def test_quoted_number_name_and_link_still_protected(self):
        src = doc('es-419', ('blockquote', '«Somos 37 % de Amazon Web Services»'))
        for bad in ('“We are 73% of Amazon Web Services”', '“We are 37% of Amazon”'):
            with self.subTest(bad=bad), self.assertRaises(TranslationError):
                validate_translation(src, doc('en', ('blockquote', bad)), 'en')
        link = copy.deepcopy(src); link['blocks'][0]['content'].append({'t': 'link', 'href': 'https://example.org/a', 'c': [{'t': 'text', 'v': 'x'}]})
        bad = copy.deepcopy(doc('en', ('blockquote', '“We are 37% of Amazon Web Services”')))
        with self.assertRaises(TranslationError): validate_translation(link, bad, 'en')


if __name__ == '__main__':
    unittest.main()
