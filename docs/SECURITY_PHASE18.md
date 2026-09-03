# Security Phase 18 — style-src-attr estrito global

## Objetivo

Aplicar globalmente `style-src-attr 'none'` após validação real em produção do probe opt-in da Phase 17.

## Evidência usada

A Phase 16 identificou os estilos inline restantes como provenientes principalmente de DataTables e Chart.js, com `app: 0`. A Phase 17 permitiu executar o dashboard em produção com `style-src-attr 'none'` apenas por opt-in. O fluxo foi validado visual e funcionalmente antes desta promoção.

## Mudanças

- `Content-Security-Policy` passa a usar `style-src-attr 'none'` por padrão.
- A compatibilidade `style-src-attr 'unsafe-inline'` é removida do enforcement.
- O probe `?style_attr_strict=1` deixa de ser necessário e não altera mais cabeçalhos.
- O cabeçalho temporário `X-OmniXML-Style-Attr-Probe` é retirado.
- O Report-Only permanece alinhado em `style-src-attr 'none'`.
- `/health` passa a expor:
  - `style_csp_enforcement = strict-elements-and-attrs-v18`
  - `style_attr_probe = validated-and-retired-v18`

## Escopo funcional

Não há alteração nas regras fiscais, classificação Entrada/Saída, CNPJ alfanumérico, processamento browser-local, DataTables, Chart.js ou exportação.

## Validação pós-deploy

Validar visual do dashboard, gráficos, tabelas, paginação, filtros, exportação Excel, modal de produtos, Arquivos com Erro e processamento de XMLs reais.
