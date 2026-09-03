# Security Phase 8 — Safe Renderers

## Objetivo

Reduzir os riscos de DOM/XSS nos renderizadores legados do dashboard sem alterar a aparência nem as regras fiscais.

## Implementação

A Fase 8 endurece o runtime JavaScript que é extraído do template e servido em `/static/dashboard_runtime_v6.js`.

Antes de entregar esse runtime ao navegador, `web_app_browser.py` aplica uma transformação explícita sobre os renderizadores conhecidos que ainda concatenavam valores dinâmicos derivados de XML/SPED em markup HTML.

Os campos cobertos incluem:

- fallback do badge de documento;
- status de NF-e/NFC-e e produtos;
- NCM da validação cruzada;
- status da auditoria;
- NCM de produtos;
- motivo de falha na tabela de erros;
- chave de acesso exibida nas divergências.

Os valores dinâmicos passam por `escapeRuntimeHtml`, que neutraliza `&`, `<`, `>`, aspas duplas e aspas simples antes da composição do markup visual.

## Consulta SEFAZ

O botão dinâmico da coluna de chave deixou de carregar um `onclick` construído por interpolação.

O runtime passa a gerar apenas atributos `data-omnixml-sefaz-chave` e `data-omnixml-sefaz-url`. O arquivo `static/safe_renderers_v8.js` usa delegação de eventos com `addEventListener` e chama `window.copiarEAbrir` somente após validar a chave de 44 dígitos.

A validação de domínio externo da Fase 3 continua ativa e permanece como segunda barreira para a navegação SEFAZ.

## Defesa em profundidade

A Fase 8 não substitui as camadas anteriores:

- Fase 2: cópia sanitizada para display nas DataTables;
- Fase 3: hardening de DOM e allowlist de destinos SEFAZ;
- Fase 4: DOM seguro em diagnóstico e tabela de falhas;
- Fase 5: migração de handlers inline;
- Fase 6: CSP estrita para scripts;
- Fase 7: cobertura de todas as DataTables principais.

A Fase 8 reduz o risco diretamente na origem dos renderizadores restantes.

## Testes

`tests/test_security_phase8.py` verifica:

- presença do escape central no runtime entregue;
- aplicação do escape nos renderizadores dinâmicos;
- ausência do `onclick="copiarEAbrir(...)"` no runtime servido;
- presença do bridge delegado da SEFAZ;
- ausência de `eval` e `new Function`;
- publicação da capacidade no `/health`;
- preservação dos indicadores das fases anteriores.

## Estado após a fase

A diretiva `script-src` continua sem `unsafe-inline`.

O principal débito de CSP restante está em `style-src`, que ainda depende de `unsafe-inline`, Tailwind CDN, DataTables e estilos legados. A etapa seguinte deve inventariar estilos inline e dependências externas antes de endurecer essa diretiva em produção.
