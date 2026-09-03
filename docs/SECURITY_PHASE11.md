# Security Phase 11 — Tailwind compilado e local

## Objetivo

Remover o Tailwind Play CDN da execução em produção sem alterar o layout do dashboard ou as regras fiscais do OmniXML.

## Implementação

- Tailwind CSS fixado em `3.4.17` no `package.json`.
- Conteúdo compilado a partir de `templates/**/*.html` e `static/**/*.js`.
- CSS minificado gerado em `static/tailwind_v11.css`.
- A página entregue ao navegador troca `https://cdn.tailwindcss.com` por `/static/tailwind_v11.css?v=1`.
- `cdn.tailwindcss.com` foi removido de `script-src` tanto na CSP aplicada quanto na política Report-Only.
- O build pode ser reproduzido com `npm install` e `npm run build:tailwind`.

## Preservação visual

O compilador escaneia o template e os scripts estáticos, incluindo classes utilizadas por componentes gerados dinamicamente. Testes verificam utilitários críticos como largura da sidebar, cores do dashboard, grid responsivo e estados hover.

## Contratos preservados

A Phase 11 não altera:

- processamento browser-local;
- identificação e classificação por CNPJ;
- suporte ao CNPJ alfanumérico;
- validação fiscal dos XMLs;
- reconciliação de inutilizações;
- DataTables e exportação Excel;
- Chart.js fixado na Phase 10;
- runtime externo da Phase 6;
- renderizadores seguros das Phases 7 e 8.

## CSP

A retirada do Tailwind CDN permite remover a origem `cdn.tailwindcss.com` do `script-src`. O `style-src` aplicado ainda mantém `'unsafe-inline'` nesta fase por compatibilidade com estilos dinâmicos/legados remanescentes. A remoção desse token deve ocorrer somente após validação visual em produção e inventário dos estilos inline restantes.

## Evidência operacional

O `/health` publica:

```text
"tailwind_assets": "compiled-local-css-v11"
```

## Próxima etapa

Após o deploy e validação visual em produção, a próxima fase deve identificar e eliminar os estilos inline restantes para permitir `style-src` estrito também na política aplicada.
