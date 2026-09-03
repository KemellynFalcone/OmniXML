# Hotfix — DataTables `tabelaErros`

## Sintoma

Após a Fase 10, alguns carregamentos podiam exibir o alerta do DataTables:

`Cannot reinitialise DataTable`

A tabela afetada era `tabelaErros`.

## Causa

O runtime principal cria `dtErros` e o `failure_table_v2.js` reconstrói essa tabela para exibir as colunas fiscais enriquecidas. O script antigo verificava apenas se a variável `dtErros` já existia. Isso não garantia que a inicialização assíncrona do DataTables — especialmente o carregamento do arquivo de idioma — já estivesse concluída.

A Fase 10 tornou o idioma do runtime principal local e mais rápido, expondo com maior consistência essa condição de corrida. Além disso, `failure_table_v2.js` ainda mantinha a URL externa do idioma.

## Correção

- aguardar o evento `init.dt` da instância original antes da reconstrução;
- confirmar `_bInitComplete` quando a instância já existir;
- executar a reconstrução somente uma vez;
- manter `dtErros.destroy()` antes da nova configuração;
- usar `/static/datatables_ptbr_v10.json` também na tabela enriquecida;
- preservar colunas, resumo financeiro, exportação e aparência existentes.

## Não alterado

- regras fiscais;
- processamento browser-local;
- CNPJ alfanumérico;
- classificação Entrada/Saída;
- validação XML;
- visual do dashboard.
