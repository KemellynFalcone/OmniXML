# Security Phase 20 — jQuery e JSZip locais

## Objetivo

Remover do carregamento do navegador as dependências externas de jQuery 3.7.0 e JSZip 3.10.1, preservando as versões já validadas no OmniXML e sem alterar layout, DataTables, exportação Excel ou regras fiscais.

## Assets versionados

- `static/vendor/jquery-3.7.0.min.js`
- `static/vendor/jszip-3.10.1.min.js`

Os arquivos são obtidos das tags upstream exatas e conferidos pelo Git blob SHA antes de entrarem na branch:

- jQuery 3.7.0 `dist/jquery.min.js`: `e7e29d5b2a3d258d389ee074ba04353e68f8ffbc`
- JSZip 3.10.1 `dist/jszip.min.js`: `ff4cfd5e8fdc49176c2d1d409afa897f40be01f4`

O passo usado apenas para materializar os arquivos na branch é temporário e deve ser removido do workflow antes do merge. Os assets resultantes permanecem versionados no repositório.

## HTML entregue

O hardening do servidor substitui as referências históricas do template diretamente por:

```html
<script src="/static/vendor/jquery-3.7.0.min.js?v=20"></script>
<script src="/static/vendor/jszip-3.10.1.min.js?v=20"></script>
```

As URLs CDN de jQuery e JSZip não aparecem no HTML final.

## CSP

A Phase 20 não remove ainda `cdn.jsdelivr.net` de `script-src`, pois Chart.js 4.5.1 continua sendo servido por esse host. `cdn.datatables.net` também permanece necessário para DataTables e Buttons.

A política de atributos de estilo da Phase 18 continua:

```text
style-src-attr 'none'
```

## Health

`/health` publica:

```text
script_assets = local-jquery-jszip-pinned-chartjs-v20
```

## Validação funcional esperada

Após deploy, validar na home normal:

1. processamento de XML;
2. inicialização e paginação das DataTables;
3. pesquisa/filtros;
4. exportação Excel (dependente de JSZip);
5. gráficos;
6. ausência de regressão visual.

Nenhum XML é enviado ao servidor; `processing = browser-local` e `xml_upload = false` permanecem inalterados.
