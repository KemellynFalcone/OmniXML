# Enviar códigos com omnixml@gmail.com

O OmniXML já suporta `OMNIXML_EMAIL_PROVIDER=gmail`. O envio usa a API HTTPS do Gmail, com autorização OAuth da conta remetente. Não usa senha do Gmail, SMTP, nem acesso de leitura à caixa de entrada. Os visitantes continuam recebendo códigos por e-mail; só o administrador autoriza a conta remetente no Google.

## 1. Criar o projeto e habilitar Gmail API

Abra [Google Cloud Console](https://console.cloud.google.com/) na conta `omnixml@gmail.com`, crie um projeto chamado **OmniXML** e habilite **Gmail API** em **APIs e serviços → Biblioteca**.

## 2. Configurar Google Auth Platform

Na Google Auth Platform (ou tela de consentimento OAuth):

- Nome do app: **OmniXML**; suporte e contato: `omnixml@gmail.com`.
- Público externo; durante a configuração use modo de teste e inclua `omnixml@gmail.com` como usuário de teste.
- Em acesso a dados, solicite apenas `https://www.googleapis.com/auth/gmail.send`. Essa permissão permite enviar; não solicite `mail.google.com`, leitura ou exclusão.
- Em **Clientes**, crie um cliente OAuth de tipo **Aplicativo da Web**.
- URI de redirecionamento autorizada: `https://developers.google.com/oauthplayground` (exatamente assim).
- Guarde o **Client ID** e **Client secret** diretamente nas variáveis do Render indicadas abaixo. Não os envie em prints, chat ou commits.

## 3. Autorizar uma vez a conta remetente

Abra o [OAuth Playground oficial do Google](https://developers.google.com/oauthplayground/).

1. Na engrenagem, mantenha endpoints **Google**, fluxo **Server-side**, acesso **Offline** e prompt **Consent Screen**.
2. Marque **Use your own OAuth credentials** e informe o Client ID e Client secret do seu projeto. Isso é necessário para o token pertencer ao seu aplicativo.
3. No campo de escopo, informe `https://www.googleapis.com/auth/gmail.send` e clique **Authorize APIs**.
4. Escolha a conta **omnixml@gmail.com** e confira o aplicativo e a permissão de envio antes de autorizar.
5. No passo 2, clique **Exchange authorization code for tokens**.
6. Copie o **Refresh token** diretamente para `OMNIXML_GMAIL_REFRESH_TOKEN` no Render. Não use o Access token: ele tem duração curta.

Não compartilhe links do Playground com a opção de incluir credenciais/tokens ativada.

## 4. Render → Environment

| Variável | Valor |
| --- | --- |
| `OMNIXML_EMAIL_PROVIDER` | `gmail` |
| `OMNIXML_EMAIL_FROM` | `OmniXML <omnixml@gmail.com>` |
| `OMNIXML_GMAIL_CLIENT_ID` | Client ID do seu projeto Google |
| `OMNIXML_GMAIL_CLIENT_SECRET` | Client secret do mesmo cliente |
| `OMNIXML_GMAIL_REFRESH_TOKEN` | Refresh token autorizado pela conta omnixml@gmail.com |
| `OMNIXML_AUTH_SECRET` | Segredo aleatório com pelo menos 32 caracteres; mantenha o já configurado, se houver. |
| `OMNIXML_ALLOWED_EMAILS` | E-mails liberados, separados por vírgula. Para começar: `omnixml@gmail.com`. |
| `OMNIXML_TRUST_PROXY` | `1` no Render |

Para gerar um segredo novo, execute em ambiente privado `python -c "import secrets; print(secrets.token_urlsafe(48))"` e cole apenas no Render. Mantenha o token administrativo como alternativa durante a ativação. Resend e SMTP não são usados quando o provedor é Gmail.

Salve/reimplante e, em `/downloads`, peça um código para o primeiro e-mail liberado. Confira a caixa de entrada e spam, valide o código e teste sair. A autorização do Google não foi executada pelos testes do projeto; o envio real precisa ser conferido após configurar as credenciais.

## Continuidade

O Google limita a validade do refresh token de apps externos em modo **Testing** a 7 dias quando solicitam acesso como `gmail.send`. Esse modo serve para validar a configuração. Antes de usar continuamente, configure o status de publicação apropriado na Google Auth Platform; siga os requisitos de verificação que o Google apresentar. Publicar o app não significa que o Google já o verificou, nem que tokens são eternos. Reautorize após mudanças de status, revogação ou expiração.

O Gmail possui limites de envio e pode recusar mensagens. O código não tenta reenviar automaticamente uma mensagem com resultado incerto. Credenciais inválidas ou envio recusado retornam uma mensagem pública genérica e um aviso fixo no log, sem tokens ou senha. As credenciais OAuth ficam nas variáveis do servidor, fora do SQLite de login.

## Referências oficiais

- [Envio pela API Gmail](https://developers.google.com/workspace/gmail/api/guides/sending)
- [Escopos Gmail](https://developers.google.com/workspace/gmail/api/auth/scopes)
- [OAuth Playground](https://developers.google.com/oauthplayground/)
- [Expiração de tokens OAuth](https://developers.google.com/identity/protocols/oauth2#expiration)
