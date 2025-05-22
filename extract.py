import os
import re
import subprocess
from pathlib import Path
import argparse

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def extract_wavs_from_bnk(bnk_path, output_dir):
    with open(bnk_path, "rb") as f:
        data = f.read()

    bnk_name = Path(bnk_path).stem
    output_dir = Path(output_dir) / bnk_name
    output_dir.mkdir(exist_ok=True)

    # Buscar nombres de archivo
    name_matches = [m.group().decode('ascii', errors='ignore') for m in re.finditer(rb'[\w\-/]{4,}\.wav', data)]

    # Buscar cabeceras RIFF
    riff_matches = list(re.finditer(b'RIFF....WAVE', data))
    if not riff_matches:
        print(f"[!] No se encontraron cabeceras RIFF en {bnk_path}")
        return

    print(f"[+] {bnk_path}: {len(riff_matches)} sonidos encontrados")

    for i, match in enumerate(riff_matches):
        start = match.start()
        size_bytes = data[start+4:start+8]
        wav_size = int.from_bytes(size_bytes, 'little')
        end = start + 8 + wav_size
        wav_data = data[start:end]

        # Asignar nombre al bnk
        if i < len(name_matches):
            filename = sanitize_filename(name_matches[i])
        else:
            filename = f"sound_{i+1:02}.wav"

        raw_path = output_dir / f"raw_{filename}"
        final_path = output_dir / filename

        # Guardar archivo crudo
        with open(raw_path, "wb") as f:
            f.write(wav_data)

        # Convertir a WAV legible
        subprocess.run(["ffmpeg", "-y", "-i", str(raw_path), str(final_path)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        raw_path.unlink()  # Eliminar crudo después de convertir

    print(f"[✓] Extraídos y convertidos a: {output_dir}/")

def process_all_bnks(input_dir, output_dir):
    for file in os.listdir(input_dir):
        if file.endswith(".bnk"):
            bnk_path = os.path.join(input_dir, file)
            extract_wavs_from_bnk(bnk_path, output_dir)

def main():
    parser = argparse.ArgumentParser(description="Extrae y convierte archivos .bnk a .wav legibles.")
    parser.add_argument("input_bnk", help="Ruta al archivo .bnk o directorio con archivos .bnk")
    parser.add_argument("-o", "--output", default="extracted_wavs", help="Carpeta de salida (por defecto: extracted_wavs)")

    args = parser.parse_args()

    # Si es un archivo, extraerlo
    if os.path.isfile(args.input_bnk):
        extract_wavs_from_bnk(args.input_bnk, args.output)
    # Si es un directorio, procesar todos los .bnk dentro de él
    elif os.path.isdir(args.input_bnk):
        process_all_bnks(args.input_bnk, args.output)
    else:
        print(f"[!] La ruta {args.input_bnk} no es válida.")

if __name__ == "__main__":
    main()

    #ejemplo de uso:
    #python extract.py archivo.bnk -o carpeta_salida
    #python extract.py directorio_con_bnks -o carpeta_salida
