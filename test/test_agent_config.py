import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from utils.config import load_project_env


class AgentConfigTests(unittest.TestCase):
    def test_env_file_loads_without_overriding_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / '.env'
            config.write_text('MIMIC_ENV=cloud\nBIGQUERY_PROJECT=file-project\n')
            with patch.dict(os.environ, {'BIGQUERY_PROJECT': 'shell-project'}, clear=True):
                load_project_env(config)
                self.assertEqual(os.environ['MIMIC_ENV'], 'cloud')
                self.assertEqual(os.environ['BIGQUERY_PROJECT'], 'shell-project')
