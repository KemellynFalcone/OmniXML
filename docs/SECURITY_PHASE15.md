# Security Phase 15 — redução de estilos inline do DataTables

## Objetivo

Reduzir a principal origem restante de atributos `style` observada em produção antes de qualquer tentativa de aplicar `style-src-attr 'none'` na CSP.

## Evidência de produção usada

Inventário da Phase 14 após processamento real de XMLs:

- DataTables: 176 ocorrências
- Chart.js: 16 ocorrências
- OmniXML/app: 0 ocorrências
- Outros: 17 ocorrências

A aplicação própria já não depende de atributos `style`; a maior concentração está no DataTables.

## Mudança

`static/browser_security_v2.js` configura o default global do DataTables com:

```js
dataTable.defaults.autoWidth = false;
```

A configuração é executada durante o parsing do documento, antes do `DOMContentLoaded`, enquanto o runtime principal já registrou — mas ainda não executou — as inicializações das tabelas no `jQuery.ready`.

Isso reduz a necessidade de o DataTables escrever larguras inline automáticas em cabeçalhos e células, sem alterar dados, colunas, paginação, filtros ou exportação.

## Segurança da mudança

A CSP aplicada continua temporariamente com `style-src-attr 'unsafe-inline'`. A política Report-Only permanece com `style-src-attr 'none'`.

A Phase 15 não remove atributos de terceiros e não altera Chart.js. O objetivo é medir a redução real em produção antes de endurecer a CSP.

## Validação pós-deploy

Após `Ctrl + F5`, processar XMLs, navegar pelas tabelas e gráficos e executar:

```js
window.__omnixmlStyleAttrInventory
```

Comparar principalmente `dataTables` com a linha de base de 176 ocorrências. Também validar visual das tabelas, paginação, pesquisa, Arquivos com Erro e exportação Excel.
