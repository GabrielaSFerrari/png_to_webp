import csv
import re
from pathlib import Path
from PIL import Image

# Pastas
pasta_origem = Path("telefone_fixo")
pasta_destino = Path("out_webp")

# Configurações
qualidade = 100
largura_max = 768
altura_max = 512
ver = 0
# Função para ordenação natural
def natural_key(path):
    return [
        int(parte) if parte.isdigit() else parte.lower()
        for parte in re.split(r'(\d+)', str(path))
    ]
# Lê os nomes do CSV
nomes = []
with open("../png_to_webp/arquivo.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for linha in reader:
        nomes.append(linha["Image Name"].strip())

# Ordena os PNGs
arquivos_png = sorted(pasta_origem.rglob("*.png"), key=natural_key)

# Confere se a quantidade bate
if len(arquivos_png) != len(nomes):
    print(f"Atenção: {len(arquivos_png)} PNG(s) e {len(nomes)} nome(s) no CSV.")

cont = 0
for arquivo_png in arquivos_png:
    try:
        if cont >= len(nomes):
            print(f"Sem nome no CSV para: {arquivo_png}")
            break

        novo_nome = f"{nomes[cont]}-{cont}-{ver}.webp"

        caminho_relativo = arquivo_png.relative_to(pasta_origem)
        destino_final = pasta_destino / caminho_relativo.parent / novo_nome
        destino_final.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(arquivo_png) as img:
            img = img.convert("RGBA")
            img.thumbnail((largura_max, altura_max))
            img.save(destino_final, "WEBP", quality=qualidade)

        print(f"Convertido: {arquivo_png} -> {destino_final}")
        cont += 1

    except Exception as e:
        print(f"Erro ao converter {arquivo_png}: {e}")

print("\nConversão finalizada!")