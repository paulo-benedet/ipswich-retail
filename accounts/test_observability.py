import io
import json
import logging
from unittest.mock import patch
from django.db import OperationalError
from django.test import TestCase, override_settings
from config.observability import SafeJsonFormatter


class ObservabilityTests(TestCase):
    def test_health_checks_database_and_returns_revision(self):
        with override_settings(APP_REVISION='test-revision'):
            response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'revision': 'test-revision'})
        self.assertIn('X-Request-ID', response)

    def test_database_failure_is_503_and_does_not_disclose_exception(self):
        with patch('config.health.connection.cursor', side_effect=OperationalError('SECRET-db-url')):
            with self.assertLogs('retail', level='ERROR') as logs:
                response = self.client.get('/health/')
        self.assertEqual(response.status_code, 503)
        formatter = SafeJsonFormatter()
        output = '\n'.join(formatter.format(r) for r in logs.records)
        self.assertNotIn('SECRET-db-url', output)
        self.assertNotIn('SECRET-db-url', response.content.decode())
        self.assertIn('OperationalError', output)

    @override_settings(MONITORING_TOKEN='test-token')
    def test_metrics_require_token(self):
        self.assertEqual(self.client.get('/metrics/').status_code, 401)
        self.assertEqual(self.client.get('/metrics/', HTTP_AUTHORIZATION='Bearer wrong').status_code, 401)
        response = self.client.get('/metrics/', HTTP_AUTHORIZATION='Bearer test-token')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()['memory_bytes'], 0)

    def test_formatter_drops_sensitive_message_and_request_data(self):
        record = logging.LogRecord('django.request', logging.ERROR, '', 1, 'SECRET-password', (), None)
        record.request = {'password': 'SECRET-password'}
        output = SafeJsonFormatter().format(record)
        self.assertNotIn('SECRET', output)
        self.assertIn('timestamp', json.loads(output))
