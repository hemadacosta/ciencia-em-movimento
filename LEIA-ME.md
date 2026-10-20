# Ciência em Movimento — painel gratuito para Moodle

## Publicar sem pagar
1. Crie conta gratuita no GitHub, se necessário.
2. Crie repositório **público** chamado `ciencia-em-movimento`.
3. Envie TODOS os arquivos e mantenha a pasta oculta `.github/workflows/publicar.yml` com sua estrutura. Pode usar `Add file > Upload files` (atenção ao diretório `.github`).
4. Em `Settings > Pages > Build and deployment > Source`, selecione `GitHub Actions`.
5. Em `Actions`, execute `Atualizar notícias e publicar painel` com `Run workflow` (ou faça um novo commit).
6. Depois do primeiro deploy bem-sucedido, acesse `https://SEU-USUARIO.github.io/ciencia-em-movimento/`.
7. Na edição HTML do recurso `Texto e mídia` do Moodle, insira:

```html
<iframe src="https://SEU-USUARIO.github.io/ciencia-em-movimento/" width="100%" height="750" style="border:0" title="Ciência em Movimento - notícias de Ciência e Tecnologia" loading="lazy"></iframe>
```

## Como funciona
GitHub Actions consulta periodicamente RSS públicos de Agência FAPESP, ScienceDaily e NASA, gera `noticias.json` e publica uma página estática. Configuração programada para aproximadamente uma vez por dia, sujeita à execução do GitHub. Se um feed falhar, outros continuam; links antigos podem ser preservados. Os feeds e a imagem do painel devem ser revisados periodicamente. O painel exibe títulos e trechos, remetendo à fonte original. Alguns textos estarão em inglês.

## Alterar fontes
Edite a lista `FONTES` no começo de `atualizar.py`. Confirme que cada URL é um RSS ativo e que seu uso respeita as condições do site.

## Limitações
A URL só existirá após a publicação no seu GitHub. Os dados de exemplo estão vazios de propósito: o painel não fabrica notícias. O GitHub pode atrasar ou suspender workflows agendados por inatividade. Os feeds podem alterar URLs ou impedir coleta. O Moodle deve permitir iframe para domínios externos.
