# Autoridades públicas de confiança da SEFAZ/SP

`sefaz-sp-ca.pem` contém **somente certificados públicos de CA**. Não contém certificado A1 de usuário nem chave privada.

Fonte obtida por HTTPS em 01/10/2026:
https://portal.fazenda.sp.gov.br/servicos/nfe/Documents/Cadeia.zip

O portal oficial também divulga esse pacote na seção "Cadeia de certificados":
https://portal.fazenda.sp.gov.br/servicos/cte

A raiz v10 destinada a SSL consta no repositório oficial ITI:
https://www.gov.br/iti/pt-br/assuntos/repositorio/repositorio-ac-raiz

| Certificado no pacote | Validade até (UTC) | SHA-256 do certificado DER |
|---|---|---|
| Raiz v10.cer — Autoridade Certificadora Raiz Brasileira v10 | 01/07/2032 12:00:59 | `6e0bff069a26994c15de2c4888cc54af84882e5495b7fbf66be9ccffec7489f6` |
| Intermédiaria.cer — AC SOLUTI SSL EV | 01/07/2032 12:00:59 | `169cbf0547f3dfc4e63e4af9e0255a76037778ff5b8f4a536abdff3a91dfc3c5` |

As assinaturas da raiz e da intermediária foram verificadas, assim como BasicConstraints CA e validade. O código confere os fingerprints antes de carregar o PEM. A inclusão é limitada ao adapter de `https://nfce.fazenda.sp.gov.br/` no provedor NFC-e/SP; não altera a confiança TLS global nem a distribuição nacional de NF-e. As CAs enviadas no A1 não são fontes de confiança do servidor. Verificação da cadeia e do hostname permanecem obrigatórias.

Não há download automático de certificados durante consultas. Atualizações exigem obter o pacote em fonte oficial autenticada, conferir a cadeia e atualizar PEM, fingerprints e testes. Se a SEFAZ mudar de raiz ou omitir uma intermediária diferente, reavaliar a cadeia real antes de incluir outros certificados. A raiz v10 cobre somente cadeias emitidas sob essa raiz; não garante resolução de qualquer TLS 20.

## Intermediárias adicionais conferidas

Também foram incluídas as intermediárias públicas abaixo do repositório ITI. O download HTTP foi tratado como transporte não confiável: antes de incluir, verificou-se criptograficamente a assinatura diretamente sob a raiz v10 autenticada pelo pacote HTTPS da SEFAZ/SP, BasicConstraints CA e validade. Os fingerprints resultantes ficam fixados no código. Não são adicionadas raízes obtidas por HTTP.

- AC SOLUTI SSL EV G2: `http://acraiz.icpbrasil.gov.br/credenciadas/SOLUTI/v10/p/AC-SOLUTI-SSL-EV-G2.crt`; válida até 2032-07-01 12:00:25+00:00; SHA-256 DER `8606539037b8ff9d1eb2e8831312cbc667c824e9e5aa2dbb326172446f441e27`.
- AC SOLUTI SSL EV G4: `http://acraiz.icpbrasil.gov.br/credenciadas/SOLUTI/v10/p/AC-SOLUTI-SSL-EV-G4.crt`; válida até 2032-07-01 12:00:59+00:00; SHA-256 DER `8e30f7f0b678ca1440a94a5be416bed9ae5aff7f0f2e08d4bbe28af2c8eb8660`.
