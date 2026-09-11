# SPED Fiscal local v26

## Objetivo

Processar arquivos EFD ICMS/IPI (`.txt`) diretamente no navegador, sem upload ao servidor, e alimentar o módulo já existente de Confronto SPED Fiscal.

## Escopo da v26

- seleção de um ou vários arquivos `.txt`;
- leitura local via `File.text()`;
- validação mínima pela presença do registro `0000`;
- leitura do registro `C100`;
- campos utilizados: `IND_OPER`, `COD_MOD`, `COD_SIT`, `SER`, `NUM_DOC`, `CHV_NFE`, `DT_DOC` e `VL_DOC`;
- modelos suportados nesta fase: 55 (NF-e) e 65 (NFC-e);
- totais separados em NF-e Entrada, NF-e Saída e NFC-e Saída;
- documentos com `COD_SIT` 02, 03, 04 ou 05 não compõem os totais;
- deduplicação por chave de acesso e, na ausência dela, por modelo/operação/série/número/data;
- reaproveitamento da tela e do detalhamento de divergências já existentes.

## Segurança e privacidade

O conteúdo do SPED não é transmitido para o servidor. A leitura ocorre integralmente no browser. A implementação não chama a rota histórica `/importar_sped`.

## Limites desta fase

A v26 não pretende interpretar todos os blocos da EFD ICMS/IPI. O núcleo do confronto financeiro usa o registro C100 para modelos 55 e 65. Registros específicos de outros documentos, como SAT/CFe, ficam para evolução posterior.

## Referência de leiaute

A posição dos campos do registro C100 segue o Guia Prático da EFD ICMS/IPI: IND_OPER (campo 02), COD_MOD (05), COD_SIT (06), NUM_DOC (08), CHV_NFE (09), DT_DOC (10) e VL_DOC (12).
