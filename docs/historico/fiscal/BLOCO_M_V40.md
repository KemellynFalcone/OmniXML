# OmniXML v40 — Confronto com o Bloco M

A v40 conecta a escrituração documental da EFD-Contribuições à apuração final do PIS e da COFINS.

## Fluxo analisado

- C170/C175: valores documentais já confrontados com XMLs;
- M210: detalhamento da contribuição para PIS;
- M200: consolidação final do PIS;
- M610: detalhamento da contribuição para COFINS;
- M600: consolidação final da COFINS.

## O que o OmniXML mostra

1. Total documental de PIS/COFINS em C170/C175;
2. Total da contribuição do período em M210/M610;
3. Diferença entre a escrituração documental suportada e o detalhamento do Bloco M;
4. Créditos descontados no período e de períodos anteriores;
5. Retenções e outras deduções;
6. Valor final a recolher informado em M200/M600.

## Regra de interpretação

Diferença entre C170/C175 e M210/M610 não é classificada automaticamente como erro. O Bloco M pode consolidar valores de outros blocos da EFD-Contribuições, além de ajustes de base, ajustes de contribuição e diferimentos.

A v40 apresenta a diferença como ponto de investigação e mantém a regra de segurança do OmniXML: nenhuma alteração automática é feita no XML ou na EFD.

## Compatibilidade

O parser contempla a estrutura atual dos registros M210/M610 (com ajustes de base) e mantém leitura do leiaute anterior para arquivos históricos.
