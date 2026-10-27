# 📊 PortoEx Reports

Sistema automatizado de geração de dashboards operacionais — **GEROT** e **Painel de Meta**.

---

## 🗂️ Estrutura do Projeto

```
portoex-reports/
├── data/                        ← Coloque aqui os arquivos exportados do sistema
│   ├── azportoex_*.csv
│   ├── pexlogistica_*.csv
│   ├── ptxtransporte_*.csv
│   └── cotacoes*.xls
│
├── outputs/                     ← Relatórios gerados automaticamente
│   ├── GEROT_PortoEx.html
│   └── Painel_Meta_PortoEx.html
│
├── scripts/
│   ├── config.py                ← ⚙️  CONFIGURAÇÕES (metas, dias úteis, regras)
│   ├── parser.py                ← Leitura e normalização dos arquivos
│   ├── metrics.py               ← Cálculo de todas as métricas
│   ├── generate_gerot.py        ← Gerador do GEROT (tema claro)
│   ├── generate_painel.py       ← Gerador do Painel de Meta (tema escuro)
│   └── main.py                  ← Ponto de entrada principal
│
├── .github/
│   └── workflows/
│       └── generate_reports.yml ← Automação via GitHub Actions
│
├── requirements.txt
└── README.md
```

---

## 🚀 Como Usar

### Passo 1 — Adicionar os dados
Coloque os arquivos exportados do sistema na pasta `/data`:
- Arquivos de faturamento: `.csv` com colunas `EMISSAO;VENDEDOR;CLIENTE;SERVICO;FRETE TOTAL;UNIDADE`
- Cotações: arquivos `cotacoes*.xls` (exportados pelo sistema)

### Passo 2 — Gerar os relatórios

**Opção A: Manualmente (localmente)**
```bash
cd portoex-reports
python scripts/main.py
```

**Opção B: Via GitHub (automático)**
- Vá na aba **Actions** do repositório
- Clique em **"Gerar Relatórios PortoEx"**
- Clique em **"Run workflow"**
- Aguarde ~30 segundos — os arquivos serão atualizados em `/outputs`

**Opção C: Automático diário**
O workflow roda automaticamente de segunda a sexta às 8h (horário de Brasília).
Também dispara automaticamente quando você envia novos arquivos para `/data`.

---

## ⚙️ Configurações — `scripts/config.py`

> Atualize este arquivo a cada mês novo.

| Configuração | O que é | Exemplo |
|---|---|---|
| `META_MATRIZ` | Meta mensal MATRIZ em R$ | `3_100_000.00` |
| `META_FILIAL` | Meta mensal FILIAL em R$ | `1_200_000.00` |
| `MES_REFERENCIA` | Nome do mês para exibição | `"Outubro 2026"` |
| `ANO_MES` | Chave para buscar dias úteis | `"2026-10"` |
| `WORKING_DAYS` | Lista de dias úteis do mês | `{"2026-10": ["01/10/2026", ...]}` |
| `DAY_REMAP` | Fins de semana → próximo dia útil | `{"25/10/2026": "26/10/2026"}` |
| `FORCE_FILIAL_KEYWORDS` | Clientes com unidade corrigida | `["LEAL"]` |
| `VENDOR_METAS` | Metas de participação por vendedor | ver arquivo |

---

## 📅 Atualizar para um Novo Mês

1. Abra `scripts/config.py`
2. Atualize `MES_REFERENCIA` e `ANO_MES`
3. Adicione a lista de dias úteis do novo mês em `WORKING_DAYS`
4. Atualize `DAY_REMAP` com os fins de semana do mês
5. Atualize `META_MATRIZ` e `META_FILIAL` se necessário
6. Faça commit e push — o workflow rodará automaticamente

---

## 🌐 Publicar com GitHub Pages

Para ter um link fixo dos relatórios:

1. Vá em **Settings** → **Pages** no repositório
2. Em **Source**, selecione a branch `main` e a pasta `/outputs`
3. Clique em **Save**
4. Seus relatórios estarão disponíveis em:
   `https://Michellbreno.github.io/portoex-reports/GEROT_PortoEx.html`

---

## 🔒 Repositório Privado?

Recomendamos manter o repositório **privado** pois contém dados operacionais da empresa.

---

## 📞 Suporte

Dúvidas sobre configuração? Abra uma issue neste repositório.
