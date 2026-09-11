# Security Phase 19 — consolidação de hosts de scripts

## Objetivo

Reduzir a superfície de dependências externas antes da vendorização local completa, mantendo o dashboard e o processamento fiscal inalterados.

## Mudanças

- jQuery 3.7.0 passa de `code.jquery.com` para jsDelivr com versão exata;
- JSZip 3.10.1 passa de `cdnjs.cloudflare.com` para jsDelivr com versão exata;
- Chart.js permanece fixado em 4.5.1;
- DataTables 1.13.6 e Buttons 2.4.1 permanecem fixados no host oficial;
- `script-src` deixa de autorizar `code.jquery.com`;
- o comportamento continua fail-closed: se as importações históricas esperadas sumirem do template, a transformação falha em vez de entregar um estado parcial.

## Por que esta etapa vem antes da vendorização local

A aplicação ainda usa bibliotecas externas grandes. Antes de trazê-las para `/static`, esta fase reduz o número de hosts de script e elimina uma inconsistência importante: o JSZip vinha de cdnjs, enquanto o CSP de scripts já não autorizava esse host. Ao movê-lo para jsDelivr, o grafo real de dependências volta a coincidir com o `script-src` aplicado.

## Segurança preservada

- `style-src-attr 'none'` continua aplicado globalmente desde a Phase 18;
- scripts inline continuam bloqueados;
- processamento XML continua 100% no navegador;
- nenhuma regra fiscal, classificação, sequência, inutilização ou suporte a CNPJ alfanumérico foi alterado.

## Próximo passo

Vendorizar gradualmente jQuery, JSZip, Chart.js e o conjunto DataTables/Buttons em `/static`, removendo depois os hosts externos correspondentes de `script-src`.