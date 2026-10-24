
"""Atualização gratuita do Ciência em Movimento: até 36 notícias PT e 9 EN."""

import calendar
import html
import json
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urlencode
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup


def google_noticias(termos, idioma='pt'):
    if idioma == 'pt':
        parametros = {
            'q': termos,
            'hl': 'pt-BR',
            'gl': 'BR',
            'ceid': 'BR:pt-419'
        }
    else:
        parametros = {
            'q': termos,
            'hl': 'en-US',
            'gl': 'US',
            'ceid': 'US:en'
        }

    return 'https://news.google.com/rss/search?' + urlencode(parametros)


# Nome, endereço, categoria e idioma.
FONTES = [
    (
        'Universidade de Brasília — UnB',
        'https://noticias.unb.br/publicacoes',
        'Ciência e Pesquisa',
        'pt'
    ),
    (
        'Agência FAPESP',
        'https://agencia.fapesp.br/rss/',
        'Ciência e Pesquisa',
        'pt'
    ),
    (
        'Ciência e Pesquisa — Brasil',
        google_noticias('pesquisa científica universidade when:7d'),
        'Ciência e Pesquisa',
        'pt'
    ),
    (
        'Inteligência Artificial — Brasil',
        google_noticias('inteligência artificial pesquisa when:7d'),
        'Inteligência Artificial',
        'pt'
    ),
    (
        'Tecnologia e Inovação — Brasil',
        google_noticias('tecnologia inovação científica when:7d'),
        'Tecnologia e Inovação',
        'pt'
    ),
    (
        'Educação e Ciência — Brasil',
        google_noticias('educação ciência universidade pesquisa when:7d'),
        'Educação',
        'pt'
    ),
    (
        'Ambiente e Clima — Brasil',
        google_noticias('pesquisa mudanças climáticas meio ambiente when:7d'),
        'Meio Ambiente',
        'pt'
    ),
    (
        'Saúde e Pesquisa — Brasil',
        google_noticias('pesquisa saúde Fiocruz universidade when:7d'),
        'Saúde',
        'pt'
    ),
    (
        'ScienceDaily — Tecnologia',
        'https://www.sciencedaily.com/rss/top/technology.xml',
        'Tecnologia e Inovação',
        'en'
    ),
    (
        'ScienceDaily — Ciência',
        'https://www.sciencedaily.com/rss/top/science.xml',
        'Ciência e Pesquisa',
        'en'
    ),
    (
        'NASA — Notícias',
        'https://www.nasa.gov/news-release/feed/',
        'Ciência e Pesquisa',
        'en'
    ),
]


def limpar(valor):
    return html.unescape(
        re.sub(r'<[^>]+>', '', valor or '')
    ).strip()


def coletar_unb(url):
    """Coleta notícias diretamente do HTML público da UnB."""

    resposta = requests.get(
        url,
        timeout=25,
        headers={
            'User-Agent': 'Mozilla/5.0 (compatible; CienciaEmMovimento/1.2)'
        }
    )

    resposta.raise_for_status()

    sopa = BeautifulSoup(resposta.text, 'html.parser')

    resultados = []
    vistos = set()

    padrao_data = re.compile(
        r'\b(\d{1,2})/(\d{1,2})/(20\d{2})\b'
    )

    for titulo_tag in sopa.select('h2'):

        ancora = titulo_tag.find('a', href=True)

        if not ancora:
            continue

        link = urljoin(
            url,
            ancora['href']
        ).split('#', 1)[0]

        caminho = urlparse(link)

        if caminho.hostname not in (
            'noticias.unb.br',
            'www.noticias.unb.br'
        ):
            continue

        if not re.search(r'/\d{3,}-', caminho.path):
            continue

        titulo = limpar(
            ancora.get_text(' ', strip=True)
        )

        if not titulo or link in vistos:
            continue

        vistos.add(link)

        contexto = titulo_tag
        data_encontrada = None

        for _ in range(7):

            contexto = contexto.parent

            if contexto is None:
                break

            texto = contexto.get_text(' ', strip=True)

            datas = list(
                padrao_data.finditer(texto)
            )

            if datas and len(texto) < 4500:
                data_encontrada = datas[0]
                break

        timestamp = 0
        resumo = ''

        if data_encontrada:

            try:
                dia, mes, ano = map(
                    int,
                    data_encontrada.groups()
                )

                timestamp = int(
                    datetime(
                        ano, mes, dia,
                        tzinfo=timezone.utc
                    ).timestamp()
                )

            except ValueError:
                pass

            for elemento in contexto.find_all(
                ['p', 'div'],
                recursive=True
            ):

                texto = limpar(
                    elemento.get_text(' ', strip=True)
                )

                if (
                    55 <= len(texto) <= 500
                    and titulo not in texto
                    and not padrao_data.search(texto)
                    and not texto.lower().startswith(
                        ('palavras-chave', 'da secretaria')
                    )
                ):
                    resumo = texto[:240]
                    break

        resultados.append({
            'titulo': titulo,
            'resumo': resumo,
            'link': link,
            'fonte': 'Universidade de Brasília — UnB',
            'categoria': 'Ciência e Pesquisa',
            'idioma': 'pt',
            'timestamp': timestamp
        })

        if len(resultados) >= 25:
            break

    print(
        f'Universidade de Brasília — UnB: '
        f'{len(resultados)} matérias extraídas do HTML'
    )

    return resultados


def coletar():

    resultados = []

    for nome, url, categoria, idioma in FONTES:

        try:

            if nome == 'Universidade de Brasília — UnB':
                resultados.extend(
                    coletar_unb(url)
                )
                continue

            resposta = requests.get(
                url,
                timeout=25,
                headers={
                    'User-Agent': (
                        'Mozilla/5.0 '
                        '(compatible; CienciaEmMovimento/1.1)'
                    )
                }
            )

            resposta.raise_for_status()

            itens = feedparser.parse(
                resposta.content
            ).entries

            print(
                f'{nome}: {len(itens)} entradas'
            )

            for item in itens[:25]:

                link = item.get('link', '')

                titulo = limpar(
                    item.get('title', '')
                )

                if not link.startswith(
                    ('https://', 'http://')
                ) or not titulo:
                    continue

                data = (
                    item.get('published_parsed')
                    or item.get('updated_parsed')
                )

                timestamp = (
                    calendar.timegm(data)
                    if data else 0
                )

                resultados.append({
                    'titulo': titulo,
                    'resumo': limpar(
                        item.get('summary', '')
                    )[:240],
                    'link': link,
                    'fonte': nome,
                    'categoria': categoria,
                    'idioma': idioma,
                    'timestamp': timestamp
                })

        except Exception as erro:

            print(
                f'{nome}: erro ao coletar: {erro}'
            )

    return resultados


def publicar():

    destino = Path(__file__).with_name(
        'noticias.json'
    )

    atuais = coletar()

    nomes_validos = {
        fonte[0] for fonte in FONTES
    }

    idiomas_por_fonte = {
        fonte[0]: fonte[3]
        for fonte in FONTES
    }

    if destino.exists():

        try:

            antigos = json.loads(
                destino.read_text(
                    encoding='utf-8'
                )
            ).get('noticias', [])

            for item in antigos:

                fonte = item.get('fonte')

                if fonte in nomes_validos:

                    item['idioma'] = (
                        idiomas_por_fonte[fonte]
                    )

                    atuais.append(item)

        except (ValueError, OSError) as erro:

            print(
                'Não foi possível reaproveitar '
                'notícias anteriores:',
                erro
            )

    unicos = {}

    for item in atuais:

        if (
            item.get('link')
            and item.get('titulo')
        ):
            unicos[item['link']] = item

    ordenados = sorted(
        unicos.values(),
        key=lambda n: n.get('timestamp', 0),
        reverse=True
    )

    portugues = [
        noticia for noticia in ordenados
        if noticia.get('idioma') == 'pt'
    ][:36]

    ingles = [
        noticia for noticia in ordenados
        if noticia.get('idioma') == 'en'
    ][:9]

    noticias = sorted(
        portugues + ingles,
        key=lambda n: n.get('timestamp', 0),
        reverse=True
    )

    destino.write_text(
        json.dumps(
            {
                'atualizado_em': datetime.now(
                    timezone.utc
                ).isoformat(),
                'noticias': noticias
            },
            ensure_ascii=False,
            indent=2
        ),
        encoding='utf-8'
    )

    print(
        f'Publicadas {len(portugues)} notícias '
        f'em português e {len(ingles)} em inglês.'
    )


if __name__ == '__main__':
    publicar()
