# COFINS v32 — diagnóstico documental por CST/CFOP

## Objetivo

Transformar a diferença global de COFINS do confronto XML x EFD-Contribuições em um diagnóstico rastreável, sem classificar automaticamente a diferença como erro fiscal.

## Regra de confronto

A v32 mantém o confronto documental da v30/v31 e acrescenta uma decomposição da COFINS por:

- CST da COFINS;
- CFOP;
- valor de COFINS nos XMLs;
- valor de COFINS na EFD-Contribuições;
- diferença XML - EFD.

Somente grupos com diferença absoluta igual ou superior a R$ 0,005 são exibidos no diagnóstico.

## Rastreabilidade

### XML

O snapshot `window.__omnixmlXmlPisCofins.snapshot()` passa a manter `cofins_detalhes`, com:

- chave;
- arquivo;
- modelo;
- número e série;
- item;
- CFOP;
- CST COFINS;
- receita;
- base de cálculo;
- valor de COFINS.

NF-e modelo 55 integralmente 5.929/6.929 continuam excluídas da base de confronto, conforme v31.

### EFD-Contribuições

Os registros C170/C175 passam a preservar também o contexto do C100 quando disponível:

- chave do documento;
- número do documento;
- arquivo de origem;
- número da linha no arquivo.

A tela resume essas referências no grupo CST/CFOP para facilitar a localização da origem da divergência.

## UX

A tabela legada de PIS/COFINS que permanecia vazia após a criação do confronto documental é ocultada. O painel principal de Receita/PIS/COFINS permanece, seguido pelo diagnóstico de COFINS quando houver diferença.

## Limites

A decomposição da v32 é documental. Ela não substitui a validação da apuração final contra o Bloco M (M200/M210 e M600/M610), que pode conter créditos, ajustes e outros componentes.

## Segurança

- processamento 100% local no navegador;
- nenhum XML ou SPED é enviado ao backend;
- sem novos endpoints;
- sem estilos inline;
- `style-src-attr 'none'` preservado.
