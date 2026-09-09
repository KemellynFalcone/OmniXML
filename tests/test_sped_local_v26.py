from pathlib import Path


def test_sped_local_v26_parseia_c100_sem_upload():
    js = Path('static/sped_local_v26.js').read_text(encoding='utf-8')
    assert "fields[1] !== 'C100'" in js
    assert "fields[2]" in js  # IND_OPER
    assert "fields[5]" in js  # COD_MOD
    assert "fields[6]" in js  # COD_SIT
    assert "fields[9]" in js  # CHV_NFE
    assert "fields[12]" in js  # VL_DOC
    assert "file.text()" in js
    assert "fetch('/importar_sped')" not in js


def test_sped_local_v26_suporta_nfe_e_nfce_e_exclui_cancelados():
    js = Path('static/sped_local_v26.js').read_text(encoding='utf-8')
    assert "new Set(['02', '03', '04', '05'])" in js
    assert "new Set(['55', '65'])" in js
    assert "doc.cod_mod === '55' && doc.operacao === 'Entrada'" in js
    assert "doc.cod_mod === '55' && doc.operacao === 'Saída'" in js
    assert "doc.cod_mod === '65' && doc.operacao === 'Saída'" in js


def test_sped_local_v26_alimenta_tela_e_detalhamento_existentes():
    js = Path('static/sped_local_v26.js').read_text(encoding='utf-8')
    assert 'spedNotasDetalhadas = summary.detalhes' in js
    assert "document.getElementById('placeholder-sped')?.classList.add('hidden')" in js
    assert "document.getElementById('resultado-sped')?.classList.remove('hidden')" in js
    assert "document.getElementById('btnDivergencias')?.classList.remove('hidden')" in js
    assert 'window.confrontarSPED = () => input.click()' in js


def test_sped_local_v26_integrado_ao_app_e_health():
    app = Path('web_app_browser.py').read_text(encoding='utf-8')
    assert '/static/sped_local_v26.js?v=1' in app
    assert "'sped_processing': 'browser-local-c100-v26'" in app
