# Security Phase 5 — migração de handlers inline

## Objetivo

Reduzir a dependência de atributos HTML `onclick` como etapa intermediária para remoção futura de `unsafe-inline` da `script-src` da Content Security Policy (CSP), sem alterar o comportamento visual ou fiscal do dashboard.

## Implementação

O arquivo `static/inline_handler_bridge_v5.js` é carregado como script externo ao final da cadeia web. No `DOMContentLoaded`, ele identifica elementos legados que ainda possuem `onclick`, interpreta somente uma gramática mínima e conhecida, registra um `addEventListener('click', ...)` equivalente e remove o atributo `onclick` do DOM.

A implementação não usa `eval`, `Function` ou execução arbitrária de texto.

## Modelo de confiança

Somente nomes de funções presentes em uma allowlist explícita podem ser vinculados. Os argumentos aceitos ficam limitados a:

- strings literais;
- números;
- `this`;
- `null`;
- booleanos.

Expressões JavaScript, acesso a propriedades, chamadas aninhadas ou qualquer sintaxe fora desse subconjunto são rejeitados. Um handler não reconhecido tem seu atributo removido e não é executado.

## Funções legadas atualmente permitidas

A allowlist cobre ações de interface existentes, como mudança de aba, importação/auditoria, filtros dos cards, fechamento de modal, confronto SPED, exportação e ações equivalentes já definidas pelo dashboard.

## Defesa em profundidade

`browser_security_v3.js` continua removendo atributos de evento não confiáveis em elementos adicionados dinamicamente. A Phase 5 complementa essa proteção ao migrar os handlers estáticos legados da interface para listeners registrados por código externo.

## CSP

A CSP aplicada ainda mantém `unsafe-inline` porque `templates/dashboard.html` contém um bloco de script inline grande responsável pela inicialização de DataTables, gráficos e várias funções globais. A política estrita permanece em `Content-Security-Policy-Report-Only`.

Portanto, a Phase 5 não declara concluída a remoção de `unsafe-inline`. Ela elimina uma categoria de dependência: handlers HTML inline.

## Próxima etapa

A próxima fase deve extrair o bloco `<script>` inline do `dashboard.html` para um arquivo JavaScript próprio, revisar seus usos remanescentes de `innerHTML` e validar o dashboard sob CSP sem `unsafe-inline` em `script-src` antes de tornar a política estrita obrigatória.

## Evidência automatizada

`tests/test_security_phase5.py` verifica:

- ordem de carregamento do bridge;
- allowlist explícita;
- uso de `addEventListener` e remoção de `onclick`;
- ausência de `eval` e `new Function`;
- rejeição de argumentos arbitrários;
- publicação da capacidade no endpoint `/health`.
