"""
main.py — Ponto de entrada principal.

Como usar:
  1. Coloque os arquivos CSV e XLS exportados do sistema na pasta /data
  2. Execute: python scripts/main.py
  3. Os relatórios serão gerados em /outputs

Para rodar automaticamente via GitHub Actions, este script é chamado pelo workflow.
"""

import sys
import os

# Adiciona o diretório scripts ao path para os imports funcionarem
sys.path.insert(0, os.path.dirname(__file__))

from parser import load_csv_files, load_xls_cotacoes
from metrics import calculate
from generate_gerot import generate_gerot
from generate_painel import generate_painel


def main():
    print("=" * 55)
    print("  PortoEx Reports — Gerador de Dashboards")
    print("=" * 55)

    # 1. Carregar dados
    print("\n📂 Lendo arquivos de faturamento (CSV)...")
    records = load_csv_files()
    print(f"   Total: {len(records):,} registros carregados")

    print("\n📂 Lendo cotações (XLS)...")
    cotacoes = load_xls_cotacoes()
    print(f"   Total: {len(cotacoes):,} cotações carregadas")

    if not records:
        print("\n⚠️  Nenhum dado de faturamento encontrado.")
        print("   Coloque os arquivos .csv exportados do sistema na pasta /data")
        sys.exit(1)

    # 2. Calcular métricas
    print("\n🔢 Calculando métricas...")
    m = calculate(records, cotacoes)

    print(f"\n   MATRIZ: {m['m_total']:,.2f} ({m['m_pct']:.1f}% da meta)")
    print(f"   FILIAL: {m['f_total']:,.2f} ({m['f_pct']:.1f}% da meta)")
    print(f"   Total:  {m['total']:,.2f} ({m['t_pct']:.1f}% da meta total)")
    print(f"   Dias:   {m['n_dias']}/{m['n_dias_mes']} úteis")

    # 3. Gerar relatórios
    print("\n🖥️  Gerando GEROT...")
    gerot_path = generate_gerot(m)
    print(f"   Salvo em: {gerot_path}")

    print("\n🖥️  Gerando Painel de Meta...")
    painel_path = generate_painel(m)
    print(f"   Salvo em: {painel_path}")

    print("\n✅ Concluído! Abra os arquivos em /outputs para visualizar.")
    print("=" * 55)


if __name__ == "__main__":
    main()
