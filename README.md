# Paribu Cineverse Bilet Takip Sistemi (Ticket Monitor)

Bu proje, Paribu Cineverse web sitesini belirli aralıklarla tarayarak hedef filmin biletleri satışa çıktığında telefonunuza anlık yüksek öncelikli alarm (ntfy) veya mesaj (Telegram) gönderen bir takip mekanizmasıdır.

Home server (ev sunucusu) üzerinde 7/24 çalışacak şekilde optimize edilmiştir.

---

## 🔔 Bildirim Kanalları Kurulumu

Telefonunuzun anlık çalması ve bildirim sesi vermesi için **ntfy** veya **Telegram** kullanabilirsiniz.

### 1. ntfy.sh Kurulumu (Önerilen - Alarm Gibi Çalar)
ntfy (notify), tamamen ücretsiz, kayıt gerektirmeyen ve açık kaynaklı bir push bildirim servisidir.
1. Telefonunuza **ntfy** mobil uygulamasını indirin ([Android Play Store](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS App Store](https://apps.apple.com/us/app/ntfy/id1625396347)).
2. Uygulamayı açın, artı (`+`) butonuna basarak yeni bir başlık (topic) ekleyin. Örneğin: `paribu_spider_man_tickets_91823` (kendinize özgü benzersiz bir isim seçin).
3. Telefonunuzun bildirim ayarlarına giderek bu başlık altındaki bildirimler için özel yüksek sesli bir melodi (alarm sesi) ayarlayabilirsiniz.
4. `.env` dosyasındaki `NTFY_TOPIC` kısmına bu belirlediğiniz başlığı yazın.

### 2. Telegram Bot Kurulumu
1. Telegram'da `@BotFather` botu ile konuşarak `/newbot` komutuyla kendi botunuzu oluşturun. Size verilen `HTTP API Token` değerini kopyalayın.
2. Botunuza Telegram üzerinden `/start` yazarak bir sohbet başlatın.
3. `@userinfobot` botuna mesaj göndererek veya tarayıcınızdan `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates` adresine giderek kendi `chat_id` (kullanıcı ID) değerinizi bulun.
4. `.env` dosyasındaki `TELEGRAM_BOT_TOKEN` ve `TELEGRAM_CHAT_ID` alanlarını doldurun.

---

## 🚀 Kurulum ve Çalıştırma

### 1. Yerel Python ile Çalıştırma
Öncelikle gereksinimleri kurun ve `.env` dosyasını yapılandırın:

```bash
# Gereksinimleri yükleyin
pip install -r requirements.txt

# Örnek konfigürasyon dosyasını kopyalayın
cp .env.example .env
```

`.env` dosyasını düzenleyerek bildirim parametrelerinizi girin. Ardından:

#### A. Sürekli Çalışan Servis (Daemon Modu)
Aşağıdaki komut, betiği belirtilen saniye aralığıyla (varsayılan 5 dk/300 sn) sürekli arka planda çalıştırır:
```bash
python monitor.py
```

#### B. Tek Seferlik Çalıştırma (Cron için)
Sunucunuzun kendi Cronjob sistemini kullanmak isterseniz:
```bash
python monitor.py --once
```
*Örnek Cron tanımlaması (Her 5 dakikada bir çalışması için):*
`*/5 * * * * cd /path/to/ticket-alert && python monitor.py --once >> monitor.log 2>&1`

---

### 2. Docker / Docker Compose ile Çalıştırma (Önerilen)
Home server'ınızda Docker kuruluysa, sistemi izole bir şekilde 7/24 çalıştırmak en temiz yöntemdir.

#### Adım A: Docker Image Oluşturma
Proje dizininde Dockerfile bulunmaktadır. Image oluşturmak için:
```bash
docker build -t ticket-monitor .
```

#### Adım B: Docker Compose ile Başlatma
`docker-compose.yml` dosyasını kullanarak container'ı başlatın:
```bash
docker compose up -d
```
Bu komut, sisteminizi arka planda (`-d` / daemon) başlatır ve `.env` dosyasındaki ayarlara göre takip etmeye başlar.
(Not: Eğer eski sürüm Docker Compose kullanıyorsanız `docker-compose up -d` yazmanız gerekebilir.)

---

## 🛠️ Log Takibi ve Durum Kontrolü

- Betik çalışırken tüm olayları `monitor.log` dosyasına ve terminal çıktısına kaydeder.
- Satış durumu `state.json` dosyasında saklanır. Biletler ilk kez satışa çıktığında bildirim gönderilir ve durum `true` yapılır. Böylece her taramada tekrar tekrar telefonunuza bildirim gönderilip sizi rahatsız etmez.
