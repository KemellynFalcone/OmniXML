# EFD-Contribuições local v29

## Objetivo

Substituir o aviso/fluxo legado da tela **Auditoria PIS/COFINS** por leitura real de arquivos `.txt` da EFD-Contribuições diretamente no navegador, sem upload para o servidor.

## Registros suportados nesta fase

- **C175**: registro analítico de NFC-e modelo 65, agregado por CFOP/CST/alíquotas. Para o painel do OmniXML são usados o valor da operação, CST PIS, base/valor de PIS e CST/base/valor de COFINS.
- **C170**: item de documento fiscal escriturado no C100. O OmniXML considera somente C170 cujo C100 pai esteja marcado como saída (`IND_OPER = 1`) para compor receita.

## Agregação

A tabela existente `tabelaPisCofins` continua recebendo:

- `cst`
- `vl_opr`
- `vl_pis`

O snapshot local também mantém `vl_cofins`, `vl_bc_pis`, `vl_bc_cofins` e contagem de registros por CST.

## Segurança e privacidade

- arquivos são lidos por `File.text()` no browser;
- nenhum conteúdo da EFD-Contribuições é enviado ao backend;
- não é criado novo endpoint de upload;
- a CSP existente permanece inalterada;
- o botão histórico `importarPisCofins()` é sobrescrito pelo módulo local após o carregamento do dashboard.

## Limites da v29

Esta fase não pretende cobrir todos os blocos possíveis da EFD-Contribuições. Registros consolidados e outras naturezas de receita/crédito além de C170/C175 deverão ser incorporados progressivamente, sempre com teste fiscal específico.
