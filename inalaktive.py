import urllib.request

# URL Dropbox sumber playlist Anda
SOURCE_URL = "https://dl.dropboxusercontent.com/scl/fi/0gj7vjreta6eb5jtr078n/nov1.m3u?rlkey=mu969r11j8lcq4auh9mwrhs1j&st=9cxjqbg8&dl=1"

def is_link_active(url):
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
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
    new_playlist = ["#EXTM3U"]
    
    i = 0
    active_count = 0
    total_count = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            total_count += 1
            meta_line = line
            url_line = ""
            if i + 1 < len(lines):
                url_line = lines[i+1].strip()
            
            if url_line and not url_line.startswith("#"):
                print(f"Mengecek ({total_count}): {url_line}")
                if is_link_active(url_line):
                    new_playlist.append(meta_line)
                    new_playlist.append(url_line)
                    active_count += 1
                    print(" -> AKTIF")
                else:
                    print(" -> MATI (Dihapus)")
                i += 2
                continue
        i += 1

    # Simpan ke file output active_plinal.m3u
    with open("active_plinal.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(new_playlist))
    
    print(f"Selesai! Dari {total_count} channel, ada {active_count} channel yang aktif.")

if __name__ == "__main__":
    process_playlist()
