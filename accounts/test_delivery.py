import io
import os
from contextlib import redirect_stdout
from unittest import TestCase
from unittest.mock import patch, MagicMock
from scripts import check_service, deploy


class DeliveryTests(TestCase):
    @patch.dict(os.environ, {'APP_URL': 'https://retail.example', 'MONITORING_TOKEN': 'secret', 'EXPECTED_REVISION': 'abc', 'CHECK_ATTEMPTS': '1', 'FAILURE_DRILL': 'false'}, clear=True)
    def test_checks_expected_revision_and_metrics(self):
        with patch.object(check_service, 'get_json', side_effect=[{'status': 'ok', 'revision': 'abc'}, {'memory_bytes': 1048576, 'cpu_seconds_total': 2}]) as get:
            with redirect_stdout(io.StringIO()) as output:
                check_service.main()
        self.assertIn('Health check passed', output.getvalue())
        self.assertNotIn('secret', output.getvalue())
        self.assertEqual(get.call_args_list[1].args, ('https://retail.example/metrics/', 'secret'))

    @patch.dict(os.environ, {'APP_URL': 'https://retail.example', 'MONITORING_TOKEN': 'secret', 'EXPECTED_REVISION': 'new', 'CHECK_ATTEMPTS': '1'}, clear=True)
    def test_old_revision_does_not_pass_deployment(self):
        with patch.object(check_service, 'get_json', return_value={'status': 'ok', 'revision': 'old'}):
            with self.assertRaises(SystemExit):
                check_service.main()

    @patch.dict(os.environ, {'APP_URL': 'https://retail.example', 'FAILURE_DRILL': 'true'}, clear=True)
    def test_drill_fails_without_logging_sensitive_exception(self):
        with patch.object(check_service, 'get_json', side_effect=ValueError('secret-token')) as get:
            with redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit):
                check_service.main()
        self.assertNotIn('secret-token', output.getvalue())
        self.assertEqual(get.call_args.args[0], 'https://retail.example/__monitoring_drill__/')

    @patch.dict(os.environ, {'RENDER_DEPLOY_HOOK': 'https://api.render.com/deploy/srv-example?key=secret', 'GITHUB_SHA': 'abc123'}, clear=True)
    def test_deploy_pins_tested_commit(self):
        response = MagicMock()
        response.__enter__.return_value.status = 200
        with patch.object(deploy, 'urlopen', return_value=response) as send:
            with redirect_stdout(io.StringIO()) as output:
                deploy.main()
        self.assertIn('ref=abc123', send.call_args.args[0].full_url)
        self.assertNotIn('secret', output.getvalue())
