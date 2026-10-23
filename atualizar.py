"""Atualização gratuita do Ciência em Movimento: até 36 notícias PT e 9 EN."""
import calendar
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import feedparser
import requests


def google_noticias(termos, idioma='pt'):
    if idioma == 'pt':
        parametros = {'q': termos, 'hl': 'pt-BR', 'gl': 'BR', 'ceid': 'BR:pt-419'}
    else:
        parametros = {'q': termos, 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'}
    return 'https://news.google.com/rss/search?' + urlencode(parametros)


# Nome, endereço RSS, categoria, idioma.
FONTES = [
    ('Agência FAPESP', 'https://agencia.fapesp.br/rss/', 'Ciência e Pesquisa', 'pt'),
    ('Ciência e Pesquisa — Brasil', google_noticias('pesquisa científica universidade when:7d'), 'Ciência e Pesquisa', 'pt'),
    ('Inteligência Artificial — Brasil', google_noticias('inteligência artificial pesquisa when:7d'), 'Inteligência Artificial', 'pt'),
    ('Tecnologia e Inovação — Brasil', google_noticias('tecnologia inovação científica when:7d'), 'Tecnologia e Inovação', 'pt'),
    ('Educação e Ciência — Brasil', google_noticias('educação ciência universidade pesquisa when:7d'), 'Educação', 'pt'),
    ('Ambiente e Clima — Brasil', google_noticias('pesquisa mudanças climáticas meio ambiente when:7d'), 'Meio Ambiente', 'pt'),
    ('Saúde e Pesquisa — Brasil', google_noticias('pesquisa saúde Fiocruz universidade when:7d'), 'Saúde', 'pt'),
    ('ScienceDaily — Tecnologia', 'https://www.sciencedaily.com/rss/top/technology.xml', 'Tecnologia e Inovação', 'en'),
    ('ScienceDaily — Ciência', 'https://www.sciencedaily.com/rss/top/science.xml', 'Ciência e Pesquisa', 'en'),
    ('NASA — Notícias', 'https://www.nasa.gov/news-release/feed/', 'Ciência e Pesquisa', 'en'),
    ('UnB - Notícias', 'https://noticias.unb.br/publicacoes', 'Educação'),
]


def limpar(valor):
    return html.unescape(re.sub(r'<[^>]+>', '', valor or '')).strip()


def coletar():
    resultados = []
    for nome, url, categoria, idioma in FONTES:
        try:
            resposta = requests.get(url, timeout=25, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; CienciaEmMovimento/1.1)'})
            resposta.raise_for_status()
            itens = feedparser.parse(resposta.content).entries
            print(f'{nome}: {len(itens)} entradas')
            for item in itens[:25]:
                link = item.get('link', '')
                titulo = limpar(item.get('title', ''))
                if not link.startswith(('https://', 'http://')) or not titulo:
                    continue
                data = item.get('published_parsed') or item.get('updated_parsed')
                timestamp = calendar.timegm(data) if data else 0
                resultados.append({
                    'titulo': titulo, 'resumo': limpar(item.get('summary', ''))[:240],
                    'link': link, 'fonte': nome, 'categoria': categoria,
                    'idioma': idioma, 'timestamp': timestamp,
                })
        except Exception as erro:
            print(f'{nome}: erro ao coletar: {erro}')
    return resultados


def publicar():
    destino = Path(__file__).with_name('noticias.json')
    atuais = coletar()
    # Se uma fonte falhar, mantém notícias anteriores APENAS das fontes vigentes.
    nomes_validos = {f[0] for f in FONTES}
    idiomas_por_fonte = {f[0]: f[3] for f in FONTES}
    if destino.exists():
        try:
            antigos = json.loads(destino.read_text(encoding='utf-8')).get('noticias', [])
            for item in antigos:
                fonte = item.get('fonte')
                if fonte in nomes_validos:
                    item['idioma'] = idiomas_por_fonte[fonte]
                    atuais.append(item)
        except (ValueError, OSError) as erro:
            print('Não foi possível reaproveitar notícias anteriores:', erro)

    unicos = {}
    for item in atuais:
        if item.get('link') and item.get('titulo'):
            unicos[item['link']] = item
    ordenados = sorted(unicos.values(), key=lambda n: n.get('timestamp', 0), reverse=True)
    portugues = [n for n in ordenados if n.get('idioma') == 'pt'][:36]
    ingles = [n for n in ordenados if n.get('idioma') == 'en'][:9]
    noticias = sorted(portugues + ingles, key=lambda n: n.get('timestamp', 0), reverse=True)

    destino.write_text(json.dumps({
        'atualizado_em': datetime.now(timezone.utc).isoformat(),
        'noticias': noticias,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Publicadas {len(portugues)} notícias em português e {len(ingles)} em inglês.')


if __name__ == '__main__':
    publicar()
