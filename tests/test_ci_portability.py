"""Exercise the same installer contracts under a GitHub runner identity."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yaml

from tests import test_studio_activation as host_contracts

ROOT = Path(__file__).resolve().parents[1]


class RunnerContracts(unittest.TestCase):
    def test_host_service_contracts_are_hermetic_under_runner_identity(self):
        suite = unittest.TestSuite(host_contracts.HostService(name) for name in (
            'test_install_and_rollback_restore_unit_and_activation',
            'test_no_user_manager_has_no_installation_side_effect',
        ))
        result = unittest.TestResult()
        with patch('pwd.getpwuid', return_value=SimpleNamespace(pw_name='runner')):
            suite.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)

    def test_contract_runner_provisions_required_tools_and_git_history(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/contract-tests.yml').read_text())
        steps = workflow['jobs']['test']['steps']
        checkout = next(step for step in steps if step.get('uses', '').startswith('actions/checkout@'))
        self.assertEqual(checkout.get('with', {}).get('fetch-depth'), 0)
        runs = '\n'.join(step.get('run', '') for step in steps)
        self.assertIn('pip install PyYAML==6.0.2', runs)
        self.assertIn('apt-get install -y age', runs)


if __name__ == '__main__':
    unittest.main()
