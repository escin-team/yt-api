# 🚀 Deploy ke Hosting Gratis (HF Spaces, Render, Railway)

## Analisis & Solusi untuk Hosting Gratis

Code ini telah dioptimalkan untuk berjalan di **hosting gratis** seperti:
- ✅ Hugging Face Spaces
- ✅ Render.com (Free tier)
- ✅ Railway.app (Free tier)
- ✅ Back4App Containers

### 🔧 Perubahan Utama

#### 1. **TANPA SSL BYPASS**
- Sebelumnya: `verify=False` (disable SSL verification)
- Sekarang: `verify=True` (SSL verification normal)
- **Alasan**: Hosting gratis sudah punya SSL certificate yang valid

#### 2. **TANPA COOKIES FILE**
- Sebelumnya: Menggunakan cookies file dari browser
- Sekarang: Tidak menggunakan cookies (`YTDL_NO_COOKIES=true`)
- **Alasan**: 
  - Cookies file bisa expired dan menyebabkan error
  - YouTube bisa detect dan block IP hosting
  - `tv_embedded` client tidak butuh cookies

#### 3. **Fallback Client yang Lebih Reliable**
- Sebelumnya: `tv > tv_embedded > web_creator > web` (butuh Bun JS runtime)
- Sekarang: `tv_embedded > web > android` (tanpa JS runtime khusus)
- **Alasan**: `tv_embedded` adalah client paling stabil tanpa EJS challenge

#### 4. **Invidious API sebagai Primary**
- Search menggunakan Invidious API sebagai prioritas pertama
- **Keuntungan**: 
  - Public API, tidak perlu autentikasi
  - Tidak rate-limited seperti YouTube direct
  - Fully compatible dengan free hosting

---

## 📋 Cara Deploy

### Opsi 1: Hugging Face Spaces

1. Buat Space baru di https://huggingface.co/spaces
2. Pilih **Docker** sebagai SDK
3. Upload semua file ke repository
4. Tambahkan **Secrets** di Settings:
   ```
   CLOUDINARY_ACCOUNTS_JSON=[{"name":"acc1","cloud_name":"xxx","api_key":"xxx","api_secret":"xxx"}]
   ```
5. Space akan otomatis build dan deploy!

### Opsi 2: Render.com

1. Login ke https://render.com
2. Create New → **Web Service**
3. Connect GitHub repository
4. Settings:
   - **Build Command**: `docker build -t app .`
   - **Start Command**: `docker run -p 7860:7860 app`
   - **Environment Variables**: Copy dari `.env.huggingface`
5. Deploy!

### Opsi 3: Railway.app

1. Login ke https://railway.app
2. New Project → **Deploy from GitHub**
3. Add environment variables dari `.env.huggingface`
4. Railway akan auto-detect Dockerfile dan deploy!

---

## ⚙️ Environment Variables

Copy file `.env.huggingface` atau set variables berikut:

```bash
# WAJIB untuk free hosting
YTDL_NO_COOKIES=true
YTDL_VERIFY_SSL=true
YTDL_CLIENT=tv_embedded

# Cloudinary (opsional tapi disarankan untuk persistensi)
CLOUDINARY_ACCOUNTS_JSON=[]

# Port (HF Spaces wajib 7860)
API_PORT=7860

# Disable Redis (tidak tersedia di free tier)
REDIS_ENABLED=false
```

---

## 🎯 Fitur yang Tetap Berfungsi

| Fitur | Status | Catatan |
|-------|--------|---------|
| Search YouTube | ✅ | Via Invidious API |
| Download Audio | ✅ | tv_embedded client |
| Cloudinary Upload | ✅ | Jika dikonfigurasi |
| MCP Integration | ✅ | stdio mode |
| Rate Limiting | ✅ | In-memory |
| Cache | ✅ | In-memory (non-persistent) |

---

## ⚠️ Limitations Free Hosting

1. **Storage Sementara**: File di `/tmp` akan hilang saat restart
2. **No Persistent Cache**: Redis tidak tersedia di free tier
3. **Rate Limits**: YouTube mungkin limit IP shared hosting
4. **Timeout**: Request > 30 detik mungkin di-kill (HF Spaces)

### Solusi:
- Gunakan Cloudinary untuk persistensi file
- Enable `REDIS_ENABLED=false` (gunakan in-memory cache)
- Set `DOWNLOAD_TIMEOUT=300` (max 5 menit)

---

## 🧪 Testing Lokal

```bash
# Build Docker image
docker build -t yt-api .

# Run dengan env free hosting
docker run --rm -it \
  -p 7860:7860 \
  -e YTDL_NO_COOKIES=true \
  -e YTDL_VERIFY_SSL=true \
  -e YTDL_CLIENT=tv_embedded \
  -e REDIS_ENABLED=false \
  yt-api
```

Test endpoint:
```bash
# Health check
curl http://localhost:7860/health

# Search test
curl "http://localhost:7860/api/v1/search?keyword=lofi+music&limit=5"

# Download test
curl -X POST "http://localhost:7860/api/v1/download/audio?video_id=dQw4w9WgXcQ&format=link"
```

---

## 🆘 Troubleshooting

### Error: "SSL: CERTIFICATE_VERIFY_FAILED"
**Solusi**: Pastikan `YTDL_VERIFY_SSL=true` (default)

### Error: "Sign in to confirm your age"
**Solusi**: Video memang restricted, coba video lain

### Error: "Video unavailable"
**Solusi**: Video sudah dihapus atau private

### Error: "Download failed after 3 attempts"
**Solusi**: 
1. Cek log untuk detail error
2. Coba ganti `YTDL_CLIENT=web` atau `YTDL_CLIENT=android`
3. Pastikan ffmpeg terinstall di container

### Invidious Down
**Solusi**: Scraper akan otomatis fallback ke youtube-search package

---

## 📝 Checklist Sebelum Deploy

- [ ] Set `REDIS_ENABLED=false`
- [ ] Set `YTDL_NO_COOKIES=true`
- [ ] Set `YTDL_VERIFY_SSL=true`
- [ ] Set `YTDL_CLIENT=tv_embedded`
- [ ] Configure Cloudinary accounts (jika ada)
- [ ] Test lokal dengan Docker
- [ ] Verify port 7860 (untuk HF Spaces)

---

## 🎉 Kesimpulan

Code ini sekarang **100% compatible** dengan hosting gratis:
- ✅ Tanpa SSL bypass
- ✅ Tanpa cookies file
- ✅ Tanpa JS runtime khusus (Bun optional)
- ✅ Fallback multi-layer untuk reliability
- ✅ Invidious API sebagai primary search method

Selamat deploy! 🚀
