# Security Phase 14 — Inventário de estilos inline de terceiros

## Objetivo

Preparar a remoção segura de `style-src-attr 'unsafe-inline'` sem comprometer DataTables, Chart.js ou a responsividade do dashboard.

## Contexto

Após a Phase 13, os estilos inline controlados diretamente pelo processador local foram removidos da barra de progresso. A política aplicada ainda mantém `style-src-attr 'unsafe-inline'` porque bibliotecas de terceiros podem escrever atributos `style` em tempo de execução.

A Phase 14 não força a remoção desses atributos. Primeiro coleta evidência real no navegador para distinguir estilos de DataTables, Chart.js, componentes próprios e outros elementos.

## Implementação

`static/browser_security_v2.js` passa a manter um inventário em memória exposto por:

```javascript
window.__omnixmlStyleAttrInventory
```

O inventário separa ocorrências em:

- `dataTables`: elementos dentro de `.dataTables_wrapper` ou tabelas DataTables;
- `chartjs`: elementos `canvas`;
- `app`: barra de progresso do OmniXML;
- `other`: demais elementos.

Também guarda uma amostra limitada dos primeiros 25 elementos observados, sem enviar dados ao servidor.

Um `MutationObserver` acompanha alterações posteriores no atributo `style`. A rotina é estritamente diagnóstica: não remove nem altera estilos.

## Como validar em produção

1. Abra o OmniXML e faça `Ctrl + F5`.
2. Processe uma pasta real de XMLs.
3. Navegue pelas tabelas, paginação e filtros.
4. Abra as telas com gráficos.
5. No console do navegador, execute:

```javascript
window.__omnixmlStyleAttrInventory
```

O resultado indicará quais grupos ainda geram atributos `style`.

## Segurança e privacidade

O inventário fica somente em memória no navegador. Nenhum XML, conteúdo fiscal ou amostra de estilo é transmitido ao servidor.

## CSP

Nesta fase a política aplicada permanece:

```text
style-src-attr 'unsafe-inline'
```

A política Report-Only continua testando:

```text
style-src-attr 'none'
```

Isso evita regressão visual antes de sabermos exatamente quais dependências ainda usam estilos inline.

## Próxima etapa

Com o inventário de uma auditoria real, a próxima fase deve eliminar ou substituir os estilos remanescentes por grupo. Somente depois disso `style-src-attr 'none'` deve ser promovido para a CSP aplicada.
