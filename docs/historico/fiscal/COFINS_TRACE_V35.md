# COFINS v35 — Rastreabilidade amigável

## Objetivo

Substituir o texto técnico longo da coluna de rastreabilidade do auditor de COFINS por um resumo operacional e um detalhamento sob demanda.

## Visão principal

A coluna passa a exibir somente um resumo, por exemplo `133 XMLs × 133 registros EFD`, seguido do botão `Ver detalhes`.

## Detalhamento

O botão abre um painel local com duas listas independentes, sem presumir pareamento nota-a-nota quando a EFD estiver agregada:

- XMLs envolvidos: número da nota quando identificável, chave, CFOP, CST, base de COFINS e valor de COFINS;
- registros EFD envolvidos: número/chave quando disponíveis, CFOP, CST, base, valor e referência `arquivo:linha`.

A referência técnica da linha do SPED continua disponível, mas deixa de ocupar a tabela principal.

## Segurança e desempenho

- nenhum `onclick` inline é utilizado;
- nenhum estilo inline é criado;
- o detalhamento só é materializado no DOM após ação do usuário;
- o hotfix anti-loop do MutationObserver da v34 é preservado;
- todo o processamento continua local no navegador.

## Regra fiscal

A v35 não altera cálculo, classificação, tolerâncias ou qualquer dado fiscal. É uma mudança de apresentação e rastreabilidade.