# OmniXML Web — processamento local no navegador

Nesta arquitetura, os XMLs não são enviados ao Render.

Fluxo:

1. O servidor entrega o dashboard.
2. O navegador seleciona XMLs ou uma pasta inteira.
3. Cada XML é lido com a File API e processado no próprio navegador.
4. O dashboard recebe apenas os resultados calculados em memória.
5. O relatório CSV é gerado localmente pelo navegador.
6. Ao recarregar a página, os dados da consulta são descartados.

Benefícios principais:

- elimina limite de upload de 200 MB;
- evita timeout de envio;
- reduz uso de disco/RAM do servidor;
- XMLs fiscais não saem do computador do usuário;
- permite processar pastas grandes sem depender da banda de upload.

Limitação inicial: ZIP deve ser extraído antes da seleção. O suporte a ZIP local poderá ser adicionado depois com descompressão no navegador.
