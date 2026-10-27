"""
generate_gerot.py — Gera o relatório GEROT (light theme).
"""

import json
import os
from metrics import fmt_brl, fmt_pct
from config import OUTPUT_FOLDER, MES_REFERENCIA, VENDOR_METAS


def _vendor_tag(actual: float, meta: float | None, label: str) -> str:
    """Retorna a tag HTML de status de vendedor."""
    if meta is None:
        return f'<span style="font-size:.72rem;color:#888">{label}</span>'
    if actual >= meta:
        return '<span class="tag-green">OK ✅</span>' if actual < meta * 1.1 else '<span class="tag-green">ACIMA ✅</span>'
    return '<span class="tag-warn">ABAIXO</span>'


def _vendor_color(actual: float, meta: float | None) -> str:
    if meta is None:
        return "#888"
    return "#2e7d32" if actual >= meta else "#f57c00"


def generate_gerot(m: dict, output_folder: str = OUTPUT_FOLDER) -> str:
    """Gera o HTML do GEROT e salva em output_folder. Retorna o caminho do arquivo."""

    # ---- Vendor rows MATRIZ ----
    vendor_rows_m = ""
    metas_m = VENDOR_METAS.get("MATRIZ", {})
    for vname, vval in m["vendors_m"]:
        if vval <= 0:
            continue
        pct = vval / m["m_total"] * 100 if m["m_total"] else 0
        meta = metas_m.get(vname)
        color = _vendor_color(pct, meta)
        tag   = _vendor_tag(pct, meta, "s/meta")
        vendor_rows_m += f"""
      <div class="vend-row">
        <span class="vend-name">{vname}</span>
        <div class="vend-bar-wrap"><div class="vend-bar" style="width:{min(pct,100):.1f}%;background:{color}"></div></div>
        <span class="vend-pct" style="color:{color}">{fmt_pct(pct)}</span>
        <span class="vend-val">{fmt_brl(vval)}</span>
        {tag}
      </div>"""

    # ---- Vendor rows FILIAL ----
    vendor_rows_f = ""
    metas_f = VENDOR_METAS.get("FILIAL", {})
    for vname, vval in m["vendors_f"]:
        if vval <= 0:
            continue
        pct   = vval / m["f_total"] * 100 if m["f_total"] else 0
        meta  = metas_f.get(vname)
        color = _vendor_color(pct, meta)
        tag   = _vendor_tag(pct, meta, "s/meta")
        vendor_rows_f += f"""
      <div class="vend-row">
        <span class="vend-name">{vname}</span>
        <div class="vend-bar-wrap"><div class="vend-bar" style="width:{min(pct,100):.1f}%;background:{color}"></div></div>
        <span class="vend-pct" style="color:{color}">{fmt_pct(pct)}</span>
        <span class="vend-val">{fmt_brl(vval)}</span>
        {tag}
      </div>"""

    # ---- Top 10 rows ----
    def top_rows(items, total):
        rows = ""
        for i, (name, val) in enumerate(items, 1):
            pct = val / total * 100 if total else 0
            short = name[:35] + "…" if len(name) > 35 else name
            rows += f"""
      <div class="top-row">
        <span class="top-rank">{i}</span>
        <span class="top-name">{short}</span>
        <span class="top-val">{fmt_brl(val)}</span>
        <span class="top-pct">{fmt_pct(pct)}</span>
      </div>"""
        return rows

    top_m = top_rows(m["top10_m"], m["m_total"])
    top_f = top_rows(m["top10_f"], m["f_total"])

    # ---- PERSONALIZADO_L rows ----
    def pers_rows(pers_dict):
        rows = ""
        for stype, data in sorted(pers_dict.items(), key=lambda x: -x[1]["val"]):
            rows += f'<div class="stat-row"><span class="stat-label">{stype}</span><span class="stat-val">{data["nf"]} NFs - {fmt_brl(data["val"])}</span></div>\n'
        return rows

    # ---- Indicadores de período ----
    m_status = "✅ ACIMA" if m["m_pct"] >= m["ideal_pct"] else "⚠️ ABAIXO"
    f_status = "✅ ACIMA" if m["f_pct"] >= m["ideal_pct"] else "⚠️ ABAIXO"
    m_color  = "#2e7d32" if m["m_pct"] >= m["ideal_pct"] else "#e53935"
    f_color  = "#2e7d32" if m["f_pct"] >= m["ideal_pct"] else "#e53935"
    m_prog_color = "orange" if m["m_pct"] >= m["ideal_pct"] else "orange"
    f_prog_color = "blue"

    # ---- JSON arrays para Chart.js ----
    dias_js    = json.dumps(m["dias_labels"])
    m_daily_js = json.dumps(m["m_daily_arr"])
    f_daily_js = json.dumps(m["f_daily_arr"])
    m_acum_js  = json.dumps(m["m_acum_arr"])
    f_acum_js  = json.dumps(m["f_acum_arr"])

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GROT PortoEx – {MES_REFERENCIA}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:"Segoe UI",Arial,sans-serif; background:#f0f2f5; color:#222; }}
  header {{ background:linear-gradient(135deg,#1a237e,#283593); color:#fff; padding:18px 28px; display:flex; justify-content:space-between; align-items:center; }}
  header h1 {{ font-size:1.5rem; font-weight:700; }}
  header .sub {{ font-size:.85rem; opacity:.85; margin-top:4px; }}
  .badge {{ background:#fff2; border-radius:6px; padding:6px 14px; font-size:.82rem; text-align:right; }}
  .container {{ max-width:1300px; margin:0 auto; padding:20px 16px; }}
  .section-title {{ font-size:1.05rem; font-weight:700; color:#1a237e; margin:24px 0 10px; border-left:4px solid #1a237e; padding-left:10px; }}
  .kpi-row {{ display:flex; gap:14px; flex-wrap:wrap; margin-bottom:4px; }}
  .kpi {{ flex:1; min-width:160px; background:#fff; border-radius:10px; padding:14px 16px; box-shadow:0 1px 6px #0001; }}
  .kpi .label {{ font-size:.72rem; color:#888; text-transform:uppercase; }}
  .kpi .value {{ font-size:1.55rem; font-weight:700; margin-top:4px; }}
  .kpi .sub {{ font-size:.75rem; color:#666; margin-top:2px; }}
  .kpi.orange{{border-top:3px solid #f57c00;}} .kpi.blue{{border-top:3px solid #1976d2;}}
  .kpi.purple{{border-top:3px solid #7b1fa2;}} .kpi.green{{border-top:3px solid #43a047;}} .kpi.red{{border-top:3px solid #e53935;}}
  .unit-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
  .unit-card {{ background:#fff; border-radius:12px; padding:18px; box-shadow:0 1px 8px #0001; }}
  .unit-card h3 {{ font-size:1rem; font-weight:700; margin-bottom:12px; padding-bottom:8px; border-bottom:2px solid; }}
  .unit-card.matriz h3{{border-color:#f57c00;color:#e65100;}} .unit-card.filial h3{{border-color:#1976d2;color:#0d47a1;}}
  .stat-row {{ display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #f0f0f0; font-size:.85rem; }}
  .stat-row:last-child{{border-bottom:none;}} .stat-label{{color:#666;}} .stat-val{{font-weight:600;}}
  .prog-wrap {{ background:#e0e0e0; border-radius:999px; height:10px; margin:8px 0; overflow:hidden; }}
  .prog-bar {{ height:100%; border-radius:999px; }}
  .prog-bar.orange{{background:linear-gradient(90deg,#f57c00,#ffa726);}} .prog-bar.blue{{background:linear-gradient(90deg,#1976d2,#42a5f5);}}
  .charts-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
  .chart-card {{ background:#fff; border-radius:12px; padding:16px; box-shadow:0 1px 8px #0001; }}
  .chart-card h4{{font-size:.88rem;font-weight:700;color:#555;margin-bottom:10px;}}
  .vendor-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;}}
  .vendor-card{{background:#fff;border-radius:12px;padding:16px;box-shadow:0 1px 8px #0001;}}
  .vendor-card h4{{font-size:.88rem;font-weight:700;margin-bottom:10px;}}
  .vend-row{{display:flex;align-items:center;gap:8px;margin:5px 0;font-size:.82rem;}}
  .vend-name{{width:100px;font-weight:600;}} .vend-bar-wrap{{flex:1;background:#eee;border-radius:4px;height:7px;overflow:hidden;}}
  .vend-bar{{height:100%;border-radius:4px;}} .vend-pct{{width:44px;text-align:right;font-weight:700;}}
  .vend-val{{width:90px;text-align:right;color:#666;font-size:.78rem;}}
  .tag-green{{background:#e8f5e9;color:#2e7d32;font-size:.72rem;padding:1px 6px;border-radius:4px;font-weight:600;}}
  .tag-warn{{background:#fff8e1;color:#f57c00;font-size:.72rem;padding:1px 6px;border-radius:4px;font-weight:600;}}
  .tag-red{{background:#ffebee;color:#c62828;font-size:.72rem;padding:1px 6px;border-radius:4px;font-weight:600;}}
  .top-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;}}
  .top-card{{background:#fff;border-radius:12px;padding:16px;box-shadow:0 1px 8px #0001;}}
  .top-card h4{{font-size:.88rem;font-weight:700;margin-bottom:10px;}}
  .top-row{{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid #f5f5f5;font-size:.82rem;}}
  .top-row:last-child{{border-bottom:none;}} .top-rank{{width:22px;color:#aaa;font-weight:700;}} .top-name{{flex:1;padding:0 6px;}} .top-val{{font-weight:700;}} .top-pct{{width:42px;text-align:right;color:#999;font-size:.78rem;}}
  .pipe-card{{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 8px #0001;}}
  .lot-card{{background:#fff;border-radius:12px;padding:18px;box-shadow:0 1px 8px #0001;}}
  .two-col{{display:grid;grid-template-columns:1fr 1fr;gap:18px;}}
  .pipe-row{{display:grid;grid-template-columns:160px 60px 110px 60px 80px;gap:8px;align-items:center;font-size:.82rem;padding:5px 0;border-bottom:1px solid #f0f0f0;}}
  .pipe-row:last-child{{border-bottom:none;}} .pipe-hdr{{font-size:.72rem;font-weight:700;color:#999;text-transform:uppercase;}}
  .alert{{background:#fff8e1;border-left:4px solid #ffa000;border-radius:6px;padding:10px 14px;font-size:.82rem;margin-bottom:14px;color:#555;}}
  .alert.info{{background:#e3f2fd;border-color:#1976d2;}}
  footer{{text-align:center;font-size:.75rem;color:#aaa;margin:30px 0 16px;}}
  @media(max-width:700px){{.unit-grid,.charts-grid,.vendor-grid,.top-grid,.two-col{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<header>
  <div>
    <h1>GROT - Relatorio Operacional PortoEx</h1>
    <div class="sub">Parcial: dias 1 ao {m['n_dias']} util | Gerado em {m['data_geracao']}</div>
  </div>
  <div class="badge">{m['n_dias']} de {m['n_dias_mes']} dias uteis<br><strong>{fmt_pct(m['ideal_pct'])} do mes</strong></div>
</header>
<div class="container">

  <div class="section-title">Visao Geral do Mes</div>
  <div class="kpi-row">
    <div class="kpi orange"><div class="label">MATRIZ Faturado</div><div class="value" style="color:#e65100">{fmt_brl(m['m_total'])}</div><div class="sub">{m['m_nf']:,} NFs - ticket {fmt_brm(m['m_ticket'])}</div></div>
    <div class="kpi blue"><div class="label">FILIAL Faturado</div><div class="value" style="color:#0d47a1">{fmt_brl(m['f_total'])}</div><div class="sub">{m['f_nf']:,} NFs - ticket {fmt_brl(m['f_ticket'])}</div></div>
    <div class="kpi purple"><div class="label">Total Geral</div><div class="value" style="color:#4a148c">{fmt_brl(m['total'])}</div><div class="sub">{m['m_nf']+m['f_nf']:,} NFs totais</div></div>
    <div class="kpi green"><div class="label">Media / Dia</div><div class="value" style="color:#2e7d32">{fmt_brl((m['m_total']+m['f_total'])/m['n_dias'] if m['n_dias'] else 0)}</div><div class="sub">M: {fmt_brl(m['m_media_dia'])} - F: {fmt_brl(m['f_media_dia'])}</div></div>
    <div class="kpi red"><div class="label">Falta para Meta</div><div class="value" style="color:#b71c1c">{fmt_brl(m['m_falta']+m['f_falta'])}</div><div class="sub">em {m['n_dias_rest']} dias uteis restantes</div></div>
  </div>

  <div class="section-title">Desempenho por Unidade</div>
  <div class="unit-grid">
    <div class="unit-card matriz">
      <h3>MATRIZ - Itajai SC</h3>
      <div class="stat-row"><span class="stat-label">Faturamento acumulado</span><span class="stat-val">{fmt_brl(m['m_total'], 2)}</span></div>
      <div class="stat-row"><span class="stat-label">Meta do mes</span><span class="stat-val">{fmt_brl(m['meta_m'], 2)}</span></div>
      <div class="stat-row"><span class="stat-label">% atingido</span><span class="stat-val" style="color:{m_color}">{fmt_pct(m['m_pct'])} {m_status}</span></div>
      <div class="stat-row"><span class="stat-label">Ideal ({m['n_dias']}/{m['n_dias_mes']} dias)</span><span class="stat-val">{fmt_pct(m['ideal_pct'])}</span></div>
      <div class="prog-wrap"><div class="prog-bar orange" style="width:{min(m['m_pct'],100):.1f}%"></div></div>
      <div class="stat-row"><span class="stat-label">Falta atingir</span><span class="stat-val" style="color:#e53935">{fmt_brl(m['m_falta'])}</span></div>
      <div class="stat-row"><span class="stat-label">Necessario / dia ({m['n_dias_rest']} dias)</span><span class="stat-val">{fmt_brl(m['m_nec_dia'])}</span></div>
      <div class="stat-row"><span class="stat-label">Media realizada / dia</span><span class="stat-val">{fmt_brl(m['m_media_dia'])}</span></div>
      <div class="stat-row"><span class="stat-label">Total de NFs</span><span class="stat-val">{m['m_nf']:,}</span></div>
    </div>
    <div class="unit-card filial">
      <h3>FILIAL - Sao Paulo SP</h3>
      <div class="stat-row"><span class="stat-label">Faturamento acumulado</span><span class="stat-val">{fmt_brl(m['f_total'], 2)}</span></div>
      <div class="stat-row"><span class="stat-label">Meta do mes</span><span class="stat-val">{fmt_brl(m['meta_f'], 2)}</span></div>
      <div class="stat-row"><span class="stat-label">% atingido</span><span class="stat-val" style="color:{f_color}">{fmt_pct(m['f_pct'])} {f_status}</span></div>
      <div class="stat-row"><span class="stat-label">Ideal ({m['n_dias']}/{m['n_dias_mes']} dias)</span><span class="stat-val">{fmt_pct(m['ideal_pct'])}</span></div>
      <div class="prog-wrap"><div class="prog-bar blue" style="width:{min(m['f_pct'],100):.1f}%"></div></div>
      <div class="stat-row"><span class="stat-label">Falta atingir</span><span class="stat-val" style="color:#e53935">{fmt_brl(m['f_falta'])}</span></div>
      <div class="stat-row"><span class="stat-label">Necessario / dia ({m['n_dias_rest']} dias)</span><span class="stat-val">{fmt_brl(m['f_nec_dia'])}</span></div>
      <div class="stat-row"><span class="stat-label">Media realizada / dia</span><span class="stat-val">{fmt_brl(m['f_media_dia'])}</span></div>
      <div class="stat-row"><span class="stat-label">Total de NFs</span><span class="stat-val">{m['f_nf']:,}</span></div>
    </div>
  </div>

  <div class="section-title">Evolucao Diaria</div>
  <div class="charts-grid">
    <div class="chart-card"><h4>Faturamento Diario por Unidade</h4><canvas id="dailyChart" height="180"></canvas></div>
    <div class="chart-card"><h4>Acumulado vs Meta</h4><canvas id="acumChart" height="180"></canvas></div>
  </div>

  <div class="section-title">Performance por Vendedor</div>
  <div class="vendor-grid">
    <div class="vendor-card">
      <h4 style="color:#e65100">MATRIZ - Vendedores</h4>
      {vendor_rows_m}
    </div>
    <div class="vendor-card">
      <h4 style="color:#0d47a1">FILIAL - Vendedores</h4>
      {vendor_rows_f}
    </div>
  </div>

  <div class="section-title">Top 10 Clientes</div>
  <div class="top-grid">
    <div class="top-card">
      <h4 style="color:#e65100">MATRIZ - Top 10</h4>
      {top_m}
    </div>
    <div class="top-card">
      <h4 style="color:#0d47a1">FILIAL - Top 10</h4>
      {top_f}
    </div>
  </div>

  <div class="section-title">Personalizado L (Lotacao)</div>
  <div class="two-col">
    <div class="lot-card">
      <h4>Resumo Lotacao - {MES_REFERENCIA}</h4>
      <div class="stat-row"><span class="stat-label">Total NFs Lotacao</span><span class="stat-val">{m['pers_m_total_nf']+m['pers_f_total_nf']}</span></div>
      <div class="stat-row"><span class="stat-label">Faturamento Total</span><span class="stat-val">{fmt_brl(m['pers_m_total_val']+m['pers_f_total_val'], 2)}</span></div>
      <div class="stat-row"><span class="stat-label">MATRIZ</span><span class="stat-val">{m['pers_m_total_nf']} NFs - {fmt_brl(m['pers_m_total_val'])}</span></div>
      <div class="stat-row"><span class="stat-label">FILIAL</span><span class="stat-val">{m['pers_f_total_nf']} NFs - {fmt_brl(m['pers_f_total_val'])}</span></div>
      <br>
      <h4 style="margin-bottom:8px">MATRIZ por Modalidade</h4>
      {pers_rows(m['pers_m'])}
    </div>
    <div class="lot-card">
      <h4 style="margin-bottom:8px">FILIAL por Modalidade</h4>
      {pers_rows(m['pers_f'])}
    </div>
  </div>

  <div class="section-title">Pipeline - Cotacoes</div>
  <div class="alert info">Cotacoes ativas: <strong>{m['cot_abertas']} abertas - {fmt_brl(m['cot_abertas_val'])}</strong> | MATRIZ: {m['cot_m_qtd']} cot. / {fmt_brl(m['cot_m_val'])} - FILIAL: {m['cot_f_qtd']} cot. / {fmt_brl(m['cot_f_val'])} | {m['cot_hoje']} vencem hoje - {m['cot_vencidas']} vencidas - {m['cot_reprovadas']} reprovadas.</div>
  <div class="pipe-card">
    <div class="pipe-row pipe-hdr"><span>Unidade</span><span>Abertas</span><span>Valor</span><span>Hoje</span><span>Vencidas</span></div>
    <div class="pipe-row"><span>MATRIZ</span><span>{m['cot_m_qtd']}</span><span>{fmt_brl(m['cot_m_val'])}</span><span>-</span><span style="color:#e53935">-</span></div>
    <div class="pipe-row"><span>FILIAL SP</span><span>{m['cot_f_qtd']}</span><span>{fmt_brl(m['cot_f_val'])}</span><span style="color:#f57c00">{m['cot_hoje']}</span><span style="color:#e53935">-</span></div>
    <div class="pipe-row" style="font-weight:700"><span>TOTAL</span><span>{m['cot_abertas']}</span><span>{fmt_brl(m['cot_abertas_val'])}</span><span style="color:#f57c00">{m['cot_hoje']}</span><span style="color:#e53935">{m['cot_vencidas']}</span></div>
  </div>

</div>
<footer>PortoEx - GROT {MES_REFERENCIA} - Gerado em {m['data_geracao']}</footer>
<script>
var dias={dias_js};
var m_daily={m_daily_js};
var f_daily={f_daily_js};
var m_acum={m_acum_js};
var f_acum={f_acum_js};
var metaM=Array(dias.length).fill({META_MATRIZ});
var metaF=Array(dias.length).fill({META_FILIAL});
var idealLine=dias.map(function(_,i){{return parseFloat((({META_MATRIZ}+{META_FILIAL})*(i+1)/dias.length).toFixed(0));}});

new Chart(document.getElementById('dailyChart'), {{
  type:'bar',
  data:{{labels:dias,datasets:[
    {{label:'MATRIZ',data:m_daily,backgroundColor:'rgba(245,124,0,0.7)',borderRadius:3}},
    {{label:'FILIAL',data:f_daily,backgroundColor:'rgba(25,118,210,0.7)',borderRadius:3}}
  ]}},
  options:{{responsive:true,plugins:{{legend:{{position:'top'}}}},scales:{{y:{{ticks:{{callback:function(v){{return'R$'+v.toLocaleString('pt-BR');}}}}}}}}}
}});

new Chart(document.getElementById('acumChart'), {{
  type:'line',
  data:{{labels:dias,datasets:[
    {{label:'MATRIZ Acum.',data:m_acum,borderColor:'#f57c00',backgroundColor:'rgba(245,124,0,0.1)',fill:true,tension:.3}},
    {{label:'FILIAL Acum.',data:f_acum,borderColor:'#1976d2',backgroundColor:'rgba(25,118,210,0.1)',fill:true,tension:.3}},
    {{label:'Meta M',data:metaM,borderColor:'#ffa726',borderDash:[6,3],borderWidth:1,pointRadius:0,fill:false}},
    {{label:'Meta F',data:metaF,borderColor:'#42a5f5',borderDash:[6,3],borderWidth:1,pointRadius:0,fill:false}}
  ]}},
  options:{{responsive:true,plugins:{{legend:{{position:'top'}}}},scales:{{y:{{ticks:{{callback:function(v){{return'R$'+v.toLocaleString('pt-BR');}}}}}}}}}
}});
</script>
</body>
</html>"""

    os.makedirs(output_folder, exist_ok=True)
    path = os.path.join(output_folder, "GEROT_PortoEx.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
