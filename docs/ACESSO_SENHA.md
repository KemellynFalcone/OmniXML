# Acesso com e-mail e senha

O portal exige login individual em todas as páginas e APIs privadas. Não envia códigos, não usa OAuth do Gmail e não depende de entrega de e-mail. O painel ADM mantém a liberação dos clientes. Liberar um e-mail não cria automaticamente uma senha.

## Ativar no Render

Preserve as três variáveis `OMNIXML_D1_ACCOUNT_ID`, `OMNIXML_D1_DATABASE_ID`, `OMNIXML_D1_API_TOKEN` e o segredo `OMNIXML_AUTH_SECRET` (pelo menos 32 caracteres). A chave de API D1 é exclusivamente do servidor, não uma credencial de login do cliente.

1. Defina `OMNIXML_ADMIN_EMAILS=omnixml@gmail.com`.
2. Defina `OMNIXML_ADMIN_INITIAL_PASSWORD` com uma senha privada de 15 a 128 caracteres. Use uma frase longa e exclusiva. Não compartilhe em capturas ou mensagens.
3. Salve as variáveis, aguarde o deploy e entre com o e-mail ADM e essa senha.
4. Após o primeiro login, remova `OMNIXML_ADMIN_INITIAL_PASSWORD` do Render. O hash permanece no D1. Essa variável só cria uma credencial ausente, não altera uma senha existente.

O D1 cria automaticamente a tabela `credentials`, separada de `clients`. Só armazena hash scrypt, versão de revogação e hash/prazo do convite. Nunca armazena senha em texto nem XML/certificado. Faça backup do cadastro seguindo a política de retenção do responsável.

As antigas sessões por código deixam de valer após a atualização. Configure a senha inicial antes de liberar o novo deploy para evitar indisponibilidade do ADM. Se perder a senha de uma conta ADM, outro ADM pode gerar seu link. Sem outra conta ADM, é necessário recuperar a credencial com acesso ao banco: a variável inicial não substitui uma senha já salva.

As variáveis `OMNIXML_GMAIL_*`, `OMNIXML_EMAIL_PROVIDER`, `OMNIXML_RESEND_API_KEY` e `OMNIXML_SMTP_*` podem ser removidas. `OMNIXML_EMAIL_FROM` ainda é um fallback legado para identificar o ADM; configure `OMNIXML_ADMIN_EMAILS` explicitamente antes de removê-la. `OMNIXML_ALLOWED_EMAILS` continua representando contas fixas do servidor; as demais devem ser cadastradas pelo painel.

## Clientes e redefinição

No painel `/admin`, informe o e-mail e clique em **Liberar e criar link**. Copie o link e entregue somente ao titular por um canal confiável, após verificar sua identidade. O aplicativo não envia mensagens automaticamente. O cliente cria a própria senha e entra com e-mail e senha. O link tem uma hora de validade e uso único; gerar outro invalida o anterior.

**Criar / redefinir senha** também fica na linha de cada conta liberada, incluindo o ADM. Não mostre links em capturas públicas: quem possui o link pode definir a senha da conta. O segredo está no fragmento da URL e o JavaScript remove o fragmento do histórico antes de carregar o CAPTCHA. Não aparece na requisição HTTP da página nem no referrer.

A senha anterior continua funcionando até a redefinição ser concluída. Nesse momento todas as sessões antigas são revogadas pela versão no D1. Bloquear um cliente revoga sessões e convites imediatamente; liberar novamente não restaura sessões antigas. Excluir também remove a credencial.

## reCAPTCHA “Não sou um robô”

A integração usa o reCAPTCHA v2 checkbox real. Cadastre uma chave com o domínio `omnixml.onrender.com`, sem `https://` nem caminhos, no console oficial do Google/reCAPTCHA. Se usar outro domínio, inclua-o no cadastro.

Configure no Render:

- `OMNIXML_RECAPTCHA_SITE_KEY`: chave pública do site.
- `OMNIXML_RECAPTCHA_SECRET_KEY`: chave secreta, somente no servidor.

Sem as duas variáveis o login usa senha e limites de tentativa, sem CAPTCHA. Se somente uma estiver preenchida, a validação bloqueia o login: complete ou remova ambas. Quando habilitado, login e criação de senha exigem verificação HTTPS no servidor, resposta válida sem erros e hostname correspondente. Indisponibilidade, erro de quota, redirecionamento e hostname incorreto bloqueiam a operação. Não há checkbox simulando uma proteção.

O CAPTCHA possui políticas e limites próprios do Google; confira os termos e a quota apresentados para sua conta. A aplicação não habilita faturamento ou cobrança automaticamente. O login com senha funciona independentemente dessa integração opcional.

## Segurança e retenção

Senhas: scrypt, de 15 a 128 caracteres; espaços e Unicode permitidos. Não há regras artificiais de composição. HTTPS e mesma origem obrigatórios. Cookies Secure, HttpOnly e SameSite Strict; duração até 8 horas. Sessões e limites ficam no SQLite temporário compartilhado pelos workers do mesmo servidor; reiniciar pode exigir novo login. Não é suporte a múltiplas instâncias com sessão distribuída.

Limite: 60 tentativas por hora por endereço observado pelo aplicativo e 10 por conta ou convite. Identificadores dos limites são HMAC; não entram no monitor. Atrás de proxies sem IP individual validado, o limite por endereço pode ser compartilhado. Não aceite X-Forwarded-For livremente para contornar esse controle. Erros de login não informam se a conta existe. O monitor continua agregado e temporário, sem histórico individual.

Referências técnicas: [Werkzeug](https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.security.generate_password_hash), [verificação reCAPTCHA](https://developers.google.com/recaptcha/docs/verify), [widget v2](https://developers.google.com/recaptcha/docs/display).
