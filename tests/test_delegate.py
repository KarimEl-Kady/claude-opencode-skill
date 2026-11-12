import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.claude/skills/opencode-delegate/scripts/delegate.py'
spec = importlib.util.spec_from_file_location('delegate', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class BridgeTests(unittest.TestCase):
    def make_args(self, **overrides):
        data = dict(mode='review', approved=False, task='Review files', task_file=None,
                    agent=None, model=None, session=None, format='text')
        data.update(overrides)
        return SimpleNamespace(**data)

    def test_review_requires_readonly_agent(self):
        cmd = module.build_command(self.make_args())
        self.assertEqual(cmd[:4], ['opencode', 'run', '--agent', 'claude-review'])
        with self.assertRaises(ValueError):
            module.build_command(self.make_args(agent='build'))

    def test_implementation_requires_approval(self):
        with self.assertRaises(ValueError):
            module.build_command(self.make_args(mode='implement'))
        cmd = module.build_command(self.make_args(mode='implement', approved=True,
                                                 model='provider/model#high', session='ses_X'))
        self.assertIn('--model', cmd)
        self.assertIn('--session', cmd)
        self.assertNotIn('--auto', cmd)

    def test_task_is_arg_not_shell(self):
        cmd = module.build_command(self.make_args(task="x; touch /tmp/SHOULD_NOT_CREATE"))
        self.assertEqual(cmd[-1], 'x; touch /tmp/SHOULD_NOT_CREATE')

    def test_cli_dry_run(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--mode', 'review',
                                 '--project', tempfile.gettempdir(), '--task', 'secret words',
                                 '--dry-run'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('<TASK>', result.stdout)
        self.assertNotIn('secret words', result.stdout)

if __name__ == '__main__':
    unittest.main()
