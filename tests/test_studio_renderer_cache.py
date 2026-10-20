"""Studio's production renderer caches work without changing publication bytes."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from tests.test_studio_storage import ROOT


class RendererCache(unittest.TestCase):
    def test_startup_warms_compiled_templates_without_host_credentials(self):
        import os
        import subprocess
        from studio.server.preview import Preview
        preview = Preview(None, ROOT)
        with patch.dict(os.environ, {'STUDIO_SESSION_KEY': 'fixture', 'GH_TOKEN_JAVIER': 'fixture',
                                     'GITHUB_TOKEN': 'fixture', 'GHOST_CONTENT_API_KEY': 'fixture'}), \
                patch('studio.server.preview.subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as run:
            preview.warm()
        self.assertIn('--warm', run.call_args.args[0])
        env = run.call_args.kwargs['env']
        self.assertNotIn('STUDIO_SESSION_KEY', env)
        self.assertNotIn('GH_TOKEN_JAVIER', env)
        self.assertNotIn('GITHUB_TOKEN', env)
        self.assertEqual(env['GHOST_CONTENT_API_KEY'], '')
        with patch('studio.server.preview.subprocess.run', side_effect=subprocess.TimeoutExpired([], 10)):
            from studio.server.preview import RendererUnavailable
            with self.assertRaisesRegex(RendererUnavailable, '10 segundos'): preview.warm()
    def test_neighbor_index_preserves_production_links_and_membership_counts(self):
        from studio.server.render_preview import StudioPaperBuilder
        from tools.paper.build import PaperBuilder
        stories = [
            {'topics': ['Alpha', 'Alpha', 'Beta'], 'organizations': ['One', 'Twin']},
            {'topics': ['Alpha', 'Beta'], 'organizations': ['One', 'twin']},
            {'topics': ['Alpha', 'Beta', 'Rare'], 'organizations': ['Two']},
        ]
        reference = PaperBuilder.__new__(PaperBuilder)
        reference.live = stories; reference.base = '/fixture/'
        reference.catalogs = {'en': {'strings': {'front': {'see_all': 'All'}}}}
        candidate = StudioPaperBuilder.__new__(StudioPaperBuilder)
        candidate.__dict__.update(reference.__dict__)
        loc = {'code': 'en', 'path_prefix': ''}
        for topic, org in [('', ''), ('Alpha', ''), ('alpha', 'One'), ('beta', 'one')]:
            for limit in (0, 1, 5, 20):
                with self.subTest(topic=topic, org=org, limit=limit):
                    self.assertEqual(candidate._topic_links(loc, exclude_topic=topic, exclude_org=org, limit=limit),
                                     reference._topic_links(loc, exclude_topic=topic, exclude_org=org, limit=limit))
        # Once indexed, additional pages do not walk the corpus at all.
        candidate.live = None
        self.assertEqual(candidate._topic_links(loc), reference._topic_links(loc))

    def test_ready_piece_uses_cached_renderer_as_well_as_drafts(self):
        from studio.server.preview import Preview
        from studio.server.storage import Store
        from tests.test_studio_storage import DOC
        import copy
        import subprocess
        with TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / 'data')
            self.addCleanup(store.close)
            slug = store.create('javier', 'essay', 'Renderer fixture', 'en')['slug']
            for loc in ('en', 'es-419', 'zh-Hans'):
                doc = copy.deepcopy(DOC); doc['locale'] = loc
                store.save(slug, loc, 'javier', store.piece(slug)['head_rev'], doc, {})
                store.locale_state(slug, loc, 'javier', 'ready', True, 'Leí y entiendo el texto chino')
            preview = Preview(store, ROOT)
            result = subprocess.CompletedProcess([], 1, b'', b'fixture failure')
            with patch('studio.server.preview.subprocess.run', return_value=result) as run:
                from studio.server.preview import RendererUnavailable
                with self.assertRaises(RendererUnavailable): preview.build(slug, strict=True)
            self.assertIn('studio.server.render_preview', run.call_args.args[0])
            self.assertNotIn('--snapshot', run.call_args.args[0])
