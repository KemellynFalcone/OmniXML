# OmniXML — Manual Operacional

> Documento vivo. Deve acompanhar as mudanças de comportamento do sistema.

## 1. Objetivo

O OmniXML é uma ferramenta de auditoria e conferência de documentos fiscais eletrônicos. A versão web atual processa os arquivos XML localmente no navegador: os XMLs selecionados não são enviados ao servidor do OmniXML.

O sistema auxilia a conferência. Um alerta não substitui análise fiscal/contábil nem significa, isoladamente, que exista infração.

## 2. Como iniciar uma auditoria

1. Abra o OmniXML no navegador.
2. Clique em **Importar e Auditar XMLs**.
3. Selecione XMLs individuais ou uma pasta inteira.
4. Aguarde o processamento local.
5. Confira o CNPJ/empresa identificada e os totais apresentados antes de interpretar os demais resultados.

## 3. Documentos tratados

### NF-e — modelo 55
Documento fiscal eletrônico normalmente utilizado em operações de mercadorias. O OmniXML extrai identificação, número, série, chave, participantes, valor e itens.

### NFC-e — modelo 65
Documento fiscal eletrônico voltado ao consumidor final. No fluxo atual é tratado como documento de saída quando o emitente é a empresa auditada.

### Evento de cancelamento
O evento de cancelamento é relacionado à chave da NF-e/NFC-e. Quando confirmado, a nota continua existindo e continua ocupando sua numeração, mas recebe situação de cancelada.

### Inutilização
O OmniXML reconhece arquivos de inutilização e usa como justificativa de sequência somente inutilizações homologadas (`cStat 102`). Uma inutilização justifica números que não possuem NF-e/NFC-e emitida.

## 4. Identificação da empresa auditada

O processamento local identifica o CNPJ principal pela participação nos documentos carregados, priorizando emitentes de NFC-e e usando emitentes das demais notas como alternativa. O usuário deve sempre conferir se a empresa exibida no cabeçalho corresponde à pasta selecionada.

## 5. Entrada e saída

A classificação é baseada nos participantes do XML:

- **Saída:** CNPJ da empresa auditada é o emitente.
- **Entrada:** CNPJ da empresa auditada é o destinatário.
- **Não classificada:** o sistema não consegue relacionar com segurança o documento à empresa identificada.

NF-e de entrada não participa da conferência de sequência das notas emitidas pela empresa.

## 6. Dashboard Geral

O dashboard consolida quantidade de XMLs, NF-e de entrada, NF-e de saída, NFC-e, cancelamentos, valores e demais indicadores. Os valores devem ser interpretados conforme o status e a operação do documento.

## 7. Gestão NF-e e NFC-e

As tabelas permitem inspecionar os documentos processados e seus principais campos. Cancelamentos são apresentados como documentos existentes com status próprio; não são considerados números ausentes.

## 8. CFOP, CST e Série

As visões de CFOP/CST/Série agrupam informações extraídas dos itens/documentos para facilitar a conferência. Alertas de combinação tributária são heurísticas de auditoria e exigem validação fiscal quando apontados.

## 9. Arquivos com erro

A área de falhas registra arquivos que não puderam ser considerados documentos fiscais finalizados ou que apresentaram problema estrutural detectado pelo OmniXML. A tabela pode apresentar arquivo, número, chave, valor e motivo, conforme os dados disponíveis no XML.

Exemplos de verificações atuais: XML malformado; ausência de `infNFe`; NF-e/NFC-e sem processo/protocolo de autorização; status de autorização não aceito; divergência entre chave do documento e protocolo; ausência de assinatura; NFC-e autorizada sem QR Code.

## 10. Diagnóstico do fechamento

O diagnóstico é uma conferência complementar e fica recolhido por padrão.

### Sequência de saída
Para cada combinação de **modelo + série**, considerando somente documentos classificados como **Saída**, o sistema encontra o menor e o maior número existentes na pasta e procura números não emitidos dentro desse intervalo.

### Resultado da sequência
Um número pode ficar em três situações relevantes:

- **Utilizado:** existe NF-e/NFC-e. Se posteriormente cancelada, continua sendo número utilizado.
- **Inutilizado:** não existe nota para o número, mas há inutilização homologada cobrindo-o.
- **A conferir:** não existe nota e não foi localizada inutilização homologada nos arquivos selecionados.

A ausência de uma inutilização na pasta não prova que ela não exista na SEFAZ. Significa apenas que o OmniXML não a encontrou no conjunto local analisado.

## 11. Duplicidades

Documentos com a mesma chave podem ser detectados como duplicados. O objetivo é evitar que cópias do mesmo XML distorçam os totais.

## 12. Exportação

A exportação disponibilizada pelo dashboard serve para transportar os dados consolidados da auditoria. Sempre preserve os XMLs originais como fonte documental.

## 13. Privacidade e segurança

Na arquitetura web atual, a leitura dos XMLs ocorre no navegador. O servidor entrega a aplicação, mas não recebe a pasta fiscal selecionada. Não compartilhe XMLs, certificados digitais ou credenciais em canais não autorizados.

## 14. Limitações atuais

- A validação atual de NF-e/NFC-e é estrutural e de autorização; validação XSD oficial completa ainda é uma evolução planejada.
- SPED/EFD local ainda será ampliado.
- Regras tributárias exibidas como alerta são apoio à auditoria, não decisão fiscal automática.
- O sistema só consegue conciliar eventos/inutilizações presentes nos arquivos selecionados.

## 15. Regra de interpretação

**Erro comprovável pelo arquivo** deve ser distinguido de **alerta**, **inconsistência para conferência** e **informação**. Quando houver dúvida, confira o XML original, os eventos oficiais e a escrituração antes de concluir o fechamento.
