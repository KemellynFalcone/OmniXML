# PIS/COFINS v31 — exclusão de NF-e 5.929/6.929 do confronto documental

## Objetivo

Alinhar o confronto XML x EFD-Contribuições à mesma regra já aplicada no Confronto SPED Fiscal para documentos de origem varejo.

## Regra

NF-e modelo 55 cuja chave esteja classificada pelo módulo `retail_origin_v28` como origem varejo — isto é, nota integralmente composta por CFOP 5.929/6.929 — não compõe a base documental de Receita, PIS e COFINS usada para apontar divergência contra C170/C175.

Notas mistas, com 5.929/6.929 e outro CFOP, permanecem no confronto.

## Rastreabilidade

O snapshot `window.__omnixmlXmlPisCofins.snapshot()` passa a expor:

- `notas_varejo_excluidas`
- `receita_varejo_excluida`

A nota não é apagada da auditoria geral; apenas deixa de ser somada na base de confronto documental PIS/COFINS, evitando dupla contagem da operação já acobertada pelo documento de varejo.

## Segurança

O processamento continua 100% local no navegador, sem upload e sem alteração da CSP.
