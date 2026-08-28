# Diagnóstico do fechamento v2

O diagnóstico é uma conferência complementar e não altera os totais fiscais do dashboard.

- Fica recolhido por padrão.
- Mostra apenas um resumo compacto no Dashboard Geral.
- Lacunas numéricas são avaliadas por modelo + série + mês.
- Apenas pequenos saltos de até 20 números são sinalizados como lacunas plausíveis.
- Saltos maiores são ignorados para evitar falsos positivos em exportações parciais ou sequências descontínuas.
- Falhas fiscais, duplicidades e alertas tributários continuam disponíveis para revisão.
