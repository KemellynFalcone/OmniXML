from pathlib import Path


def test_v38_nao_observa_dom_global_e_usa_host_estavel():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'MutationObserver' not in js
    assert "document.getElementById('res-pis-cofins')" in js
    assert "document.getElementById('cofins-auditor-v34')" not in js


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


def test_v38_badges_usam_status_real_para_estilo_e_label_com_contagem():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'function badge(status, label = status)' in js
    assert 'badge(s, `${s}: ${counts[s] || 0}`)' in js
