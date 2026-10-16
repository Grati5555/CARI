import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

SOURCE_URL = "https://dl.dropboxusercontent.com/scl/fi/0gj7vjreta6eb5jtr078n/nov1.m3u?rlkey=mu969r11j8lcq4auh9mwrhs1j&st=9cxjqbg8&dl=1"

def is_link_active(url):
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*'
            }
        )
        # Menggunakan timeout 4 detik
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status != 200:
                return False
            
            # Cek tipe konten (Content-Type) untuk memastikan bukan halaman HTML error
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Jika server mengembalikan halaman HTML (biasanya halaman error 404/500 custom), anggap mati
            if 'text/html' in content_type:
                return False
                
            # Baca sedikit bytes pertama untuk memastikan ada respons data stream
            chunk = response.read(512)
            if not chunk and 'video' not in content_type and 'audio' not in content_type and 'application' not in content_type:
                return False
                
            return True
            
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
    print(f"Total channel ditemukan: {total_count}. Menjalankan filter ketat lanjutan...")

    new_playlist = ["#EXTM3U"]
    active_count = 0

    def check_entry(entry):
        meta, url = entry
        if is_link_active(url):
            return (meta, url, True)
        return (meta, url, False)

    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(check_entry, entry): entry for entry in entries}
        
        for future in as_completed(futures):
            meta, url, is_active = future.result()
            if is_active:
                new_playlist.append(meta)
                new_playlist.append(url)
                active_count += 1
                print(f"[VALID] {url}")
            else:
                print(f"[DIHAPUS] {url}")

    with open("active_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(new_playlist))
    
    print(f"Selesai! Dari {total_count} channel, tersisa {active_count} channel yang benar-benar aktif.")

if __name__ == "__main__":
    process_playlist()
