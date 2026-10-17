import urllib.request
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

SOURCE_URL = "https://dl.dropboxusercontent.com/scl/fi/0gj7vjreta6eb5jtr078n/nov1.m3u?rlkey=mu969r11j8lcq4auh9mwrhs1j&st=9cxjqbg8&dl=1"

def is_link_active(url):
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Range': 'bytes=0-1023'
            }
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            return response.status in [200, 206]
    except Exception:
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
                # Cek apakah metadata mengandung kategori INAL atau B-INAL (case-insensitive)
                meta_upper = meta_line.upper()
                if "INAL" in meta_upper or "B-INAL" in meta_upper:
                    # Lewati / hapus channel ini karena mengandung kategori terlarang
                    i += 2
                    continue
                
                entries.append((meta_line, url_line))
                i += 2
                continue
        i += 1

    total_count = len(entries)
    print(f"Total channel setelah filter kategori INAL/B-INAL: {total_count}. Mulai pengecekan link...")

    new_playlist = ["#EXTM3U"]
    active_count = 0

    def check_entry(entry):
        meta, url = entry
        if is_link_active(url):
            # Mengubah sisa nama channel yang masih mengandung kata INAL menjadi CH
            updated_meta = meta.replace("INAL", "CH").replace("inal", "CH").replace("Inal", "CH")
            return (updated_meta, url, True)
        return (meta, url, False)

    # Jalankan pengecekan bersamaan (max 20 thread)
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
    
    print(f"Selesai! Tersisa {active_count} channel aktif yang bersih dari kategori INAL/B-INAL.")

if __name__ == "__main__":
    process_playlist()
