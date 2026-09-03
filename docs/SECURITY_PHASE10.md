# Security Phase 10 — redução de dependências externas

## Objetivo

Reduzir chamadas externas desnecessárias e tornar dependências de frontend mais previsíveis, sem alterar o layout nem as regras fiscais do OmniXML.

## Implementação

- a tradução `pt-BR` usada pelo DataTables deixa de ser buscada em `cdn.datatables.net` e passa a ser servida localmente em `/static/datatables_ptbr_v10.json`;
- o runtime entregue substitui automaticamente a URL externa do idioma pela URL local;
- o Chart.js deixa de usar a referência não versionada `npm/chart.js` e passa a usar a versão fixa `4.5.1` no jsDelivr;
- `/health` publica `external_assets = local-datatables-i18n-pinned-chartjs-v10`.

## Ganho de segurança e disponibilidade

A CSP aplicada já restringe `connect-src` a `'self'`. Portanto, buscar o JSON de idioma do DataTables em um domínio externo era incompatível com a política de conexão desejada. Servir o arquivo local elimina essa dependência de rede e mantém a interface em português mesmo sob a CSP atual.

Fixar a versão do Chart.js evita que uma mudança futura no pacote `latest` seja incorporada automaticamente sem revisão, reduzindo risco de regressão e de cadeia de suprimentos.

## Compatibilidade

Não há alteração intencional em:

- processamento de XML ou SPED;
- classificação Entrada/Saída;
- CNPJ numérico ou alfanumérico;
- validação fiscal;
- aparência das tabelas e gráficos;
- exportação Excel.

As versões já fixadas de jQuery, DataTables, Buttons e JSZip permanecem inalteradas nesta fase.

## Débito restante

O dashboard ainda depende externamente de Tailwind CDN, jQuery/DataTables, JSZip, DataTables Buttons, Google Fonts e Chart.js. O principal bloqueador para remover `style-src 'unsafe-inline'` da CSP aplicada continua sendo o Tailwind CDN e estilos dinâmicos de componentes terceiros.

## Próximo passo

Preparar uma estratégia de build/localização do Tailwind e dos demais ativos de apresentação. A remoção de `unsafe-inline` da política aplicada só deve ocorrer depois que o dashboard puder ser renderizado sem estilos injetados em tempo de execução.
