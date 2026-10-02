# Acesso por e-mail no OmniXML

O visitante informa um e-mail previamente liberado e valida um código de 6 dígitos enviado pela API HTTPS do Resend (padrão) ou por SMTP. O código dura 10 minutos, tem no máximo 5 tentativas e é consumido atomicamente ao validar. A sessão dura 8 horas e usa cookie Secure, HttpOnly e SameSite=Strict. O acesso não substitui o certificado A1 exigido pela SEFAZ.

## Configurar no Render → Environment

| Variável | Conteúdo |
| --- | --- |
| `OMNIXML_AUTH_SECRET` | Segredo aleatório de pelo menos 32 caracteres, mantido apenas no servidor. Gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"`. |
| `OMNIXML_ALLOWED_EMAILS` | E-mails autorizados, separados por vírgula. Ex.: `administrador@empresa.com,contador@empresa.com`. |
| `OMNIXML_EMAIL_PROVIDER` | `resend` (padrão e recomendado para Render gratuito) ou `smtp`. |
| `OMNIXML_RESEND_API_KEY` | Chave do Resend com permissão de envio; só no Render. |
| `OMNIXML_EMAIL_FROM` | Remetente autorizado/verificado. Ex.: `OmniXML <acesso@empresa.com>`. |
| `OMNIXML_SMTP_HOST` | Host do provedor de envio. |
| `OMNIXML_SMTP_PORT` | 587 com STARTTLS (padrão) ou 465 com TLS direto. |
| `OMNIXML_SMTP_USER` | Usuário SMTP do provedor. |
| `OMNIXML_SMTP_PASSWORD` | Credencial SMTP do provedor. |
| `OMNIXML_TRUST_PROXY` | `1` no Render, para reconhecer HTTPS do proxy. |
| `OMNIXML_AUTH_DB` | Opcional: caminho SQLite. Padrão `/tmp/omnixml-auth.sqlite3`. |

Nenhum segredo é incluído no GitHub. A funcionalidade só é ativada quando a configuração está completa. O token administrativo existente continua disponível em uma seção recolhida; mantenha `OMNIXML_SEFAZ_TOKEN` enquanto configura o e-mail.

Use um provedor com remetente verificado e SPF/DKIM configurados conforme suas instruções. O [Render gratuito bloqueia SMTP nas portas 25, 465 e 587](https://render.com/docs/free). O conector Resend já usa HTTPS, com TLS verificado e sem redirecionamento de credenciais. As variáveis SMTP só são necessárias quando o provedor selecionado é `smtp`. Não há envio automático durante testes: o transporte é simulado.

## Operação

- Remover um e-mail da lista revoga suas sessões no próximo acesso.
- Até 5 pedidos de código por e-mail/hora, intervalo mínimo de 60 segundos, 30 pedidos e 60 verificações por endereço de origem/hora. No Render, sem encaminhamento confiável de IP, o limite de origem é compartilhado conservadoramente.
- Códigos e identificadores de sessão são armazenados como HMAC; A1, senha do certificado e XMLs não entram no banco de autenticação.
- O SQLite funciona entre os workers de uma mesma instância. `/tmp` é efêmero: reinícios/deploys podem exigir novo login. Para várias instâncias, migrar o armazenamento para banco compartilhado antes de escalar.
- Falhas de entrega produzem um aviso fixo `omnixml_email_delivery_failed` no log, sem e-mail, código ou senha. A resposta pública é genérica para não revelar quais e-mails estão cadastrados.
- Para validar a implantação: liberar seu e-mail, pedir o código, conferir entrega/spam, entrar, consultar uma nota e sair; verificar também código inválido e código reutilizado.

## Ativação recomendada

1. Criar/usar uma conta no Resend e verificar o domínio remetente conforme [as instruções oficiais](https://resend.com/docs/dashboard/domains/introduction).
2. Criar uma chave de envio e configurar no Render: `OMNIXML_EMAIL_PROVIDER=resend`, `OMNIXML_RESEND_API_KEY`, `OMNIXML_EMAIL_FROM`, `OMNIXML_AUTH_SECRET`, `OMNIXML_ALLOWED_EMAILS` e `OMNIXML_TRUST_PROXY=1`.
3. Salvar/reimplantar e testar o código com o primeiro e-mail autorizado. Não colar a chave em chats ou no repositório.
