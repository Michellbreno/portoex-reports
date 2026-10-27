"""
generate_painel.py — Gera o Painel de Meta (dark theme, percentuais).
"""

import json
import os
from metrics import fmt_pct
from config import OUTPUT_FOLDER, MES_REFERENCIA, VENDOR_METAS


def _vtag(actual: float, meta: float | None) -> str:
    """Tag de status para vendedor no Painel Meta."""
    if meta is None:
        return '<span class="vtag" style="background:#21262d;color:#8b949e;border:1px solid #30363d">s/meta</span>'
    if actual >= meta:
        return '<span class="vtag ok">ACIMA</span>'
    return '<span class="vtag alert">ABAIXO</span>'


def _vcolor(actual: float, meta: float | None) -> str:
    if meta is None:
        return "#8b949e"
    return "#3fb950" if actual >= meta else "#f85149"


def _vbar_color(actual: float, meta: float | None) -> str:
    if meta is None:
        return "#8b949e"
    return "#3fb950" if actual >= meta else "#f85149"


def generate_painel(m: dict, output_folder: str = OUTPUT_FOLDER) -> str:
    """Gera o HTML do Painel Meta e salva em output_folder. Retorna o caminho."""

    ideal = m["ideal_pct"]
    m_pct = m["m_pct"]
    f_pct = m["f_pct"]
    m_vs  = m["m_vs_ideal"]
    f_vs  = m["f_vs_ideal"]

    # ---- Gauge tags MATRIZ ----
    m_tag1_cls = "green" if m_vs >= 0 else "red"
    m_tag1_txt = f"+{m_vs:.1f}pp vs ideal" if m_vs >= 0 else f"{m_vs:.1f}pp vs ideal"
    m_falta_cls = "neutral" if m_pct >= ideal else "yellow"

    # ---- Gauge tags FILIAL ----
    f_tag1_cls = "green" if f_vs >= 0 else ("yellow" if f_vs > -15 else "red")
    f_tag1_txt = f"+{f_vs:.1f}pp vs ideal" if f_vs >= 0 else f"{f_vs:.1f}pp vs ideal"
    f_nec_dia  = m["f_nec_dia"]
    f_media    = m["f_media_dia"]
    f_ratio    = f_nec_dia / f_media if f_media else 0

    # ---- KPI: MATRIZ vs Ideal ----
    mvsi_color = "#3fb950" if m_vs >= 0 else "#f85149"
    fvsi_color = "#3fb950" if f_vs >= 0 else ("#d29922" if f_vs > -15 else "#f85149")

    # ---- Vendor rows ----
    def vendor_rows(vendors, total, metas):
        rows = ""
        for vname, vval in vendors:
            if vval <= 0:
                continue
            pct  = vval / total * 100 if total else 0
            meta = metas.get(vname)
            col  = _vcolor(pct, meta)
            bcol = _vbar_color(pct, meta)
            tag  = _vtag(pct, meta)
            meta_txt = f"meta {fmt_pct(meta, 0)}" if meta else "s/meta"
            rows += f"""      <div class="velo-row">
        <span class="vname">{vname}</span>
        <div class="vbar-wrap"><div class="vbar" style="width:{min(pct,100):.1f}%;background:{bcol}"></div></div>
        <span class="vpct" style="color:{col}">{fmt_pct(pct)}</span>
        <span class="vmeta">{meta_txt}</span>
        {tag}
      </div>\n"""
        return rows

    vrows_m = vendor_rows(m["vendors_m"], m["m_total"], VENDOR_METAS.get("MATRIZ", {}))
    vrows_f = vendor_rows(m["vendors_f"], m["f_total"], VENDOR_METAS.get("FILIAL", {}))

    # ---- Top 10 rows ----
    def top_rows(items, total, color):
        rows = ""
        if not items:
            return rows
        max_val = items[0][1] if items else 1
        for i, (name, val) in enumerate(items, 1):
            pct  = val / total * 100 if total else 0
            bar  = val / max_val * 100 if max_val else 0
            short = name[:32] + "…" if len(name) > 32 else name
            rows += f"""      <div class="top-row">
        <span class="top-rank">{i}</span>
        <span class="top-name">{short}</span>
        <div class="top-bar-wrap"><div class="top-bar" style="width:{bar:.0f}%;background:{color}"></div></div>
        <span class="top-pct" style="color:{color}">{fmt_pct(pct)}</span>
      </div>\n"""
        return rows

    top_m = top_rows(m["top10_m"], m["m_total"], "#f57c00")
    top_f = top_rows(m["top10_f"], m["f_total"], "#42a5f5")

    # ---- JSON para gráficos ----
    dias_js   = json.dumps(m["dias_labels"])
    mAcum_js  = json.dumps(m["m_acum_arr"])
    fAcum_js  = json.dumps(m["f_acum_arr"])
    mDaily_js = json.dumps(m["m_daily_arr"])
    fDaily_js = json.dumps(m["f_daily_arr"])
    meta_m    = m["meta_m"]
    meta_f    = m["meta_f"]
    n_dias    = m["n_dias"]

    # ---- Mensagem motivacional ----
    if m_vs >= 0:
        m_msg = f'<span class="highlight">MATRIZ</span> acima do ritmo ideal ({m_tag1_txt.strip()}).'
    else:
        m_msg = f'<span class="highlight">MATRIZ</span> abaixo do ideal ({m_tag1_txt}). Reforçar nos dias restantes.'

    if f_ratio > 1.5:
        f_msg = f'<span class="highlight">FILIAL</span> em desafio critico: precisa de <span class="highlight">{f_ratio:.1f}x o ritmo atual</span> (R${f_nec_dia:,.0f} vs media R${f_media:,.0f}/dia).'
    elif f_vs < 0:
        f_msg = f'<span class="highlight">FILIAL</span> abaixo do ideal: precisa acelerar para R${f_nec_dia:,.0f}/dia nos dias restantes.'
    else:
        f_msg = f'<span class="highlight">FILIAL</span> no ritmo ({f_tag1_txt}).'

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Painel Meta – PortoEx {MES_REFERENCIA}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:"Segoe UI",Arial,sans-serif;background:#0d1117;color:#e6edf3;min-height:100vh;}}
  header{{background:linear-gradient(135deg,#0d1117,#161b22);border-bottom:1px solid #30363d;padding:16px 28px;display:flex;justify-content:space-between;align-items:center;}}
  header h1{{font-size:1.4rem;font-weight:700;color:#58a6ff;}}
  header .sub{{font-size:.8rem;color:#8b949e;margin-top:3px;}}
  .badge{{background:#21262d;border:1px solid #30363d;border-radius:8px;padding:6px 14px;font-size:.8rem;text-align:right;color:#8b949e;}}
  .badge strong{{color:#58a6ff;font-size:1rem;}}
  .container{{max-width:1300px;margin:0 auto;padding:20px 16px;}}
  .section-title{{font-size:.9rem;font-weight:700;color:#58a6ff;margin:24px 0 12px;text-transform:uppercase;letter-spacing:1px;border-left:3px solid #58a6ff;padding-left:10px;}}
  .gauge-row{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:4px;}}
  .gauge-card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:20px;display:flex;flex-direction:column;align-items:center;}}
  .gauge-card h3{{font-size:.95rem;font-weight:700;margin-bottom:6px;}}
  .gauge-card h3.orange{{color:#f57c00;}} .gauge-card h3.blue{{color:#42a5f5;}}
  canvas.gauge{{display:block;}}
  .gauge-pct{{font-size:2.4rem;font-weight:800;margin-top:4px;}}
  .gauge-pct.orange{{color:#f57c00;}} .gauge-pct.blue{{color:#42a5f5;}}
  .gauge-sub{{font-size:.78rem;color:#8b949e;margin-top:2px;}}
  .gauge-tags{{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;justify-content:center;}}
  .gtag{{font-size:.72rem;padding:3px 10px;border-radius:20px;font-weight:700;}}
  .gtag.green{{background:#1a3a2a;color:#3fb950;border:1px solid #3fb950;}}
  .gtag.red{{background:#3a1a1a;color:#f85149;border:1px solid #f85149;}}
  .gtag.yellow{{background:#3a2e1a;color:#d29922;border:1px solid #d29922;}}
  .gtag.neutral{{background:#21262d;color:#8b949e;border:1px solid #30363d;}}
  .kpi-row{{display:flex;gap:12px;flex-wrap:wrap;}}
  .kpi{{flex:1;min-width:140px;background:#161b22;border:1px solid #30363d;border-radius:10px;padding:14px;}}
  .kpi .lbl{{font-size:.68rem;color:#8b949e;text-transform:uppercase;letter-spacing:.5px;}}
  .kpi .val{{font-size:1.4rem;font-weight:700;margin-top:4px;}}
  .kpi .sub{{font-size:.72rem;color:#8b949e;margin-top:2px;}}
  .charts-row{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}
  .chart-card{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;}}
  .chart-card h4{{font-size:.8rem;font-weight:700;color:#8b949e;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px;}}
  .velo-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}
  .velo-card{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;}}
  .velo-card h4{{font-size:.82rem;font-weight:700;margin-bottom:12px;}}
  .velo-card h4.orange{{color:#f57c00;}} .velo-card h4.blue{{color:#42a5f5;}}
  .velo-row{{display:flex;align-items:center;gap:8px;margin:7px 0;font-size:.8rem;}}
  .vname{{width:90px;font-weight:600;color:#c9d1d9;}}
  .vbar-wrap{{flex:1;background:#21262d;border-radius:4px;height:8px;overflow:hidden;}}
  .vbar{{height:100%;border-radius:4px;}}
  .vpct{{width:40px;text-align:right;font-weight:700;}}
  .vmeta{{width:55px;text-align:right;font-size:.72rem;color:#8b949e;}}
  .vtag{{font-size:.68rem;padding:1px 6px;border-radius:4px;font-weight:700;}}
  .vtag.ok{{background:#1a3a2a;color:#3fb950;}}
  .vtag.warn{{background:#3a2e1a;color:#d29922;}}
  .vtag.alert{{background:#3a1a1a;color:#f85149;}}
  .top-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}
  .top-card{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;}}
  .top-card h4{{font-size:.82rem;font-weight:700;margin-bottom:12px;}}
  .top-card h4.orange{{color:#f57c00;}} .top-card h4.blue{{color:#42a5f5;}}
  .top-row{{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #21262d;font-size:.8rem;}}
  .top-row:last-child{{border-bottom:none;}}
  .top-rank{{width:20px;color:#484f58;font-weight:700;font-size:.72rem;}}
  .top-name{{flex:1;color:#c9d1d9;}}
  .top-pct{{font-weight:700;font-size:.85rem;}}
  .top-bar-wrap{{width:80px;background:#21262d;border-radius:3px;height:5px;overflow:hidden;}}
  .top-bar{{height:100%;border-radius:3px;}}
  .motiv{{background:linear-gradient(135deg,#1a237e22,#0d47a122);border:1px solid #1a237e55;border-radius:12px;padding:18px 22px;text-align:center;margin-top:8px;}}
  .motiv .title{{font-size:1.1rem;font-weight:700;color:#58a6ff;margin-bottom:6px;}}
  .motiv .msg{{font-size:.85rem;color:#8b949e;line-height:1.6;}}
  .motiv .highlight{{color:#f0f6fc;font-weight:600;}}
  footer{{text-align:center;font-size:.72rem;color:#484f58;margin:30px 0 16px;}}
  @media(max-width:700px){{.gauge-row,.charts-row,.velo-grid,.top-grid{{grid-template-columns:1fr;}}}}
</style>
</head>
<body>
<header>
  <div>
    <h1>Painel de Meta — PortoEx {MES_REFERENCIA}</h1>
    <div class="sub">Referencia: {m['dias_labels'][0] if m['dias_labels'] else ''} a {m['dias_labels'][-1] if m['dias_labels'] else ''} | {m['n_dias']} de {m['n_dias_mes']} dias uteis</div>
  </div>
  <div class="badge">Ideal do periodo<br><strong>{fmt_pct(ideal)}</strong></div>
</header>

<div class="container">

  <div class="section-title">Termometro de Meta por Unidade</div>
  <div class="gauge-row">
    <div class="gauge-card">
      <h3 class="orange">MATRIZ — Itajai SC</h3>
      <canvas class="gauge" id="gaugeM" width="220" height="120"></canvas>
      <div class="gauge-pct orange">{fmt_pct(m_pct)}</div>
      <div class="gauge-sub">{m['n_dias']}/{m['n_dias_mes']} dias uteis | Ideal {fmt_pct(ideal)}</div>
      <div class="gauge-tags">
        <span class="gtag {m_tag1_cls}">{m_tag1_txt}</span>
        <span class="gtag {m_falta_cls}">Falta {fmt_pct(100-m_pct)}</span>
        <span class="gtag neutral">{m['n_dias_rest']} dias restantes</span>
      </div>
    </div>
    <div class="gauge-card">
      <h3 class="blue">FILIAL SP — Sao Paulo</h3>
      <canvas class="gauge" id="gaugeF" width="220" height="120"></canvas>
      <div class="gauge-pct blue">{fmt_pct(f_pct)}</div>
      <div class="gauge-sub">{m['n_dias']}/{m['n_dias_mes']} dias uteis | Ideal {fmt_pct(ideal)}</div>
      <div class="gauge-tags">
        <span class="gtag {f_tag1_cls}">{f_tag1_txt}</span>
        <span class="gtag red">Falta {fmt_pct(100-f_pct)}</span>
        <span class="gtag yellow">Precisa +{fmt_pct(f_nec_dia/meta_f*100, 0)}/dia</span>
      </div>
    </div>
  </div>

  <div class="section-title">Indicadores Gerais</div>
  <div class="kpi-row">
    <div class="kpi"><div class="lbl">Total Geral</div><div class="val" style="color:#58a6ff">{fmt_pct(m['t_pct'])}</div><div class="sub">{m['m_nf']+m['f_nf']:,} NFs | {m['n_dias']} dias</div></div>
    <div class="kpi"><div class="lbl">Falta Total</div><div class="val" style="color:#f85149">{fmt_pct(100-m['t_pct'])}</div><div class="sub">em {m['n_dias_rest']} dias restantes</div></div>
    <div class="kpi"><div class="lbl">Ideal Periodo</div><div class="val" style="color:#d29922">{fmt_pct(ideal)}</div><div class="sub">{m['n_dias']} de {m['n_dias_mes']} dias uteis</div></div>
    <div class="kpi"><div class="lbl">MATRIZ vs Ideal</div><div class="val" style="color:{mvsi_color}">{m_tag1_txt}</div><div class="sub">{fmt_pct(m_pct)} vs {fmt_pct(ideal)}</div></div>
    <div class="kpi"><div class="lbl">FILIAL vs Ideal</div><div class="val" style="color:{fvsi_color}">{f_tag1_txt}</div><div class="sub">{fmt_pct(f_pct)} vs {fmt_pct(ideal)}</div></div>
    <div class="kpi"><div class="lbl">Dias Restantes</div><div class="val" style="color:#58a6ff">{m['n_dias_rest']}</div><div class="sub">dias uteis</div></div>
  </div>

  <div class="section-title">Evolucao Diaria</div>
  <div class="charts-row">
    <div class="chart-card"><h4>% Meta Acumulada por Unidade</h4><canvas id="pctChart" height="160"></canvas></div>
    <div class="chart-card"><h4>Participacao Diaria (%)</h4><canvas id="dailyPctChart" height="160"></canvas></div>
  </div>

  <div class="section-title">Ritmo por Vendedor</div>
  <div class="velo-grid">
    <div class="velo-card">
      <h4 class="orange">MATRIZ — Participacao no Faturamento</h4>
{vrows_m}    </div>
    <div class="velo-card">
      <h4 class="blue">FILIAL — Participacao no Faturamento</h4>
{vrows_f}    </div>
  </div>

  <div class="section-title">Top 10 Clientes — Participacao no Faturamento</div>
  <div class="top-grid">
    <div class="top-card">
      <h4 class="orange">MATRIZ — Top 10</h4>
{top_m}    </div>
    <div class="top-card">
      <h4 class="blue">FILIAL — Top 10</h4>
{top_f}    </div>
  </div>

  <div class="motiv">
    <div class="title">Foco nos {m['n_dias_rest']} dias restantes!</div>
    <div class="msg">
      {m_msg}<br>
      {f_msg}
    </div>
  </div>

</div>

<footer>PortoEx — Painel Meta {MES_REFERENCIA} — Atualizado em {m['data_geracao']}</footer>

<script>
function drawGauge(id, pct, color) {{
  var c = document.getElementById(id);
  var ctx = c.getContext("2d");
  var cx = c.width/2, cy = c.height-10, r = 90;
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.beginPath(); ctx.arc(cx,cy,r,Math.PI,0,false);
  ctx.strokeStyle="#21262d"; ctx.lineWidth=18; ctx.stroke();
  var angle = Math.PI * Math.min(pct/100, 1);
  ctx.beginPath(); ctx.arc(cx,cy,r,Math.PI,Math.PI+angle,false);
  ctx.strokeStyle=color; ctx.lineWidth=18; ctx.lineCap="round"; ctx.stroke();
  var idealAngle = Math.PI * {ideal/100:.4f};
  ctx.beginPath(); ctx.arc(cx,cy,r,Math.PI+idealAngle-0.01,Math.PI+idealAngle+0.01,false);
  ctx.strokeStyle="#58a6ff"; ctx.lineWidth=24; ctx.stroke();
}}
drawGauge("gaugeM", {m_pct:.1f}, "#f57c00");
drawGauge("gaugeF", {f_pct:.1f}, "#42a5f5");

var dias={dias_js};
var mAcum={mAcum_js};
var fAcum={fAcum_js};
var mDaily={mDaily_js};
var fDaily={fDaily_js};

var mPct=[],fPct=[],idealLine=[];
for(var i=0;i<dias.length;i++){{
  mPct.push(parseFloat((mAcum[i]/{meta_m}*100).toFixed(1)));
  fPct.push(parseFloat((fAcum[i]/{meta_f}*100).toFixed(1)));
  idealLine.push(parseFloat(((i+1)/{n_dias}*{ideal:.2f}).toFixed(1)));
}}

new Chart(document.getElementById('pctChart'),{{
  type:'line',
  data:{{labels:dias,datasets:[
    {{label:'MATRIZ %',data:mPct,borderColor:'#f57c00',backgroundColor:'rgba(245,124,0,0.1)',fill:true,tension:.3}},
    {{label:'FILIAL %',data:fPct,borderColor:'#42a5f5',backgroundColor:'rgba(66,165,245,0.1)',fill:true,tension:.3}},
    {{label:'Ideal',data:idealLine,borderColor:'#58a6ff',borderDash:[4,4],borderWidth:1.5,pointRadius:0,fill:false}}
  ]}},
  options:{{responsive:true,plugins:{{legend:{{position:'top',labels:{{color:'#8b949e'}}}}}},scales:{{x:{{ticks:{{color:'#8b949e'}}}},y:{{ticks:{{color:'#8b949e',callback:function(v){{return v+'%'}}}}}}}}}}
}});

var totalDailyPct=dias.map(function(_,i){{
  var td=mDaily[i]+fDaily[i];
  return parseFloat((td/({meta_m}+{meta_f})*100).toFixed(1));
}});
new Chart(document.getElementById('dailyPctChart'),{{
  type:'bar',
  data:{{labels:dias,datasets:[
    {{label:'MATRIZ %',data:mDaily.map(function(v){{return parseFloat((v/{meta_m}*100).toFixed(1));}}) ,backgroundColor:'rgba(245,124,0,0.7)',borderRadius:3}},
    {{label:'FILIAL %',data:fDaily.map(function(v){{return parseFloat((v/{meta_f}*100).toFixed(1));}}) ,backgroundColor:'rgba(66,165,245,0.7)',borderRadius:3}}
  ]}},
  options:{{responsive:true,plugins:{{legend:{{position:'top',labels:{{color:'#8b949e'}}}}}},scales:{{x:{{ticks:{{color:'#8b949e'}}}},y:{{ticks:{{color:'#8b949e',callback:function(v){{return v+'%'}}}}}}}}}}
}});
</script>
</body>
</html>"""

    os.makedirs(output_folder, exist_ok=True)
    path = os.path.join(output_folder, "Painel_Meta_PortoEx.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
