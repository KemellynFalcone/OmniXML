# Confronto PIS/COFINS v30

## Objetivo

Transformar a tela **Auditoria PIS/COFINS** em uma auditoria documental de fato, comparando os valores extraídos dos XMLs com os valores escriturados na EFD-Contribuições.

## Camada documental

O confronto v30 utiliza:

- XMLs NF-e/NFC-e de saída da empresa auditada;
- tributos PIS e COFINS informados nos itens dos XMLs;
- registros **C170** e **C175** da EFD-Contribuições;
- agregação por CST do PIS;
- comparação de receita documental, PIS documental e COFINS documental.

Cancelamentos identificados por eventos homologados não entram na base XML de saída.

## Limite fiscal importante

O confronto C170/C175 x XML é documental e não equivale à apuração final das contribuições.

A apuração final deve ser confrontada posteriormente com o Bloco M, especialmente:

- M200/M210 para PIS/Pasep;
- M600/M610 para Cofins.

Esses blocos podem conter créditos, ajustes e outros componentes que não devem ser confundidos com os valores documentais dos XMLs.

## UX

A v30 remove os gráficos puramente ilustrativos do estado vazio do Dashboard Geral e do Confronto SPED Fiscal. Estados vazios passam a orientar a próxima ação sem simular dados que não serão alimentados.

## Segurança

Todo o processamento continua local no navegador. Nenhum XML ou arquivo SPED é enviado ao servidor e a CSP existente permanece inalterada.
