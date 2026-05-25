"""
disease_analyzer.py

Análise de DataFrames vindos do PySUS.
Este módulo não sabe nada sobre terminal, Rich ou menus.
Recebe DataFrames, devolve resultados. Só isso.
"""

import pandas as pd


class DiseaseAnalyzer:
    """Analisa dados epidemiológicos de um DataFrame do SINAN."""

    def count_by_sex(self, df: pd.DataFrame) -> dict[str, int]:
        """Conta notificações por sexo (M / F / I)."""
        mapa = {"M": "Masculino", "F": "Feminino", "I": "Ignorado"}
        contagem = df["CS_SEXO"].value_counts()
        return {mapa.get(k, k): int(v) for k, v in contagem.items()}

    def count_by_state(self, df: pd.DataFrame) -> dict[str, int]:
        """Conta notificações por estado (UF)."""
        contagem = df["SG_UF_NOT"].value_counts()
        return {str(k): int(v) for k, v in contagem.items()}

    def top_states(self, df: pd.DataFrame, n: int = 5) -> dict[str, int]:
        """Retorna os N estados com mais notificações."""
        return dict(list(self.count_by_state(df).items())[:n])

    def count_by_age_group(self, df: pd.DataFrame) -> dict[str, int]:
        """Agrupa notificações por faixa etária."""
        bins   = [0, 5, 12, 18, 30, 45, 60, 101]
        labels = ["0–4", "5–12", "13–18", "19–30", "31–45", "46–60", "60+"]
        faixas = pd.cut(df["NU_IDADE_N"], bins=bins, labels=labels, right=False)
        return {str(k): int(v) for k, v in faixas.value_counts().sort_index().items()}

    def summary(self, df: pd.DataFrame) -> dict:
        """Retorna um resumo geral do DataFrame."""
        return {
            "total": len(df),
            "ano":   int(df["NU_ANO"].iloc[0]),
            "doenca": str(df["ID_AGRAVO"].iloc[0]),
            "estados_afetados": df["SG_UF_NOT"].nunique(),
            "idade_media": round(float(df["NU_IDADE_N"].mean()), 1),
        }


class HospitalizationAnalyzer:
    """Analisa dados de internações hospitalares do SIH."""

    def summary(self, df: pd.DataFrame) -> dict:
        return {
            "total":       len(df),
            "valor_total": round(float(df["VAL_TOT"].sum()), 2),
            "media_dias":  round(float(df["DIAS_PERM"].mean()), 1),
            "valor_medio": round(float(df["VAL_TOT"].mean()), 2),
        }

    def top_diagnoses(self, df: pd.DataFrame, n: int = 6) -> dict[str, int]:
        """Retorna os N diagnósticos principais mais frequentes (CID-10)."""
        contagem = df["DIAG_PRINC"].value_counts().head(n)
        return {str(k): int(v) for k, v in contagem.items()}

    def count_by_sex(self, df: pd.DataFrame) -> dict[str, int]:
        mapa = {"1": "Masculino", "3": "Feminino"}
        contagem = df["SEXO"].value_counts()
        return {mapa.get(k, k): int(v) for k, v in contagem.items()}


class MortalityAnalyzer:
    """Analisa dados de mortalidade do SIM."""

    def summary(self, df: pd.DataFrame) -> dict:
        return {"total": len(df)}

    def top_causes(self, df: pd.DataFrame, n: int = 6) -> dict[str, int]:
        """Retorna as N principais causas de óbito (CID-10)."""
        contagem = df["CAUSABAS"].value_counts().head(n)
        return {str(k): int(v) for k, v in contagem.items()}

    def count_by_sex(self, df: pd.DataFrame) -> dict[str, int]:
        mapa = {"1": "Masculino", "2": "Feminino"}
        contagem = df["SEXO"].value_counts()
        return {mapa.get(k, k): int(v) for k, v in contagem.items()}

