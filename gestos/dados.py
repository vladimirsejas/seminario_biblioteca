"""
dados.py - os mesmos numeros do terminal, sem pandas e sem PySUS.

O terminal (src/epidemiology_service.py) nao baixa dados de verdade: ele SIMULA
os dados com o modulo random, a partir de uma "semente" fixa. Mesma semente =
mesmos sorteios = mesmos numeros. Aqui repetimos exatamente os mesmos sorteios,
na mesma ordem, e por isso o show mostra os mesmos valores que o terminal.
Sao numeros ilustrativos, nao dados oficiais.
"""

import random
from collections import Counter
from functools import lru_cache

# codigo: (nome, nome curto para os botoes, cor em BGR)
DOENCAS = {
    "DENG": ("Dengue", "Dengue", (70, 70, 255)),
    "CHIK": ("Chikungunya", "Chikung.", (40, 120, 235)),
    "ZIKA": ("Zika", "Zika", (0, 230, 255)),
    "TUBE": ("Tuberculose", "Tuberc.", (0, 160, 230)),
    "HANS": ("Hanseniase", "Hansen.", (60, 200, 255)),
    "LEPT": ("Leptospirose", "Leptosp.", (60, 210, 60)),
    "MENI": ("Meningite", "Meningite", (255, 60, 255)),
    "MALA": ("Malaria", "Malaria", (255, 255, 0)),
    "HEPA": ("Hepatites Virais", "Hepatites", (255, 140, 60)),
    "CHAG": ("Doenca de Chagas", "Chagas", (230, 110, 180)),
}

# A ordem precisa ser a mesma do terminal: o sorteio escolhe da lista nessa ordem
ESTADOS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapa",
    "AM": "Amazonas", "BA": "Bahia", "CE": "Ceara",
    "DF": "Distrito Federal", "ES": "Espirito Santo", "GO": "Goias",
    "MA": "Maranhao", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Para", "PB": "Paraiba",
    "PR": "Parana", "PE": "Pernambuco", "PI": "Piaui",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondonia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "Sao Paulo", "SE": "Sergipe", "TO": "Tocantins",
}

# Centro aproximado de cada estado (longitude, latitude), para desenhar o mapa
CENTRO_ESTADO = {
    "AC": (-70.5, -9.0), "AM": (-64.5, -4.0), "RR": (-61.3, 2.0), "AP": (-51.8, 1.4),
    "PA": (-52.5, -4.0), "TO": (-48.3, -10.2), "RO": (-62.8, -10.9), "MT": (-55.9, -12.9),
    "MA": (-45.3, -5.0), "PI": (-42.8, -7.4), "CE": (-39.6, -5.1), "RN": (-36.4, -5.6),
    "PB": (-36.2, -7.0), "PE": (-37.6, -8.4), "AL": (-36.3, -9.7), "SE": (-37.4, -10.8),
    "BA": (-41.7, -12.5), "GO": (-50.0, -16.2), "DF": (-47.6, -15.4), "MS": (-54.8, -20.5),
    "MG": (-44.6, -18.5), "ES": (-40.4, -19.6), "RJ": (-42.7, -22.3), "SP": (-48.6, -22.2),
    "PR": (-51.6, -24.6), "SC": (-50.5, -27.2), "RS": (-53.3, -29.7),
}

CID = {
    "A90": "Dengue", "A15": "Tuberculose", "B50": "Malaria", "J18": "Pneumonia",
    "I21": "Infarto", "G03": "Meningite", "K35": "Apendicite", "C34": "Cancer de pulmao",
    "N18": "Doenca renal", "E11": "Diabetes",
}


@lru_cache(maxsize=None)
def sinan(codigo, ano):
    """Notificacoes de uma doenca num ano (o mesmo sorteio de _simulate_sinan)."""
    rng = random.Random(codigo + str(ano))
    n = rng.randint(800, 5000)
    ufs = [rng.choice(list(ESTADOS)) for _ in range(n)]
    idades = [rng.randint(1, 90) for _ in range(n)]
    sexos = Counter(rng.choice(["M", "F", "I"]) for _ in range(n))
    return {
        "total": n,
        "por_uf": dict(Counter(ufs).most_common()),
        "idade_media": round(sum(idades) / n, 1),
        "mulheres": sexos["F"],
        "homens": sexos["M"],
    }


@lru_cache(maxsize=None)
def sih(uf, ano, mes):
    """Internacoes hospitalares de um estado num mes (o mesmo sorteio de _simulate_sih)."""
    rng = random.Random(uf + str(ano) + str(mes))
    n = rng.randint(200, 3000)
    cids = [rng.choice(["A90", "A15", "B50", "J18", "I21", "G03", "K35"]) for _ in range(n)]
    [rng.randint(0, 95) for _ in range(n)]                       # idade (sorteada, nao usada)
    sexos = Counter(rng.choice(["1", "3"]) for _ in range(n))
    valores = [round(rng.uniform(500, 25000), 2) for _ in range(n)]
    dias = [rng.randint(1, 30) for _ in range(n)]
    return {
        "total": n,
        "valor_total": round(sum(valores), 2),
        "valor_medio": round(sum(valores) / n, 2),
        "media_dias": round(sum(dias) / n, 1),
        "por_cid": dict(Counter(cids).most_common()),
        "mulheres": sexos["3"],
        "homens": sexos["1"],
    }


@lru_cache(maxsize=None)
def sim(uf, ano):
    """Obitos de um estado num ano (o mesmo sorteio de _simulate_sim)."""
    rng = random.Random(uf + "SIM" + str(ano))
    n = rng.randint(100, 2000)
    causas = [rng.choice(["A90", "A15", "C34", "I21", "J18", "N18", "E11"]) for _ in range(n)]
    [rng.randint(0, 100) for _ in range(n)]                      # idade (sorteada, nao usada)
    sexos = Counter(rng.choice(["1", "2"]) for _ in range(n))
    return {
        "total": n,
        "por_causa": dict(Counter(causas).most_common()),
        "mulheres": sexos["2"],
        "homens": sexos["1"],
    }
