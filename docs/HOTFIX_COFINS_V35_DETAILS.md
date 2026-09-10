# Hotfix COFINS v35 — abertura do detalhamento

## Problema

O botão `Ver detalhes` era renderizado e recebia tratamento por delegação de eventos, mas o modal era removido imediatamente após ser inserido no DOM.

A causa era o `MutationObserver` do auditor: a própria inserção do modal disparava nova renderização e `render()` fechava o detalhamento no início da montagem.

## Correção

O observer agora ignora mutações enquanto `#cofins-auditor-v35-modal` estiver presente. Assim, abrir o painel não retroalimenta a renderização do auditor.

O mecanismo anti-loop introduzido no hotfix da v34 permanece ativo.

## Escopo

Nenhum cálculo, classificação fiscal, valor de COFINS, regra 5.929/6.929 ou processamento da EFD foi alterado.
