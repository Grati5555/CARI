import urllib.request
import urllib.error
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

SOURCE_URL = "https://dl.dropboxusercontent.com/scl/fi/0gj7vjreta6eb5jtr078n/nov1.m3u?rlkey=mu969r11j8lcq4auh9mwrhs1j&st=9cxjqbg8&dl=1"

def is_link_active(url):
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': '*/*'
            }
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            if response.status != 200:
                return False
            
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                return False
                
            return True
            
    except (urllib.error.HTTPError, urllib.error.URLError, Exception):
        return False

def clean_and_format_meta(meta_line):
    # 1. Cek Kategori (group-title). Jika kategorinya INAL atau B INAL, hapus (return None)
    group_match = re.search(r'group-title="([^"]*)"', meta_line, re.IGNORECASE)
    if group_match:
        group_val = group_match.group(1).strip().upper()
        if group_val in ["INAL", "B INAL"] or "INAL" in group_val:
            return None  # Kategori dihapus/di-skip

    # 2. Ganti Nama Channel yang mengandung INAL / B INAL menjadi CH
    parts = meta_line.split(',', 1)
    if len(parts) == 2:
        attributes, channel_name = parts
        
        # Jika nama channel mengandung kata inal / b inal, ganti jadi CH
        if re.search(r'\b(b\s*)?inal\b', channel_name, re.IGNORECASE):
            channel_name = "CH"
            
        # Bersihkan juga tvg-name jika ada isinya inal
        attributes = re.sub(r'tvg-name="[^"]*inal[^"]*"', 'tvg-name="CH"', attributes, flags=re.IGNORECASE)
        
        meta_line = f"{attributes},{channel_name}"
        
    return meta_line

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
                # Proses filter kategori dan ganti nama
                processed_meta = clean_and_format_meta(meta_line)
                if processed_meta is not None:
                    entries.append((processed_meta, url_line))
                i += 2
                continue
        i += 1

    total_count = len(entries)
    print(f"Total channel setelah filter kategori: {total_count}. Memulai pengecekan link aktif...")

    new_playlist = ["#EXTM3U"]
    active_count = 0

    def check_entry(entry):
        meta, url = entry
        if is_link_active(url):
            return (meta, url, True)
        return (meta, url, False)

    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(check_entry, entry): entry for entry in entries}
        
        for future in as_completed(futures):
            meta, url, is_active = future.result()
            if is_active:
                new_playlist.append(meta)
                new_playlist.append(url)
                active_count += 1
                print(f"[AKTIF & BERSIH] {url}")
            else:
                print(f"[DIBUANG - ERROR] {url}")

    with open("active_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(new_playlist))
    
    print(f"Selesai! Tersisa {active_count} channel aktif.")

if __name__ == "__main__":
    process_playlist()
