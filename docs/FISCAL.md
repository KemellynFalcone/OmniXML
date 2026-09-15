# Auditoria Fiscal — visão consolidada

## Objetivo

O OmniXML cruza documentos fiscais e escriturações para indicar **o que diverge, quanto diverge, onde está a origem provável e o que deve ser revisado**. O sistema não altera XMLs nem arquivos SPED automaticamente.

## Camadas de análise

### XMLs

- NF-e e NFC-e válidas são classificadas e totalizadas.
- cancelamentos homologados não compõem a base válida.
- documentos com falha permanecem rastreáveis por arquivo, número, série, chave e valor quando disponíveis.

### SPED Fiscal

O confronto documental utiliza registros C100 dos modelos suportados e mantém rastreabilidade de operações tratadas como varejo, inclusive CFOP 5.929/6.929 quando aplicável.

### EFD-Contribuições

A auditoria documental compara XMLs com C170/C175, incluindo receita, PIS e COFINS por CST/CFOP e, quando possível, por documento.

O confronto segue a hierarquia:

`Competência → CST → CFOP → Documento`

Quando há chave segura, o OmniXML pode vincular a divergência a documentos específicos. Sem chave suficiente, a diferença é apresentada como agregada, sem afirmar vínculo nota a nota.

## PIS/COFINS e Bloco M

O fluxo atual é:

`XML → C170/C175 → M210/M610 → M200/M600`

- **C170/C175**: escrituração documental.
- **M210**: detalhamento da contribuição do PIS.
- **M610**: detalhamento da contribuição da COFINS.
- **M200/M600**: consolidação final, incluindo créditos, retenções, deduções e valor a recolher.

Diferença entre C170/C175 e M210/M610 **não é classificada automaticamente como erro**, porque o Bloco M pode incorporar outros componentes da apuração.

## Arredondamento

Quando a diferença documental é pequena, o Bloco M fecha matematicamente pela base consolidada e não existem ajustes incompatíveis com essa leitura, o OmniXML pode classificar o cenário como **provável diferença de arredondamento**. A diferença permanece visível para conferência.

## Diagnóstico

A análise pode apresentar:

- tipo da divergência;
- gravidade;
- valor de impacto;
- evidências;
- diagnóstico;
- ação sugerida;
- confiança;
- status de revisão.

O objetivo é diferenciar divergência comprovada, diferença agregada, arredondamento provável e situações que exigem investigação fiscal.

### Diagnóstico Fiscal 2.0

A camada de priorização transforma os grupos divergentes em achados ordenados para revisão. Para cada CST/CFOP, o OmniXML calcula e apresenta:

- **gravidade**: Crítico, Revisar ou Baixo impacto;
- **impacto estimado**: valor absoluto da diferença de contribuição;
- **causa provável**: Base de cálculo, Alíquota, Base de cálculo + Alíquota, Arredondamento ou Valor divergente;
- **confiança**: Alta quando existe rastreabilidade por chave em ambos os lados, ou Média quando a conclusão permanece agregada;
- **ação recomendada**: orientação específica de conferência conforme o tipo de causa;
- **prioridade**: ordenação que combina gravidade e maior impacto estimado.

O resumo executivo mostra impacto total estimado, quantidade de itens críticos, itens para revisão, itens de baixo impacto e a causa predominante. Essa classificação é diagnóstica e não substitui validação fiscal/contábil.

## Segurança da interpretação

Nenhuma sugestão do OmniXML substitui validação fiscal/contábil. O sistema é uma ferramenta de auditoria e apoio à investigação, não um mecanismo de ajuste automático da escrituração.

## Histórico técnico

A evolução detalhada das versões de SPED, EFD-Contribuições, PIS/COFINS, COFINS e Bloco M foi preservada em `docs/historico/fiscal/`.
