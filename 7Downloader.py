import os
import threading
import requests
import time
import sys
from urllib.parse import urlparse


def get_file_size(url):
    with requests.Session() as session:
        response = session.head(url, allow_redirects=True)
        file_size = int(response.headers.get('content-length', 0))
    return file_size


def download_chunk(url, start_byte, end_byte, part_number, filepath, progress_dict, lock):
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    session = requests.Session()
    response = session.get(url, headers=headers, stream=True)
    total_size = end_byte - start_byte + 1
    downloaded = 0

    with open(f"{filepath}.part{part_number}", "wb") as f:
        for chunk in response.iter_content(chunk_size=16 * 1024):  # Aumentado a 256 KB
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                with lock:
                    progress_dict[part_number] = downloaded
    session.close()


def print_progress(progress_dict, file_size):
    start_time = time.time()
    while True:
        total_downloaded = sum(progress_dict.values())
        percentage = (total_downloaded / file_size) * 100
        elapsed_time = time.time() - start_time
        speed = total_downloaded / elapsed_time if elapsed_time > 0 else 0
        sys.stdout.write(f"\rDescargando... {percentage:.2f}% completado - Velocidad: {speed / 1024 / 1024:.2f} MB/s")
        sys.stdout.flush()
        if total_downloaded >= file_size:
            break
        time.sleep(0.5)


def merge_chunks(filepath, num_parts):
    with open(filepath, "wb") as final_file:
        for i in range(num_parts):
            part_filename = f"{filepath}.part{i}"
            with open(part_filename, "rb") as part_file:
                final_file.write(part_file.read())
            os.remove(part_filename)


def multi_threaded_download(url, num_hilos, ruta_salida):
    if (ruta_salida == ""):
        downloads_dir = "downloads"
        os.makedirs(downloads_dir, exist_ok=True)
    else:
        downloads_dir = ruta_salida

    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path) or "downloaded_file"
    filepath = os.path.join(downloads_dir, filename)
    file_size = get_file_size(url)

    if file_size == 0:
        print("No se pudo determinar el tamaño del archivo. Descarga normal.")
        response = requests.get(url, stream=True)
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=16 * 1024):
                if chunk:
                    f.write(chunk)
        return

    num_threads = min(num_hilos, max(4, file_size // (10 * 1024 * 1024)))  # Ajuste dinámico de hilos
    chunk_size = file_size // num_threads
    threads = []
    progress_dict = {i: 0 for i in range(num_threads)}
    lock = threading.Lock()

    progress_thread = threading.Thread(target=print_progress, args=(progress_dict, file_size), daemon=True)
    progress_thread.start()

    for i in range(num_threads):
        start_byte = i * chunk_size
        end_byte = (start_byte + chunk_size - 1) if i < num_threads - 1 else file_size - 1
        thread = threading.Thread(target=download_chunk,
                                  args=(url, start_byte, end_byte, i, filepath, progress_dict, lock))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    merge_chunks(filepath, num_threads)
    print(f"\nDescarga completada: {filepath}")


def main():
    num_hilos = int(input("Ingresa la cantidad de hilos a utilizar (max 30 para mediafire): "))
    url = input("Ingresa la URL del archivo a descargar: ")
    ruta_salida = input(
        "Ingresa ruta donde se guardara el archivo (Ejemplo: C:\\Users\\nicolas\\Downloads  o presionar Enter para guardar en la carpeta downloads del proyecto): ")
    multi_threaded_download(url, num_hilos, ruta_salida)


if __name__ == "__main__":
    main()
