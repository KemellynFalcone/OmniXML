# COFINS v39 — Origem da diferença

A v39 adiciona uma camada de navegação sobre o diagnóstico de COFINS já existente.

## Fluxo

**Competência → CST → CFOP → Documento**

Ao abrir uma divergência, o OmniXML identifica a competência dos XMLs e dos registros C170/C175 e permite selecionar o mês para chegar aos documentos que compõem aquele agrupamento.

## Pareamento seguro

Quando XML e EFD possuem chave de acesso, o sistema confronta os valores por documento e informa que há pareamento individual disponível.

Quando a EFD não fornece chave suficiente, o sistema mantém o diagnóstico agregado e sinaliza explicitamente que não existe vínculo nota a nota conclusivo.

## Dados exibidos por documento

- número do documento;
- chave resumida;
- COFINS no XML;
- COFINS na EFD;
- diferença;
- referência de origem na EFD (arquivo e linha).

## Segurança fiscal

A v39 é somente diagnóstica e de rastreabilidade. Ela não altera XML, não reescreve a EFD e não aplica ajuste fiscal automático.
