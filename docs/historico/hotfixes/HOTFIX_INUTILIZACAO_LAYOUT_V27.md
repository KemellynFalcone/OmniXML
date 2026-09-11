# Hotfix Inutilização + Layout v27

## Problema observado

Um XML de NF-e/NFC-e sem protocolo de autorização podia aparecer em `Arquivos com Erro` mesmo quando a mesma numeração estava coberta por uma inutilização homologada (`cStat=102`) da própria empresa. A tabela de falhas também podia ultrapassar a largura normal do dashboard por causa de nomes de arquivo, chaves de acesso e motivos longos.

## Correção fiscal

A v27 captura localmente os metadados mínimos do XML com falha (CNPJ emitente, modelo, série, número e chave), inclusive quando a validação interrompe `File.text()`.

Antes de fechar o diagnóstico, falhas relacionadas a ausência/invalidade de autorização são reconciliadas com `window.__omnixmlInutilizacoes`.

Uma falha só é retirada quando existe inutilização:

- homologada (`cStat=102`);
- da mesma empresa/emitente;
- do mesmo modelo;
- da mesma série;
- cuja faixa contém o número da nota.

Erros de outra natureza continuam sendo exibidos. A reconciliação não transforma o XML sem protocolo em documento autorizado; ela apenas evita classificá-lo como pendência quando a numeração está fiscalmente justificada por inutilização homologada.

## Correção visual

A tabela `#tabelaErros` recebeu CSS local específico:

- `table-layout: fixed`;
- larguras proporcionais por coluna;
- quebra de texto para arquivo, chave e motivo;
- contenção do wrapper na largura disponível;
- rolagem horizontal apenas em telas menores.

Não foram adicionados `style` attributes e a política CSP existente permanece compatível.

## Arquivos

- `static/failure_reconciliation_v27.js`
- `static/failure_reconciliation_v27.css`
- `static/inline_handler_bridge_v5.js`
- `tests/test_inutilizacao_failure_v27.py`
