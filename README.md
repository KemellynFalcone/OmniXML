# OmniXML — Auditoria Fiscal de XML

O **OmniXML** é uma aplicação web para leitura, conferência e auditoria de documentos fiscais eletrônicos, com foco atual em **NF-e (modelo 55)**, **NFC-e (modelo 65)**, eventos de cancelamento, inutilizações e diagnóstico de fechamento.

🌐 **Produção:** https://omnixml.onrender.com

> Na arquitetura web atual, os XMLs são processados **localmente no navegador do usuário**. O backend entrega a aplicação, mas não recebe os arquivos fiscais selecionados no fluxo normal de auditoria.

---

## Estado atual

O projeto já ultrapassou a fase inicial de refatoração e possui uma arquitetura web browser-local em produção, com testes automatizados, documentação de requisitos, hardening de segurança e fluxo de auditoria fiscal ativo.

### Capacidades implementadas

- seleção de XMLs individuais ou de uma pasta inteira;
- processamento local dos XMLs no navegador;
- leitura de NF-e modelo 55 e NFC-e modelo 65;
- identificação da empresa auditada por CNPJ dos participantes;
- classificação de operações em **Entrada**, **Saída** ou **Não classificada**;
- cancelamentos relacionados pela chave da NF-e/NFC-e;
- inutilizações homologadas (`cStat = 102`);
- deduplicação por chave de acesso;
- validação estrutural e de autorização do documento;
- conferência de CFOP, CST/CSOSN, série, produtos e faturamento;
- diagnóstico de sequência fiscal somente das saídas;
- conciliação de lacunas numéricas com inutilizações homologadas;
- área de arquivos com erro com chave, número, valor e motivo quando disponíveis;
- exportação dos dados consolidados;
- healthcheck de produção;
- Content-Security-Policy e demais cabeçalhos HTTP de segurança;
- proteção adicional contra conteúdo hostil proveniente de XML/SPED;
- limites preventivos para cargas excessivas;
- auditoria de dependências Python no CI;
- Dependabot para Python e GitHub Actions.

---

## Como funciona

```text
Arquivos selecionados
        ↓
Leitura local no navegador
        ↓
Parsing e identificação do XML
        ↓
Validação estrutural/autorização
        ↓
Extração dos dados fiscais
        ↓
Identificação do CNPJ auditado
        ↓
Classificação Entrada / Saída
        ↓
Cancelamentos e inutilizações
        ↓
Consolidações e regras de auditoria
        ↓
Dashboard + Diagnóstico do fechamento
```

### Regra de operação

A classificação principal é determinada pelos participantes do XML:

- **Saída:** a empresa auditada é o emitente;
- **Entrada:** a empresa auditada é o destinatário;
- **Não classificada:** o documento não pode ser relacionado com segurança à empresa identificada.

NF-e de entrada não participa da sequência de numeração das notas emitidas pela empresa.

---

## Diagnóstico do fechamento

A conferência de sequência considera somente documentos de **Saída**, agrupados por **modelo + série**.

Dentro do intervalo entre o primeiro e o último número encontrado na pasta:

- uma nota emitida ocupa sua numeração, mesmo se posteriormente cancelada;
- uma inutilização homologada justifica um número sem nota;
- um número sem nota e sem inutilização homologada permanece como **A conferir**.

A ausência de um evento ou inutilização nos arquivos selecionados não prova que ele não exista na SEFAZ; indica apenas que ele não foi localizado no conjunto analisado.

---

## Segurança e privacidade

O OmniXML trata documentos fiscais como dados sensíveis e adota processamento browser-local como princípio arquitetural da versão web atual.

Controles implementados incluem:

- XMLs não são enviados ao backend durante a auditoria normal;
- CSP e cabeçalhos contra framing, MIME sniffing e exposição desnecessária de referência/origem;
- tratamento de conteúdo vindo de XML como entrada não confiável;
- camada de escape antes da renderização de dados dinâmicos críticos;
- limite de até **50.000 arquivos** por seleção;
- limite de **20 MB por XML**;
- limite de **1,5 GB por seleção**;
- `pip-audit` no GitHub Actions;
- Dependabot para dependências Python e GitHub Actions.

A remoção progressiva de renderizações legadas com `innerHTML` e de `unsafe-inline` da CSP permanece no roadmap de segurança.

---

## Documentação

A documentação do projeto é mantida junto ao código:

- [Manual Operacional](docs/MANUAL_OPERACIONAL.md)
- [Documento de Engenharia](docs/ENGENHARIA.md)
- [ERS — Especificação de Requisitos de Software](docs/ERS.md)
- [Matriz de Rastreabilidade da ERS](docs/ERS_RASTREABILIDADE.md)

Política de engenharia do projeto:

```text
mudança funcional = código + teste + documentação
```

---

## Execução local

Crie o ambiente virtual:

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

Para executar a aplicação web equivalente ao fluxo atual de produção:

```bash
python web_app_browser.py
```

Em produção o serviço é iniciado com:

```bash
gunicorn web_app_browser:app
```

---

## Testes e CI

Execute localmente:

```bash
pytest -q
```

O GitHub Actions executa os testes automaticamente em Pull Requests para `main` e nos pushes configurados. O pipeline também executa auditoria das dependências de produção com `pip-audit`.

---

## Dados fiscais no repositório

Nunca faça commit de:

- XMLs fiscais de clientes;
- arquivos SPED/EFD reais;
- certificados digitais;
- senhas, tokens ou credenciais;
- bases exportadas contendo dados fiscais reais.

O `.gitignore` bloqueia extensões e diretórios comuns, mas sempre revise `git status` antes de publicar alterações.

---

## Próximas evoluções

As prioridades técnicas e fiscais atuais incluem:

1. concluir a auditoria XSS e reduzir/remover `unsafe-inline` da CSP;
2. validação XSD oficial da SEFAZ por modelo e versão;
3. validação avançada de chave, protocolo e eventos;
4. reconciliação fiscal XML × SPED por chave;
5. motor de regras tributárias contextual e versionado;
6. filtros avançados por período, modelo, série e status;
7. exportação Excel profissional em múltiplas abas;
8. Web Workers para grandes volumes;
9. redução de dependências externas/CDNs e evolução para modo offline/PWA.

---

## Limites da auditoria

O OmniXML é uma ferramenta de apoio à auditoria fiscal. O sistema diferencia **erro**, **inconsistência**, **alerta** e **informação** sempre que possível.

Uma heurística ou combinação tributária atípica não deve ser interpretada automaticamente como infração fiscal. A conclusão final deve considerar o XML original, eventos oficiais, escrituração e análise profissional aplicável.
