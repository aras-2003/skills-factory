import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.package.build_utils import package_version


class ReleaseVersionTests(unittest.TestCase):
    def test_same_source_same_version_across_channels_and_rebuilds(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'release').mkdir()
            (root / 'release/package.yaml').write_text('release:\n  versioning: git-first-parent\n  version_prefix: "1.38"\n')
            subprocess.run(['git', 'init', '-q', temp], check=True)
            def commit():
                subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '--allow-empty', '-qm', 'source'], cwd=root, check=True)
            commit()
            old = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
            with patch.dict(os.environ, {'SOURCE_REVISION': old}):
                self.assertEqual('1.38.1', package_version(root, 'lab'))
                self.assertEqual(package_version(root, 'lab'), package_version(root, 'package'))
                commit()
                self.assertEqual('1.38.1', package_version(root, 'package'))
            new = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
            with patch.dict(os.environ, {'SOURCE_REVISION': new}):
                self.assertEqual('1.38.2', package_version(root, 'lab'))

    def test_shallow_history_cannot_invent_a_release_number(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'release').mkdir()
            (root / 'release/package.yaml').write_text('release:\n  versioning: git-first-parent\n  version_prefix: "1.38"\n')
            with patch('scripts.package.build_utils.source_revision', return_value='a' * 40), patch('scripts.package.build_utils.subprocess.check_output', return_value='true\n'):
                with self.assertRaisesRegex(ValueError, 'full Git history'):
                    package_version(root, 'lab')
