import json, re, html
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import feedparser
import requests

FONTES = [
    ('Agência FAPESP', 'https://agencia.fapesp.br/rss/', 'Ciência'),
    ('ScienceDaily — Tecnologia', 'https://www.sciencedaily.com/rss/top/technology.xml', 'Tecnologia'),
    ('ScienceDaily — Ciência', 'https://www.sciencedaily.com/rss/top/science.xml', 'Ciência'),
    ('NASA — Notícias', 'https://www.nasa.gov/news-release/feed/', 'Espaço'),
]

def limpar(valor):
    return html.unescape(re.sub(r'<[^>]+>', '', valor or '')).strip()

noticias = []
for nome, url, categoria in FONTES:
    try:
        r = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0 (compatible; CienciaEmMovimento/1.0)'})
        r.raise_for_status()
        feed = feedparser.parse(r.content)
        if not feed.entries:
            print('Sem entradas:', nome)
        for item in feed.entries[:15]:
            link = item.get('link', '')
            if not link.startswith(('https://', 'http://')):
                continue
            stamp = item.get('published_parsed') or item.get('updated_parsed')
            timestamp = __import__('calendar').timegm(stamp) if stamp else 0
            noticias.append({'titulo': limpar(item.get('title')),
                             'resumo': limpar(item.get('summary', ''))[:240],
                             'link': link, 'fonte': nome, 'categoria': categoria,
                             'timestamp': timestamp})
        print(nome, 'OK')
    except Exception as err:
        print(nome, 'ERRO:', err)

# Preserve previously collected articles if sources are temporarily inaccessible.
destino = Path(__file__).with_name('noticias.json')
if destino.exists():
    try:
        anterior = json.loads(destino.read_text(encoding='utf-8')).get('noticias', [])
        noticias += anterior
    except Exception:
        pass
unicas = {n['link']: n for n in noticias if n.get('titulo') and n.get('link')}
ordenadas = sorted(unicas.values(), key=lambda n: n.get('timestamp', 0), reverse=True)[:60]
destino.write_text(json.dumps({'atualizado_em': datetime.now(timezone.utc).isoformat(),
                               'noticias': ordenadas}, ensure_ascii=False, indent=2), encoding='utf-8')
print('Notícias publicadas:', len(ordenadas))
