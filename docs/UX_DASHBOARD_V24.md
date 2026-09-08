# UX Dashboard v24 — Preview de valor antes da importação

## Objetivo

Evoluir o estado inicial do Dashboard Geral sem alterar a lógica fiscal, os KPIs reais ou os gráficos existentes. A tela continua orientada à importação, mas passa a comunicar melhor o valor que aparecerá depois da auditoria.

## Comportamento antes da importação

- O banner `Bem-vindo ao OmniXML Fiscal` e o CTA `Importar e Auditar XMLs` permanecem.
- Os três KPIs principais continuam visíveis e zerados: NF-e Entradas, NF-e Saídas e NFC-e.
- Um único bloco `Previsão de impacto e próximos passos` aparece abaixo dos KPIs.
- O bloco é explicitamente marcado como `Dados ilustrativos` e não apresenta valores fiscais reais ou simulados em moeda.
- Os gráficos reais de Evolução, CFOP e CST ficam ocultos enquanto não há XML processado.

## Comportamento após a auditoria

Ao concluir `iniciarProcessamento()` com sucesso:

1. o banner de boas-vindas é ocultado, como já ocorria;
2. o preview ilustrativo é ocultado;
3. os gráficos reais existentes são exibidos;
4. `atualizarPainelDinamico(dados)` e `renderizarGraficos(...)` permanecem inalterados.

## Segurança

A v24 não introduz `style=`. O CSS fica no bloco de estilo próprio do template, que continua sendo externalizado pelo servidor. A política `style-src-attr 'none'` permanece válida.

## Fora do escopo

- classificação de NF-e/NFC-e;
- cálculos fiscais;
- CNPJ alfanumérico;
- SPED;
- DataTables;
- Chart.js;
- processamento ou upload de XML no servidor.
