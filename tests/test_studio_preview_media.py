"""A lagging host checkout (missing story media) must not turn the preview into a 503."""
import json
import tempfile
import unittest
from pathlib import Path

from studio.server.render_preview import StudioPaperBuilder
from tools.paper.build import PaperBuilder, MISSING_MEDIA_PLACEHOLDER
from tests.test_studio_storage import ROOT


def builder(cls, out):
    b = cls.__new__(cls)
    b.stories = [{'id': 'X', 'media': {'local_path': 'assets/story-media/definitely-missing-zz.svg'}}]
    b.out = Path(out)
    return b


class MissingStoryMedia(unittest.TestCase):
    def test_preview_builder_writes_placeholder_instead_of_failing(self):
        with tempfile.TemporaryDirectory() as tmp:
            builder(StudioPaperBuilder, tmp)._copy_story_media()
            self.assertEqual((Path(tmp) / 'assets/story-media/definitely-missing-zz.svg').read_text(), MISSING_MEDIA_PLACEHOLDER)

    def test_production_builder_still_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'referenced story media is missing'):
                builder(PaperBuilder, tmp)._copy_story_media()

    def test_full_preview_with_absent_media_is_200_not_503(self):
        from studio.server.preview import Preview
        from studio.server.storage import Store
        from tests.test_studio_storage import DOC
        (ROOT / '_audit').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as tmp:
            tmp = Path(tmp); (tmp / 'site/data').mkdir(parents=True)
            data = json.loads((ROOT / 'site/data/stories.v2.json').read_text())
            for story in data['stories']:
                if story.get('media'): story['media']['local_path'] = 'assets/story-media/absent-' + story['id'] + '.svg'
            (tmp / 'site/data/stories.v2.json').write_text(json.dumps(data))
            (tmp / 'site/data/newsroom-status.json').write_text((ROOT / 'site/data/newsroom-status.json').read_text())
            store = Store(tmp / 'data')
            try:
                store.public_root = tmp
                slug = store.create('javier', 'essay', 'Medios ausentes', 'en')['slug']
                store.save(slug, 'en', 'javier', 0, DOC, {})
                self.assertIn(b'<html', Preview(store, ROOT).page(slug, 'en'))
            finally: store.close()


if __name__ == '__main__': unittest.main()
