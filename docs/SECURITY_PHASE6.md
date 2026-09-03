# Security Phase 6 — Runtime externo e CSP estrita de scripts

## Objetivo

Eliminar a dependência de `unsafe-inline` em `script-src` sem alterar o visual ou a lógica fiscal do dashboard.

## Implementação

O template legado ainda contém o bloco JavaScript principal no arquivo-fonte para evitar uma migração estrutural de alto risco em um único passo. Entretanto, o HTML entregue ao navegador não contém esse bloco inline.

`web_app_browser.py` identifica o último `<script>` sem `src`, extrai seu conteúdo e:

1. substitui o bloco no HTML por `/static/dashboard_runtime_v6.js?v=1`;
2. publica o conteúdo extraído por uma rota JavaScript same-origin;
3. aplica `script-src` sem `'unsafe-inline'` na CSP efetiva.

A política de estilos continua contendo `'unsafe-inline'` nesta fase, porque o template ainda possui CSS inline e o Tailwind atual depende da configuração existente.

## Handlers de clique

A Fase 5 permanece responsável por migrar atributos `onclick` confiáveis para `addEventListener`. A Fase 6 inclui `copiarEAbrir` na allowlist para que o botão dinâmico de consulta SEFAZ continue funcional mesmo com handlers inline bloqueados nativamente pela CSP.

O bridge continua sem `eval` e sem `new Function`.

## Evidências automatizadas

`tests/test_security_phase6.py` verifica:

- ausência de blocos `<script>` inline no HTML entregue;
- carregamento do runtime externo;
- preservação das funções principais do dashboard;
- remoção de `'unsafe-inline'` especificamente da diretiva `script-src` aplicada;
- permanência controlada de `'unsafe-inline'` em `style-src`;
- cobertura da ação dinâmica `copiarEAbrir`;
- indicadores de capacidade no `/health`.

## Estado após a fase

A política aplicada passa a bloquear execução JavaScript inline. O próximo débito relevante é reduzir os sinks HTML restantes no runtime legado e, depois, tratar CSS inline/CDNs para endurecer também `style-src` e reduzir dependências externas.
