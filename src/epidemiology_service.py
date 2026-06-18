
"""
epidemiology_service.py

O coração do projeto. Toda e qualquer interação com a biblioteca
PySUS acontece APENAS aqui. Nenhum outro módulo importa pysus diretamente.

Biblioteca: PySUS — https://github.com/AlertaDengue/PySUS
Documentação: https://pysus.readthedocs.io/
"""

import inspect
import random
from typing import get_args

import pandas as pd
import pysus


DOENCAS = {
    "DENG": {"nome": "Dengue",              "cor": "bright_red"},
    "CHIK": {"nome": "Chikungunya",         "cor": "red"},
    "ZIKA": {"nome": "Zika",                "cor": "yellow"},
    "TUBE": {"nome": "Tuberculose",         "cor": "orange3"},
    "HANS": {"nome": "Hanseniase",          "cor": "dark_orange"},
    "LEPT": {"nome": "Leptospirose",        "cor": "green"},
    "MENI": {"nome": "Meningite",           "cor": "magenta"},
    "MALA": {"nome": "Malaria",             "cor": "cyan"},
    "HEPA": {"nome": "Hepatites Virais",    "cor": "blue"},
    "CHAG": {"nome": "Doenca de Chagas",    "cor": "purple4"},
}

ESTADOS = {
    "AC": "Acre",           "AL": "Alagoas",        "AP": "Amapa",
    "AM": "Amazonas",       "BA": "Bahia",          "CE": "Ceara",
    "DF": "Distrito Federal","ES": "Espirito Santo", "GO": "Goias",
    "MA": "Maranhao",       "MT": "Mato Grosso",    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",   "PA": "Para",           "PB": "Paraiba",
    "PR": "Parana",         "PE": "Pernambuco",     "PI": "Piaui",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondonia",       "RR": "Roraima",        "SC": "Santa Catarina",
    "SP": "Sao Paulo",      "SE": "Sergipe",        "TO": "Tocantins",
}


class EpidemiologyService:

    def get_disease_data(self, disease_code, year):
        # return pysus.sinan(disease_code, year)
        return self._simulate_sinan(disease_code, year)

    def get_hospitalizations(self, state, year, month):
        # return pysus.sih(state, year, month)
        return self._simulate_sih(state, year, month)

    def get_mortality(self, state, year):
        # return pysus.sim(state, year)
        return self._simulate_sim(state, year)

    def list_available_diseases(self):
        annotation = inspect.signature(pysus.sinan).parameters["disease"].annotation
        return list(get_args(annotation))

    def _simulate_sinan(self, disease_code, year):
        random.seed(disease_code + str(year))
        n = random.randint(800, 5000)
        states = list(ESTADOS.keys())
        return pd.DataFrame({
            "SG_UF_NOT":  [random.choice(states) for _ in range(n)],
            "NU_ANO":     [year] * n,
            "ID_AGRAVO":  [disease_code] * n,
            "NU_IDADE_N": [random.randint(1, 90) for _ in range(n)],
            "CS_SEXO":    [random.choice(["M", "F", "I"]) for _ in range(n)],
            "EVOLUCAO":   [random.choice([1, 2, 9]) for _ in range(n)],
        })

    def _simulate_sih(self, state, year, month):
        random.seed(state + str(year) + str(month))
        n = random.randint(200, 3000)
        cids = ["A90", "A15", "B50", "J18", "I21", "G03", "K35"]
        return pd.DataFrame({
            "UF_ZI":      [state] * n,
            "ANO_CMPT":   [year] * n,
            "MES_CMPT":   [month] * n,
            "DIAG_PRINC": [random.choice(cids) for _ in range(n)],
            "IDADE":      [random.randint(0, 95) for _ in range(n)],
            "SEXO":       [random.choice(["1", "3"]) for _ in range(n)],
            "VAL_TOT":    [round(random.uniform(500, 25000), 2) for _ in range(n)],
            "DIAS_PERM":  [random.randint(1, 30) for _ in range(n)],
        })

    def _simulate_sim(self, state, year):
        random.seed(state + "SIM" + str(year))
        n = random.randint(100, 2000)
        causas = ["A90", "A15", "C34", "I21", "J18", "N18", "E11"]
        return pd.DataFrame({
            "CODMUNRES": [state] * n,
            "CAUSABAS":  [random.choice(causas) for _ in range(n)],
            "IDADE":     [random.randint(0, 100) for _ in range(n)],
            "SEXO":      [random.choice(["1", "2"]) for _ in range(n)],
            "DTOBITO":   [
                f"{year}{random.randint(1, 12):02d}{random.randint(1, 28):02d}"
                for _ in range(n)
            ],
        })