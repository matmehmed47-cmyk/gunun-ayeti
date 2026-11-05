package net.gununayeti

import android.annotation.SuppressLint
import android.app.Activity
import android.content.ContentValues
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.util.Base64
import android.webkit.JavascriptInterface
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.core.content.FileProvider
import androidx.webkit.WebViewAssetLoader
import java.io.File

/** Web uygulamasını (assets/www) gösterir; kilit ekranı, paylaşma ve kaydetme için köprü sağlar. */
class AnaEkran : Activity() {
    private lateinit var web: WebView
    private var dosyaSecici: ValueCallback<Array<Uri>>? = null

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
        web.addJavascriptInterface(Kopru(), "Android")
        web.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(v: WebView, r: WebResourceRequest): WebResourceResponse? =
                yukleyici.shouldInterceptRequest(r.url)
            override fun shouldOverrideUrlLoading(v: WebView, r: WebResourceRequest): Boolean {
                if (r.url.host == "appassets.androidplatform.net") return false
                startActivity(Intent(Intent.ACTION_VIEW, r.url)); return true
            }
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(v: WebView, cb: ValueCallback<Array<Uri>>, p: FileChooserParams): Boolean {
                dosyaSecici?.onReceiveValue(null)
                dosyaSecici = cb
                val i = Intent(Intent.ACTION_GET_CONTENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE)
                startActivityForResult(Intent.createChooser(i, "Fotoğraf seç"), 7)
                return true
            }
        }
        if (savedInstanceState != null) web.restoreState(savedInstanceState)
        else web.loadUrl("https://appassets.androidplatform.net/assets/www/index.html")
        Zamanlayici.kur(this) // açıksa yarın sabahı tekrar planla
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

    private fun mesaj(s: String) = runOnUiThread { Toast.makeText(this, s, Toast.LENGTH_LONG).show() }

    inner class Kopru {
        @JavascriptInterface fun var_mi(): Boolean = true

        /** Kullanıcının fotoğrafı (base64 JPEG). Boş metin = fotoğrafı sil. */
        @JavascriptInterface fun fotoKaydet(b64: String) {
            val f = File(filesDir, "foto.jpg")
            if (b64.isEmpty()) { f.delete(); return }
            f.writeBytes(Base64.decode(b64, Base64.DEFAULT))
        }
        @JavascriptInterface fun yerAyarla(yer: String) = Ayar.yerKoy(this@AnaEkran, yer)
        @JavascriptInterface fun otomatik(): Boolean = Ayar.otomatik(this@AnaEkran)
        @JavascriptInterface fun otomatikAyarla(acik: Boolean) {
            Ayar.otomatikKoy(this@AnaEkran, acik)
            Zamanlayici.kur(this@AnaEkran)
        }
        /** Hemen kilit ekranına uygular; sonucu metin döner. */
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
