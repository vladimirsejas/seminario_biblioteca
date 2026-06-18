import pandas as pd


class DiseaseAnalyzer:

    def count_by_sex(self, df):
        mapa = {"M": "Masculino", "F": "Feminino", "I": "Ignorado"}
        contagem = df["CS_SEXO"].value_counts()
        return {mapa.get(k, k): int(v) for k, v in contagem.items()}

    def count_by_state(self, df):
        contagem = df["SG_UF_NOT"].value_counts()
        return {str(k): int(v) for k, v in contagem.items()}

    def top_states(self, df, n=5):
        return dict(list(self.count_by_state(df).items())[:n])

    def count_by_age_group(self, df):
        bins   = [0, 5, 12, 18, 30, 45, 60, 101]
        labels = ["0-4", "5-12", "13-18", "19-30", "31-45", "46-60", "60+"]
        faixas = pd.cut(df["NU_IDADE_N"], bins=bins, labels=labels, right=False)
        return {str(k): int(v) for k, v in faixas.value_counts().sort_index().items()}

    def summary(self, df):
        return {
            "total": len(df),
            "ano":   int(df["NU_ANO"].iloc[0]),
            "doenca": str(df["ID_AGRAVO"].iloc[0]),
            "estados_afetados": df["SG_UF_NOT"].nunique(),
            "idade_media": round(float(df["NU_IDADE_N"].mean()), 1),
        }


class HospitalizationAnalyzer:

    def summary(self, df):
        return {
            "total":       len(df),
            "valor_total": round(float(df["VAL_TOT"].sum()), 2),
            "media_dias":  round(float(df["DIAS_PERM"].mean()), 1),
            "valor_medio": round(float(df["VAL_TOT"].mean()), 2),
        }

    def top_diagnoses(self, df, n=6):
        contagem = df["DIAG_PRINC"].value_counts().head(n)
        return {str(k): int(v) for k, v in contagem.items()}

    def count_by_sex(self, df):
        mapa = {"1": "Masculino", "3": "Feminino"}
        contagem = df["SEXO"].value_counts()
        return {mapa.get(k, k): int(v) for k, v in contagem.items()}


class MortalityAnalyzer:

    def summary(self, df):
        return {"total": len(df)}

    def top_causes(self, df, n=6):
        contagem = df["CAUSABAS"].value_counts().head(n)
        return {str(k): int(v) for k, v in contagem.items()}

    def count_by_sex(self, df):
        mapa = {"1": "Masculino", "2": "Feminino"}
        contagem = df["SEXO"].value_counts()
        return {mapa.get(k, k): int(v) for k, v in contagem.items()}