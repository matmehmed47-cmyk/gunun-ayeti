package net.gununayeti

import android.annotation.SuppressLint
import android.app.Activity
import android.app.StatusBarManager
import android.graphics.drawable.Icon
import android.app.WallpaperManager
import android.content.ComponentName
import android.content.ContentValues
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.util.Base64
import android.Manifest
import android.content.pm.PackageManager
import android.webkit.GeolocationPermissions
import android.webkit.JavascriptInterface
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.core.content.FileProvider
import androidx.webkit.WebViewAssetLoader
import java.io.File

/** Web uygulamasını gösterir: önce siteden (her zaman en yeni), internet yoksa telefondaki kopyadan (assets/www).
 *  Kilit ekranı, paylaşma ve kaydetme için köprü sağlar. */
class AnaEkran : Activity() {
    private val SITE = "https://matmehmed47-cmyk.github.io/gunun-ayeti/"
    private val YEREL = "https://appassets.androidplatform.net/assets/www/index.html"
    private var yereleGecti = false
    private lateinit var web: WebView
    private var dosyaSecici: ValueCallback<Array<Uri>>? = null
    private var konumBekleyen: Pair<String, GeolocationPermissions.Callback>? = null

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val yukleyici = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()
        web = WebView(this)
        setContentView(web)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.databaseEnabled = true
        web.settings.setGeolocationEnabled(true)
        web.addJavascriptInterface(Kopru(), "Android")
        web.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(v: WebView, r: WebResourceRequest): WebResourceResponse? =
                yukleyici.shouldInterceptRequest(r.url)
            override fun shouldOverrideUrlLoading(v: WebView, r: WebResourceRequest): Boolean {
                val u = r.url.toString()
                if (r.url.host == "appassets.androidplatform.net" || (u.startsWith(SITE) && !u.endsWith(".apk"))) return false
                startActivity(Intent(Intent.ACTION_VIEW, r.url)); return true
            }
            override fun onReceivedError(v: WebView, r: WebResourceRequest, e: WebResourceError) {
                if (r.isForMainFrame && !yereleGecti) { yereleGecti = true; v.loadUrl(if (intent?.getBooleanExtra("kible", false) == true) "$YEREL#kible" else YEREL) }
            }
        }
        web.webChromeClient = object : WebChromeClient() {
            // Kıble için konum: önce Android izni, sonra sayfaya ver
            override fun onGeolocationPermissionsShowPrompt(origin: String, cb: GeolocationPermissions.Callback) {
                if (checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                    cb.invoke(origin, true, false)
                } else {
                    konumBekleyen = origin to cb
                    requestPermissions(arrayOf(Manifest.permission.ACCESS_COARSE_LOCATION), 8)
                }
            }
            override fun onShowFileChooser(v: WebView, cb: ValueCallback<Array<Uri>>, p: FileChooserParams): Boolean {
                dosyaSecici?.onReceiveValue(null)
                dosyaSecici = cb
                // Sayfa ne istiyorsa onu aç: fotoğraf ya da ezan sesi
                val ses = p.acceptTypes.any { it.startsWith("audio") }
                val i = Intent(Intent.ACTION_GET_CONTENT).setType(if (ses) "audio/*" else "image/*").addCategory(Intent.CATEGORY_OPENABLE)
                startActivityForResult(Intent.createChooser(i, if (ses) "Ezan sesi seç" else "Fotoğraf seç"), 7)
                return true
            }
        }
        val kible = intent?.getBooleanExtra("kible", false) == true
        if (savedInstanceState != null && !kible) web.restoreState(savedInstanceState)
        else web.loadUrl(if (kible) "$SITE#kible" else SITE)
        Zamanlayici.kur(this) // açıksa yarın sabahı tekrar planla
        Thread {
            Vakit.gerekirseIndir(this); Vakit.alarmKur(this); try { Ezan.kur(this) } catch (_: Exception) {}
            // Kilit ekranı bilgisi yenilendiyse (ör. yeni esma satırı) ekranı hemen tazele
            if (Icerik.gerekirseIndir(this) && Ayar.otomatik(this)) try { KilitCizici.uygula(this) } catch (_: Exception) {}
        }.start()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 8) {
            val izin = grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED
            konumBekleyen?.let { (o, cb) -> cb.invoke(o, izin, false) }
            konumBekleyen = null
        }
    }

    /** Uygulama açıkken kıble kutucuğuna basılırsa pusulayı aç. */
    override fun onNewIntent(i: Intent) {
        super.onNewIntent(i); setIntent(i)
        if (i.getBooleanExtra("kible", false)) web.evaluateJavascript("window.kibleAcDis ? kibleAcDis() : (location.hash = 'kible')", null)
    }

    override fun onSaveInstanceState(outState: Bundle) { super.onSaveInstanceState(outState); web.saveState(outState) }

    @Deprecated("Activity API")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 7) {
            val u = data?.data
            dosyaSecici?.onReceiveValue(if (resultCode == RESULT_OK && u != null) arrayOf(u) else null)
            dosyaSecici = null
        }
    }

    @Deprecated("Activity API")
    override fun onBackPressed() { if (web.canGoBack()) web.goBack() else super.onBackPressed() }

    /** Ezan için gereken izinler: bildirim (Durdur düğmesi) ve pil kısıtlamasını kaldırma (bir kez sorulur). */
    private fun ezanIzinleri() = runOnUiThread {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED)
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 9)
        val pm = getSystemService(POWER_SERVICE) as android.os.PowerManager
        val ayar = getSharedPreferences("ezan", MODE_PRIVATE)
        if (!pm.isIgnoringBatteryOptimizations(packageName) && !ayar.getBoolean("pilSoruldu", false)) {
            ayar.edit().putBoolean("pilSoruldu", true).apply()
            try {
                @SuppressLint("BatteryLife")
                val i = Intent(android.provider.Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName"))
                startActivity(i)
                mesaj("Ezanın vaktinde çalması için \"İzin ver\" de.")
            } catch (_: Exception) {}
        }
    }

    private fun mesaj(s: String) = runOnUiThread { Toast.makeText(this, s, Toast.LENGTH_LONG).show() }

    inner class Kopru {
        @JavascriptInterface fun var_mi(): Boolean = true
        /** Telefonda kayıtlı ayarlar: site ile yerel kopya arasında geçişte kaybolmasın diye web bunları geri okur. */
        @JavascriptInterface fun vakitOku(): String = try { File(filesDir, "vakit.json").readText() } catch (e: Exception) { "" }
        @JavascriptInterface fun fotoOku(): String = try { Base64.encodeToString(File(filesDir, "foto.jpg").readBytes(), Base64.NO_WRAP) } catch (e: Exception) { "" }
        @JavascriptInterface fun yerOku(): String = Ayar.yer(this@AnaEkran)
        @JavascriptInterface fun surumKodu(): Long = try {
            val pi = packageManager.getPackageInfo(packageName, 0)
            if (Build.VERSION.SDK_INT >= 28) pi.longVersionCode else @Suppress("DEPRECATION") pi.versionCode.toLong()
        } catch (e: Exception) { 0L }

        /** Kullanıcının fotoğrafı (base64 JPEG). Boş metin = fotoğrafı sil. */
        @JavascriptInterface fun fotoKaydet(b64: String) {
            val f = File(filesDir, "foto.jpg")
            if (b64.isEmpty()) { f.delete(); return }
            f.writeBytes(Base64.decode(b64, Base64.DEFAULT))
        }
        @JavascriptInterface fun yerAyarla(yer: String) = Ayar.yerKoy(this@AnaEkran, yer)
        @JavascriptInterface fun boyutOku(): Int = Ayar.boyut(this@AnaEkran)
        @JavascriptInterface fun boyutAyarla(i: Int) = Ayar.boyutKoy(this@AnaEkran, i)
        // ---- Ezan ----
        @JavascriptInterface fun ezanDurum(): String = Ezan.durum(this@AnaEkran)
        @JavascriptInterface fun ezanAyarla(i: Int, acik: Boolean) { Ezan.acikKoy(this@AnaEkran, i, acik); if (acik) ezanIzinleri() }
        @JavascriptInterface fun ezanSesKaydet(i: Int, b64: String, ad: String): Boolean = try {
            Ezan.sesKaydet(this@AnaEkran, i, Base64.decode(b64, Base64.DEFAULT), ad); true } catch (e: Exception) { false }
        @JavascriptInterface fun ezanSesSil(i: Int) = Ezan.sesSil(this@AnaEkran, i)
        @JavascriptInterface fun ezanDene(i: Int) { ezanIzinleri(); try { Ezan.cal(this@AnaEkran, i, true) } catch (_: Exception) { mesaj("Ses çalınamadı.") } }
        @JavascriptInterface fun ezanDurdur() { try { startService(Intent(this@AnaEkran, EzanServisi::class.java).setAction("DURDUR")) } catch (_: Exception) {} }
        /** Şehrin vakit verisi (vakitler/<id>.json içeriği). Boş = şehir kaldırıldı. */
        @JavascriptInterface fun vakitKaydet(json: String) {
            Vakit.kaydet(this@AnaEkran, json); Vakit.alarmKur(this@AnaEkran); try { Ezan.kur(this@AnaEkran) } catch (_: Exception) {}
            if (Ayar.otomatik(this@AnaEkran)) try { KilitCizici.uygula(this@AnaEkran) } catch (_: Exception) {}
        }
        @JavascriptInterface fun otomatik(): Boolean = Ayar.otomatik(this@AnaEkran)
        @JavascriptInterface fun otomatikAyarla(acik: Boolean) {
            Ayar.otomatikKoy(this@AnaEkran, acik)
            Zamanlayici.kur(this@AnaEkran)
            Vakit.alarmKur(this@AnaEkran)
        }
        /** Hemen kilit ekranına uygular; sonucu metin döner. */
        /** Canlı duvar kağıdı: açık mı (seçili ve telefonda gerçekten kurulu) */
        @JavascriptInterface fun canliMi(): Boolean = Ayar.canli(this@AnaEkran) &&
            WallpaperManager.getInstance(this@AnaEkran).wallpaperInfo?.packageName == packageName
        /** Fotoğrafları indir, sonra telefonun "duvar kağıdı olarak ayarla" ekranını aç. */
        @JavascriptInterface fun canliAc() {
            Ayar.canliKoy(this@AnaEkran, true); Zamanlayici.kur(this@AnaEkran)
            mesaj("Fotoğraflar hazırlanıyor, biraz bekle…")
            Thread {
                try { FotoHavuz.yenile(this@AnaEkran, true) } catch (_: Exception) {}
                runOnUiThread {
                    try {
                        startActivity(Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER)
                            .putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT, ComponentName(this@AnaEkran, CanliDuvar::class.java)))
                    } catch (e: Exception) {
                        try { startActivity(Intent(WallpaperManager.ACTION_LIVE_WALLPAPER_CHOOSER)) } catch (_: Exception) { mesaj("Bu telefon canlı duvar kağıdını desteklemiyor.") }
                    }
                }
            }.start()
        }
        /** Kendi fotoğrafına dön: canlıyı kapat, kilit ekranına sabit resmi koy. */
        @JavascriptInterface fun canliKapat(): String = try {
            Ayar.canliKoy(this@AnaEkran, false)
            Ayar.otomatikKoy(this@AnaEkran, true); Zamanlayici.kur(this@AnaEkran); Vakit.alarmKur(this@AnaEkran)
            KilitCizici.uygula(this@AnaEkran)
            mesaj("Kilit ekranında artık kendi fotoğrafın var. Ana ekranı telefon ayarlarından değiştirebilirsin.")
            "tamam"
        } catch (e: Exception) { "hata: " + (e.message ?: e.javaClass.simpleName) }

        /** Bildirim paneline Kıble kutucuğunu ekle (Android 13+ telefon kendisi sorar). */
        @JavascriptInterface fun kutucukEkle(): Boolean {
            if (Build.VERSION.SDK_INT < 33) return false
            val sb = getSystemService(StatusBarManager::class.java)
            runOnUiThread {
                sb.requestAddTileService(ComponentName(this@AnaEkran, KibleKutucuk::class.java), "Kıble",
                    Icon.createWithResource(this@AnaEkran, R.drawable.ic_kible), mainExecutor) { s ->
                    if (s == StatusBarManager.TILE_ADD_REQUEST_RESULT_TILE_ADDED || s == StatusBarManager.TILE_ADD_REQUEST_RESULT_TILE_ALREADY_ADDED)
                        mesaj("Kıble kutucuğu bildirim panelinde.")
                }
            }
            return true
        }

        @JavascriptInterface fun simdiUygula(): String = try {
            KilitCizici.uygula(this@AnaEkran); "tamam"
        } catch (e: Exception) { "hata: " + (e.message ?: e.javaClass.simpleName) }

        @JavascriptInterface fun paylas(b64: String, metin: String) {
            val dir = File(cacheDir, "paylas").apply { mkdirs() }
            val f = File(dir, "gunun-ayeti.png").apply { writeBytes(Base64.decode(b64, Base64.DEFAULT)) }
            val uri = FileProvider.getUriForFile(this@AnaEkran, "net.gununayeti.dosya", f)
            val i = Intent(Intent.ACTION_SEND).setType("image/png")
                .putExtra(Intent.EXTRA_STREAM, uri).putExtra(Intent.EXTRA_TEXT, metin)
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            runOnUiThread { startActivity(Intent.createChooser(i, "Paylaş")) }
        }
        @JavascriptInterface fun kaydet(b64: String, ad: String) {
            try {
                val bytes = Base64.decode(b64, Base64.DEFAULT)
                if (Build.VERSION.SDK_INT >= 29) {
                    val cv = ContentValues().apply {
                        put(MediaStore.Images.Media.DISPLAY_NAME, ad)
                        put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
                        put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/Günün Ayeti")
                    }
                    val u = contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cv)!!
                    contentResolver.openOutputStream(u)!!.use { it.write(bytes) }
                } else {
                    val d = File(getExternalFilesDir(Environment.DIRECTORY_PICTURES), ad); d.writeBytes(bytes)
                }
                mesaj("Galeriye kaydedildi")
            } catch (e: Exception) { mesaj("Kaydedilemedi: " + e.message) }
        }
    }
}
