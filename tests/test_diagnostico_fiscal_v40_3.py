from pathlib import Path


def test_diagnostico_fiscal_2_classifica_gravidade_causa_e_impacto():
    js = Path('static/diagnostico_fiscal_v40_3.js').read_text(encoding='utf-8')
    assert "return 'Base de cálculo + Alíquota'" in js
    assert "return 'Base de cálculo'" in js
    assert "return 'Alíquota'" in js
    assert "return 'Arredondamento'" in js
    assert "return 'Valor divergente'" in js
    assert "return 'Crítico'" in js
    assert "return 'Revisar'" in js
    assert "return 'Baixo impacto'" in js
    assert 'Math.abs(Number(group?.diff || 0))' in js


def test_diagnostico_fiscal_2_mostra_resumo_executivo_estavel():
    js = Path('static/diagnostico_fiscal_v40_3.js').read_text(encoding='utf-8')
    assert 'Diagnóstico Fiscal 2.0' in js
    assert 'Impacto estimado' in js
    assert 'Principal causa' in js
    assert 'auditor.parentNode.insertBefore(panel, auditor)' in js
    assert 'scheduleInitialRender' in js
    assert 'enhanceTable' not in js
    assert 'STATUS_ORDER' in js
    assert 'b.impact - a.impact' in js


def test_diagnostico_fiscal_2_substitui_resumo_visual_da_v38():
    css = Path('static/diagnostico_fiscal_v40_3.css').read_text(encoding='utf-8')
    assert '#cofins-pendencias-v38{display:none!important}' in css


def test_diagnostico_fiscal_2_enriquece_detalhe_sem_duplicar_acao():
    js = Path('static/diagnostico_fiscal_v40_3.js').read_text(encoding='utf-8')
    assert 'Causa provável' in js
    assert 'Confiança' in js
    assert 'Ação sugerida' in js
    assert "actionRow.querySelector('span').textContent = item.action" in js
    assert 'requestAnimationFrame(() => requestAnimationFrame(enrichModal))' in js


def test_diagnostico_fiscal_2_e_carregado_pela_camadas_de_pendencias():
    js = Path('static/cofins_pendencias_v38.js').read_text(encoding='utf-8')
    assert 'loadDiagnosticoFiscalV403' in js
    assert '/static/diagnostico_fiscal_v40_3.js?v=1' in js
    assert '/static/diagnostico_fiscal_v40_3.css?v=1' in js


def test_diagnostico_fiscal_2_nao_altera_arquivos_fiscais():
    js = Path('static/diagnostico_fiscal_v40_3.js').read_text(encoding='utf-8').lower()
    assert 'xmlserializer' not in js
    assert 'download' not in js
    assert 'writefile' not in js
