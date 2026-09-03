# Security Phase 12 — CSP de estilos separada

## Objetivo

Endurecer a política de estilos após a migração do Tailwind para CSS compilado/local, sem quebrar DataTables e outros componentes que ainda ajustam atributos `style` dinamicamente.

## Implementação

A política aplicada deixa de usar `'unsafe-inline'` no `style-src` geral e passa a separar explicitamente:

- `style-src`: origens autorizadas para estilos;
- `style-src-elem`: folhas de estilo e elementos `<style>`, sem `'unsafe-inline'`;
- `style-src-attr`: compatibilidade temporária com atributos `style`, ainda com `'unsafe-inline'`.

A política Report-Only é mais agressiva e testa `style-src-attr 'none'`, permitindo identificar o que ainda depende de estilos inline dinâmicos antes de bloquear em produção.

## Ganho de segurança

Depois das Phases 9 e 11, o OmniXML já entrega o CSS próprio e o Tailwind por arquivos externos. A Phase 12 impede que blocos `<style>` inline sejam aceitos pela política aplicada e restringe a exceção de compatibilidade somente aos atributos de estilo.

## Por que `style-src-attr` ainda não é bloqueado

DataTables, jQuery e componentes de layout podem definir largura, visibilidade e posicionamento por atributos `style` em tempo de execução. Bloquear esses atributos sem inventário/remoção prévia pode provocar regressões visuais ou funcionais.

Por isso, a Phase 12 não declara a remoção total de estilos inline. Ela isola a dívida remanescente e testa o bloqueio total em Report-Only.

## Evidência operacional

O `/health` publica:

```text
"style_csp_enforcement": "strict-elements-compat-attrs-v12"
```

## Contratos preservados

A fase não altera regras fiscais, processamento browser-local, CNPJ alfanumérico, classificação Entrada/Saída, validação XML, DataTables, exportação Excel ou gráficos.

## Próxima etapa

Inventariar os estilos aplicados dinamicamente por DataTables/runtime, substituir os casos controláveis por classes CSS e então remover `'unsafe-inline'` também de `style-src-attr`.
