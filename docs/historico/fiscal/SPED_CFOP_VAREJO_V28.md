# SPED Fiscal v28 — CFOP 5.929/6.929 e origem varejo

## Objetivo

Evitar falso positivo no confronto de NF-e de saída quando o XML representa documento fiscal emitido para operação já acobertada por documento fiscal do varejo.

## Regra

O OmniXML identifica, por chave de acesso, NF-e modelo 55 que contenha item com CFOP 5.929 ou 6.929.

Essas notas:

- continuam presentes na auditoria XML e permanecem rastreáveis;
- não são tratadas como nota faltante no SPED para o confronto financeiro de NF-e Saídas;
- têm seu valor removido apenas da base XML usada nessa comparação;
- não alteram os totais gerais do dashboard nem os valores das NFC-e;
- não são convertidas em canceladas ou inutilizadas.

O status do processamento SPED informa quantas NF-e foram tratadas como origem varejo. A estrutura `window.__omnixmlSpedLocalLast.totais` registra o valor e a quantidade excluídos da comparação.

## Segurança

Todo o reconhecimento ocorre no navegador. Nenhum XML ou SPED é enviado ao servidor e nenhuma diretiva CSP foi relaxada.

## Validação

A implementação possui testes para identificação por CFOP/chave, exclusão apenas da comparação de saída, rastreabilidade e carregamento local do módulo.
