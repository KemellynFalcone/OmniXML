# Security Phase 21 — Chart.js local

## Objetivo

Eliminar a dependência externa do Chart.js no runtime do dashboard sem alterar gráficos, layout, processamento fiscal ou arquitetura browser-local.

## Mudança

- Chart.js permanece na versão 4.5.1.
- O build UMD passa a ser servido por `/static/vendor/chart-4.5.1.umd.min.js?v=21`.
- jQuery 3.7.0 e JSZip 3.10.1 continuam locais conforme a Phase 20.
- DataTables permanece externo nesta fase.
- O host `https://cdn.jsdelivr.net` é removido de `script-src` na CSP aplicada e na Report-Only.
- O contrato `/health` passa a publicar `script_assets = local-jquery-jszip-chartjs-v21`.

## Origem e fixação

O arquivo é materializado a partir do pacote npm `chart.js@4.5.1` via jsDelivr, com URL versionada. O bootstrap valida o cabeçalho `Chart.js v4.5.1` antes de versionar o arquivo no repositório. O asset resultante passa a ser servido exclusivamente pelo próprio OmniXML.

## Não alterado

- regras fiscais e classificação Entrada/Saída;
- CNPJ alfanumérico;
- sequência e inutilização;
- DataTables e exportação Excel;
- CSP de estilos da Phase 18;
- processamento XML integralmente no navegador.

## Validação de produção

Após o deploy do `main`, confirmar `/health`, carregar o dashboard com Ctrl+F5, processar XMLs e validar os gráficos. No HTML/CSP não deve existir `cdn.jsdelivr.net` como fonte de scripts.
