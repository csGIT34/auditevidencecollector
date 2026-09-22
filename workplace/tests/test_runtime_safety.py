import unittest
from unittest.mock import Mock, patch
from tests.test_hosting import environment
from cloud_governance.hosting import execute


class RuntimeSafetyTests(unittest.TestCase):
    def test_expired_operation_never_creates_credentials_or_storage(self):
        factory=Mock(side_effect=AssertionError('must not connect'))
        for expires in ('2020-01-01T00:00:00Z','2030-01-01T00:00:00','invalid'):
            with self.subTest(expires=expires),self.assertLogs('cloud_governance'),self.assertRaises(RuntimeError):
                execute('collect',env={**environment(),'CG_EXECUTION_EXPIRES_AT':expires},factory=factory)
        factory.assert_not_called()


    def test_standard_package_contains_only_runtime_files(self):
        import tempfile,zipfile
        from pathlib import Path
        from scripts.package_functions import package
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'source.zip';package(path)
            with zipfile.ZipFile(path) as archive:
                self.assertTrue(all(n.startswith('cloud_governance/') or n in {'function_app.py', 'host.json', 'requirements.txt', 'constraints.txt'} for n in archive.namelist()))

    def test_linux_arm_builder_rejected_before_installing_or_writing(self):
        from scripts.build_functions_package import build
        with patch('scripts.build_functions_package.platform.system',return_value='Linux'),patch('scripts.build_functions_package.platform.machine',return_value='aarch64'),patch('scripts.build_functions_package.subprocess.run') as install:
            with self.assertRaisesRegex(RuntimeError,'x86_64'):build('/tmp/unsupported-arm-functions.zip')
            install.assert_not_called()

    def test_private_build_files_remain_readable_in_deployment_archive(self):
        import os, tempfile, zipfile
        from pathlib import Path
        from scripts.build_functions_package import build

        def install(command, **kwargs):
            target = Path(command[command.index('--target') + 1])
            target.mkdir(parents=True)
            (target / 'private_dependency.py').write_text('VALUE = 1\n')
            (target / 'private_dependency.py').chmod(0o600)

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'function.zip'
            previous = os.umask(0o077)
            try:
                with patch('scripts.build_functions_package.platform.system', return_value='Linux'), \
                     patch('scripts.build_functions_package.platform.machine', return_value='x86_64'), \
                     patch('scripts.build_functions_package.sys.version_info', (3, 12)), \
                     patch('scripts.build_functions_package.subprocess.run', side_effect=install):
                    build(output)
            finally:
                os.umask(previous)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with zipfile.ZipFile(output) as archive:
                self.assertIn('.python_packages/lib/site-packages/private_dependency.py', archive.namelist())
                for item in archive.infolist():
                    self.assertEqual((item.external_attr >> 16) & 0o777, 0o644, item.filename)
