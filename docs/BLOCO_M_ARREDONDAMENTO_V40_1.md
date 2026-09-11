# OmniXML v40.1 — Explicação de arredondamento no Bloco M

## Objetivo

A v40.1 melhora a leitura das diferenças entre a escrituração documental (C170/C175) e o detalhamento do Bloco M (M210/M610).

Uma diferença pequena deixa de ser apresentada apenas como ponto genérico de investigação quando houver evidência suficiente de que ela é compatível com arredondamento acumulado por item.

## Quando o OmniXML sugere provável arredondamento

A classificação somente é aplicada quando:

1. o valor do Bloco M é matematicamente compatível com `base ajustada × alíquota`, arredondado para centavos;
2. não existem ajustes de acréscimo, redução ou diferimentos no M210/M610 que expliquem a diferença;
3. a diferença entre C170/C175 e M210/M610 está dentro de uma tolerância proporcional à quantidade de itens documentais tributados.

A tolerância considera até meio centavo de efeito de arredondamento por item, acrescido de uma margem de um centavo para comparação.

## Mensagem apresentada

Quando as condições forem atendidas, o OmniXML apresenta:

> Provável diferença de arredondamento. O C170/C175 soma valores calculados por item, enquanto o Bloco M calcula a contribuição sobre a base consolidada. Validar antes de tratar como divergência fiscal.

A diferença permanece visível na tabela e não é eliminada nem automaticamente considerada correta.

## Segurança fiscal

Se qualquer condição não for atendida, o sistema mantém o diagnóstico de investigação e orienta revisar outros blocos, ajustes e a composição da apuração.

A v40.1 é apenas diagnóstica e não altera XML, EFD-Contribuições ou qualquer valor fiscal automaticamente.
