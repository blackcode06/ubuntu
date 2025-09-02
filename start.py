import subprocess
import os
import sys
import time
import socket

def print_header():
    header = """
\033[94m
════════════════════════════════════════════════════════════════════════════════
             BlackCode - UBUNTU SERVER BAKIM VE KURULUM BETİĞİ
════════════════════════════════════════════════════════════════════════════════
    Versiyon: 1.3
    Tarih: 2 Eylül 2025
    Ubuntu Version: 22.04 LTS
    
    Bu betik sunucunuzda aşağıdaki işlemleri otomatik olarak gerçekleştirir:
    - Sistem güncelleme kontrolü ve otomatik güncelleme
    - Sistem dili kontrolü ve gerekirse Türkçe'ye çevirme
    - Swap alanı oluşturma ve yönetimi
    - Gereksiz servislerin kapatılması
    - Logların temizlenmesi
    - UFW güvenlik duvarı kurulumu ve yapılandırması
    - Docker kurulumu ve güncellemesi
    - Docker Compose kurulumu ve güncellemesi
    - Portainer kurulumu ve güncellemesi
    - Netdata kurulumu, güncellemesi ve port ayarları
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

def run(cmd, show_output=True):
    try:
        if show_output:
            # Çıktıyı ekranda göster
            result = subprocess.run(cmd, shell=True, text=True, timeout=300)
            return result
        else:
            # Çıktıyı gizle (sadece return code için)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
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
    result = run("apt update -y", show_output=True)
    if result.returncode != 0:
        print_title("Güncelleme hatası, yeniden deneniyor")
        run("rm -rf /var/lib/apt/lists/*", show_output=False)
        run("apt update -y", show_output=True)
    
    result = run("apt list --upgradable 2>/dev/null | wc -l", show_output=False)
    if result.returncode == 0 and int(result.stdout.strip()) > 1:
        print_title("Güncelleme mevcut, sistem güncelleniyor")
        run("apt upgrade -y", show_output=True)
        run("apt autoremove -y && apt autoclean -y", show_output=True)
        print_title("Sistem güncellemesi tamamlandı ve kuruldu")
    else:
        print_title("Sistem zaten güncel")

def set_locale_tr():
    print_title("Sistem dili kontrol ediliyor")
    locale_result = run("locale | grep LANG=", show_output=False)
    if "tr_TR.UTF-8" not in locale_result.stdout:
        print_title("Sistem dili Türkçe değil, Türkçe'ye geçiriliyor")
        run("apt install -y language-pack-tr", show_output=True)
        run("locale-gen tr_TR.UTF-8", show_output=True)
        run("update-locale LANG=tr_TR.UTF-8", show_output=True)
        run("localectl set-locale LANG=tr_TR.UTF-8", show_output=True)
        run("timedatectl set-timezone Europe/Istanbul", show_output=True)
        print_title("Türkçe locale ayarlandı ve kuruldu")
    else:
        print_title("Sistem dili zaten Türkçe")

def install_zram():
    print_title("ZRAM kurulumu kontrol ediliyor")
    
    # Önce mevcut swap'ı kontrol et
    swap_result = run("swapon --show", show_output=False)
    if "zram" in swap_result.stdout:
        print_title("ZRAM zaten kurulu")
        return
    
    # ZRAM kurulumu
    result = run("apt install -y zram-config", show_output=True)
    
    if result.returncode != 0:
        print_title("ZRAM-config kurulamadı, alternatif yöntem deneniyor")
        run("apt install -y zram-tools", show_output=True)
    
    # ZRAM servisini başlat
    run("systemctl enable zram-config.service 2>/dev/null || systemctl enable zramswap.service 2>/dev/null || true", show_output=False)
    run("systemctl start zram-config.service 2>/dev/null || systemctl start zramswap.service 2>/dev/null || true", show_output=False)
    
    time.sleep(3)
    status = run("swapon --show | grep zram", show_output=False)
    if status.returncode == 0:
        print_title("ZRAM başarıyla kuruldu")
        print(f"ZRAM durumu: {status.stdout.strip()}")
    else:
        print_title("ZRAM kurulumu başarısız, standart swap kullanılacak")
        create_swap(2)

def create_swap(size_gb=2):
    swap_file = "/swapfile"
    if os.path.exists(swap_file):
        run("swapoff /swapfile 2>/dev/null", show_output=False)
        run(f"rm -f {swap_file}", show_output=False)
        print_title("Mevcut swap alanı kaldırıldı")
    
    # Swap dosyası oluştur
    result = run(f"dd if=/dev/zero of={swap_file} bs=1M count={size_gb * 1024} status=progress", show_output=True)
    if result.returncode != 0:
        print_title("Swap dosyası oluşturulamadı")
        return
    
    run(f"chmod 600 {swap_file}", show_output=True)
    run(f"mkswap {swap_file}", show_output=True)
    run(f"swapon {swap_file}", show_output=True)
    
    # fstab'a ekle
    with open("/etc/fstab", "r") as f:
        fstab_content = f.read()
    
    if "/swapfile" not in fstab_content:
        with open("/etc/fstab", "a") as f:
            f.write(f"{swap_file} none swap sw 0 0\n")
    
    print_title(f"{size_gb}GB swap alanı oluşturuldu")
    run("swapon --show", show_output=True)

def optimize_services():
    services = [
        "snapd", "cups", "bluetooth", "modemmanager", 
        "avahi-daemon", "whoopsie", "rpcbind", "apport"
    ]
    
    for service in services:
        run(f"systemctl stop {service} 2>/dev/null || true", show_output=False)
        run(f"systemctl disable {service} 2>/dev/null || true", show_output=False)
        print_title(f"{service} servisi durduruldu ve devre dışı bırakıldı")
    
    run("systemctl daemon-reload", show_output=False)
    print_title("Gereksiz servisler devre dışı bırakıldı")

def clean_journal():
    run("journalctl --vacuum-time=7d", show_output=True)
    run("journalctl --vacuum-size=100M", show_output=True)
    print_title("Sistem logları temizlendi")

def security_ufw():
    print_title("UFW güvenlik duvarı kontrolü")
    
    # UFW kurulu mu?
    ufw_check = run("which ufw", show_output=False)
    if ufw_check.returncode != 0:
        print_title("UFW kurulu değil, kuruluyor")
        run("apt install -y ufw", show_output=True)
    
    # UFW durumu
    status = run("ufw status", show_output=False)
    if "inactive" in status.stdout:
        print_title("UFW aktif değil, yapılandırılıyor")
        run("ufw allow OpenSSH", show_output=True)
        run("ufw allow 22/tcp", show_output=True)
        run("echo 'y' | ufw enable", show_output=True)
        print_title("UFW aktif edildi")
    else:
        print_title("UFW zaten aktif")

def install_docker():
    print_title("Docker kurulumu kontrolü")
    
    # Docker zaten çalışıyor mu?
    docker_check = run("docker --version", show_output=False)
    service_active = check_service("docker")
    
    if docker_check.returncode == 0 and service_active:
        print_title("Docker zaten kurulu ve çalışıyor - güncellemeler kontrol ediliyor")
        
        # Docker repository'sini ekleyip güncellemeleri kontrol et
        run("apt install -y ca-certificates curl gnupg lsb-release", show_output=True)
        
        # Docker GPG anahtarını kontrol et, varsa üzerine yazma
        if not os.path.exists("/etc/apt/keyrings/docker.gpg"):
            run("mkdir -p /etc/apt/keyrings", show_output=True)
            run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg", show_output=True)
        
        # Repository ekle (varsa üzerine yazma)
        if not os.path.exists("/etc/apt/sources.list.d/docker.list"):
            run('echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list', show_output=True)
        
        run("apt update -y", show_output=True)
        
        # Docker güncellemelerini kontrol et
        result = run("apt list --upgradable 2>/dev/null | grep docker || true", show_output=False)
        if "docker" in result.stdout:
            print_title("Docker güncellemeleri yükleniyor")
            run("apt upgrade -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin", show_output=True)
            run("systemctl restart docker", show_output=True)
            print_title("Docker güncellemeleri tamamlandı")
        else:
            print_title("Docker zaten güncel")
        return
    
    elif docker_check.returncode == 0 and not service_active:
        print_title("Docker kurulu ama servis çalışmıyor - servis başlatılıyor")
        run("systemctl start docker", show_output=True)
        run("systemctl enable docker", show_output=True)
        
        if check_service("docker"):
            print_title("Docker servisi başlatıldı")
        else:
            print_title("Docker servisi başlatılamadı, yeniden kurulacak")
            # Servis başlatılamazsa yeniden kur
            run("apt remove -y docker docker-engine docker.io containerd runc", show_output=True)
            run("apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin", show_output=True)
    
    else:
        print_title("Docker kurulu değil, kuruluyor...")
        
        # Gerekli paketler
        run("apt install -y ca-certificates curl gnupg lsb-release", show_output=True)
        
        # Docker GPG anahtarı
        run("mkdir -p /etc/apt/keyrings", show_output=True)
        run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg", show_output=True)
        
        # Repository ekle
        run('echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list', show_output=True)
        
        # Güncelle ve kur
        run("apt update -y", show_output=True)
        run("apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin", show_output=True)
    
    # Docker servisini başlat
    run("systemctl enable docker", show_output=True)
    run("systemctl start docker", show_output=True)
    
    # Docker grubuna kullanıcı ekle (opsiyonel)
    run("usermod -aG docker $SUDO_USER 2>/dev/null || true", show_output=False)
    
    time.sleep(3)
    if check_service("docker"):
        print_title("Docker başarıyla kuruldu/güncellendi")
    else:
        print_title("Docker kurulumunda hata")

def install_docker_compose():
    print_title("Docker Compose kontrolü")
    
    # Docker Compose v2 kontrolü (plugin)
    compose_v2_check = run("docker compose version", show_output=False)
    if compose_v2_check.returncode == 0:
        print_title("Docker Compose Plugin zaten kurulu")
        return
    
    # Standalone Docker Compose v1 kontrolü
    compose_v1_check = run("docker-compose --version", show_output=False)
    if compose_v1_check.returncode == 0:
        print_title("Docker Compose v1 kurulu, v2 plugin kuruluyor")
        # v1'i kaldırmaya gerek yok, sadece v2 plugin'ini kur
        run("apt install -y docker-compose-plugin", show_output=True)
        print_title("Docker Compose Plugin kuruldu")
        return
    
    print_title("Docker Compose Plugin kuruluyor")
    run("apt install -y docker-compose-plugin", show_output=True)
    print_title("Docker Compose Plugin kuruldu")

def install_portainer():
    print_title("Portainer kontrolü")
    
    # Portainer çalışıyor mu?
    portainer_check = run("docker ps | grep portainer", show_output=False)
    if portainer_check.returncode == 0:
        print_title("Portainer zaten çalışıyor - güncelleme kontrolü")
        
        # Mevcut Portainer'ı durdur
        run("docker stop portainer 2>/dev/null || true", show_output=True)
        run("docker rm portainer 2>/dev/null || true", show_output=True)
        
        # En son image'ı çek
        run("docker pull portainer/portainer-ce:latest", show_output=True)
        
        # Yeniden başlat
        run("docker run -d -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest", show_output=True)
        
        print_title("Portainer güncellendi ve yeniden başlatıldı")
        return
    
    print_title("Portainer kuruluyor")
    run("docker volume create portainer_data", show_output=True)
    run("docker run -d -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest", show_output=True)
    
    time.sleep(5)
    if run("docker ps | grep portainer", show_output=False).returncode == 0:
        print_title("Portainer başarıyla kuruldu")
        print_title("Erişim: http://sunucu-ip:9000")
    else:
        print_title("Portainer kurulumunda hata")
def install_netdata():
    print_title("Netdata kontrolü")
    
    netdata_check = run("which netdata", show_output=False)
    if netdata_check.returncode == 0:
        print_title("Netdata zaten kurulu - güncelleme kontrolü")
        # Netdata güncelleme komutu
        run("netdata-updater.sh -f || true", show_output=True)
        print_title("Netdata güncellemesi tamamlandı")
        return
    
    print_title("Netdata kuruluyor")
    
    # Netdata için gerekli paketler
    run("apt install -y curl git", show_output=True)
    
    # Netdata kurulum scripti - resmi dokümantasyondaki güncel yöntem
    run("curl -Ss 'https://raw.githubusercontent.com/netdata/netdata/master/packaging/installer/install-required-packages.sh' --output /tmp/install-required-packages.sh && bash /tmp/install-required-packages.sh -i netdata", show_output=True)
    
    # Alternatif kurulum yöntemi
    run("wget -O /tmp/netdata-kickstart.sh https://my-netdata.io/kickstart.sh && sh /tmp/netdata-kickstart.sh --no-update --stable-channel", show_output=True)
    
    # Temizlik
    run("rm -f /tmp/install-required-packages.sh /tmp/netdata-kickstart.sh", show_output=False)
    
    if check_service("netdata"):
        run("ufw allow 19999/tcp", show_output=True)
        print_title("Netdata kuruldu: http://sunucu-ip:19999")
    else:
        print_title("Netdata kurulumunda hata, alternatif yöntem deneniyor")
        # Son çare olarak paket deposundan kurmayı dene
        run("apt install -y netdata", show_output=True)
        
        if check_service("netdata"):
            run("ufw allow 19999/tcp", show_output=True)
            print_title("Netdata paket deposundan kuruldu: http://sunucu-ip:19999")
        else:
            print_title("Netdata kurulumu tamamen başarısız")
            
def boot_analysis():
    print_title("Boot süresi analizi")
    run("systemd-analyze", show_output=True)
    run("systemd-analyze blame | head -10", show_output=True)
    print_title("Boot analizi tamamlandı")

def hardware_test():
    print_title("Donanım bilgileri")
    run("lscpu | grep -E '^(Model name|CPU\(s\)|Thread|Core)'", show_output=True)
    run("free -h", show_output=True)
    run("df -h | grep -E '^(Filesystem|/dev/)'", show_output=True)
    run("lsblk", show_output=True)
    print_title("Donanım testleri tamamlandı")

def network_test():
    print_title("Ağ bilgileri")
    run("ip addr show | grep -E '^([0-9]+:|inet )'", show_output=True)
    
    # ping komutu yoksa kur
    ping_check = run("which ping", show_output=False)
    if ping_check.returncode != 0:
        run("apt install -y iputils-ping", show_output=True)
    
    # "Server busy" hatasını önlemek için daha kısa ping
    run("ping -c 1 8.8.8.8", show_output=True)
    
    # IP adresi kontrolü (timeout ile)
    try:
        result = run("curl -s --connect-timeout 5 http://ipinfo.io/ip", show_output=False)
        if result.returncode == 0:
            print(f"Genel IP Adresi: {result.stdout.strip()}")
        else:
            print("Genel IP alınamadı (timeout)")
    except:
        print("Genel IP alınamadı")
    
    print_title("Ağ testleri tamamlandı")

def generate_summary():
    print_title("SİSTEM ÖZET RAPORU")
    
    # Sunucu bilgileri
    print("\n\033[1;32m● SUNUCU BİLGİLERİ:\033[0m")
    run("hostnamectl", show_output=True)
    
    # Donanım bilgileri
    print("\n\033[1;32m● DONANIM BİLGİLERİ:\033[0m")
    run("echo 'CPU Bilgisi:' && lscpu | grep -E '^(Model name|CPU\(s\)|Thread|Core)'", show_output=True)
    run("echo 'RAM Bilgisi:' && free -h", show_output=True)
    run("echo 'Disk Bilgisi:' && df -h | grep -E '^(Filesystem|/dev/)'", show_output=True)
    
    # Ağ bilgileri
    print("\n\033[1;32m● AĞ BİLGİLERİ:\033[0m")
    run("echo 'IP Adresleri:' && hostname -I", show_output=True)
    
    try:
        result = run("curl -s --connect-timeout 3 http://ipinfo.io/ip", show_output=False)
        if result.returncode == 0:
            print(f"Genel IP: {result.stdout.strip()}")
        else:
            print("Genel IP: Alınamadı")
    except:
        print("Genel IP: Alınamadı")
    
    # Docker bilgileri
    print("\n\033[1;32m● DOCKER BİLGİLERİ:\033[0m")
    docker_check = run("docker --version", show_output=False)
    if docker_check.returncode == 0:
        run("docker --version", show_output=True)
        run("docker ps", show_output=True)
    else:
        print("Docker kurulu değil")
    
    # Servis bilgileri
    print("\n\033[1;32m● SERVİS DURUMLARI:\033[0m")
    services = ["docker", "ufw"]
    for service in services:
        status = run(f"systemctl is-active {service}", show_output=False)
        if status.returncode == 0:
            print(f"{service}: \033[1;32mÇALIŞIYOR\033[0m")
        else:
            print(f"{service}: \033[1;31mDURDURULMUŞ\033[0m")
    
    # ZRAM kontrolü
    zram_status = run("swapon --show | grep zram", show_output=False)
    if zram_status.returncode == 0:
        print("zram: \033[1;32mAKTİF\033[0m")
    else:
        print("zram: \033[1;31mPASİF\033[0m")
    
    # Port bilgileri
    print("\n\033[1;32m● PORT VE ERİŞİM BİLGİLERİ:\033[0m")
    print("Netdata: \033[1;36mhttp://sunucu-ip:19999\033[0m")
    print("Portainer: \033[1;36mhttp://sunucu-ip:9000\033[0m")
    
    # Güvenlik duvarı durumu
    print("\n\033[1;32m● GÜVENLİK DUVARI KURALLARI:\033[0m")
    run("ufw status", show_output=True)

def main():
    if os.geteuid() != 0:
        print("Bu betiği root olarak çalıştırmalısınız!")
        sys.exit(1)

    print_header()
    
    # Yapılan işlemleri takip etmek için liste
    completed_tasks = []

    menu = [
        ("Sistem güncellemesi", update_system),
        ("Türkçe dil desteği", set_locale_tr),
        ("ZRAM kurulumu", install_zram),
        ("Gereksiz servisleri kapatma", optimize_services),
        ("Logları temizleme", clean_journal),
        ("Güvenlik duvarı (UFW) yapılandırma", security_ufw),
        ("Docker kurulumu", install_docker),
        ("Docker Compose kurulumu", install_docker_compose),
        ("Portainer kurulumu", install_portainer),
        ("Netdata kurulumu", install_netdata),
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
            secimler = list(range(1, len(menu)+1))
            break
        elif secim:
            try:
                secimler = [int(x) for x in secim.split(",") if x.strip().isdigit() and 1 <= int(x) <= len(menu)]
                if secimler:
                    break
                else:
                    print("Geçersiz seçim, tekrar deneyin.")
            except ValueError:
                print("Geçersiz giriş, tekrar deneyin.")
        else:
            print("Lütfen bir seçim yapın.")

    print()
    for idx in secimler:
        try:
            desc, func = menu[idx-1]
            print_title(f"BAŞLIYOR: {desc}")
            func()
            print_title(f"TAMAMLANDI: {desc}")
            completed_tasks.append(f"✓ {desc}")
        except Exception as e:
            error_msg = f"✗ {desc} - Hata: {str(e)}"
            print_title(f"HATA: {error_msg}")
            completed_tasks.append(error_msg)

    # Özet raporu göster
    generate_summary()
    
    # Yapılan işlemleri listele
    print_title("GERÇEKLEŞTİRİLEN İŞLEMLER")
    for task in completed_tasks:
        if task.startswith("✓"):
            print(f"\033[1;32m{task}\033[0m")
        else:
            print(f"\033[1;31m{task}\033[0m")
    
    cevap = input("\nSunucuyu yeniden başlatmak ister misiniz? (e/h): ").strip().lower()
    if cevap == "e":
        print("Sunucu yeniden başlatılıyor...")
        run("reboot", show_output=True)
    else:
        print("İşlemler tamamlandı. Sunucu yeniden başlatılmadı.")

if __name__ == "__main__":

    main()
