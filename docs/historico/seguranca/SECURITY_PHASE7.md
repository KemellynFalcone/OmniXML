# Security Phase 7 — Runtime sinks

## Objetivo

Reduzir a superfície de XSS ainda presente nos renderizadores legados do dashboard sem alterar regras fiscais, classificação, sequência documental ou aparência planejada.

## Implementado

- A sanitização de cópia para display passa a incluir também `dtErros`, que recebe nomes de arquivo, caminhos e motivos derivados de XML/validação.
- `cloneForDisplay` e `patchDataTables` passam a ser expostos no namespace técnico `window.__omnixmlSecurityV2` para facilitar testes de regressão e inspeção.
- O carregamento de `browser_security_v2.js` recebe novo cache-bust (`v=2`).
- `/health` publica `runtime_sinks = all-primary-datatables-display-escaped-v7`.
- Foram adicionados testes estáticos para cobertura de caracteres adversariais (`&`, `<`, `>`, aspas) e para garantir que a tabela de erros permaneça incluída na camada de display seguro.

## Escopo e limitações

Esta fase endurece a fronteira de dados das DataTables principais. Ela não afirma que todo uso de HTML no runtime legado foi eliminado. Renderizadores que produzem markup controlado continuam existindo, mas os valores textuais derivados de XML/SPED são sanitizados antes de chegar a esses renderizadores.

A CSP de scripts permanece estrita conforme a Fase 6. `style-src` ainda contém `unsafe-inline` e será tratado em fase posterior.

## Evidência

- `static/browser_security_v2.js`
- `tests/test_security_phase7.py`
- `web_app_browser.py` (`/health`)

## Próximos passos

1. revisar renderizadores HTML remanescentes e substituir markup dinâmico por criação de DOM quando viável;
2. reduzir dependência de estilos inline;
3. avaliar hospedagem local das dependências CDN e endurecimento de `style-src`.
