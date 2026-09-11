# Security Phase 16 — Inventário detalhado de atributos `style`

## Objetivo

A Phase 15 reduziu em produção os estilos inline observados no DataTables de 176 para 15, mantendo `app: 0`. A Phase 16 não altera a CSP aplicada nem remove estilos. O objetivo é identificar exatamente quais propriedades CSS e quais elementos ainda dependem de atributos `style` antes de qualquer novo endurecimento.

## Evidência de entrada

Após a Phase 15, o inventário em produção apresentou:

- DataTables: 15
- Chart.js: 13
- App: 0
- Outros: 8

## Implementação

`static/browser_security_v2.js` passa a agregar, além das contagens por origem:

- propriedades CSS por origem (`width`, `height`, `display`, etc.);
- assinatura dos elementos que recebem `style`;
- amostras ampliadas para diagnóstico;
- snapshot ordenado para facilitar comparação;
- reset manual do inventário para medir uma interação específica.

O inventário continua estritamente local no navegador e não remove, altera ou envia os estilos observados.

## Uso no navegador

Snapshot completo:

```javascript
window.__omnixmlStyleAttrInventory.snapshot()
```

Para medir somente uma sequência de interação:

```javascript
window.__omnixmlStyleAttrInventory.reset()
```

Depois navegue pelas tabelas/gráficos e execute novamente `snapshot()`.

## Segurança e compatibilidade

- `style-src-attr 'unsafe-inline'` permanece na CSP aplicada nesta fase.
- `style-src-attr 'none'` permanece em Report-Only.
- `autoWidth = false` da Phase 15 continua ativo.
- Nenhuma regra fiscal, classificação Entrada/Saída, CNPJ alfanumérico, exportação, DataTables ou Chart.js é alterada funcionalmente.
