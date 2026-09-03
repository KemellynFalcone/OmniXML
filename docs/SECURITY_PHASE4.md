# OmniXML — Segurança Fase 4: Safe DOM

## Objetivo

A Fase 4 reduz a superfície de XSS removendo usos desnecessários de `innerHTML` em componentes que recebem ou exibem dados derivados de XML. A abordagem passa a priorizar APIs de DOM e `textContent` para dados dinâmicos.

## Escopo implementado

### Diagnóstico do fechamento

`static/closing_diagnosis_v2.js` deixa de montar linhas de lacunas com HTML dinâmico. Células, linhas e conteúdos são criados com `document.createElement` e recebem valores por `textContent`.

O texto explicativo do diagnóstico também deixa de depender de `innerHTML` para conteúdo dinâmico.

### Arquivos com erro

`static/failure_table_v2.js` passa a construir a estrutura auxiliar e o cabeçalho da tabela com APIs de DOM. Os campos derivados do XML continuam tratados como texto e os renderizadores preservam escape explícito onde ainda precisam retornar marcação controlada para o DataTables.

## Princípio de segurança

Dados fiscais são entrada não confiável. Campos como nome de arquivo, chave, motivo, razão social, produto e qualquer texto originado do XML não devem ser interpretados como HTML executável.

Preferência arquitetural:

```text
valor fiscal não confiável
        ↓
textContent / DataTables com escape
        ↓
DOM
```

Evitar:

```text
valor fiscal não confiável
        ↓
concatenação de HTML / innerHTML
        ↓
DOM
```

## Compatibilidade

A Fase 4 não altera a lógica fiscal nem o visual planejado do dashboard. A CSP aplicada ainda mantém `unsafe-inline` porque o template principal possui handlers e scripts inline legados. A política estrita permanece em modo Report-Only enquanto essa migração é concluída.

## Evidência automatizada

`tests/test_security_phase4.py` verifica que:

- o diagnóstico não volta a renderizar linhas dinâmicas via `innerHTML`;
- a tabela de falhas não volta a construir sua estrutura principal com `innerHTML`;
- APIs seguras de DOM permanecem presentes;
- `/health` informa a capacidade `safe-dom-v4`.

## Próxima etapa

A próxima evolução de segurança deve migrar handlers `onclick` e scripts inline existentes em `templates/dashboard.html` para listeners e arquivos JavaScript externos. Somente depois dessa migração a remoção de `unsafe-inline` da CSP aplicada deve ser ativada em produção.

## Requisitos relacionados

- RNF-002 — tratamento seguro de conteúdo não confiável no front-end;
- RNF-003 — hardening HTTP;
- RNF-004 — evolução da Content Security Policy;
- RNF-009 — regressão automatizada;
- RNF-014 — documentação versionada.
