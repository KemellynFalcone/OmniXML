import pytest

@pytest.fixture(autouse=True)
def authenticated_page_rendering(request, monkeypatch):
    # Legacy rendering/fiscal unit tests run inside the portal; auth suites use real sessions.
    if request.module.__name__.split('.')[-1] not in {'test_portal_login', 'test_email_access', 'test_client_admin', 'test_d1_registry'}:
        import web_app_browser
        monkeypatch.setattr(web_app_browser, 'current_user', lambda: 'render-test@example.com')
