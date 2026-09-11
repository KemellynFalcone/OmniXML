# UX SPED v23 — Estado vazio conservador

## Objetivo

Melhorar a orientação do usuário no Confronto SPED Fiscal sem repetir a regressão visual observada na v22 e sem alterar regras fiscais, processamento ou resultados.

## Decisões de UX

- O cabeçalho original do módulo é preservado.
- O botão `Importar SPED (.txt)` mantém a mesma ação e recebe maior prioridade visual.
- O estado vazio usa um único bloco principal, uma prévia gráfica discreta e três passos operacionais.
- O status `Aguardando importação` é neutro/âmbar, evitando aparência de sucesso concluído.
- A prévia declara explicitamente que é ilustrativa e não representa resultados fiscais reais.
- Em larguras menores, a prévia gráfica é ocultada e os passos passam para uma coluna.

## Segurança

- Nenhum `style=` foi adicionado.
- O CSS permanece no bloco próprio do template e é externalizado pela rota histórica `/static/dashboard_style_v9.css`.
- A política `style-src-attr 'none'` permanece inalterada.

## Compatibilidade

Permanecem inalterados:

- `#resultado-sped`;
- `#btnDivergencias`;
- `#tabelaDivergencias`;
- IDs dos valores de entrada/saída/NFC-e;
- `confrontarSPED()` e `mostrarDivergencias()`;
- processamento browser-local;
- CNPJ alfanumérico;
- CSP e assets locais já validados.

## Validação

Os testes verificam o HTML renderizado, a posição do placeholder em relação ao resultado, o CSS responsivo externo e a manutenção de `style-src-attr 'none'`.
