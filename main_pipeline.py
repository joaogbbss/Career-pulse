import argparse
from engine.build_web_app import build_interactive_webapp


def main():
    parser = argparse.ArgumentParser(description="CareerPulse - Pipeline Estatístico & Gerador Web")
    parser.add_argument("--out", default="web", help="Diretório de saída do app estático para GitHub Pages")
    args = parser.parse_args()

    print("[1/2] Executando Motor Estatístico de 6 Camadas (Empirical Bayes + PAdj + GMM + Kalman-RTS)...")
    index_file = build_interactive_webapp(output_dir=args.out)
    print(f"[2/2] Sucesso! Aplicação interativa gerada em: {index_file}")
    print("      -> Abra 'web/index.html' direto no navegador ou rode 'streamlit run app_streamlit.py'")


if __name__ == "__main__":
    main()
