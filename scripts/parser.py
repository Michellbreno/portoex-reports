"""
parser.py — Leitura e normalização dos arquivos exportados do sistema.
Suporta: CSV (faturamento) e XLS/HTML (cotações).
"""

import csv
import os
import glob
from html.parser import HTMLParser
from config import DATA_FOLDER, FORCE_FILIAL_KEYWORDS, DAY_REMAP


# ============================================================
# UTILITÁRIOS
# ============================================================

def parse_float(value: str) -> float:
    """Converte string brasileira (1.234,56) para float."""
    try:
        return float(value.strip().replace(".", "").replace(",", "."))
    except (ValueError, AttributeError):
        return 0.0


def normalize_date(date_str: str) -> str:
    """Remapeia datas não úteis para o próximo dia útil."""
    return DAY_REMAP.get(date_str.strip(), date_str.strip())


def apply_unit_override(cliente: str, unidade: str) -> str:
    """
    Aplica overrides de unidade para clientes com cadastro errado no sistema.
    Ex: IND.E COM.LEAL está como MATRIZ no PTX mas deve ser FILIAL.
    """
    cliente_upper = cliente.upper()
    for keyword in FORCE_FILIAL_KEYWORDS:
        if keyword in cliente_upper:
            return "FILIAL SP"
    return unidade


# ============================================================
# PARSER DE CSV (faturamento)
# ============================================================

def load_csv_files(data_folder: str = DATA_FOLDER) -> list[dict]:
    """
    Lê todos os arquivos .csv da pasta data/.
    Retorna lista de registros normalizados.
    Colunas esperadas: EMISSAO, VENDEDOR, CLIENTE, SERVICO, FRETE TOTAL, UNIDADE
    """
    records = []
    csv_files = glob.glob(os.path.join(data_folder, "*.csv"))

    if not csv_files:
        print(f"⚠️  Nenhum arquivo .csv encontrado em '{data_folder}/'")
        return records

    for filepath in csv_files:
        filename = os.path.basename(filepath)
        count = 0
        try:
            with open(filepath, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    unidade  = row.get("UNIDADE", "").strip()
                    cliente  = row.get("CLIENTE", "").strip()
                    vendedor = row.get("VENDEDOR", "").strip()
                    servico  = row.get("SERVICO", "").strip()
                    emissao  = normalize_date(row.get("EMISSAO", "").strip())
                    frete    = parse_float(row.get("FRETE TOTAL", "0"))

                    # Aplicar override de unidade
                    unidade = apply_unit_override(cliente, unidade)

                    records.append({
                        "file":     filename,
                        "emissao":  emissao,
                        "vendedor": vendedor,
                        "cliente":  cliente,
                        "servico":  servico,
                        "frete":    frete,
                        "unidade":  unidade,
                    })
                    count += 1
        except Exception as e:
            print(f"  Erro ao ler {filename}: {e}")
            continue

        print(f"  {filename}: {count} registros")

    return records


# ============================================================
# PARSER DE XLS (cotações — arquivo HTML disfarçado de XLS)
# ============================================================

class _TableParser(HTMLParser):
    """Parser interno para extrair tabelas de arquivos XLS/HTML."""
    def __init__(self):
        super().__init__()
        self.tables = []
        self._current_table = None
        self._current_row = None
        self._current_cell = None
        self._in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._current_table = []
        elif tag == "tr" and self._current_table is not None:
            self._current_row = []
        elif tag in ("td", "th") and self._current_row is not None:
            self._current_cell = []
            self._in_cell = True

    def handle_endtag(self, tag):
        if tag == "table" and self._current_table is not None:
            self.tables.append(self._current_table)
            self._current_table = None
        elif tag == "tr" and self._current_row is not None:
            if self._current_table is not None:
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag in ("td", "th") and self._in_cell:
            if self._current_row is not None:
                self._current_row.append(" ".join(self._current_cell).strip())
            self._current_cell = None
            self._in_cell = False

    def handle_data(self, data):
        if self._in_cell and self._current_cell is not None:
            self._current_cell.append(data.strip())


def load_xls_cotacoes(data_folder: str = DATA_FOLDER) -> list[dict]:
    """
    Lê arquivos .xls de cotações da pasta data/.
    Esses arquivos são na verdade tabelas HTML exportadas pelo sistema.
    Retorna lista de cotações com campos: unidade, status, valor, vencimento.
    """
    cotacoes = []
    xls_files = glob.glob(os.path.join(data_folder, "cotacoes*.xls"))

    if not xls_files:
        print(f"  Nenhum arquivo de cotações encontrado em '{data_folder}/'")
        return cotacoes

    for filepath in xls_files:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, encoding="latin-1") as f:
                content = f.read()

            parser = _TableParser()
            parser.feed(content)

            if len(parser.tables) < 2:
                print(f"  {filename}: estrutura inesperada (menos de 2 tabelas)")
                continue

            # Tabela de dados está no índice 1; linha 0 é o cabeçalho
            data_table = parser.tables[1]
            if not data_table:
                continue

            headers = [h.upper().strip() for h in data_table[0]]

            def col(row, name):
                try:
                    idx = next(i for i, h in enumerate(headers) if name in h)
                    return row[idx].strip() if idx < len(row) else ""
                except StopIteration:
                    return ""

            for row in data_table[1:]:
                if not any(cell.strip() for cell in row):
                    continue
                cotacoes.append({
                    "file":       filename,
                    "unidade":    col(row, "UNIDADE"),
                    "status":     col(row, "STATUS"),
                    "valor":      parse_float(col(row, "VALOR")),
                    "vencimento": col(row, "VENCIMENTO"),
                    "cliente":    col(row, "CLIENTE"),
                })

            print(f"  {filename}: {len(data_table)-1} cotações")

        except Exception as e:
            print(f"  Erro ao ler {filename}: {e}")

    return cotacoes
