"""Server-only D1 adapter for the minimal client registry."""
import os
import re
import requests

KEYS = ('OMNIXML_D1_ACCOUNT_ID', 'OMNIXML_D1_DATABASE_ID', 'OMNIXML_D1_API_TOKEN')


class StorageUnavailable(RuntimeError):
    pass


def selected():
    return any(os.environ.get(key) for key in KEYS)


class Result:
    def __init__(self, result):
        self.rows = [tuple(row[key] for key in ('email', 'active', 'created') if key in row)
                     for row in result.get('results', [])]
        self.rowcount = result.get('meta', {}).get('changes', 0)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def __iter__(self):
        return iter(self.rows)


class Connection:
    def __init__(self):
        account, database, token = (os.environ.get(key, '') for key in KEYS)
        if not re.fullmatch(r'[a-fA-F0-9]{32}', account) or not re.fullmatch(r'[a-fA-F0-9-]{36}', database) or not token:
            raise StorageUnavailable('Complete as três variáveis OMNIXML_D1 no Render.')
        self.url = f'https://api.cloudflare.com/client/v4/accounts/{account}/d1/database/{database}/query'
        self.headers = {'Authorization': f'Bearer {token}'}

    def execute(self, sql, params=()):
        try:
            response = requests.post(self.url, headers=self.headers,
                                     json={'sql':sql, 'params':list(params)},
                                     timeout=(5, 20), allow_redirects=False)
            if response.status_code != 200:
                raise StorageUnavailable('Banco D1 indisponível. Confira a configuração ou tente novamente.')
            data = response.json()
            results = data.get('result')
            if data.get('success') is not True or not isinstance(results, list) or len(results) != 1 or results[0].get('success') is not True:
                raise StorageUnavailable('Não foi possível consultar o banco D1.')
            return Result(results[0])
        except (requests.RequestException, ValueError, TypeError, KeyError, AttributeError):
            # Never expose provider response, token, SQL values or email in errors.
            raise StorageUnavailable('Não foi possível consultar o banco D1. Tente novamente.') from None
