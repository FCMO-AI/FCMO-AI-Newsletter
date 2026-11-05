import unittest
from tools.paper import d_plates


class DPlates(unittest.TestCase):
    def _story(self, i):
        return {"id": f"FCMO-{i:012d}", "topics": [{"slug": "agents"}]}

    def test_assignment_is_deterministic(self):
        s = self._story(1)
        a = d_plates.html(s, "3 / 1", {"plate": {"alt_decorative": "Material study"}}, "/", {}, False)
        b = d_plates.html(s, "3 / 1", {"plate": {"alt_decorative": "Material study"}}, "/", {}, False)
        self.assertEqual(a, b)
        self.assertIn('data-plate="', a)

    def test_neighbours_on_a_page_differ(self):
        seen = {}
        names = []
        for i in range(8):
            h = d_plates.html(self._story(i), "3 / 1", {"plate": {"alt_decorative": "Material study"}}, "/", seen, True)
            names.append(h.split('data-plate="')[1].split('"')[0])
        self.assertEqual(len(set(names)), len(names))

    def test_a_page_spreads_material_families(self):
        # 11-02 M4: the live front page took cracked stone, cast iron and dry clay for 5 rows and read as repeats.
        self.assertEqual(set(d_plates.FAMILY), set(d_plates.PLATES))
        families = set(d_plates.FAMILY.values())
        for offset in range(0, 40, 5):
            seen = {}
            for i in range(len(families)):
                d_plates.choose(self._story(offset + i), seen, wide=i == 0)
            self.assertEqual(len({d_plates.FAMILY[n] for n in seen.values()}), len(families))

    def test_families_group_by_look_not_by_material_name(self):
        # 11-02 design debt: cracked clay (arcilla) next to a cracked stone lead, and a paper slab next to a concrete block.
        F = d_plates.FAMILY
        self.assertEqual(F["arcilla-seca"], F["piedra-grieta"])
        self.assertEqual(F["papel-pliegue"], F["concreto-bloque"])
        self.assertNotEqual(F["papel-pila"], F["papel-pliegue"])

    def test_neighbours_alternate_tone_when_possible(self):
        # 11-05: the whole bank is warm-lit; two dark slabs in a row read as one image.
        self.assertEqual(set(d_plates.TONE), set(d_plates.PLATES))
        for offset in range(0, 60, 6):
            seen = {}
            names = [d_plates.choose(self._story(offset + i), seen, wide=i == 0) for i in range(6)]
            tones = [d_plates.TONE[n] for n in names]
            same = sum(a == b for a, b in zip(tones, tones[1:]))
            self.assertLessEqual(same, 1, (names, tones))  # a new look still outranks tone when only one is left

    def test_warm_plate_is_thumb_only(self):
        self.assertIn("arcilla-seca", d_plates.THUMB_ONLY)


if __name__ == "__main__":
    unittest.main()
