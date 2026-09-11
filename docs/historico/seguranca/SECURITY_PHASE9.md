# Security Phase 9 — CSS próprio externo e preparação de CSP de estilos

## Objetivo

Reduzir o débito que ainda exige `style-src 'unsafe-inline'`, sem causar regressão visual no dashboard.

## Contexto

A política de scripts já opera sem `unsafe-inline`. Para estilos, ainda existem dois grupos diferentes:

1. CSS próprio do OmniXML, anteriormente presente em um bloco `<style>` no template;
2. CSS gerado/injetado em tempo de execução por dependências externas, principalmente Tailwind CDN e componentes de terceiros.

Remover `unsafe-inline` diretamente da política aplicada antes de substituir essas dependências pode quebrar a interface.

## Implementação da Fase 9

- o bloco CSS próprio do dashboard é removido do HTML entregue;
- esse conteúdo passa a ser servido por `/static/dashboard_style_v9.css`;
- o HTML entregue recebe um `<link rel="stylesheet">` para o recurso local;
- a CSP aplicada continua temporariamente com `style-src 'unsafe-inline'` para compatibilidade com Tailwind/DataTables;
- a CSP Report-Only passa a testar uma diretiva `style-src` sem `unsafe-inline`;
- `/health` publica `style_csp = own-css-external-strict-report-only-v9`.

## Segurança

A mudança reduz a quantidade de CSS inline controlado pela aplicação e permite medir o débito restante antes de endurecer a política aplicada.

## Compatibilidade

Não há alteração intencional em regras fiscais, processamento de XML/SPED, layout, cores ou navegação.

## Dependências ainda relevantes

O HTML continua usando Tailwind CDN e DataTables CDN. O Tailwind via CDN gera estilos em tempo de execução, por isso a política aplicada ainda não pode remover `unsafe-inline` com segurança.

## Próxima etapa

Substituir Tailwind CDN e demais dependências que exigem estilo inline/dinâmico por ativos locais ou uma estratégia de build compatível com CSP estrita. Somente depois disso `unsafe-inline` deve ser removido do `style-src` aplicado.
