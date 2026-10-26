"""D evidence grammar: cardinality, escaping and unsupported relationships."""
import unittest
import xml.etree.ElementTree as ET
from tools.paper.i18n import load_catalogs
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EvidenceComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs = load_catalogs(ROOT)

    def components(self):
        from tools.paper.templates import d_components
        return d_components

    def test_map_cardinality_and_xml_for_every_locale(self):
        d = self.components()
        for code, cat in self.catalogs.items():
            for n in (0, 1, 8):
                with self.subTest(code=code, n=n):
                    sources = [{'url': f'https://example.test/{i}?a=1&b=2', 'domain': f'source-{i}', 'primary': True} for i in range(n)]
                    evidence = {'claims': [{'label': 'CLAIMED', 'text': '中文 <claim> & title ' * 8} for _ in range(n)],
                                'gaps': [{'description': '中文 <gap> & unknown ' * 8} for _ in range(n)]}
                    svg = d.evidence_map({'sources': sources}, cat, evidence=evidence, title='中文 & <long> ' * 30)
                    root = ET.fromstring(svg)
                    self.assertEqual(len(root.findall('.//*[@data-node="source"]')), n)
                    self.assertEqual(len(root.findall('.//*[@data-node="gap"]')), n)
                    self.assertEqual(len(root.findall('.//*[@data-node="claim"]')), n)
                    self.assertIn('viewBox', root.attrib)
                    self.assertNotIn('<long>', svg)

    def test_claim_states_never_upgrade_unverified(self):
        d = self.components()
        for raw, want in [('DEMONSTRATED', 'shown'), ('VENDOR_CLAIM', 'claimed'), ('INFERRED', 'not-established'), ('DISPUTED', 'not-established'), ('', 'not-established')]:
            self.assertIn('d-claim--' + want, d.claim(raw, self.catalogs['en']))

    def test_empty_and_many_ledgers_are_truthful(self):
        d = self.components()
        for n in (0, 1, 12):
            evidence = {'claims': [{'label': 'CLAIMED', 'text': f'claim <{i}>'} for i in range(n)]}
            html = d.ledger(evidence, self.catalogs['en'])
            self.assertEqual(html.count('data-ledger-item='), n)
            self.assertNotIn('claim <0>', html)
            if not n:
                self.assertIn(self.catalogs['en']['strings']['record']['none'], html)

    def test_no_claim_source_relationships_are_invented(self):
        d = self.components()
        html = d.claims_sources({'sources': [{'url': 'https://a.test', 'domain': 'a.test'}]},
                                {'claims': [{'text': 'Unmapped claim', 'label': 'CLAIMED'}]}, self.catalogs['en'])
        self.assertNotIn('data-edge=', html)
        self.assertIn('Unmapped claim', html)
        self.assertIn('https://a.test', html)

    def test_unknown_grade_and_unsafe_source(self):
        d = self.components()
        self.assertIn('?', d.grade({'evidence_class': '<A>'}, self.catalogs['en']))
        html = d.claims_sources({'sources': [{'url': 'javascript:alert(1)', 'domain': '<unsafe>'}]}, {}, self.catalogs['en'])
        self.assertNotIn('href="javascript:', html)
        self.assertNotIn('<unsafe>', html)

    def test_source_attribution_keeps_recorded_author_outlet_and_date(self):
        html = self.components().claims_sources({'sources': [{'url': 'https://example.test/paper',
            'title': 'A measured result', 'author': 'Recorded author', 'outlet': 'Recorded journal',
            'published_at': '2026-10-22', 'primary': True}]}, {}, self.catalogs['en'])
        for value in ('A measured result', 'Recorded author', 'Recorded journal', '2026-10-22'):
            self.assertIn(value, html)

    def test_d_text_pairs_meet_aa(self):
        import json
        from design.check_contrast import ratio
        colors = json.loads((ROOT/'design/tokens.json').read_text())['d']['color']
        for foreground, background in [('bone','ink'),('fog','ink'),('stone','ink'),('ink','bone'),('body','bone')]:
            self.assertGreaterEqual(ratio(colors[foreground],colors[background]),4.5)

    def test_timeline_uses_only_recorded_dates(self):
        d = self.components()
        cat = self.catalogs['es-419']
        self.assertEqual(d.timeline({}, cat), '')
        html = d.timeline({'event_at': '2026-10-22T12:00:00Z', 'updated_at': '2026-10-24T13:00:00Z'}, cat)
        self.assertEqual(html.count('<time'), 2)
        self.assertNotIn('2024', html)

    def test_qualified_claim_codes_and_unknowns_preserve_proof(self):
        d = self.components()
        for code, expected in [('CLAIMED_SELF_REPORTED', 'claimed'), ('PRIMARY_EXTRAORDINARY_CLAIM', 'claimed'), ('INFERRED_FROM_PRIMARY', 'not-established')]:
            self.assertEqual(d.proof_kind(code), expected)

    def test_stat_does_not_repeat_its_number(self):
        from html.parser import HTMLParser
        class Text(HTMLParser):
            def __init__(self):
                super().__init__(); self.parts = []
            def handle_data(self, value): self.parts.append(value)
        p = Text(); p.feed(self.components().stat(12, '12 primary sources'))
        self.assertEqual(' '.join(p.parts), '12 primary sources')

    def test_map_wraps_in_a_wide_branching_grid(self):
        svg = self.components().evidence_map({'sources': [{'title': 's'}]*5}, self.catalogs['en'],
                 evidence={'gaps': [{'description': 'g'}]*8}, title='title')
        root = ET.fromstring(svg)
        xs = {n.attrib['x'] for n in root.findall('.//*[@data-node="gap"]')}
        self.assertGreater(len(xs), 1)


class FrontVariants(unittest.TestCase):
    def test_no_image_and_long_chinese_headline_keep_typographic_hero(self):
        from tools.paper.templates.landing import _Ctx
        from tools.paper.templates import d_front
        ctx = _Ctx({'code':'zh-Hans','path_prefix':'zh/'}, '/paper/')
        title = '可核实的来源与尚未证实的结果' * 20
        story = {'id':'FCMO-000000000001','topics':[],'sources':[],
                 'evidence':{'claims':[],'gaps':[]}}
        feature = {'title':title,'title_class':'title-extra-compact','beat':'研究','href':'/paper/story/',
                   'dek':'摘要','badge':'自动研究','cta':'阅读'}
        html = d_front.cover(feature,story,ctx)
        self.assertIn(title, html)
        self.assertNotIn('d-cover-plate', html)
        self.assertNotIn('<img', html)
        self.assertIn('d-evidence-map', html)

    def test_rank_accepts_one_or_many_records_without_losing_order(self):
        from tools.paper.templates.landing import _Ctx
        from tools.paper.templates import d_front
        ctx = _Ctx({'code':'en','path_prefix':''}, '/paper/')
        for n in (0,1,17):
            stories = [{'id':f'FCMO-{i:012X}','url_date':'2026-10-26','slug':f'story-{i}',
                        'headline':f'Story {i}','topics':[],'sources':[],'evidence':{}} for i in range(n)]
            html = d_front.rank(stories,ctx)
            self.assertEqual(html.count('<article class="d-rank-entry">'), n)
            if n:
                self.assertIn(f'{n:02d}</b>',html)
