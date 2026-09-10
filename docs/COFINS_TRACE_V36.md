# COFINS v36 — evidências somente da divergência

A v36 simplifica o drill-down do auditor de COFINS.

## Regra de exibição

- Quando XML e EFD possuem chave suficiente para pareamento seguro, o detalhe mostra somente os documentos/registros cuja COFINS diverge acima da tolerância.
- Registros conciliados ficam ocultos e aparecem apenas em um resumo quantitativo.
- Quando a EFD está agregada ou não contém chave suficiente para parear documento a documento, o OmniXML não lista todas as linhas como se fossem divergentes. Mostra a divergência agregada e informa que não existe vínculo individual conclusivo.
- A referência `arquivo:linha` continua disponível apenas como evidência técnica quando houver uma linha individual efetivamente exibida.

Nenhuma regra fiscal, valor, tolerância ou cálculo do auditor de COFINS foi alterado nesta fase.
