"""
metrics.py — Cálculo de todas as métricas de negócio.
Recebe os registros brutos do parser e devolve dicionários prontos para os geradores de HTML.
"""

from collections import defaultdict
from datetime import date
from config import (
    META_MATRIZ, META_FILIAL, ANO_MES, WORKING_DAYS,
    CORP_KEYWORDS, VENDOR_MAP, VENDOR_METAS, PERSONALIZADO_L_PREFIX,
)


# ============================================================
# UTILITÁRIOS
# ============================================================

def fmt_brl(value: float, decimals: int = 0) -> str:
    """Formata valor em reais no padrão brasileiro. Ex: 1234567.89 → 'R$1.234.568'"""
    if decimals == 0:
        return f"R${value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R${value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(value: float, decimals: int = 1) -> str:
    """Formata percentual no padrão brasileiro. Ex: 86.1 → '86,1%'"""
    return f"{value:.{decimals}f}%".replace(".", ",")


def vendor_group(vendedor: str) -> str:
    """Classifica um vendedor no seu grupo de negócio."""
    v = vendedor.upper()
    if any(kw in v for kw in CORP_KEYWORDS):
        return "CORPORATIVOS"
    for keyword, group in VENDOR_MAP.items():
        if keyword in v:
            return group
    return "OUTROS"


def today_str() -> str:
    """Retorna a data de hoje no formato DD/MM/YYYY."""
    d = date.today()
    return d.strftime("%d/%m/%Y")


# ============================================================
# CÁLCULO PRINCIPAL
# ============================================================

def calculate(records: list[dict], cotacoes: list[dict]) -> dict:
    """
    Processa todos os registros e retorna um dicionário com todas as métricas
    necessárias para gerar o GEROT e o Painel Meta.
    """
    working_days = WORKING_DAYS.get(ANO_MES, [])
    working_days_set = set(working_days)

    # Filtrar registros até hoje (apenas dias úteis)
    today = today_str()
    days_so_far = [d for d in working_days if d <= today]
    days_so_far_set = set(days_so_far)

    # --------------------------------------------------------
    # Acumuladores
    # --------------------------------------------------------
    m_daily   = defaultdict(float)
    f_daily   = defaultdict(float)
    m_clients = defaultdict(float)
    f_clients = defaultdict(float)
    m_vendors = defaultdict(float)
    f_vendors = defaultdict(float)
    m_nf = 0
    f_nf = 0

    # PERSONALIZADO_L
    pers_m = defaultdict(lambda: {"nf": 0, "val": 0.0})
    pers_f = defaultdict(lambda: {"nf": 0, "val": 0.0})

    for r in records:
        day     = r["emissao"]
        unidade = r["unidade"]
        frete   = r["frete"]
        cliente = r["cliente"]
        vend    = vendor_group(r["vendedor"])
        servico = r["servico"]

        if day not in days_so_far_set:
            continue

        if unidade == "MATRIZ":
            m_daily[day]    += frete
            m_clients[cliente] += frete
            m_vendors[vend]  += frete
            m_nf += 1
            if servico.startswith(PERSONALIZADO_L_PREFIX):
                subtype = servico.strip() if servico.strip() != PERSONALIZADO_L_PREFIX else PERSONALIZADO_L_PREFIX
                pers_m[subtype]["nf"]  += 1
                pers_m[subtype]["val"] += frete

        elif unidade == "FILIAL SP":
            f_daily[day]    += frete
            f_clients[cliente] += frete
            f_vendors[vend]  += frete
            f_nf += 1
            if servico.startswith(PERSONALIZADO_L_PREFIX):
                subtype = servico.strip()
                pers_f[subtype]["nf"]  += 1
                pers_f[subtype]["val"] += frete

    # --------------------------------------------------------
    # Totais e percentuais
    # --------------------------------------------------------
    m_total = sum(m_daily[d] for d in days_so_far)
    f_total = sum(f_daily[d] for d in days_so_far)
    total   = m_total + f_total

    n_dias      = len(days_so_far)
    n_dias_mes  = len(working_days)
    n_dias_rest = n_dias_mes - n_dias

    ideal_pct   = (n_dias / n_dias_mes * 100) if n_dias_mes else 0

    m_pct = (m_total / META_MATRIZ * 100) if META_MATRIZ else 0
    f_pct = (f_total / META_FILIAL * 100) if META_FILIAL else 0
    t_pct = (total / (META_MATRIZ + META_FILIAL) * 100)

    m_falta = META_MATRIZ - m_total
    f_falta = META_FILIAL - f_total

    m_nec_dia = (m_falta / n_dias_rest) if n_dias_rest > 0 else 0
    f_nec_dia = (f_falta / n_dias_rest) if n_dias_rest > 0 else 0

    m_media_dia = (m_total / n_dias) if n_dias else 0
    f_media_dia = (f_total / n_dias) if n_dias else 0

    m_ticket = (m_total / m_nf) if m_nf else 0
    f_ticket = (f_total / f_nf) if f_nf else 0

    # --------------------------------------------------------
    # Séries diárias para gráficos
    # --------------------------------------------------------
    m_daily_arr = [round(m_daily.get(d, 0), 2) for d in days_so_far]
    f_daily_arr = [round(f_daily.get(d, 0), 2) for d in days_so_far]

    m_acum_arr, f_acum_arr = [], []
    ms = fs = 0
    for m, f in zip(m_daily_arr, f_daily_arr):
        ms += m; fs += f
        m_acum_arr.append(round(ms, 2))
        f_acum_arr.append(round(fs, 2))

    dias_labels = [d[:5] for d in days_so_far]  # "DD/MM"

    # --------------------------------------------------------
    # Top 10 clientes
    # --------------------------------------------------------
    top10_m = sorted(m_clients.items(), key=lambda x: -x[1])[:10]
    top10_f = sorted(f_clients.items(), key=lambda x: -x[1])[:10]

    # --------------------------------------------------------
    # Vendedores
    # --------------------------------------------------------
    vendors_m = sorted(m_vendors.items(), key=lambda x: -x[1])
    vendors_f = sorted(f_vendors.items(), key=lambda x: -x[1])

    # --------------------------------------------------------
    # PERSONALIZADO_L (lotação)
    # --------------------------------------------------------
    pers_m_total_nf  = sum(v["nf"]  for v in pers_m.values())
    pers_m_total_val = sum(v["val"] for v in pers_m.values())
    pers_f_total_nf  = sum(v["nf"]  for v in pers_f.values())
    pers_f_total_val = sum(v["val"] for v in pers_f.values())

    # --------------------------------------------------------
    # Cotações
    # --------------------------------------------------------
    cot_abertas   = [c for c in cotacoes if "ABER" in c["status"].upper()]
    cot_vencidas  = [c for c in cotacoes if "VENC" in c["status"].upper() and "HOJE" not in c["status"].upper()]
    cot_hoje      = [c for c in cotacoes if "HOJE" in c["status"].upper()]
    cot_reprov    = [c for c in cotacoes if "REPROV" in c["status"].upper()]

    cot_m_aberta  = [c for c in cot_abertas if "MATRIZ" in c["unidade"].upper()]
    cot_f_aberta  = [c for c in cot_abertas if "FILIAL" in c["unidade"].upper()]

    # --------------------------------------------------------
    # Data de geração
    # --------------------------------------------------------
    d = date.today()
    data_geracao = d.strftime("%d/%m/%Y")

    # --------------------------------------------------------
    # Resultado final
    # --------------------------------------------------------
    return {
        # Totais
        "m_total": m_total, "f_total": f_total, "total": total,
        "m_pct": m_pct, "f_pct": f_pct, "t_pct": t_pct,
        "m_falta": m_falta, "f_falta": f_falta,
        "m_nec_dia": m_nec_dia, "f_nec_dia": f_nec_dia,
        "m_media_dia": m_media_dia, "f_media_dia": f_media_dia,
        "m_ticket": m_ticket, "f_ticket": f_ticket,
        "m_nf": m_nf, "f_nf": f_nf,

        # Metas e período
        "meta_m": META_MATRIZ, "meta_f": META_FILIAL,
        "n_dias": n_dias, "n_dias_mes": n_dias_mes, "n_dias_rest": n_dias_rest,
        "ideal_pct": ideal_pct,
        "m_vs_ideal": m_pct - ideal_pct,
        "f_vs_ideal": f_pct - ideal_pct,

        # Gráficos
        "dias_labels": dias_labels,
        "m_daily_arr": m_daily_arr, "f_daily_arr": f_daily_arr,
        "m_acum_arr": m_acum_arr, "f_acum_arr": f_acum_arr,

        # Rankings
        "top10_m": top10_m, "top10_f": top10_f,

        # Vendedores
        "vendors_m": vendors_m, "vendors_f": vendors_f,

        # Personalizado L
        "pers_m": dict(pers_m), "pers_f": dict(pers_f),
        "pers_m_total_nf": pers_m_total_nf, "pers_m_total_val": pers_m_total_val,
        "pers_f_total_nf": pers_f_total_nf, "pers_f_total_val": pers_f_total_val,

        # Cotações
        "cot_abertas": len(cot_abertas),
        "cot_abertas_val": sum(c["valor"] for c in cot_abertas),
        "cot_hoje": len(cot_hoje),
        "cot_vencidas": len(cot_vencidas),
        "cot_reprovadas": len(cot_reprov),
        "cot_m_qtd": len(cot_m_aberta),
        "cot_m_val": sum(c["valor"] for c in cot_m_aberta),
        "cot_f_qtd": len(cot_f_aberta),
        "cot_f_val": sum(c["valor"] for c in cot_f_aberta),

        # Meta
        "vendor_metas": VENDOR_METAS,
        "data_geracao": data_geracao,
    }
