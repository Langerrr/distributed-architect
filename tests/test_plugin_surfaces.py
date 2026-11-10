"""Check packaged references, with explicit exceptions for project-owned artifacts."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_PATHS = {
    '.dist-architect/topology.yaml',  # Optional input, never packaged.
    '.dist-architect/pattern-drafts/<slug>.md',  # Generated output.
}


def references(text):
    """Recognize Markdown links and bare/backticked file or directory paths."""
    links = re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', text)
    # Strip links to avoid counting their targets twice.
    prose = re.sub(r'\[[^\]]*\]\([^)]*\)', '', text)
    paths = re.findall(
        r'(?<![\w/])(?:\.{1,2}/)?(?:[\w.-]+/)*'
        r'(?:[\w<>.-]+\.(?:md|yaml|yml|json|py)|[\w.-]+/)', prose
    )
    # Slash-separated prose (state/data, etc.) is not a directory reference.
    dirs = re.findall(r'`([^`\s]+/)`', prose)
    return links + [p for p in paths if not p.endswith('/')] + dirs


class PluginSurfaces(unittest.TestCase):
    def test_packaged_references_resolve(self):
        files = sorted(p for folder in ('skills', 'modules', 'catalog')
                       for p in (ROOT / folder).rglob('*.md'))
        self.assertTrue(files)
        count = 0
        for source in files:
            text = source.read_text()
            self.assertNotIn('${CLAUDE_PLUGIN_ROOT}', text, source)
            self.assertNotIn('$ARGUMENTS', text, source)
            for target in references(text):
                if target in PROJECT_PATHS:
                    continue
                with self.subTest(source=str(source.relative_to(ROOT)), target=target):
                    self.assertFalse('://' in target, 'Unexpected external reference')
                    path = (source.parent / target.split('#')[0]).resolve()
                    self.assertTrue(path.is_relative_to(ROOT), 'Reference escapes plugin')
                    self.assertTrue(path.exists(), f'Missing reference: {path}')
                    count += 1
        self.assertGreaterEqual(count, 20, 'Reference extraction missed packaged links')

    def test_codex_skill_root(self):
        manifest = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())
        claude = json.loads((ROOT / '.claude-plugin/plugin.json').read_text())
        self.assertEqual(manifest['version'], '0.4.0')
        self.assertEqual(manifest['version'], claude['version'])
        self.assertEqual(manifest['skills'], './skills/')
        skill_root = ROOT / manifest['skills']
        self.assertEqual(
            {str(p.relative_to(skill_root)) for p in skill_root.rglob('SKILL.md')},
            {f'{name}/SKILL.md' for name in ('async-reasoning', 'dist-check', 'dist-debug', 'dist-design')},
        )
        self.assertTrue((ROOT / 'modules').is_dir())
        self.assertTrue((ROOT / 'catalog').is_dir())

    def test_path_extraction_forms(self):
        self.assertEqual(references('[a](../modules/a.md) `missing.md` `../catalog/`'),
                         ['../modules/a.md', 'missing.md', '../catalog/'])


if __name__ == '__main__':
    unittest.main()
