from pathlib import Path


def test_v38_nao_renderiza_fila_em_toda_mutacao_da_pagina():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'shouldRenderQueue' in js
    assert "node.id === 'cofins-auditor-v34'" in js
    assert 'if (shouldRenderQueue) renderQueue();' in js
    assert "const signature = JSON.stringify(counts);" in js
    assert 'panel.dataset.renderSignature === signature' in js


def test_v38_ainda_injeta_tratativa_quando_modal_e_criado():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert "node.id === 'cofins-auditor-v35-modal'" in js
    assert 'if (modal) injectTreatment(modal);' in js


def test_v38_salvar_tratativa_forca_atualizacao_da_fila():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'delete panel.dataset.renderSignature' in js
    assert 'renderQueue();' in js
