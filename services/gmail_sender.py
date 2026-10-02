"""Send transactional email with a pre-authorized Gmail OAuth refresh token."""
import base64
import os
import requests


def send_message(message):
    # Tokens never go in URLs, logs, browser responses or the SQLite auth store.
    response = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': os.environ['OMNIXML_GMAIL_CLIENT_ID'],
        'client_secret': os.environ['OMNIXML_GMAIL_CLIENT_SECRET'],
        'refresh_token': os.environ['OMNIXML_GMAIL_REFRESH_TOKEN'],
        'grant_type': 'refresh_token',
    }, timeout=15, allow_redirects=False)
    if response.status_code != 200:
        raise RuntimeError('gmail authorization unavailable')
    info = response.json()
    token = info.get('access_token') if isinstance(info, dict) else None
    if not isinstance(token, str) or not token or len(token) > 8192:
        raise RuntimeError('gmail authorization unavailable')
    response = requests.post('https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
        headers={'Authorization': 'Bearer '+token},
        json={'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('ascii')},
        timeout=15, allow_redirects=False)
    if response.status_code != 200:
        raise RuntimeError('gmail delivery unavailable')
