#Bibliotecas
import csv
import re
import unicodedata
from pathlib import Path
from PIL import Image, ImageOps

# CONFIGURAÇÕES
csv_path = Path("arquivo.csv")          # ajuste aqui
pasta_origem = Path("telefone_fixo")
pasta_destino = Path("out_webp")

qualidade = 100
largura_max = 768
altura_max = 512

# Nome da coluna do CSV que contém o título usado no rename
coluna_titulo = "Image Name"

def menu1():
    print("1 - Primeira Versão")
    print("2 - Versão n")
    op = int(input("Digite o numero: "))
    return op

def menu2():
    print("1 - Todos")
    print("2 - Apenas os:")
    op = int(input("Digite o numero: "))
    return op

def pedir_indices():
    entrada = input('Digite os índices separados por vírgula (ex: 13,17,18): ').strip()
    if not entrada:
        return set()
    partes = [p.strip() for p in entrada.split(",")]
    indices = set()
    for p in partes:
        if p.isdigit():
            indices.add(int(p))
        else:
            print(f'Valor ignorado: "{p}"')
    return indices

def carregar_csv():
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    if not fieldnames:
        raise ValueError("O CSV está vazio ou sem cabeçalho.")
    if coluna_titulo not in fieldnames:
        raise ValueError(f'A coluna "{coluna_titulo}" não foi encontrada no CSV.')
    return rows, fieldnames

def garantir_coluna_version(rows, fieldnames):
    alterou = False
    if "version" not in fieldnames:
        fieldnames.append("version")
        for row in rows:
            row["version"] = "0"
        alterou = True
    else:
        for row in rows:
            if not str(row.get("version", "")).strip():
                row["version"] = "0"
                alterou = True
    return rows, fieldnames, alterou

def salvar_csv(rows, fieldnames):
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def to_kebab(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    texto = re.sub(r"-+", "-", texto).strip("-")
    return texto

def montar_nome_saida(titulo, indice, versao):
    titulo_kebab = to_kebab(titulo)
    return f"{titulo_kebab}-{indice}-{versao}.webp"

def converter_png_para_webp(origem, destino):
    with Image.open(origem) as img:
        tem_alpha = img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        )
        if tem_alpha:
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        # Faz a imagem ficar EXATAMENTE 768x512
        # Pode recortar um pouco para encaixar no formato
        img = ImageOps.fit(
            img,
            (largura_max, altura_max),
            method=Image.Resampling.LANCZOS
        )
        img.save(destino, "WEBP", quality=qualidade)

def listar_pngs_numericos():
    arquivos = []
    for arq in pasta_origem.glob("*.png"):
        if arq.stem.isdigit():
            arquivos.append(arq)
    return sorted(arquivos, key=lambda x: int(x.stem))

def processar_imagens(modo="primeira", indices_especificos=None):
    """
    modo:
      - 'primeira'   -> mantém version = 0
      - 'reprocessar'-> incrementa version só dos processados
    """
    pasta_destino.mkdir(parents=True, exist_ok=True)

    rows, fieldnames = carregar_csv()
    rows, fieldnames, alterou_csv = garantir_coluna_version(rows, fieldnames)

    if alterou_csv:
        salvar_csv(rows, fieldnames)
        print('Coluna "version" criada/preenchida com 0.')

    arquivos_png = listar_pngs_numericos()

    if not arquivos_png:
        print("Nenhum PNG numérico encontrado.")
        return

    atualizou_version = False

    for arq_png in arquivos_png:
        indice = int(arq_png.stem)

        # Relação:
        # 0.png -> rows[0] -> primeira linha de dados
        # 1.png -> rows[1] -> segunda linha de dados
        if indice >= len(rows):
            print(f"Sem linha correspondente no CSV para {arq_png.name}.")
            continue
        if indices_especificos is not None and indice not in indices_especificos:
            continue
        row = rows[indice]
        titulo = str(row[coluna_titulo]).strip()
        versao_atual = int(str(row.get("version", "0")).strip() or "0")
        if modo == "primeira":
            nova_versao = versao_atual
        elif modo == "reprocessar":
            nova_versao = versao_atual + 1
        else:
            raise ValueError("Modo inválido.")

        nome_saida = montar_nome_saida(titulo, indice, nova_versao)
        caminho_saida = pasta_destino / nome_saida

        converter_png_para_webp(arq_png, caminho_saida)

        if modo == "reprocessar":
            row["version"] = str(nova_versao)
            atualizou_version = True

        print(f"{arq_png.name} -> {nome_saida}")

    if atualizou_version:
        salvar_csv(rows, fieldnames)
        print("CSV atualizado com as novas versões.")

def main():
    match menu1():
        case 1:
            # Primeira versão: processa tudo, mantendo version 0
            processar_imagens(modo="primeira", indices_especificos=None)
        case 2:
            match menu2():
                case 1:
                    # Versão n de todos: incrementa todos
                    processar_imagens(modo="reprocessar", indices_especificos=None)
                case 2:
                    # Versão n apenas de alguns
                    indices = pedir_indices()
                    if not indices:
                        print("Nenhum índice válido informado.")
                        return
                    processar_imagens(modo="reprocessar", indices_especificos=indices)
                case _:
                    print("none")
        case _:
            print("none")
if __name__ == "__main__":
    main()