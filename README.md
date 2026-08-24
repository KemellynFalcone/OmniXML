# OmniXML — Validador Fiscal

Aplicação local em Flask para leitura e auditoria de documentos fiscais XML e cruzamentos com SPED.

## Estado atual

Esta versão inicia a refatoração do núcleo sem alterar o fluxo principal do dashboard. O foco desta etapa é tornar a leitura dos documentos previsível e segura antes da implementação de XSD e regras fiscais avançadas.

### Correções da Fase 1

- parsing XML independente de namespace;
- remoção do uso incorreto de `Element.find(...) or ...`;
- Entrada/Saída determinada pelo `tpNF` do XML, e não pelo nome da pasta;
- cancelamentos identificados pelo conteúdo do evento (`tpEvento=110111`);
- cancelamento só aplicado quando há confirmação SEFAZ compatível (`cStat` 135/155);
- identificação explícita de NF-e/NFC-e, CT-e, MDF-e e CF-e SAT;
- duplicidades por chave são registradas e não sobrescrevem silenciosamente o primeiro documento;
- valores monetários e quantitativos do parser usam `Decimal`;
- parser protegido com `defusedxml` no fluxo Flask;
- testes automatizados do parser e do fluxo principal;
- `build/`, `dist/`, XMLs, SPEDs e demais dados de clientes ignorados pelo Git.

## Instalação

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
pip install -r requirements-dev.txt
python app.py
```

## Testes

```bash
pytest -q
```

O GitHub Actions executa os testes automaticamente em pushes para `main`/`develop` e em pull requests para `main`.

## Dados fiscais e privacidade

Não faça commit de XMLs, arquivos SPED ou bases de clientes. O `.gitignore` já bloqueia as extensões mais comuns, mas revise sempre `git status` antes de publicar alterações.

## Próximas fases

1. validação XSD por documento e versão;
2. validação da chave de acesso e dígito verificador;
3. protocolo e situação documental SEFAZ;
4. reconciliação de totais da NF-e;
5. motor de regras fiscais contextual e versionado;
6. parsers SPED isolados e versionados;
7. assets do dashboard locais/offline.

## Cloudflare

Cloudflare não é necessário para o modelo atual, pois o OmniXML é um aplicativo desktop/local que usa Tkinter para seleção de arquivos e Flask apenas em `127.0.0.1`. Uma implantação em Cloudflare faria sentido depois de separar o motor fiscal da interface desktop e criar uma API/web app com upload seguro ou processamento em infraestrutura apropriada.
