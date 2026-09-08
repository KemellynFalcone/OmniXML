# UX SPED v22 — Preview orientado à ação

## Objetivo

Eliminar o estado vazio pouco informativo do Confronto SPED Fiscal e orientar o usuário para a primeira ação, sem alterar a lógica fiscal, o processamento browser-local ou os resultados reais.

## Alterações

- O CTA `Importar SPED (.txt)` passa a ser sólido em azul e visualmente prioritário.
- O `#placeholder-sped` continua existindo e é substituído por uma prévia visual dos tipos de análise que aparecerão depois da importação.
- A prévia informa explicitamente `dados ilustrativos` e não apresenta valores monetários fictícios.
- O estado `Aguardando importação` existe somente dentro do placeholder; desaparece quando o fluxo existente oculta o placeholder.
- Três próximos passos explicam o fluxo: importar SPED, confrontar com XMLs e revisar divergências.
- `#resultado-sped`, `#btnDivergencias`, `#tabelaDivergencias` e os IDs de valores reais permanecem inalterados.

## Segurança

A nova UI não usa `style=`. O CSS do preview é incorporado ao mesmo stylesheet externo `/static/dashboard_style_v9.css`, preservando `style-src-attr 'none'`.

## Contrato de produção

O `/health` publica `sped_empty_state = preview-action-guidance-v22`.

## Fora do escopo

- interpretação de SPED;
- classificação fiscal;
- cálculo de divergências;
- CNPJ alfanumérico;
- DataTables, exportação Excel e Chart.js;
- upload de XML para o servidor.
