from pathlib import Path


def test_failure_table_espera_init_completo_e_usa_idioma_local():
    script = Path('static/failure_table_v2.js').read_text(encoding='utf-8')
    assert "_bInitComplete" in script
    assert "init.dt.failureV2Bootstrap" in script
    assert "$.fn.DataTable.isDataTable('#tabelaErros')" in script
    assert "language: { url: '/static/datatables_ptbr_v10.json' }" in script
    assert 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json' not in script


def test_failure_table_preserva_rebuild_e_detalhes_financeiros():
    script = Path('static/failure_table_v2.js').read_text(encoding='utf-8')
    assert 'dtErros.destroy' in script
    assert 'Chave de Acesso' in script
    assert 'Valor total envolvido' in script
    assert "table.dataset.failureV2 = '1'" in script
