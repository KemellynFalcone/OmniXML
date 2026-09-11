# Documentação do OmniXML

Esta pasta contém somente a documentação **atual e de consulta recorrente** do projeto. Documentos de versões, fases de segurança, hotfixes e decisões antigas foram preservados em `docs/historico/` para manter rastreabilidade sem poluir a visão principal.

## Documentos principais

- [ERS.md](./ERS.md) — especificação de requisitos do sistema.
- [ERS_RASTREABILIDADE.md](./ERS_RASTREABILIDADE.md) — relação entre requisitos, implementações e evidências.
- [ENGENHARIA.md](./ENGENHARIA.md) — arquitetura, decisões técnicas e organização de engenharia.
- [MANUAL_OPERACIONAL.md](./MANUAL_OPERACIONAL.md) — uso operacional do OmniXML.
- [FISCAL.md](./FISCAL.md) — visão consolidada da auditoria fiscal, SPED, EFD-Contribuições e PIS/COFINS.
- [SEGURANCA.md](./SEGURANCA.md) — princípios e estado atual de segurança do projeto.
- [ARQUITETURA_BROWSER_LOCAL.md](./ARQUITETURA_BROWSER_LOCAL.md) — processamento local no navegador.
- [CNPJ_ALFANUMERICO.md](./CNPJ_ALFANUMERICO.md) — compatibilidade com CNPJ alfanumérico.

## Histórico

A evolução por versão continua disponível em [historico/README.md](./historico/README.md). Esses arquivos não devem ser usados como fonte principal do comportamento atual quando houver um documento consolidado correspondente.

## Regra para novas documentações

Evitar criar um novo arquivo na raiz de `docs/` para cada versão ou hotfix. Atualizações funcionais devem ser incorporadas aos documentos consolidados. Se for necessário preservar a decisão específica de uma versão, registrar em `docs/historico/`.
