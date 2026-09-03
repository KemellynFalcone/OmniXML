# Security Phase 13 — estilos inline próprios

## Objetivo

Reduzir a dependência de `style-src-attr 'unsafe-inline'` removendo estilos inline gerados pelo próprio processador browser-local, sem alterar o visual ou as regras fiscais.

## Implementação

O indicador de progresso deixou de usar `element.style.display` e `element.style.width`. A exibição e o percentual agora são controlados por classes CSS externas:

- `progress-visible` para mostrar o container;
- `progress-pct-0` até `progress-pct-100` para a largura da barra.

As classes de percentual são geradas no CSS externo do dashboard e o script apenas adiciona/remove classes.

## CSP

A política aplicada ainda mantém `style-src-attr 'unsafe-inline'` nesta fase. Isso é intencional: DataTables e Chart.js ainda podem gerar estilos de elemento em tempo de execução para dimensões, visibilidade e layout. A política Report-Only continua testando `style-src-attr 'none'` para medir essa dívida antes de enforcement total.

Não seria seguro remover a compatibilidade de atributos agora apenas porque o código próprio foi migrado; isso poderia quebrar tabelas ou gráficos em produção.

## Contratos preservados

A Phase 13 não altera:

- processamento fiscal dos XMLs;
- classificação Entrada/Saída;
- suporte a CNPJ alfanumérico;
- DataTables;
- gráficos Chart.js;
- exportação Excel;
- reconciliação de inutilizações;
- CSP estrita para scripts e elementos de estilo já conquistada nas fases anteriores.

## Evidência operacional

O `/health` publica:

```text
"style_attr_app": "class-driven-progress-v13"
```

## Próxima etapa

Inventariar e, quando viável, eliminar/encapsular os estilos de atributo gerados por DataTables e Chart.js. Só então `style-src-attr 'none'` deverá ser aplicado de forma obrigatória.