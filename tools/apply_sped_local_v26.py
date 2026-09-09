from pathlib import Path

path = Path('web_app_browser.py')
text = path.read_text(encoding='utf-8')

script_marker = "        '<script src=\"/static/browser_local_v2.js?v=2&cnpj=1&style=13\"></script>'\n"
script_line = script_marker + "        '<script src=\"/static/sped_local_v26.js?v=1\"></script>'\n"
if '/static/sped_local_v26.js?v=1' not in text:
    if script_marker not in text:
        raise SystemExit('Ponto de injeção após browser_local_v2.js não encontrado')
    text = text.replace(script_marker, script_line, 1)

health_marker = "        'script_assets': 'local-jquery-jszip-chartjs-v21',\n"
health_line = health_marker + "        'sped_processing': 'browser-local-c100-v26',\n"
if "'sped_processing': 'browser-local-c100-v26'" not in text:
    if health_marker not in text:
        raise SystemExit('Ponto do /health para SPED local não encontrado')
    text = text.replace(health_marker, health_line, 1)

path.write_text(text, encoding='utf-8')
print('SPED local v26 materializado em web_app_browser.py')
