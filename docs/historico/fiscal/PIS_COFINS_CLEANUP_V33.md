# PIS/COFINS v33 — remoção visual da tabela legada

## Objetivo

Eliminar da tela Auditoria PIS/COFINS o bloco DataTables antigo que permanecia vazio após a introdução do confronto XML x EFD-Contribuições e do diagnóstico de COFINS.

## Mudança

A interface passa a ocultar de forma determinística:

- `#tabelaPisCofins`
- `#tabelaPisCofins_wrapper`

Com isso deixam de aparecer os controles antigos de Exportar Excel, Pesquisar, paginação e a mensagem `Nenhum registro encontrado`.

## Preservado

- Receita Bruta Total SPED;
- confronto documental XML x EFD-Contribuições;
- diagnóstico de diferença de COFINS por CST/CFOP;
- rastreabilidade por chave/arquivo/linha;
- exclusão de NF-e integralmente 5.929/6.929;
- processamento 100% local no navegador;
- CSP estrita e demais contratos de segurança.
