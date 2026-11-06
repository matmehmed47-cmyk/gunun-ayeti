package net.gununayeti

import android.app.KeyguardManager
import android.app.WallpaperManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Build
import android.service.wallpaper.WallpaperService
import android.view.SurfaceHolder
import java.io.File

/**
 * Canlı duvar kağıdı: ekran her kapandığında sıradaki fotoğraf hazırlanır; kilit ekranında ayet, esma ve
 * sıradaki vakit üstüne yazılır, kilit açılınca ana ekranda yazısız fotoğraf kalır.
 */
class CanliDuvar : WallpaperService() {
    override fun onCreateEngine(): Engine = Motor()

    inner class Motor : Engine() {
        private var W = 0; private var H = 0
        private var foto: Bitmap? = null; private var fotoAd = ""
        private val alici = object : BroadcastReceiver() {
            override fun onReceive(x: Context, i: Intent) {
                when (i.action) {
                    Intent.ACTION_SCREEN_OFF -> { Ayar.canliSiraArtir(this@CanliDuvar); ciz(true) }
                    Intent.ACTION_USER_PRESENT -> ciz(false)
                }
            }
        }

        override fun onCreate(h: SurfaceHolder) {
            super.onCreate(h)
            val f = IntentFilter().apply { addAction(Intent.ACTION_SCREEN_OFF); addAction(Intent.ACTION_USER_PRESENT) }
            if (Build.VERSION.SDK_INT >= 33) registerReceiver(alici, f, Context.RECEIVER_NOT_EXPORTED) else registerReceiver(alici, f)
            if (!isPreview) {
                Zamanlayici.kur(applicationContext)
                // Eski sabit kilit resmi canlının önünde kalmasın
                if (Ayar.canli(applicationContext)) try { WallpaperManager.getInstance(applicationContext).clear(WallpaperManager.FLAG_LOCK) } catch (_: Exception) {}
            }
        }

        override fun onDestroy() {
            try { unregisterReceiver(alici) } catch (_: Exception) {}
            foto?.recycle(); foto = null
            super.onDestroy()
        }

        override fun onSurfaceChanged(h: SurfaceHolder, format: Int, w: Int, hh: Int) {
            super.onSurfaceChanged(h, format, w, hh); W = w; H = hh; ciz(kilitli())
        }

        override fun onVisibilityChanged(gorunur: Boolean) { if (gorunur) ciz(kilitli()) }

        private fun kilitli() = (getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager).isKeyguardLocked

        private fun simdikiFoto(): Bitmap? {
            val liste = FotoHavuz.dosyalar(this@CanliDuvar)
            val dosya = if (liste.isEmpty()) File(filesDir, "foto.jpg") else liste[Ayar.canliSira(this@CanliDuvar) % liste.size]
            if (dosya.path == fotoAd && foto != null) return foto
            foto?.recycle(); foto = null; fotoAd = dosya.path
            if (!dosya.exists()) return null
            val s = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeFile(dosya.path, s)
            var k = 1; while (s.outHeight / (k * 2) >= H && s.outWidth / (k * 2) >= W) k *= 2
            foto = BitmapFactory.decodeFile(dosya.path, BitmapFactory.Options().apply { inSampleSize = k })
            return foto
        }

        private fun ciz(yazili: Boolean) {
            if (W <= 0 || H <= 0) return
            val cv = try { surfaceHolder.lockCanvas() } catch (e: Exception) { null } ?: return
            try { KilitCizici.ciz(this@CanliDuvar, cv, W, H, simdikiFoto(), yazili) }
            catch (_: Exception) {}
            finally { try { surfaceHolder.unlockCanvasAndPost(cv) } catch (_: Exception) {} }
        }
    }
}
