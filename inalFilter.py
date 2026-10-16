import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

SOURCE_URL = "https://dl.dropboxusercontent.com/scl/fi/0gj7vjreta6eb5jtr078n/nov1.m3u?rlkey=mu969r11j8lcq4auh9mwrhs1j&st=9cxjqbg8&dl=1"

def is_link_active(url):
    try:
        # Menggunakan metode GET dengan rentang byte kecil atau stream singkat agar bisa mendeteksi error dengan akurat
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Range': 'bytes=0-1023' # Hanya ambil sebagian kecil data untuk tes koneksi stream
            }
        )
        # Timeout diperketat jadi 4 detik agar yang lemot/mati langsung terdeteksi
        with urllib.request.urlopen(req, timeout=4) as response:
            # Cek apakah status code masuk kategori sukses (200 atau 206 Partial Content untuk stream)
            if response.status in [200, 206]:
                return True
            return False
    except urllib.error.HTTPError as e:
        # Menangkap error seperti 404, 500, 403, dll secara langsung
        return False
    except Exception:
        # Menangkap timeout, koneksi terputus, atau link mati total
        return False

def process_playlist():
    print("Mengunduh playlist dari Dropbox...")
    req = urllib.request.Request(
        SOURCE_URL,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Gagal mengunduh playlist: {e}")
        return

    lines = content.splitlines()
    entries = []
    
    # Ambil pasangan #EXTINF dan URL-nya
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            meta_line = line
            url_line = ""
            if i + 1 < len(lines):
                url_line = lines[i+1].strip()
            
            if url_line and not url_line.startswith("#"):
                entries.append((meta_line, url_line))
                i += 2
                continue
        i += 1

    total_count = len(entries)
    print(f"Total channel ditemukan: {total_count}. Mulai filter ketat (menghapus error 404/mati)...")

    new_playlist = ["#EXTM3U"]
    active_count = 0

    def check_entry(entry):
        meta, url = entry
        if is_link_active(url):
            # Mengganti semua variasi INAL menjadi CH
            updated_meta = meta.replace("INAL", "CH").replace("inal", "CH").replace("Inal", "CH")
            return (updated_meta, url, True)
        return (meta, url, False)

    # Jalankan pengecekan bersamaan (max 20 thread agar server tujuan tidak memblokir tes kita)
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_entry, entry): entry for entry in entries}
        
        for future in as_completed(futures):
            meta, url, is_active = future.result()
            if is_active:
                new_playlist.append(meta)
                new_playlist.append(url)
                active_count += 1
                print(f"[AKTIF] {url}")
            else:
                print(f"[DIHAPUS/MATI/404] {url}")

    # Simpan hasil akhir
    with open("active_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(new_playlist))
    
    print(f"Selesai! Dari {total_count} channel, tersisa {active_count} channel yang benar-benar aktif.")

if __name__ == "__main__":
    process_playlist()
