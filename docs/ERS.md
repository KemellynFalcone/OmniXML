# OmniXML — ERS — Especificação de Requisitos de Software

**Versão:** 1.0  
**Status:** Documento vivo  
**Produto:** OmniXML  
**Tipo de sistema:** Auditoria e conferência de documentos fiscais eletrônicos  
**Arquitetura atual:** Aplicação web com processamento local no navegador

> Esta ERS descreve os requisitos do sistema conforme o comportamento atualmente implementado e o backlog técnico já definido. Ela deve ser atualizada sempre que uma regra funcional, fiscal, de segurança ou arquitetura for alterada.

---

## 1. Objetivo do documento

Esta Especificação de Requisitos de Software define o escopo, os requisitos funcionais, requisitos não funcionais, regras de negócio, restrições, interfaces, critérios de aceitação e limites do OmniXML.

O documento serve como referência para desenvolvimento, testes, manutenção, auditoria técnica, documentação operacional e evolução do produto.

---

## 2. Visão geral do produto

O OmniXML é uma ferramenta destinada à leitura, organização, conferência e auditoria de documentos fiscais eletrônicos, com foco inicial em NF-e modelo 55, NFC-e modelo 65, eventos de cancelamento e inutilizações.

Na arquitetura web atual, os XMLs são processados localmente no navegador do usuário. O servidor do OmniXML entrega a interface, scripts e healthcheck, mas não recebe os arquivos fiscais selecionados durante o fluxo normal de auditoria.

O sistema apresenta os resultados em dashboard, tabelas, indicadores, diagnósticos e exportações.

---

## 3. Objetivos de negócio

O OmniXML deve:

- reduzir o tempo necessário para conferência de grandes volumes de XMLs;
- facilitar a identificação de falhas estruturais e fiscais observáveis nos documentos;
- separar corretamente operações de entrada e saída da empresa auditada;
- consolidar dados por modelo, série, CFOP, CST/CSOSN, período e produto;
- identificar documentos cancelados, duplicidades e inutilizações;
- detectar lacunas na numeração das saídas;
- distinguir lacunas justificadas por inutilização de números ainda a conferir;
- preservar a privacidade dos documentos processando-os localmente sempre que possível;
- fornecer informações de auditoria sem transformar heurísticas em conclusões fiscais definitivas.

---

## 4. Partes interessadas

### 4.1 Usuário operacional
Profissional que seleciona os XMLs, acompanha o processamento, interpreta o dashboard e exporta os resultados.

### 4.2 Profissional fiscal/contábil
Responsável pela validação fiscal dos achados, conferência de alertas e tomada de decisão sobre eventuais inconsistências.

### 4.3 Engenharia/desenvolvimento
Responsável pela implementação, testes, segurança, documentação, manutenção e evolução do sistema.

### 4.4 Administração do produto
Responsável por definir prioridades, escopo, roadmap e regras de uso do OmniXML.

---

## 5. Escopo funcional atual

O escopo da versão atual inclui:

- seleção de arquivos XML individuais;
- seleção de pasta contendo XMLs e subpastas;
- processamento local no navegador;
- identificação do tipo documental;
- leitura de NF-e modelo 55;
- leitura de NFC-e modelo 65;
- leitura de eventos de cancelamento;
- leitura de inutilizações;
- validação estrutural mínima de documentos autorizados;
- identificação da empresa auditada por CNPJ;
- classificação em Entrada, Saída ou Não classificada;
- deduplicação por chave;
- consolidação fiscal e financeira;
- diagnóstico de sequência de numeração;
- conciliação de lacunas com inutilizações homologadas;
- exibição de falhas e alertas;
- exportação dos dados consolidados;
- healthcheck da aplicação.

---

## 6. Fora do escopo atual

Não fazem parte do escopo funcional consolidado da versão atual:

- autenticação de usuários;
- banco de dados fiscal no servidor;
- armazenamento permanente de XMLs no backend;
- consulta automática em tempo real à SEFAZ;
- uso de certificado digital pelo servidor;
- validação XSD oficial completa de todos os documentos;
- escrituração SPED/EFD integralmente processada no fluxo browser-local;
- decisão tributária automática;
- substituição de análise profissional fiscal/contábil.

---

# 7. Requisitos funcionais

## RF-001 — Seleção de XMLs

O sistema deve permitir ao usuário selecionar múltiplos arquivos XML individuais para processamento.

**Critério de aceitação:** ao selecionar arquivos válidos, o sistema deve iniciar o processamento local e apresentar progresso.

---

## RF-002 — Seleção de pasta

O sistema deve permitir a seleção de uma pasta contendo XMLs, incluindo arquivos existentes em subpastas quando suportado pelo navegador.

**Critério de aceitação:** todos os arquivos `.xml` selecionados pelo mecanismo de pasta devem ser considerados na execução.

---

## RF-003 — Processamento local

O sistema deve processar os XMLs selecionados no navegador, sem enviá-los ao backend no fluxo web atual.

**Critério de aceitação:** a aplicação de produção não deve depender de endpoint de upload para realizar a auditoria de XMLs.

---

## RF-004 — Identificação do tipo documental

O sistema deve identificar, no mínimo, documentos e eventos suportados pelas estruturas:

- `NFe`;
- `nfeProc`;
- `evento`;
- `procEventoNFe`;
- `retEvento`;
- `procInutNFe`;
- `retInutNFe`;
- `inutNFe`.

Documentos não reconhecidos devem ser classificados como não tratados ou erro de processamento, conforme a implementação vigente.

---

## RF-005 — Leitura de NF-e modelo 55

O sistema deve extrair de NF-e, quando disponíveis, no mínimo:

- chave de acesso;
- número da nota;
- série;
- data de emissão;
- modelo;
- valor total;
- CNPJ/CPF e nome do emitente;
- CNPJ/CPF e nome do destinatário;
- itens;
- código de produto;
- descrição;
- NCM;
- CFOP;
- CST ou CSOSN;
- quantidade;
- valor do item.

---

## RF-006 — Leitura de NFC-e modelo 65

O sistema deve processar NFC-e modelo 65 e extrair os mesmos grupos essenciais de dados aplicáveis às NF-e.

---

## RF-007 — Validação estrutural do XML

O sistema deve rejeitar ou sinalizar XMLs malformados ou documentos fiscais sem estruturas mínimas exigidas pela regra implementada.

Devem ser verificadas, conforme aplicável:

- presença de `infNFe`;
- existência de `nfeProc` para documento fiscal final;
- existência de `protNFe/infProt`;
- status de autorização aceito;
- assinatura XML;
- coerência entre chave da NF-e e chave do protocolo;
- QR Code em NFC-e quando exigido pela regra vigente.

---

## RF-008 — Identificação da empresa auditada

O sistema deve identificar um CNPJ principal da empresa auditada com base nos documentos carregados.

A estratégia atual deve priorizar a frequência de CNPJs emitentes de NFC-e e, na ausência, utilizar emitentes das demais notas.

**Observação:** trata-se de uma heurística operacional e o usuário deve conferir a empresa identificada no cabeçalho.

---

## RF-009 — Classificação de Saída

O sistema deve classificar um documento como **Saída** quando o CNPJ da empresa auditada for igual ao CNPJ do emitente.

---

## RF-010 — Classificação de Entrada

O sistema deve classificar um documento como **Entrada** quando o CNPJ da empresa auditada for igual ao CNPJ do destinatário e a empresa não for o emitente.

---

## RF-011 — Documento não classificado

O sistema deve classificar como **Não classificada** uma nota que não possa ser relacionada com segurança à empresa auditada pelas regras atuais.

---

## RF-012 — Cancelamento

O sistema deve reconhecer eventos de cancelamento com `tpEvento = 110111` e relacioná-los à NF-e/NFC-e correspondente pela chave de acesso.

Quando o cancelamento for considerado confirmado pela regra implementada, o documento original deve permanecer no conjunto processado, com status de cancelado.

---

## RF-013 — Numeração de documento cancelado

Uma nota cancelada deve continuar sendo considerada número utilizado na sequência fiscal.

---

## RF-014 — Inutilização

O sistema deve reconhecer XMLs de inutilização e extrair, quando disponíveis:

- modelo;
- série;
- número inicial;
- número final;
- CNPJ;
- justificativa;
- `cStat`;
- protocolo ou metadados correlatos.

---

## RF-015 — Inutilização homologada

O sistema deve considerar automaticamente como justificativa de lacuna somente uma inutilização homologada conforme a regra vigente, atualmente `cStat = 102`.

---

## RF-016 — Deduplicação por chave

O sistema deve detectar documentos repetidos com a mesma chave de acesso e impedir que cópias do mesmo documento distorçam as consolidações.

A duplicidade deve ser apresentada para conferência.

---

## RF-017 — Consolidação de CFOP

O sistema deve agrupar e totalizar valores de saída por CFOP, respeitando os filtros e regras de exclusão do processador vigente.

---

## RF-018 — Consolidação de CST/CSOSN

O sistema deve agrupar e totalizar valores de saída por CST/CSOSN.

---

## RF-019 — Consolidação por série

O sistema deve agrupar documentos de saída por modelo e série para fins de análise financeira e de sequência.

---

## RF-020 — Faturamento diário

O sistema deve gerar consolidação diária das saídas consideradas válidas para o cálculo conforme as regras atuais.

---

## RF-021 — Alertas tributários

O sistema deve gerar alertas quando combinações de NCM, CFOP, CST/CSOSN ou outras regras implementadas forem consideradas atípicas.

Esses resultados devem ser apresentados como **alerta** ou **conferência**, e não como conclusão fiscal definitiva, salvo quando a condição for objetivamente comprovável pelo arquivo.

---

## RF-022 — Arquivos com erro

O sistema deve apresentar os arquivos que falharam na leitura ou validação, incluindo, sempre que disponível:

- arquivo/caminho;
- número;
- chave;
- valor;
- motivo da falha.

---

## RF-023 — Diagnóstico de fechamento

O sistema deve apresentar um diagnóstico complementar contendo, no mínimo, indicadores de:

- falhas fiscais;
- lacunas na sequência das saídas;
- inutilizações que justificam lacunas;
- números ainda a conferir;
- duplicidades;
- alertas tributários.

---

## RF-024 — Sequência somente de saídas

A conferência de sequência deve considerar exclusivamente documentos classificados como **Saída** da empresa auditada.

NF-e de entrada de fornecedores não deve participar do cálculo.

---

## RF-025 — Agrupamento da sequência

A sequência deve ser analisada separadamente por **modelo + série**.

---

## RF-026 — Intervalo da sequência

Para cada grupo de modelo + série, o sistema deve considerar como intervalo:

- número inicial = menor número encontrado entre as saídas da pasta;
- número final = maior número encontrado entre as saídas da pasta.

A análise não deve inferir documentos fora desse intervalo apenas por ausência na pasta carregada.

---

## RF-027 — Número ausente

O sistema deve identificar números inexistentes dentro do intervalo definido para cada modelo + série.

---

## RF-028 — Conciliação com inutilização

Para cada número ausente, o sistema deve verificar se ele está coberto por uma faixa de inutilização homologada do mesmo modelo e série.

---

## RF-029 — Situação de sequência

O sistema deve distinguir pelo menos as seguintes situações:

- **Utilizado:** existe NF-e/NFC-e para o número;
- **Cancelado:** existe documento e cancelamento confirmado; continua utilizado;
- **Inutilizado:** número ausente coberto por inutilização homologada;
- **A conferir:** número ausente sem justificativa localizada no conjunto de arquivos processados.

---

## RF-030 — Exportação

O sistema deve permitir exportar os dados consolidados em formato disponível na interface atual, preservando campos fiscais essenciais.

---

## RF-031 — Healthcheck

O backend deve disponibilizar endpoint de saúde da aplicação contendo status e identificadores das principais capacidades de produção.

---

# 8. Regras de negócio

## RN-001 — Classificação por participante

A classificação de Entrada/Saída deve ser baseada nos CNPJs dos participantes do documento, e não no nome da pasta onde o XML foi encontrado.

## RN-002 — Cancelamento não cria lacuna

O cancelamento não elimina a utilização da numeração da nota original.

## RN-003 — Inutilização justifica ausência

A inutilização homologada justifica a ausência de um número dentro da sequência normal de emissão.

## RN-004 — Entrada não participa da sequência

Documentos de entrada de fornecedores nunca devem ser usados para determinar lacunas da numeração emitida pela empresa auditada.

## RN-005 — Escopo local da conferência

A análise reflete exclusivamente os arquivos carregados pelo usuário. A ausência de um evento ou inutilização na pasta não prova que ele não exista na SEFAZ.

## RN-006 — Duplicidade não soma duas vezes

Documentos duplicados por chave não devem duplicar valores nos totais consolidados.

## RN-007 — Alertas não são autuações

Alertas tributários e heurísticas devem ser apresentados como apoio à auditoria, não como afirmação definitiva de irregularidade.

## RN-008 — Integridade acima da completude aparente

Um XML incompleto ou sem autorização válida não deve ser tratado como documento fiscal final somente por estar bem-formado sintaticamente.

---

# 9. Requisitos não funcionais

## RNF-001 — Privacidade

Os XMLs devem permanecer no dispositivo do usuário durante o processamento da arquitetura browser-local atual.

## RNF-002 — Segurança de entrada

Todo conteúdo proveniente de XML deve ser tratado como não confiável.

Dados textuais extraídos do XML não devem ser executados como HTML ou JavaScript.

## RNF-003 — Cabeçalhos HTTP de segurança

O backend deve aplicar políticas de segurança HTTP, incluindo proteção contra framing, MIME sniffing e políticas de origem/referência compatíveis com a aplicação.

## RNF-004 — Content Security Policy

A aplicação deve possuir Content-Security-Policy. Dependências legadas que exijam `unsafe-inline` devem ser tratadas como débito técnico e progressivamente removidas.

## RNF-005 — Disponibilidade

Falhas ao processar um XML individual não devem interromper obrigatoriamente o processamento de todos os demais arquivos, salvo erro fatal da aplicação.

## RNF-006 — Desempenho

O sistema deve permanecer responsivo durante cargas grandes, realizando liberação periódica do event loop ou mecanismo equivalente.

O roadmap deve prever Web Workers para melhorar cargas muito grandes.

## RNF-007 — Limites de recursos

O sistema deve evoluir para impor limites explícitos de quantidade, tamanho e complexidade de arquivos, evitando consumo excessivo de memória ou CPU.

## RNF-008 — Compatibilidade

A seleção de pasta depende de recursos de navegador compatíveis com `webkitdirectory` ou mecanismo equivalente suportado pela interface.

## RNF-009 — Testabilidade

Toda alteração de regra fiscal ou funcional relevante deve possuir teste automatizado de regressão.

## RNF-010 — Integração contínua

Pull Requests destinados à `main` devem executar testes automatizados no GitHub Actions antes do merge.

## RNF-011 — Gestão de dependências

Dependências Python e GitHub Actions devem ser monitoradas para atualizações e vulnerabilidades conhecidas.

## RNF-012 — Observabilidade mínima

O backend deve disponibilizar healthcheck simples, sem expor dados fiscais ou segredos.

## RNF-013 — Não persistência fiscal no backend

Na arquitetura atual, o backend não deve armazenar conteúdo fiscal dos XMLs processados localmente.

## RNF-014 — Manutenibilidade

Documentação de engenharia, ERS, manual operacional e testes devem acompanhar mudanças de comportamento.

---

# 10. Requisitos de interface

## RI-001 — Dashboard geral

A interface deve exibir indicadores consolidados de quantidade de documentos, operações, valores, cancelamentos e falhas.

## RI-002 — Tabelas por domínio

A interface deve disponibilizar visões separadas para NF-e, NFC-e, cancelamentos, CFOP/CST/Série, auditoria, produtos e arquivos com erro, conforme módulos habilitados.

## RI-003 — Diagnóstico recolhível

O diagnóstico de fechamento deve poder permanecer recolhido por padrão para não dominar visualmente o dashboard.

## RI-004 — Progresso

Durante o processamento, a interface deve informar andamento e quantidade de arquivos processados.

## RI-005 — Mensagem de privacidade

A interface de importação deve informar que os XMLs são processados no navegador e não são enviados ao servidor no fluxo atual.

---

# 11. Modelo de dados lógico mínimo

## 11.1 Nota fiscal

Uma nota processada deve poder representar, no mínimo:

```text
arquivo
chave
numero_nota
serie
data
valor
tipo/modelo
operacao
status
emitente_nome
emitente_cnpj
destinatario_nome
destinatario_cnpj
itens
```

## 11.2 Item

```text
codigo
nome
ncm
cfop
cst/csosn
unidade
quantidade
valor_bruto
desconto
valor
```

## 11.3 Cancelamento

```text
tipo
arquivo
chave
confirmado
cstat
motivo
```

## 11.4 Inutilização

```text
arquivo
modelo
serie
numero_inicial
numero_final
cnpj
cstat
motivo/justificativa
homologada
```

## 11.5 Erro

```text
arquivo
caminho
numero
chave
valor
motivo
```

---

# 12. Casos de uso principais

## UC-001 — Auditar uma pasta fiscal

**Ator:** Usuário operacional  
**Pré-condição:** usuário possui uma pasta com XMLs fiscais.  
**Fluxo principal:**

1. usuário abre o OmniXML;
2. seleciona a opção de importar pasta;
3. escolhe a pasta;
4. sistema filtra os XMLs;
5. sistema lê e valida cada arquivo localmente;
6. sistema identifica a empresa;
7. sistema classifica entradas e saídas;
8. sistema aplica eventos e inutilizações;
9. sistema calcula consolidações;
10. sistema apresenta o dashboard e diagnóstico.

**Pós-condição:** dados da auditoria ficam disponíveis na sessão atual do navegador.

---

## UC-002 — Conferir uma lacuna

**Ator:** Profissional fiscal/contábil  
**Fluxo:**

1. usuário abre o Diagnóstico do fechamento;
2. seleciona visualmente um modelo e série com número ausente;
3. sistema verifica se o número está coberto por inutilização homologada;
4. se estiver, apresenta como inutilizado/justificado;
5. se não estiver, mantém como a conferir.

---

## UC-003 — Identificar XML inválido ou incompleto

**Ator:** Usuário operacional  
**Fluxo:**

1. XML é selecionado;
2. sistema tenta realizar parsing e validação estrutural;
3. documento não atende requisitos mínimos;
4. sistema registra a falha;
5. arquivo aparece na área de erros com motivo.

---

# 13. Critérios gerais de aceitação

Uma versão só deve ser considerada pronta para produção quando:

- testes automatizados relevantes estiverem passando;
- regras de negócio alteradas estiverem documentadas;
- ERS e documento de engenharia estiverem coerentes com a implementação;
- funcionalidades críticas tiverem comportamento verificável com XMLs de teste;
- não houver regressão conhecida nos fluxos de importação, classificação e dashboard;
- alterações de segurança tiverem teste correspondente sempre que tecnicamente possível.

---

# 14. Matriz de rastreabilidade inicial

| Requisito | Componente principal | Teste/controle esperado |
|---|---|---|
| RF-003 | `web_app_browser.py` / `browser_local_v2.js` | ausência de endpoint de upload + fluxo local |
| RF-007 | `browser_validation.js` | testes de validação fiscal |
| RF-008 a RF-011 | `browser_local_v2.js` | testes de classificação por CNPJ |
| RF-012/RF-013 | `browser_local_v2.js` | testes de cancelamento |
| RF-014/RF-015 | `inutilization_capture.js` | testes de inutilização |
| RF-024 a RF-029 | `closing_diagnosis_v2.js` | testes de diagnóstico/fechamento |
| RF-016 | `browser_local_v2.js` | testes de duplicidade |
| RNF-003/RNF-004 | `web_app_browser.py` | `test_security_headers.py` |
| RNF-009/RNF-010 | `.github/workflows/tests.yml` | execução de CI |
| RNF-011 | `.github/dependabot.yml` | monitoramento periódico |

---

# 15. Segurança — requisitos futuros prioritários

Os seguintes itens devem ser tratados como backlog de segurança prioritário:

- auditoria completa de todos os usos de `innerHTML`;
- sanitização/escape uniforme de dados provenientes de XML;
- testes com payloads XSS em campos como `xNome`, `xProd`, `xMotivo` e similares;
- limites de tamanho por arquivo;
- limite total de arquivos por execução;
- limite de memória e estratégia de processamento em lotes;
- inventário de CDNs;
- uso de SRI ou hospedagem local de dependências quando viável;
- remoção progressiva de `unsafe-inline` da CSP;
- scanner automatizado de dependências no CI;
- testes com XMLs adversariais e arquivos extremamente grandes.

---

# 16. Evoluções planejadas

A ERS deverá receber novos requisitos quando forem implementados:

- validação XSD oficial SEFAZ;
- auditoria avançada de eventos;
- validação XML × SPED por chave;
- motor de regras fiscais por produto;
- filtros avançados por período, modelo, série e status;
- exportação Excel profissional em múltiplas abas;
- Web Workers;
- PWA/offline;
- seleção explícita de empresa/CNPJ;
- eventual integração controlada com serviços oficiais, se aprovada arquiteturalmente.

---

# 17. Convenção de prioridade

Os requisitos poderão ser classificados futuramente como:

- **P0 — Crítico:** segurança, integridade ou comportamento indispensável;
- **P1 — Alto:** necessário para operação fiscal principal;
- **P2 — Médio:** melhora relevante de produtividade ou qualidade;
- **P3 — Baixo:** conveniência ou evolução futura.

---

# 18. Gestão de mudanças

Toda alteração de requisito deve registrar:

- requisito afetado;
- motivação;
- mudança de comportamento;
- impacto no código;
- testes correspondentes;
- impacto no Manual Operacional;
- impacto no Documento de Engenharia;
- versão da ERS.

A política documental do projeto é:

```text
mudança funcional = código + teste + documentação
```

---

# 19. Referências internas do projeto

Esta ERS deve ser lida em conjunto com:

- `docs/MANUAL_OPERACIONAL.md`;
- `docs/ENGENHARIA.md`;
- testes automatizados do projeto;
- código da branch principal em produção.

---

# 20. Aprovação

**Versão 1.0:** estabelece a linha de base inicial de requisitos do OmniXML conforme o comportamento implementado até a presente versão do produto.

Alterações posteriores devem incrementar a versão desta ERS e atualizar a matriz de rastreabilidade.
