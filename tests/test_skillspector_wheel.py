import base64
import csv
import hashlib
import io
from pathlib import Path
import tempfile
import sys
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import check_skillspector_wheel as w


def fixture():
    return {'skillspector/cli_entry.py': b'# fixture\n',
            w.DIST + 'METADATA': b'Name: skillspector\nVersion: 2.13.7\n',
            w.DIST + 'WHEEL': b'Root-Is-Purelib: true\nTag: py3-none-any\n',
            w.DIST + 'entry_points.txt': b'[console_scripts]\nskillspector = skillspector.cli_entry:app\n'}


def archive(files, *, bad_record=False, duplicate=False, symlink=False):
    entries = dict(files)
    text = io.StringIO(newline='')
    rows = csv.writer(text)
    for name, data in entries.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
        rows.writerow([name, 'sha256=' + ('x' if bad_record else digest), str(len(data))])
    rows.writerow([w.RECORD, '', ''])
    entries[w.RECORD] = text.getvalue().encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in entries.items():
            if symlink and name == 'skillspector/cli_entry.py':
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = 0o120777 << 16
                z.writestr(info, data)
            else:
                z.writestr(name, data)
        if duplicate:
            z.writestr('SKILLSPECTOR/cli_entry.py', b'fixture')
    return out.getvalue()


class WheelTests(unittest.TestCase):
    def setUp(self):
        self.files = fixture()
        self.source = {'skillspector/cli_entry.py': w.git_blob(self.files['skillspector/cli_entry.py'])}

    def test_valid(self):
        result = w.inspect(archive(self.files), self.source)
        self.assertEqual(result['package_files'], 1)
        self.assertEqual(result['record'], 'PASS')
        self.assertEqual(result['execution'], 'NOT_RUN')

    def test_source_mismatch_despite_valid_record(self):
        self.files['skillspector/cli_entry.py'] = b'# modified\n'
        with self.assertRaisesRegex(w.WheelError, 'WHEEL_SOURCE_MISMATCH'):
            w.inspect(archive(self.files), self.source)

    def test_record_hash_mismatch(self):
        with self.assertRaisesRegex(w.WheelError, 'WHEEL_RECORD_MISMATCH'):
            w.inspect(archive(self.files, bad_record=True), self.source)

    def test_unexpected_entries(self):
        for name in ('../outside', 'startup.pth', 'skillspector/telemetry.py', 'extra.data/x'):
            with self.subTest(name=name), self.assertRaises(w.WheelError):
                w.inspect(archive({**self.files, name: b'fixture'}), self.source)

    def test_missing_package(self):
        del self.files['skillspector/cli_entry.py']
        with self.assertRaisesRegex(w.WheelError, 'WHEEL_ENTRY_MISSING'):
            w.inspect(archive(self.files), self.source)

    def test_duplicate_and_link(self):
        for kw in ({'duplicate': True}, {'symlink': True}):
            with self.subTest(kw=kw), self.assertRaisesRegex(w.WheelError, 'WHEEL_ENTRY_INVALID'):
                w.inspect(archive(self.files, **kw), self.source)

    def test_entrypoint_mismatch(self):
        self.files[w.DIST + 'entry_points.txt'] += b'other = skillspector.cli_entry:app\n'
        with self.assertRaisesRegex(w.WheelError, 'WHEEL_ENTRYPOINT'):
            w.inspect(archive(self.files), self.source)

    def test_size_limit(self):
        with mock.patch.object(w, 'MAX_ENTRY', 2), self.assertRaisesRegex(w.WheelError, 'WHEEL_SIZE_LIMIT'):
            w.inspect(archive(self.files), self.source)

    def test_pin_rejected_before_source_access(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / w.WHEEL_NAME
            path.write_bytes(b'fixture')
            with mock.patch.object(w, 'source_manifest') as manifest:
                with self.assertRaisesRegex(w.WheelError, 'WHEEL_PIN'):
                    w.verify(path, Path(folder))
                manifest.assert_not_called()


if __name__ == '__main__':
    unittest.main()
