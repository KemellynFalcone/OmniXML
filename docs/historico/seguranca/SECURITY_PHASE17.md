# Security Phase 17 — probe opt-in de `style-src-attr 'none'`

## Contexto

Após a Phase 15/16, o inventário real de produção mostrou que o OmniXML não gera mais estilos inline próprios (`app: 0`). As ocorrências remanescentes concentram-se em DataTables, Chart.js e elementos temporários de medição/layout criados por bibliotecas.

Referência observada em produção antes desta fase:

- DataTables: 15, apenas `width` em cabeçalhos de tabela;
- Chart.js: 13, com `box-sizing`, `display`, `height` e `width` nos três canvases;
- App: 0;
- Outros: 8, todos `div`, com propriedades típicas de medição/layout de inicialização.

## Objetivo

Testar a CSP estrita real no navegador sem alterar a política aplicada a todos os usuários.

## Modo de prova

A home aceita explicitamente:

`/?style_attr_strict=1`

Somente nessa requisição, a CSP aplicada troca:

`style-src-attr 'unsafe-inline'`

por:

`style-src-attr 'none'`

A resposta também inclui:

`X-OmniXML-Style-Attr-Probe: strict-v17`

Sem o parâmetro, a política padrão da Phase 12 permanece inalterada.

## Escopo e segurança

O probe:

- atua somente na rota `/`;
- exige opt-in explícito por query string;
- não altera `/health`, scripts ou CSS estáticos;
- não altera regras fiscais, processamento browser-local, CNPJ alfanumérico, DataTables ou Chart.js;
- não remove estilos nem modifica bibliotecas;
- serve apenas para validar comportamento real sob CSP estrita.

## Validação manual esperada

No modo estrito, validar:

1. carregamento e aparência geral do dashboard;
2. sidebar e abas;
3. DataTables: cabeçalhos, colunas, busca, paginação e exportação;
4. gráficos CFOP, CST e evolução;
5. modal de produtos;
6. processamento de XMLs;
7. tabela de erros e diagnóstico de fechamento;
8. console do navegador para erros funcionais relevantes.

Se o comportamento permanecer estável, a evidência permite avançar para a aplicação global de `style-src-attr 'none'` em fase posterior.