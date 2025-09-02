Ubuntu Server Bakım ve Kurulum Betiği
Bu betik, Ubuntu sunucularınız için bakım, optimizasyon ve temel servis kurulumlarını otomatikleştiren kapsamlı bir araçtır.

🚀 Özellikler
Sistem Güncelleme: Otomatik paket güncelleme ve yükseltme

Türkçe Dil Desteği: Sistem dilini Türkçe'ye çevirme ve saat dilimi ayarlama

Bellek Optimizasyonu: ZRAM ve swap alanı yönetimi

Servis Optimizasyonu: Gereksiz servisleri devre dışı bırakma

Güvenlik: UFW güvenlik duvarı yapılandırması

Konteyner Desteği: Docker, Docker Compose ve Portainer kurulumu

İzleme: Netdata ile sistem izleme

Analiz: Boot süresi analizi ve performans testleri

📋 Ön Koşullar
Ubuntu 22.04 LTS (diğer sürümlerde test edilmemiştir)

Root erişimi

İnternet bağlantısı

🛠️ Kurulum
Betiği indirin:

bash
wget https://raw.githubusercontent.com/blackcode06/ubuntu/start.py
Çalıştırma izni verin:

bash
chmod +x start.py
Betiği çalıştırın:

bash
sudo ./start.py

📝 Kullanım
Betik çalıştırıldığında interaktif bir menü sunar:

Tüm işlemleri otomatik olarak yapmak için 0 seçeneğini seçin

Belirli işlemleri yapmak için virgülle ayırarak numaraları girin (örn: 1,3,5)

Mevcut İşlemler:
Sistem güncellemesi

Türkçe dil desteği

ZRAM kurulumu

Gereksiz servisleri kapatma

Logları temizleme

Güvenlik duvarı (UFW) yapılandırma

Docker kurulumu

Docker Compose kurulumu

Portainer kurulumu

Netdata kurulumu

Boot analizi

Donanım testleri

Ağ testleri

🔧 Kurulan Servisler ve Erişim
Portainer: http://sunucu-ip:9000

Netdata: http://sunucu-ip:19999

Docker: Otomatik kurulum ve yapılandırma

📊 Sistem Gereksinimleri
Minimum: 1GB RAM, 10GB disk alanı

Önerilen: 2GB+ RAM, 20GB+ disk alanı

⚠️ Uyarılar
Betik root yetkisi gerektirir

Üretim sunucularında çalıştırmadan önce test ortamında deneyin

Bazı işlemler sunucuyu yeniden başlatma gerektirebilir

🔄 Güncellemeler
Sürüm 1.3 (2 Eylül 2025):

Hata düzeltmeleri ve iyileştirmeler

Netdata kurulum scripti güncellendi

Docker kurulum süreci optimize edildi

🤝 Katkıda Bulunma
Hata raporları ve özellik istekleri için GitHub Issues kullanın.

Bu depoyu fork edin

📜 Lisans
Bu proje MIT lisansı altında lisanslanmıştır. Detaylı bilgi için LICENSE dosyasına bakın.

📞 Destek
Sorularınız veya problemleriniz için:

GitHub Issues: Hata Bildirimi

Not: Bu betik özgür yazılımdır ve hiçbir garantisi yoktur. Kullanmadan önce yedek almanız önerilir. Kullananın kendi sorumluluğundadır. doğacak sorunlardan blackcode06 sorumlu değildir.
