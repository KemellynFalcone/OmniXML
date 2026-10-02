"""Send transactional email; log only fixed diagnostic categories, never payloads."""
import base64
import logging
import os
import requests

_logger = logging.getLogger(__name__)
_OAUTH_ERRORS = {'invalid_grant', 'invalid_client', 'unauthorized_client', 'invalid_scope', 'access_denied'}
_GMAIL_REASONS = {'authError', 'forbidden', 'insufficientPermissions', 'accessNotConfigured', 'rateLimitExceeded', 'userRateLimitExceeded', 'dailyLimitExceeded', 'backendError', 'invalidArgument'}


def fail(stage, reason, status=0):
    _logger.warning('omnixml_gmail_failed stage=%s reason=%s http_status=%s', stage, reason, status)
    raise RuntimeError('gmail delivery unavailable') from None


def post(stage, url, **kwargs):
    try:
        return requests.post(url, timeout=15, allow_redirects=False, **kwargs)
    except requests.Timeout:
        fail(stage, 'timeout')
    except requests.RequestException:
        fail(stage, 'connection_error')


def error_reason(response, stage):
    try:
        data = response.json()
        error = data.get('error') if isinstance(data, dict) else None
        if stage == 'oauth_refresh':
            return error if isinstance(error, str) and error in _OAUTH_ERRORS else 'provider_error'
        if isinstance(error, dict):
            for item in error.get('errors', []):
                if isinstance(item, dict) and item.get('reason') in _GMAIL_REASONS:
                    return item['reason']
        return 'provider_error'
    except (ValueError, TypeError):
        return 'invalid_response'


def send_message(message):
    keys = ('OMNIXML_GMAIL_CLIENT_ID', 'OMNIXML_GMAIL_CLIENT_SECRET', 'OMNIXML_GMAIL_REFRESH_TOKEN')
    if not all(os.environ.get(key) for key in keys):
        fail('configuration', 'missing_credentials')
    response = post('oauth_refresh', 'https://oauth2.googleapis.com/token', data={
        'client_id': os.environ[keys[0]],
        'client_secret': os.environ[keys[1]],
        'refresh_token': os.environ[keys[2]],
        'grant_type': 'refresh_token',
    })
    if response.status_code != 200:
        fail('oauth_refresh', error_reason(response, 'oauth_refresh'), response.status_code)
    try:
        info = response.json()
    except ValueError:
        fail('oauth_refresh', 'invalid_response', response.status_code)
    token = info.get('access_token') if isinstance(info, dict) else None
    if not isinstance(token, str) or not token or len(token) > 8192:
        fail('oauth_refresh', 'missing_access_token', response.status_code)
    response = post('gmail_send', 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
        headers={'Authorization': 'Bearer '+token},
        json={'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('ascii')})
    if response.status_code != 200:
        fail('gmail_send', error_reason(response, 'gmail_send'), response.status_code)
