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


# ---------------------------------------------------------------------------
# Catálogo de doenças — metadados das principais notificações do SINAN
# ---------------------------------------------------------------------------

DOENCAS = {
    "DENG": {"nome": "Dengue",              "emoji": "🦟", "cor": "bright_red"},
    "CHIK": {"nome": "Chikungunya",         "emoji": "🦟", "cor": "red"},
    "ZIKA": {"nome": "Zika",                "emoji": "🦟", "cor": "yellow"},
    "TUBE": {"nome": "Tuberculose",         "emoji": "🫁", "cor": "orange3"},
    "HANS": {"nome": "Hanseníase",          "emoji": "🔬", "cor": "dark_orange"},
    "LEPT": {"nome": "Leptospirose",        "emoji": "🐀", "cor": "green"},
    "MENI": {"nome": "Meningite",           "emoji": "🧠", "cor": "magenta"},
    "MALA": {"nome": "Malária",             "emoji": "🌿", "cor": "cyan"},
    "HEPA": {"nome": "Hepatites Virais",    "emoji": "🫀", "cor": "blue"},
    "CHAG": {"nome": "Doença de Chagas",    "emoji": "🪲", "cor": "purple4"},
}

ESTADOS = {
    "AC": "Acre",           "AL": "Alagoas",        "AP": "Amapá",
    "AM": "Amazonas",       "BA": "Bahia",          "CE": "Ceará",
    "DF": "Distrito Federal","ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão",       "MT": "Mato Grosso",    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",   "PA": "Pará",           "PB": "Paraíba",
    "PR": "Paraná",         "PE": "Pernambuco",     "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia",       "RR": "Roraima",        "SC": "Santa Catarina",
    "SP": "São Paulo",      "SE": "Sergipe",        "TO": "Tocantins",
}


class EpidemiologyService:
    """
    Serviço de acesso aos dados públicos de saúde via PySUS.

    Encapsula as três bases principais:
      - SINAN: agravos e doenças de notificação compulsória
      - SIH:   internações hospitalares
      - SIM:   mortalidade
    """

    def get_disease_data(self, disease_code: str, year: int) -> pd.DataFrame:
        """
        Busca registros do SINAN para uma doença e ano via PySUS.

        Chamada real (requer conexão com o servidor PySUS):
            return pysus.sinan(disease_code, year)

        Retorna DataFrame com colunas reais do SINAN:
            SG_UF_NOT, NU_ANO, ID_AGRAVO, NU_IDADE_N, CS_SEXO, EVOLUCAO
        """
        # return pysus.sinan(disease_code, year)   # ← linha real de produção
        return self._simulate_sinan(disease_code, year)

    def get_hospitalizations(self, state: str, year: int, month: int) -> pd.DataFrame:
        """
        Busca dados de internações hospitalares via PySUS (SIH).

        Chamada real:
            return pysus.sih(state, year, month)

        Retorna DataFrame com colunas reais do SIH:
            UF_ZI, ANO_CMPT, MES_CMPT, DIAG_PRINC, IDADE, SEXO, VAL_TOT, DIAS_PERM
        """
        # return pysus.sih(state, year, month)   # ← linha real de produção
        return self._simulate_sih(state, year, month)

    def get_mortality(self, state: str, year: int) -> pd.DataFrame:
        """
        Busca dados de mortalidade via PySUS (SIM).

        Chamada real:
            return pysus.sim(state, year)

        Retorna DataFrame com colunas reais do SIM:
            CODMUNRES, CAUSABAS, IDADE, SEXO, DTOBITO
        """
        # return pysus.sim(state, year)   # ← linha real de produção
        return self._simulate_sim(state, year)

    def list_available_diseases(self) -> list[str]:
        """
        Retorna todos os códigos de doença disponíveis no SINAN via PySUS.

        Os códigos são extraídos diretamente da assinatura tipada de
        pysus.sinan(), garantindo sincronia com a biblioteca instalada.
        """
        annotation = inspect.signature(pysus.sinan).parameters["disease"].annotation
        return list(get_args(annotation))

    # -----------------------------------------------------------------------
    # Simuladores — mesma estrutura de colunas do dado real
    # -----------------------------------------------------------------------

    def _simulate_sinan(self, disease_code: str, year: int) -> pd.DataFrame:
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

    def _simulate_sih(self, state: str, year: int, month: int) -> pd.DataFrame:
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

    def _simulate_sim(self, state: str, year: int) -> pd.DataFrame:
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
