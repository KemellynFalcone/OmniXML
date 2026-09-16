from pathlib import Path


def test_serie_detalhe_expande_linha_com_bruto_cancelado_liquido():
    js = Path('static/serie_cancelados_v41.js').read_text(encoding='utf-8')
    assert 'Total bruto' in js
    assert 'Cancelado' in js
    assert 'Total líquido' in js
    assert 'serieTable.row(rowNode).child' in js
    assert 'const bruto = liquido + cancelado;' in js


def test_serie_detalhe_separa_tipo_e_serie_para_nao_misturar_documentos():
    js = Path('static/serie_cancelados_v41.js').read_text(encoding='utf-8')
    assert 'cancelledByTypeAndSeries' in js
    assert 'const key = `${tipo}|${serie}`;' in js
    assert 'quantidade' in js


def test_serie_detalhe_preserva_liquido_atual_e_calcula_bruto():
    js = Path('static/serie_cancelados_v41.js').read_text(encoding='utf-8')
    assert 'const liquido = Number(data?.valor || 0);' in js
    assert 'const cancelado = Number(cancellation?.valor || 0);' in js
    assert 'const bruto = liquido + cancelado;' in js


def test_serie_detalhe_tem_acessibilidade_basica():
    js = Path('static/serie_cancelados_v41.js').read_text(encoding='utf-8')
    assert "this.setAttribute('tabindex', '0')" in js
    assert "event.key !== 'Enter' && event.key !== ' '" in js
    assert "this.setAttribute('aria-expanded'" in js
