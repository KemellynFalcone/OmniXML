# OmniXML — Matriz de Rastreabilidade da ERS

**Documento relacionado:** `docs/ERS.md`  
**Linha de base:** ERS 1.0  
**Objetivo:** ligar requisito → prioridade → status → implementação → evidência/teste.

> Esta matriz é operacional. A ERS define **o que** o produto deve fazer; esta matriz registra **onde** o requisito está implementado e **como** sua evidência é obtida.

## Legenda

- **P0:** crítico — segurança, privacidade, integridade ou fluxo indispensável.
- **P1:** alto — operação fiscal principal.
- **P2:** médio — produtividade/qualidade relevante.
- **P3:** baixo — conveniência ou evolução.
- **IMPLEMENTADO:** comportamento existe na linha de base atual.
- **PARCIAL:** parte do requisito existe, mas há evolução prevista.
- **PLANEJADO:** requisito ainda não consolidado em produção.

## Requisitos funcionais

| ID | Prioridade | Status | Implementação principal | Evidência / teste |
|---|---|---|---|---|
| RF-001 | P1 | IMPLEMENTADO | `browser_local_v2.js` | fluxo de seleção de múltiplos XMLs |
| RF-002 | P1 | IMPLEMENTADO | `browser_local_v2.js` | input com seleção de pasta/subpastas |
| RF-003 | P0 | IMPLEMENTADO | `web_app_browser.py`, `browser_local_v2.js` | `/health`: `xml_upload=false`; processamento local |
| RF-004 | P1 | IMPLEMENTADO | `browser_local_v2.js`, `inutilization_capture.js` | testes de eventos/inutilizações |
| RF-005 | P1 | IMPLEMENTADO | `browser_local_v2.js` | parsing NF-e modelo 55 |
| RF-006 | P1 | IMPLEMENTADO | `browser_local_v2.js` | parsing NFC-e modelo 65 |
| RF-007 | P0 | IMPLEMENTADO | `browser_validation.js` | suíte de validação fiscal |
| RF-008 | P1 | IMPLEMENTADO | `browser_local_v2.js` | testes de classificação por CNPJ |
| RF-009 | P1 | IMPLEMENTADO | `browser_local_v2.js` | emitente = empresa → Saída |
| RF-010 | P1 | IMPLEMENTADO | `browser_local_v2.js` | destinatário = empresa → Entrada |
| RF-011 | P1 | IMPLEMENTADO | `browser_local_v2.js` | fallback Não classificada |
| RF-012 | P1 | IMPLEMENTADO | `browser_local_v2.js` | evento `110111` por chave |
| RF-013 | P1 | IMPLEMENTADO | `browser_local_v2.js`, `closing_diagnosis_v2.js` | cancelada continua ocupando número |
| RF-014 | P1 | IMPLEMENTADO | `inutilization_capture.js` | testes de captura de inutilização |
| RF-015 | P0 | IMPLEMENTADO | `inutilization_capture.js`, `closing_diagnosis_v2.js` | somente `cStat=102` justifica lacuna |
| RF-016 | P1 | IMPLEMENTADO | `browser_local_v2.js` | deduplicação por chave |
| RF-017 | P1 | IMPLEMENTADO | `browser_local_v2.js` | consolidação CFOP |
| RF-018 | P1 | IMPLEMENTADO | `browser_local_v2.js` | consolidação CST/CSOSN |
| RF-019 | P1 | IMPLEMENTADO | `browser_local_v2.js` | consolidação modelo+série |
| RF-020 | P2 | IMPLEMENTADO | `browser_local_v2.js` | faturamento diário |
| RF-021 | P1 | PARCIAL | `browser_local_v2.js` | heurísticas tributárias atuais; motor fiscal é evolução |
| RF-022 | P1 | IMPLEMENTADO | `failure_table_v2.js`, `failure_summary.js` | tabela de falhas enriquecida |
| RF-023 | P1 | IMPLEMENTADO | `closing_diagnosis_v2.js` | testes de diagnóstico |
| RF-024 | P0 | IMPLEMENTADO | `closing_diagnosis_v2.js` | filtro explícito `Saída` |
| RF-025 | P1 | IMPLEMENTADO | `closing_diagnosis_v2.js` | agrupamento modelo+série |
| RF-026 | P1 | IMPLEMENTADO | `closing_diagnosis_v2.js` | primeiro/último número da pasta |
| RF-027 | P1 | IMPLEMENTADO | `closing_diagnosis_v2.js` | detecção de ausentes no intervalo |
| RF-028 | P0 | IMPLEMENTADO | `closing_diagnosis_v2.js` | conciliação com inutilização homologada |
| RF-029 | P1 | IMPLEMENTADO | `closing_diagnosis_v2.js` | utilizado/cancelado/inutilizado/a conferir |
| RF-030 | P2 | IMPLEMENTADO | dashboard / `browser_local_v2.js` | exportações atuais |
| RF-031 | P1 | IMPLEMENTADO | `web_app_browser.py` | testes e endpoint `/health` |

## Regras de negócio

| ID | Prioridade | Status | Evidência principal |
|---|---|---|---|
| RN-001 | P0 | IMPLEMENTADO | classificação por CNPJ em `browser_local_v2.js` |
| RN-002 | P0 | IMPLEMENTADO | cancelada permanece na sequência |
| RN-003 | P0 | IMPLEMENTADO | inutilização homologada (`cStat 102`) |
| RN-004 | P0 | IMPLEMENTADO | sequência filtra somente Saídas |
| RN-005 | P1 | IMPLEMENTADO | diagnóstico trabalha apenas com conjunto local |
| RN-006 | P1 | IMPLEMENTADO | mapa de chaves/deduplicação |
| RN-007 | P1 | IMPLEMENTADO | interface diferencia alerta de erro objetivo |
| RN-008 | P0 | IMPLEMENTADO | `browser_validation.js` exige estrutura de autorização |

## Requisitos não funcionais

| ID | Prioridade | Status | Implementação / evidência |
|---|---|---|---|
| RNF-001 | P0 | IMPLEMENTADO | arquitetura browser-local; sem upload fiscal |
| RNF-002 | P0 | PARCIAL | `browser_security_v2.js` escapa dados; `browser_security_v3.js` bloqueia nós/atributos e navegações perigosas adicionados dinamicamente; remoção dos sinks legados na origem continua |
| RNF-003 | P0 | IMPLEMENTADO | headers em `web_app_browser.py`; `test_security_headers.py` |
| RNF-004 | P0 | PARCIAL | CSP ativa e ampliada; política estrita sem `unsafe-inline` em `Report-Only`; migração dos scripts inline ainda pendente |
| RNF-005 | P1 | IMPLEMENTADO | falha individual vira registro e lote continua |
| RNF-006 | P1 | PARCIAL | yield periódico; Web Workers ainda planejados |
| RNF-007 | P0 | IMPLEMENTADO | limites: 50.000 arquivos, 20 MB/arquivo, 1,5 GB total em `browser_security_v2.js` |
| RNF-008 | P2 | IMPLEMENTADO | seleção de pasta baseada em `webkitdirectory` |
| RNF-009 | P0 | IMPLEMENTADO | testes de regressão no repositório |
| RNF-010 | P0 | IMPLEMENTADO | GitHub Actions em PR para `main`; ruleset da `main` exige PR/check |
| RNF-011 | P0 | IMPLEMENTADO | Dependabot + `pip-audit` no CI |
| RNF-012 | P1 | IMPLEMENTADO | `/health` sem conteúdo fiscal |
| RNF-013 | P0 | IMPLEMENTADO | backend sem persistência de XML no fluxo atual |
| RNF-014 | P1 | IMPLEMENTADO | ERS + Engenharia + Manual + testes versionados |

## Requisitos de interface

| ID | Prioridade | Status | Evidência |
|---|---|---|---|
| RI-001 | P1 | IMPLEMENTADO | Dashboard Geral |
| RI-002 | P1 | IMPLEMENTADO | abas NF-e, NFC-e, cancelados, CFOP/CST/Série, auditoria, produtos e erros |
| RI-003 | P2 | IMPLEMENTADO | Diagnóstico do fechamento recolhido por padrão |
| RI-004 | P1 | IMPLEMENTADO | barra/status durante processamento |
| RI-005 | P0 | IMPLEMENTADO | modal informa processamento local e não envio |

## Controles de segurança — Fase 2 e Fase 3

| Controle | Status | Evidência |
|---|---|---|
| Escape de strings derivadas de XML/SPED nas tabelas principais | IMPLEMENTADO | `browser_security_v2.js` |
| Bloqueio de XML individual excessivamente grande | IMPLEMENTADO | limite 20 MB |
| Limite de quantidade de arquivos | IMPLEMENTADO | limite 50.000 |
| Limite agregado de seleção | IMPLEMENTADO | limite 1,5 GB |
| Auditoria de dependências Python | IMPLEMENTADO | `pip-audit -r requirements-prod.txt` no CI |
| Atualizações automatizadas | IMPLEMENTADO | `.github/dependabot.yml` |
| Proteção da `main` por PR e status check | IMPLEMENTADO | GitHub ruleset `Protect main` |
| Bloqueio defensivo de tags dinâmicas perigosas (`script`, `iframe`, `object`, `embed`) | IMPLEMENTADO | `browser_security_v3.js`, `test_security_phase3.py` |
| Bloqueio de handlers/eventos e `srcdoc` não confiáveis em nós dinâmicos | IMPLEMENTADO | `browser_security_v3.js` |
| Bloqueio de esquemas `javascript:`/`vbscript:`/HTML em data URL | IMPLEMENTADO | `browser_security_v3.js` |
| Validação de chave e destino antes de abrir portal SEFAZ | IMPLEMENTADO | wrapper de `copiarEAbrir` em `browser_security_v3.js` |
| CSP mais restritiva sem `unsafe-inline` | PARCIAL | `Content-Security-Policy-Report-Only`; migração do código inline pendente |
| Dependências JS locais/SRI | PLANEJADO | inventário de CDN pendente |
| Remoção dos sinks `innerHTML` na origem | PLANEJADO | próxima etapa da Fase 3 |
| Web Workers | PLANEJADO | performance/isolamento para lotes grandes |
| Testes end-to-end em navegador com payload XSS | PLANEJADO | complementar aos testes estáticos atuais |

## Política de mudança

Para cada requisito alterado, o PR correspondente deve indicar:

1. IDs de requisitos afetados;
2. regra de negócio impactada;
3. arquivos de implementação;
4. teste/evidência de aceitação;
5. documentação atualizada;
6. risco de regressão e impacto de segurança, quando aplicável.

A rastreabilidade deve ser revisada sempre que um requisito mudar de **PLANEJADO → PARCIAL → IMPLEMENTADO**.
