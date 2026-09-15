from pathlib import Path


def test_v38_nao_observa_dom_global_e_mantem_painel_fora_do_auditor():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'MutationObserver' not in js
    assert "document.getElementById('res-pis-cofins')" in js
    assert "document.getElementById('cofins-auditor-v34')" in js
    assert 'auditor.parentNode.insertBefore(panel, auditor)' in js
    assert 'auditor.append' not in js


def test_v38_injeta_tratativa_por_evento_de_clique():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert "document.addEventListener('click'" in js
    assert "event.target.closest('[data-cofins-details]')" in js
    assert 'requestAnimationFrame' in js
    assert 'injectTreatment(modal)' in js


def test_v38_atualiza_fila_sem_reescrever_quando_estado_nao_muda():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'panel.dataset.renderSignature === signature' in js
    assert 'delete panel.dataset.renderSignature' in js
    assert "omnixml:cofins-pendency-updated" in js


def test_v38_mostra_apenas_badges_com_contagem_maior_que_zero():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'function badge(status, label = status)' in js
    assert '.filter(status => (counts[status] || 0) > 0)' in js
    assert '`${status} ${counts[status]}`' in js


def test_v38_remove_resumo_quando_nao_ha_divergencias_atuais():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'if (!items.length)' in js
    assert 'panel?.remove();' in js
