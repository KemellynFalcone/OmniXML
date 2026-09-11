# Segurança — visão consolidada

## Princípios atuais

O OmniXML trata dados fiscais como entrada não confiável. Campos vindos de XML, SPED, nomes de arquivo e textos auxiliares não devem ser interpretados como HTML executável.

A arquitetura de segurança prioriza:

- `textContent` e APIs seguras de DOM para conteúdo dinâmico;
- escape explícito quando renderizadores precisam retornar marcação controlada;
- migração de handlers inline para listeners externos;
- Content Security Policy progressivamente mais restritiva;
- dependências de front-end fixadas e, quando possível, servidas localmente;
- processamento fiscal no navegador, sem envio dos XMLs ao servidor;
- testes automatizados para impedir regressões de segurança.

## XSS e DOM

A base segura é:

`dado fiscal não confiável → tratamento/escape → DOM`

Evitar concatenação de HTML com valores fiscais, nomes, motivos, produtos, razão social ou qualquer texto vindo de arquivo importado.

## CSP e scripts

A evolução de segurança removeu dependências de `unsafe-inline` conforme handlers e scripts foram migrados. A CSP deve permanecer alinhada aos assets realmente utilizados em produção.

## Dependências locais

A evolução mais recente documentada mantém Chart.js 4.5.1 servido localmente. jQuery e JSZip também passaram por fixação/localização em fases anteriores. Dependências externas remanescentes devem ser reduzidas de forma controlada e acompanhadas por testes.

## Arquitetura browser-local

O princípio central permanece: o processamento dos arquivos fiscais ocorre localmente no navegador. O backend não deve receber o conteúdo integral dos XMLs apenas para executar a auditoria.

## Validação

Mudanças de segurança devem preservar:

- regras fiscais;
- classificação Entrada/Saída;
- compatibilidade com CNPJ alfanumérico;
- inutilização e sequência;
- exportações e relatórios;
- funcionamento do dashboard.

## Histórico

As fases de segurança 4 a 21 foram preservadas integralmente em `docs/historico/seguranca/`. Esses arquivos registram a evolução passo a passo e servem como trilha de auditoria técnica; este documento representa a visão consolidada atual.
