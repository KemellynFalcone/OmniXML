from pathlib import Path


def test_v38_fica_desativada_no_loader_durante_hotfix_de_congelamento():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'const ENABLE_COFINS_PENDENCIAS_V38 = false;' in bridge
    assert 'if (ENABLE_COFINS_PENDENCIAS_V38) loadCofinsPendenciasV38();' in bridge


def test_demais_modulos_de_auditoria_continuam_carregados():
    bridge = Path('static/inline_handler_bridge_v5.js').read_text(encoding='utf-8')
    assert 'loadCofinsAuditorV34();' in bridge
    assert 'loadCofinsOrigemV39();' in bridge
    assert 'loadBlocoMV40();' in bridge
    assert 'loadBlocoMArredondamentoV401();' in bridge
