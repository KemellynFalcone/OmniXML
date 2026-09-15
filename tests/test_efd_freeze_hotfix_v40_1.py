from pathlib import Path


def test_v38_nao_observa_mutacoes_globais_para_renderizar_fila():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'MutationObserver' not in js
    assert "document.getElementById('res-pis-cofins')" in js
    assert "const signature = JSON.stringify(counts);" in js
    assert 'panel.dataset.renderSignature === signature' in js


def test_v38_injeta_tratativa_por_interacao_explicita_no_modal():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert "document.addEventListener('click'" in js
    assert "event.target.closest('[data-cofins-details]')" in js
    assert 'requestAnimationFrame' in js
    assert 'if (modal) injectTreatment(modal);' in js


def test_v38_salvar_tratativa_forca_atualizacao_da_fila():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'delete panel.dataset.renderSignature' in js
    assert 'renderQueue();' in js
    assert 'omnixml:cofins-pendency-updated' in js
