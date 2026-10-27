"""
config.py — Configurações centrais do sistema PortoEx Reports.
Atualize este arquivo a cada mês: metas, dias úteis, e regras de negócio.
"""

# ============================================================
# METAS MENSAIS (R$)
# ============================================================
META_MATRIZ = 3_100_000.00
META_FILIAL = 1_200_000.00

# ============================================================
# MÊS DE REFERÊNCIA
# ============================================================
MES_REFERENCIA = "Outubro 2026"
ANO_MES        = "2026-10"       # usado para selecionar dias úteis abaixo

# ============================================================
# DIAS ÚTEIS POR MÊS
# Adicione novos meses conforme necessário.
# Formato de data: DD/MM/YYYY
# ============================================================
WORKING_DAYS = {
    "2026-10": [
        "01/10/2026", "02/10/2026", "05/10/2026", "06/10/2026",
        "07/10/2026", "08/10/2026", "09/10/2026", "13/10/2026",
        "14/10/2026", "15/10/2026", "16/10/2026", "19/10/2026",
        "20/10/2026", "21/10/2026", "22/10/2026", "23/10/2026",
        "26/10/2026", "27/10/2026", "28/10/2026", "29/10/2026",
        "30/10/2026",
    ],
}

DAY_REMAP = {
    "04/10/2026": "05/10/2026",
    "10/10/2026": "13/10/2026",
    "11/10/2026": "13/10/2026",
    "17/10/2026": "19/10/2026",
    "18/10/2026": "19/10/2026",
    "24/10/2026": "26/10/2026",
    "25/10/2026": "26/10/2026",
}

CORP_KEYWORDS = ["MICHELL", "MAURO", "MARLON", "MURILO", "SABRINA"]

VENDOR_MAP = {
    "URIEL":   "URIEL",
    "TIAGO":   "TIAGO",
    "CAIO":    "CAIO",
    "MARCELO": "MARCELO",
}

VENDOR_METAS = {
    "MATRIZ": {
        "CORPORATIVOS": 65.0,
        "URIEL":        14.0,
        "TIAGO":        14.0,
        "CAIO":          5.0,
    },
    "FILIAL": {
        "CORPORATIVOS": 40.0,
        "TIAGO":        14.0,
        "CAIO":          5.0,
        "MARCELO":       5.0,
    },
}

FORCE_FILIAL_KEYWORDS = ["LEAL"]
PERSONALIZADO_L_PREFIX = "PERSONALIZADO_L"
DATA_FOLDER   = "data"
OUTPUT_FOLDER = "outputs"
