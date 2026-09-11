# COFINS v34 — Auditor de cálculo

## Objetivo

Explicar diferenças documentais de COFINS entre XMLs e EFD-Contribuições sem realizar correção fiscal automática.

## Diagnóstico

A v34 agrupa os itens por CST da COFINS + CFOP e compara:

- base de cálculo dos XMLs;
- base de cálculo da EFD;
- alíquota efetiva dos XMLs (`COFINS / base × 100`);
- alíquota efetiva da EFD;
- valor de COFINS XML x EFD;
- diferença;
- rastreabilidade por chave XML e arquivo/linha da EFD.

A classificação diagnóstica indica se a diferença está associada a base, alíquota efetiva, ambas, ou valor divergente com base/alíquota próximas.

## Limites

A alíquota exibida é efetiva, calculada a partir de valor/base do grupo. Ela não substitui a análise da modalidade de cálculo nem da apuração final do Bloco M.

Nenhum XML ou SPED é alterado automaticamente. O diagnóstico deve ser validado antes de qualquer ajuste fiscal.

## Segurança

Todo o processamento permanece local no navegador e a CSP estrita é preservada.
