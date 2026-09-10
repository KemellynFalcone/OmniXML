# Hotfix COFINS v34 — congelamento na importação EFD

## Sintoma

Após importar a EFD-Contribuições, a tela de Auditoria PIS/COFINS podia aparentar travamento e deixar de concluir a renderização do conteúdo.

## Causa

O `MutationObserver` do auditor COFINS v34 chamava `render()` para qualquer mutação do DOM. O próprio `render()` removia e recriava o bloco `#cofins-auditor-v34`, gerando novas mutações observadas e, portanto, um ciclo contínuo de renderização.

## Correção

O observer agora é desconectado durante a renderização do auditor e reconectado em `finally`. A primeira renderização também ocorre antes do início da observação. Assim, alterações legítimas feitas pela importação da EFD ainda atualizam o auditor, mas as alterações produzidas pelo próprio auditor não retroalimentam o observer.

## Escopo

- sem alteração de regra fiscal;
- sem alteração automática de XML ou SPED;
- mantém o diagnóstico de base, alíquota efetiva e valor COFINS da v34;
- mantém processamento local no navegador.
