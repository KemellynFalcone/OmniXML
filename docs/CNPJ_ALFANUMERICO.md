# Compatibilidade com CNPJ Alfanumérico

## Objetivo

Preparar o OmniXML para coexistência entre CNPJ numérico legado e o novo CNPJ alfanumérico, sem alterar as regras fiscais de classificação por participante.

## Regra oficial adotada

Conforme documentação da Receita Federal, o CNPJ continua com 14 posições. As 12 primeiras posições podem conter números de `0` a `9` e letras maiúsculas de `A` a `Z`; as duas posições finais continuam sendo dígitos verificadores numéricos.

Referências oficiais:

- Receita Federal — CNPJ Alfanumérico: https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/cnpj-alfanumerico
- Receita Federal — Cálculo do DV: https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/documentos-tecnicos/cnpj
- Receita Federal — primeiro CNPJ alfanumérico: https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2026/julho/receita-federal-gera-o-primeiro-cnpj-em-formato-alfanumerico

O primeiro exemplo oficial divulgado pela Receita foi `00.000.000/E08G-12`, cuja forma normalizada é `00000000E08G12`.

## Implementação

O módulo `static/cnpj_alfanumerico_v1.js` centraliza:

- normalização textual em caixa alta;
- remoção de máscara sem remover letras;
- validação estrutural de 12 posições alfanuméricas + 2 DVs numéricos;
- cálculo dos dígitos verificadores pelo módulo 11;
- formatação no padrão `XX.XXX.XXX/XXXX-DV`;
- comparação textual normalizada.

O processador browser-local continua classificando operação pela mesma regra:

- CNPJ do emitente igual ao CNPJ da empresa auditada → Saída;
- CNPJ do destinatário igual ao CNPJ da empresa auditada → Entrada.

A diferença é que o CNPJ passa a ser tratado explicitamente como identificador textual e nunca como número.

## Compatibilidade retroativa

CNPJs numéricos existentes continuam funcionando. As URLs históricas de `browser_local_v2.js` e `inutilization_capture.js` foram preservadas para não quebrar contratos de testes e cache das fases anteriores.

## Inutilizações

O CNPJ capturado em arquivos de inutilização também passa pela mesma normalização textual, evitando divergência de chave entre notas e inutilizações quando houver CNPJ alfanumérico.

## Evidência automatizada

`tests/test_cnpj_alfanumerico.py` verifica:

- ordem de carregamento do módulo de compatibilidade;
- estrutura oficial de 14 posições;
- pesos do cálculo dos DVs;
- cálculo `12` para a base oficial `00000000E08G`;
- ausência de conversão de CNPJ para `Number`/`parseInt` no ponto de classificação;
- normalização em inutilizações;
- publicação do contrato `cnpj_support` em `/health`.
