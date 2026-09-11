# Hotfix Dashboard v25 — sincronização do estado real

## Problema

Após a UX Dashboard v24, o preview `Dados ilustrativos` deveria desaparecer quando a auditoria local terminasse. Em produção, os KPIs reais eram preenchidos e a faixa de resumo era exibida, mas o preview permanecia visível.

## Causa

A v24 amarrou a troca de estado ao fluxo histórico `iniciarProcessamento()` do runtime do template. Em produção, o processamento efetivo é feito por `static/browser_local_v2.js`, que atualiza os KPIs e remove `hidden` de `#faixa-resumo-auditoria`, mas não executa o trecho histórico que escondia `#dashboard-preview-v24` e mostrava `#dashboard-real-v24`.

## Correção

O bridge externo, já carregado após o processador browser-local, passa a sincronizar o estado visual do Dashboard Geral usando a própria faixa de resumo como fonte de verdade:

- `#faixa-resumo-auditoria.hidden` → preview visível e gráficos reais ocultos;
- faixa de resumo visível → preview oculto e gráficos reais visíveis.

Um `MutationObserver` observa somente a classe da faixa de resumo. Nenhum dado fiscal é alterado e nenhum `style=` é criado.

## Escopo preservado

- classificação fiscal;
- valores dos KPIs;
- gráficos reais;
- CNPJ alfanumérico;
- processamento browser-local;
- CSP `style-src-attr 'none'`.
