from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import git_inspector as m

class Tests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.root = Path(t.name).resolve() / 'repo'; self.root.mkdir()
        self.git('init', '-q'); self.git('config','user.name','Fixture'); self.git('config','user.email','fixture@example.invalid')
    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.root),*args]).strip()
    def commit(self):
        (self.root/'a').write_text('a'); self.git('add','.'); self.git('commit','-qm','initial')
    def test_unborn(self):
        r=m.observe(self.root); self.assertEqual(r['head_state'],'UNBORN'); self.assertIsNone(r['head'])
    def test_clean_head(self):
        self.commit(); r=m.observe(self.root); self.assertEqual(r['head'],self.git('rev-parse','HEAD').decode()); self.assertTrue(r['worktree_clean'])
    def test_dirty(self):
        self.commit(); (self.root/'a').write_text('b'); (self.root/'private.txt').write_text('secret')
        r=m.observe(self.root); self.assertEqual(r['changes'],{'tracked_changed':1,'untracked':1}); self.assertNotIn('private.txt',str(r)); self.assertNotIn('secret',str(r))
    def test_detached(self):
        self.commit(); self.git('checkout','--detach','-q'); self.assertEqual(m.observe(self.root)['head_state'],'DETACHED')
    def test_refs_and_remote_no_url(self):
        self.commit(); self.git('branch','extra'); self.git('tag','light'); self.git('tag','-a','annotated','-m','fixture'); self.git('remote','add','origin','https://example.invalid/private')
        r=m.observe(self.root); self.assertEqual(r['refs'],{'local_branches':2,'annotated_tags':1,'other_tags':1}); self.assertEqual(r['remote_count'],1); self.assertNotIn('example.invalid',str(r))
    def test_nested_rejected(self):
        p=self.root/'nested'; p.mkdir()
        with self.assertRaisesRegex(m.InspectError,'ROOT_REQUIRED'): m.observe(p)
    def test_non_git_rejected(self):
        p=self.root.parent/'other'; p.mkdir()
        with self.assertRaisesRegex(m.InspectError,'QUERY_FAILED'): m.observe(p)
    def test_inherited_git_context_ignored(self):
        self.commit()
        with patch.dict(os.environ,{'GIT_DIR':'/invalid','GIT_WORK_TREE':'/invalid','GIT_CONFIG_COUNT':'1'}): self.assertTrue(m.observe(self.root)['worktree_clean'])
    def test_child_environment_is_allowlisted(self):
        with patch.dict(os.environ, {'TESSERA_SYNTHETIC': 'fixture',
                                     'GIT_CONFIG_COUNT': '1',
                                     'GIT_DIR': '/invalid',
                                     'PYTHONPATH': '/invalid'}):
            env = m.child_environment()
            for name in ('TESSERA_SYNTHETIC', 'GIT_CONFIG_COUNT', 'GIT_DIR', 'PYTHONPATH'):
                self.assertNotIn(name, env)
            self.assertEqual(env['GIT_OPTIONAL_LOCKS'], '0')
            self.assertEqual(env['GIT_CONFIG_GLOBAL'], os.devnull)
            self.assertTrue(m.observe(self.root)['worktree_clean'])
    def test_no_index_write(self):
        self.commit(); index=self.root/'.git/index'; before=(index.read_bytes(),index.stat().st_mtime_ns); m.observe(self.root); self.assertEqual(before,(index.read_bytes(),index.stat().st_mtime_ns))
    def test_stale_observations(self):
        self.commit(); original=m.query; calls=0
        def query(root,exe,*args):
            nonlocal calls
            if args[0]=='status':
                calls+=1
                if calls==2: (root/'new').write_text('new')
            return original(root,exe,*args)
        with patch.object(m,'query',side_effect=query): self.assertEqual(m.observe(self.root)['status'],'STALE')
    def test_branch_target_change_detected(self):
        self.commit(); self.git('branch','extra'); old=self.git('rev-parse','HEAD')
        (self.root/'a').write_text('new'); self.git('commit','-qam','second')
        original=m.query; calls=0
        def query(root,exe,*args):
            nonlocal calls
            if args[0]=='for-each-ref':
                calls+=1
                if calls==2: self.git('branch','-f','extra','HEAD')
            return original(root,exe,*args)
        self.assertNotEqual(old,self.git('rev-parse','HEAD'))
        with patch.object(m,'query',side_effect=query): self.assertEqual(m.observe(self.root)['status'],'STALE')
    def test_malformed_status(self):
        for data in (b'',b'# branch.oid bad\0# branch.head main\0',b'# branch.oid (initial)\0# branch.head main\0X\0'):
            with self.assertRaises(m.InspectError): m.parse_status(data)
    def test_metadata_is_not_content_integrity(self):
        self.commit(); f=self.root/'a'; f.write_text('x'); a=m.observe(self.root); f.write_text('y'); b=m.observe(self.root); self.assertEqual(a['status_sha256'],b['status_sha256']); self.assertEqual(b['content_integrity'],'NOT_VERIFIED')

if __name__=='__main__': unittest.main()
