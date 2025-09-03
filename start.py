import subprocess
import os
import sys
import time
import socket

# İYİLEŞTİRME: Betik boyunca kullanılacak bilgileri saklamak için bir sözlük
script_state = {
    "public_ip": None,
    "local_ip": None
}

def print_header():
    header = """
\033[94m
════════════════════════════════════════════════════════════════════════════════
                             BlackCode - UBUNTU SERVER BAKIM VE KURULUM BETİĞİ
════════════════════════════════════════════════════════════════════════════════
    Versiyon: 1.5 (Netdata Docker Entegrasyonu)
    Tarih: 3 Eylül 2025
    Ubuntu Version: 22.04 LTS

    Bu betik sunucunuzda aşağıdaki işlemleri otomatik olarak gerçekleştirir:
    - Sistem güncelleme kontrolü ve otomatik güncelleme
    - Sistem dili kontrolü ve gerekirse Türkçe'ye çevirme
    - Swap alanı oluşturma ve yönetimi (ZRAM öncelikli)
    - Gereksiz servislerin kapatılması
    - Logların temizlenmesi
    - UFW güvenlik duvarı kurulumu ve yapılandırması
    - Docker kurulumu ve güncellemesi
    - Docker Compose kurulumu ve güncellemesi
    - Portainer kurulumu ve güncellemesi
    - Netdata kurulumu (Docker ile), güncellemesi ve port ayarları
    - Boot analizi
    - Donanım testleri
    - Ağ testleri
════════════════════════════════════════════════════════════════════════════════
\033[0m"""
    print(header)
    while True:
        cevap = input("\nBetik çalıştırılsın mı? (e/h): ").strip().lower()
        if cevap == 'e':
            print("\nBetik başlatılıyor...\n")
            break
        elif cevap == 'h':
            print("\nBetik iptal edildi.\n")
            sys.exit(0)
        else:
            print("\nLütfen 'e' veya 'h' girin.")

def print_title(title):
    print(f"\033[94m\n=== {title} ===\033[0m")

def run(cmd, show_output=True, non_interactive=False):
    try:
        env = os.environ.copy()
        if non_interactive:
            env["DEBIAN_FRONTEND"] = "noninteractive"
            cmd = f'apt-get -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" {cmd}'

        result = subprocess.run(
            cmd, shell=True, text=True, capture_output=not show_output,
            timeout=600, env=env
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"Komut zaman aşımına uğradı: {cmd}")
        return subprocess.CompletedProcess(cmd, 1, "", "Timeout")
    except Exception as e:
        print(f"Komut çalıştırma hatası: {e}")
        return subprocess.CompletedProcess(cmd, 1, "", str(e))

def check_service(service):
    result = run(f"systemctl is-active {service}", show_output=False)
    return result.returncode == 0 and result.stdout.strip() == "active"

def update_system():
    print_title("Sistem güncelleme kontrolü başlatıldı")
    result = run("update -y", show_output=True, non_interactive=True)
    if result.returncode != 0:
        print_title("Güncelleme hatası, listeler temizlenip yeniden deneniyor")
        run("rm -rf /var/lib/apt/lists/*", show_output=False)
        run("update -y", show_output=True, non_interactive=True)

    upgradable_count = run("apt list --upgradable 2>/dev/null | wc -l", show_output=False)
    if upgradable_count.returncode == 0 and int(upgradable_count.stdout.strip()) > 1:
        print_title("Güncelleme mevcut, sistem güncelleniyor (Bu işlem biraz zaman alabilir)")
        run("upgrade -y", show_output=True, non_interactive=True)
        run("autoremove -y && apt-get autoclean -y", show_output=True, non_interactive=True)
        print_title("Sistem güncellemesi tamamlandı ve kuruldu")
    else:
        print_title("Sistem zaten güncel")

# ... (Diğer fonksiyonlar: set_locale_tr, install_zram, create_swap, etc. aynı kalıyor) ...

def set_locale_tr():
    print_title("Sistem dili kontrol ediliyor")
    locale_result = run("locale | grep LANG=", show_output=False)
    if "tr_TR.UTF-8" not in locale_result.stdout:
        print_title("Sistem dili Türkçe değil, Türkçe'ye geçiriliyor")
        run("install -y language-pack-tr", show_output=True, non_interactive=True)
        run("locale-gen tr_TR.UTF-8", show_output=True)
        run("update-locale LANG=tr_TR.UTF-8", show_output=True)
        run("localectl set-locale LANG=tr_TR.UTF-8", show_output=True)
        run("timedatectl set-timezone Europe/Istanbul", show_output=True)
        print_title("Türkçe locale ayarlandı ve kuruldu")
    else:
        print_title("Sistem dili zaten Türkçe")

def install_zram():
    print_title("ZRAM kurulumu kontrol ediliyor")
    swap_result = run("swapon --show", show_output=False)
    if "zram" in swap_result.stdout:
        print_title("ZRAM zaten kurulu")
        return

    result = run("install -y zram-config", show_output=True, non_interactive=True)
    if result.returncode != 0:
        print_title("ZRAM-config kurulamadı, alternatif olarak zram-tools deneniyor")
        run("install -y zram-tools", show_output=True, non_interactive=True)

    run("systemctl enable zram-config.service 2>/dev/null || systemctl enable zramswap.service 2>/dev/null || true", show_output=False)
    run("systemctl start zram-config.service 2>/dev/null || systemctl start zramswap.service 2>/dev/null || true", show_output=False)
    time.sleep(3)
    status = run("swapon --show | grep zram", show_output=False)
    if status.returncode == 0:
        print_title("ZRAM başarıyla kuruldu")
        print(f"ZRAM durumu: {status.stdout.strip()}")
    else:
        print_title("ZRAM kurulumu başarısız, standart swap alanı oluşturulacak")
        create_swap(2)

def create_swap(size_gb=2):
    swap_file = "/swapfile"
    if os.path.exists(swap_file):
        run(f"swapoff {swap_file}", show_output=False)
        run(f"rm -f {swap_file}", show_output=False)
        print_title("Mevcut swap alanı kaldırıldı")

    print_title(f"{size_gb}GB swap alanı oluşturuluyor...")
    result = run(f"fallocate -l {size_gb}G {swap_file}", show_output=True)
    if result.returncode != 0:
        print_title("fallocate başarısız oldu, dd ile deneniyor.")
        run(f"dd if=/dev/zero of={swap_file} bs=1M count={size_gb * 1024} status=progress", show_output=True)

    run(f"chmod 600 {swap_file}", show_output=False)
    run(f"mkswap {swap_file}", show_output=True)
    run(f"swapon {swap_file}", show_output=True)

    if f"{swap_file} none swap sw 0 0" not in open("/etc/fstab").read():
        with open("/etc/fstab", "a") as f:
            f.write(f"\n{swap_file} none swap sw 0 0\n")

    print_title(f"{size_gb}GB swap alanı oluşturuldu")
    run("swapon --show", show_output=True)

def optimize_services():
    print_title("Gereksiz servisler devre dışı bırakılıyor")
    services = ["snapd", "cups", "bluetooth", "modemmanager", "avahi-daemon", "whoopsie", "rpcbind", "apport"]
    for service in services:
        run(f"systemctl stop {service} 2>/dev/null || true", show_output=False)
        run(f"systemctl disable {service} 2>/dev/null || true", show_output=False)
        print(f"- {service} servisi durduruldu ve devre dışı bırakıldı.")
    run("systemctl daemon-reload", show_output=False)

def clean_journal():
    print_title("Sistem logları (journal) temizleniyor")
    run("journalctl --vacuum-time=7d", show_output=True)
    run("journalctl --vacuum-size=100M", show_output=True)

def security_ufw():
    print_title("UFW güvenlik duvarı kontrolü")
    if run("which ufw", show_output=False).returncode != 0:
        print_title("UFW kurulu değil, kuruluyor")
        run("install -y ufw", show_output=True, non_interactive=True)

    if "inactive" in run("ufw status", show_output=False).stdout:
        print_title("UFW aktif değil, yapılandırılıyor")
        run("ufw allow OpenSSH", show_output=True)
        run("ufw allow 22/tcp", show_output=True)
        run("ufw --force enable", show_output=True)
        print_title("UFW aktif edildi")
    else:
        print_title("UFW zaten aktif")

def install_docker():
    print_title("Docker kurulumu kontrolü")
    if check_service("docker"):
        print_title("Docker zaten kurulu ve çalışıyor. Güncellemeler kontrol ediliyor.")
        run("install --only-upgrade -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin", show_output=True, non_interactive=True)
        return

    print_title("Docker kuruluyor...")
    run("install -y ca-certificates curl gnupg lsb-release", show_output=True, non_interactive=True)
    
    os.makedirs("/etc/apt/keyrings", exist_ok=True)
    run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg", show_output=True)
    run('echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list', show_output=True)
    
    run("update -y", show_output=True, non_interactive=True)
    run("install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin", show_output=True, non_interactive=True)

    run("systemctl enable docker", show_output=True)
    run("systemctl start docker", show_output=True)
    
    current_user = os.environ.get("SUDO_USER", os.getlogin())
    if current_user != "root":
        run(f"usermod -aG docker {current_user}", show_output=False)
        print_title(f"'{current_user}' kullanıcısı docker grubuna eklendi. Değişikliklerin etkili olması için yeniden giriş yapmanız gerekebilir.")
    
    time.sleep(3)
    if check_service("docker"):
        print_title("Docker başarıyla kuruldu/güncellendi")
    else:
        print_title("Docker kurulumunda hata oluştu")

def install_docker_compose():
    print_title("Docker Compose kontrolü")
    if run("docker compose version", show_output=False).returncode == 0:
        print_title("Docker Compose Plugin (v2) zaten kurulu")
    else:
        print_title("Docker Compose Plugin (v2) kuruluyor")
        run("install -y docker-compose-plugin", show_output=True, non_interactive=True)
        if run("docker compose version", show_output=False).returncode == 0:
            print_title("Docker Compose Plugin başarıyla kuruldu.")
        else:
            print_title("Docker Compose Plugin kurulamadı.")

def install_portainer():
    print_title("Portainer kontrolü")
    if run("docker ps -a --format '{{.Names}}' | grep '^portainer$'", show_output=False).returncode == 0:
        print_title("Portainer zaten mevcut - en son versiyona güncelleniyor")
        run("docker stop portainer", show_output=True)
        run("docker rm portainer", show_output=True)
        run("docker pull portainer/portainer-ce:latest", show_output=True)
    else:
        print_title("Portainer kuruluyor")
    
    run("docker volume create portainer_data", show_output=False)
    run("docker run -d -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest", show_output=True)
    
    time.sleep(3)
    if "portainer" in run("docker ps --format '{{.Names}}'", show_output=False).stdout:
        print_title("Portainer başarıyla kuruldu/güncellendi")
    else:
        print_title("Portainer kurulumunda hata oluştu")

# YENİ FONKSİYON: Netdata'yı Docker ile kurar
def install_netdata_docker():
    print_title("Netdata (Docker) kontrolü")

    # Docker'ın çalışıp çalışmadığını kontrol et
    if not check_service("docker"):
        print("\033[1;31mHATA: Netdata'yı Docker ile kurmak için önce Docker'ın kurulu ve çalışır olması gerekir.\033[0m")
        print("Lütfen menüden Docker kurulumunu seçin.")
        return

    netdata_command = """
    docker run -d --name=netdata \\
    --pid=host \\
    --network=host \\
    -v netdataconfig:/etc/netdata \\
    -v netdatalib:/var/lib/netdata \\
    -v netdatacache:/var/cache/netdata \\
    -v /:/host/root:ro,rslave \\
    -v /etc/passwd:/host/etc/passwd:ro \\
    -v /etc/group:/host/etc/group:ro \\
    -v /etc/localtime:/etc/localtime:ro \\
    -v /proc:/host/proc:ro \\
    -v /sys:/host/sys:ro \\
    -v /etc/os-release:/host/etc/os-release:ro \\
    -v /var/log:/host/var/log:ro \\
    -v /var/run/docker.sock:/var/run/docker.sock:ro \\
    -v /run/dbus:/run/dbus:ro \\
    --restart unless-stopped \\
    --cap-add SYS_PTRACE \\
    --cap-add SYS_ADMIN \\
    --security-opt apparmor=unconfined \\
    netdata/netdata
    """
    
    # Mevcut Netdata konteynerini kontrol et
    if run("docker ps -a --format '{{.Names}}' | grep '^netdata$'", show_output=False).returncode == 0:
        print_title("Netdata zaten mevcut - en son versiyona güncelleniyor")
        run("docker stop netdata", show_output=True)
        run("docker rm netdata", show_output=True)
        run("docker pull netdata/netdata", show_output=True)
    else:
        print_title("Netdata (Docker) kuruluyor")

    # Netdata konteynerini çalıştır
    run(netdata_command, show_output=True)
    time.sleep(5)

    # Kurulumun başarılı olup olmadığını kontrol et
    if "netdata" in run("docker ps --format '{{.Names}}'", show_output=False).stdout:
        print_title("Netdata (Docker) başarıyla kuruldu/güncellendi")
        # UFW'da portu aç
        print_title("Güvenlik duvarında 19999 portu açılıyor...")
        run("ufw allow 19999/tcp", show_output=True)
    else:
        print_title("Netdata (Docker) kurulumunda hata oluştu")

def boot_analysis():
    print_title("Boot süresi analizi")
    run("systemd-analyze", show_output=True)
    print("\nEn çok yavaşlatan 10 servis:")
    run("systemd-analyze blame | head -10", show_output=True)

def hardware_test():
    print_title("Donanım bilgileri")
    run("lscpu | grep -E '^(Model name|CPU\(s\)|Thread|Core)'", show_output=True)
    run("free -h", show_output=True)
    run("df -h --output=source,size,used,avail,pcent,target | grep -E '^(Filesystem|/dev/)'", show_output=True)
    run("lsblk", show_output=True)

def network_test():
    print_title("Ağ bilgileri ve testleri")
    run("ip -4 addr show | grep 'inet'", show_output=True)
    
    if run("which ping", show_output=False).returncode != 0:
        run("install -y iputils-ping", show_output=True, non_interactive=True)
    
    print("\nİnternet bağlantısı testi (ping 8.8.8.8):")
    run("ping -c 3 8.8.8.8", show_output=True)

    print("\nIP adresleri alınıyor...")
    try:
        public_ip_res = run("curl -s --connect-timeout 5 http://ipinfo.io/ip", show_output=False)
        if public_ip_res.returncode == 0 and public_ip_res.stdout.strip():
            script_state["public_ip"] = public_ip_res.stdout.strip()
            print(f"Genel IP Adresi: {script_state['public_ip']}")
    except Exception:
        pass
    
    local_ip_res = run("hostname -I", show_output=False)
    if local_ip_res.returncode == 0 and local_ip_res.stdout.strip():
        script_state["local_ip"] = local_ip_res.stdout.strip().split()[0]
        print(f"Yerel IP Adresi: {script_state['local_ip']}")

def generate_summary():
    print_title("SİSTEM ÖZET RAPORU")

    if not script_state.get("local_ip"):
        network_test() 

    local_ip = script_state.get("local_ip", "ALINAMADI")
    public_ip = script_state.get("public_ip", local_ip)

    print("\n\033[1;32m● SUNUCU BİLGİLERİ:\033[0m")
    run("hostnamectl", show_output=True)
    
    print("\n\033[1;32m● DONANIM BİLGİLERİ:\033[0m")
    run("echo 'CPU:' && lscpu | grep 'Model name'", show_output=True)
    run("echo 'RAM:' && free -h | grep 'Mem:'", show_output=True)
    run("echo 'Disk:' && df -h | grep -E '^/dev/'", show_output=True)
    
    print("\n\033[1;32m● AĞ BİLGİLERİ:\033[0m")
    print(f"Yerel IP: {local_ip}")
    print(f"Genel IP: {public_ip}")

    print("\n\033[1;32m● DOCKER BİLGİLERİ:\033[0m")
    if run("which docker", show_output=False).returncode == 0:
        run("docker --version", show_output=True)
        print("Çalışan Konteynerler:")
        run("docker ps", show_output=True)
    else:
        print("Docker kurulu değil.")
    
    print("\n\033[1;32m● SERVİS & KONTEYNER DURUMLARI:\033[0m")
    services = {"docker": "Docker Servisi", "ufw": "Güvenlik Duvarı (UFW)"}
    for s_id, s_name in services.items():
        if check_service(s_id):
            print(f"{s_name}: \033[1;32mÇALIŞIYOR\033[0m")
        else:
            print(f"{s_name}: \033[1;31mDURDURULMUŞ\033[0m")

    # GÜNCELLEME: Netdata'yı sistem servisi yerine Docker konteyneri olarak kontrol et
    if "netdata" in run("docker ps --format '{{.Names}}'", show_output=False).stdout:
        print(f"Netdata Konteyneri: \033[1;32mÇALIŞIYOR\033[0m")
    else:
        print(f"Netdata Konteyneri: \033[1;31mDURDURULMUŞ/KURULU DEĞİL\033[0m")
            
    if "zram" in run("swapon --show", show_output=False).stdout:
        print("ZRAM Swap: \033[1;32mAKTİF\033[0m")
    else:
        print("ZRAM Swap: \033[1;31mPASİF\033[0m")

    print("\n\033[1;32m● PORT VE ERİŞİM BİLGİLERİ:\033[0m")
    print(f"Netdata: \033[1;36mhttp://{public_ip}:19999\033[0m")
    print(f"Portainer: \033[1;36mhttp://{public_ip}:9000\033[0m")
    
    print("\n\033[1;32m● GÜVENLİK DUVARI KURALLARI:\033[0m")
    run("ufw status numbered", show_output=True)

def main():
    if os.geteuid() != 0:
        print("\033[1;31mBu betiği root olarak çalıştırmalısınız! (sudo python3 script.py)\033[0m")
        sys.exit(1)

    print_header()
    
    completed_tasks = []
    menu = [
        ("Sistem güncellemesi", update_system),
        ("Türkçe dil desteği", set_locale_tr),
        ("ZRAM/Swap kurulumu", install_zram),
        ("Gereksiz servisleri kapatma", optimize_services),
        ("Logları temizleme", clean_journal),
        ("Güvenlik duvarı (UFW) yapılandırma", security_ufw),
        ("Docker kurulumu", install_docker),
        ("Docker Compose kurulumu", install_docker_compose),
        ("Portainer kurulumu", install_portainer),
        # GÜNCELLEME: Menüdeki fonksiyon ve açıklama değiştirildi
        ("Netdata kurulumu (Docker ile)", install_netdata_docker),
        ("Boot analizi", boot_analysis),
        ("Donanım testleri", hardware_test),
        ("Ağ testleri", network_test)
    ]

    print("\nYapılacak işlemleri seçin (virgül ile ayırın, ör: 1,3,5):\n")
    print("0. Tümünü yap (tüm işlemler)")
    for idx, (desc, _) in enumerate(menu, 1):
        print(f"{idx}. {desc}")
    
    while True:
        secim = input("\nSeçiminiz: ").strip()
        if secim == "0":
            secimler = list(range(1, len(menu) + 1))
            break
        elif secim:
            try:
                secimler = [int(x) for x in secim.split(',') if x.strip().isdigit() and 1 <= int(x) <= len(menu)]
                if secimler:
                    break
                else:
                    print("Geçersiz seçim, tekrar deneyin.")
            except ValueError:
                print("Geçersiz giriş, tekrar deneyin.")
        else:
            print("Lütfen bir seçim yapın.")

    print()
    start_time = time.time()
    for idx in secimler:
        try:
            desc, func = menu[idx-1]
            func()
            completed_tasks.append(f"✓ {desc}")
        except Exception as e:
            error_msg = f"✗ {desc} - Hata: {str(e)}"
            print_title(f"HATA: {error_msg}")
            completed_tasks.append(error_msg)

    generate_summary()
    
    print_title("GERÇEKLEŞTİRİLEN İŞLEMLER")
    for task in completed_tasks:
        if task.startswith("✓"):
            print(f"\033[1;32m{task}\033[0m")
        else:
            print(f"\033[1;31m{task}\033[0m")

    end_time = time.time()
    print(f"\nToplam süre: {int(end_time - start_time)} saniye.")

    cevap = input("\nSunucuyu yeniden başlatmak ister misiniz? (e/h): ").strip().lower()
    if cevap == "e":
        print("Sunucu 3 saniye içinde yeniden başlatılıyor...")
        time.sleep(3)
        run("reboot", show_output=True)
    else:
        print("İşlemler tamamlandı. Sunucu yeniden başlatılmadı.")

if __name__ == "__main__":
    main()
