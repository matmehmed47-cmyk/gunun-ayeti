package net.gununayeti

import android.app.WallpaperManager
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface
import android.os.Build
import android.text.Layout
import android.text.StaticLayout
import android.text.TextPaint
import android.util.DisplayMetrics
import android.view.WindowManager
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDate
import java.time.ZoneId
import java.time.temporal.ChronoUnit

object Ayar {
    private fun p(c: Context) = c.getSharedPreferences("ga", Context.MODE_PRIVATE)
    fun otomatik(c: Context) = p(c).getBoolean("otomatik", false)
    fun otomatikKoy(c: Context, v: Boolean) = p(c).edit().putBoolean("otomatik", v).apply()
    fun yer(c: Context) = p(c).getString("yer", "alt") ?: "alt"
    fun yerKoy(c: Context, v: String) = p(c).edit().putString("yer", v).apply()
    /** Canlı duvar kağıdı seçildi mi (seçiliyse sabit kilit resmi konmaz). */
    fun canli(c: Context) = p(c).getBoolean("canli", false)
    fun canliKoy(c: Context, v: Boolean) = p(c).edit().putBoolean("canli", v).apply()
    fun canliSira(c: Context) = p(c).getInt("canliSira", 0)
    fun canliSiraArtir(c: Context) = p(c).edit().putInt("canliSira", canliSira(c) + 1).apply()
    /** Yazı büyüklüğü: 0 Normal, 1 Büyük, 2 Çok büyük, 3 En büyük, 4 Dev. Sadece yazılar büyür, fotoğraf aynı kalır. */
    fun boyut(c: Context) = p(c).getInt("boyut", 0).coerceIn(0, 4)
    fun boyutKoy(c: Context, v: Int) = p(c).edit().putInt("boyut", v.coerceIn(0, 4)).apply()
    fun boyutKat(c: Context) = floatArrayOf(1f, 1.25f, 1.5f, 1.75f, 2f)[boyut(c)]
}

/** Kullanıcının fotoğrafı + bugünün ayeti → kilit ekranı. Web sürümündeki kilitCiz() ile aynı düzen. */
object KilitCizici {
    /** Bugün: (meal, ref, esma, ust etiketi, ramazan mı). Önce siteden gelen bilgi, yoksa uygulamanın içindeki liste. */
    private data class Gun(val meal: String, val ref: String, val esma: String, val ust: String, val ramazan: Boolean)

    private fun bugunku(c: Context): Gun {
        Icerik.bugun(c)?.let { g ->
            if (g.optString("meal").isNotEmpty())
                return Gun(g.getString("meal"), g.optString("ref"), g.optString("esma"), g.optString("ust"), g.optBoolean("ramazan"))
        }
        val ayar = JSONObject(c.assets.open("www/ayar.json").bufferedReader().readText())
        val liste = JSONArray(c.assets.open("www/sirali.json").bufferedReader().readText())
        val bas = LocalDate.parse(ayar.getString("baslangic"))
        val bugun = LocalDate.now(ZoneId.of("Europe/Istanbul"))
        val gun = maxOf(0L, ChronoUnit.DAYS.between(bas, bugun)).toInt()
        val a = liste.getJSONObject(gun % liste.length())
        val ayetNo = a.getString("ref").substringAfter(':')
        return Gun(a.getString("meal"), "${a.getString("sure")} Suresi, $ayetNo. ayet", "", "", false)
    }

    private fun ekranBoyu(c: Context): Pair<Int, Int> {
        val wm = c.getSystemService(Context.WINDOW_SERVICE) as WindowManager
        val (w, h) = if (Build.VERSION.SDK_INT >= 30) {
            val b = wm.maximumWindowMetrics.bounds; b.width() to b.height()
        } else {
            val m = DisplayMetrics(); @Suppress("DEPRECATION") wm.defaultDisplay.getRealMetrics(m); m.widthPixels to m.heightPixels
        }
        var W = minOf(w, h); var H = maxOf(w, h)
        if (W <= 0 || H <= 0) { W = 1080; H = 2340 }
        if (W > 1440) { H = H * 1440 / W; W = 1440 }
        return W to H
    }

    fun ciz(c: Context): Bitmap {
        val (W, H) = ekranBoyu(c)
        val bmp = Bitmap.createBitmap(W, H, Bitmap.Config.ARGB_8888)
        val foto = File(c.filesDir, "foto.jpg")
        val im = if (foto.exists()) BitmapFactory.decodeFile(foto.path) else null
        ciz(c, Canvas(bmp), W, H, im, true)
        im?.recycle()
        return bmp
    }

    /** Fotoğrafı tuvale yerleştirir; yazili ise ayet, esma ve vakti üstüne yazar (canlı duvar kağıdı da bunu kullanır). */
    fun ciz(c: Context, cv: Canvas, W: Int, H: Int, im: Bitmap?, yazili: Boolean) {
        if (im != null) {
            val o = maxOf(W.toFloat() / im.width, H.toFloat() / im.height)
            val w = im.width * o; val h = im.height * o
            cv.drawColor(Color.BLACK)
            cv.drawBitmap(im, null, RectF((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2), Paint(Paint.FILTER_BITMAP_FLAG))
        } else {
            val p = Paint().apply { shader = LinearGradient(0f, 0f, 0f, H.toFloat(), Color.rgb(15, 42, 44), Color.rgb(22, 64, 63), Shader.TileMode.CLAMP) }
            cv.drawRect(Rect(0, 0, W, H), p)
        }
        if (!yazili) return
        val gun = bugunku(c); val meal = gun.meal; val ref = gun.ref
        val gen = (W * 0.8f).toInt()
        val k = Ayar.boyutKat(c)
        val tp = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE; typeface = Typeface.create(Typeface.SERIF, Typeface.BOLD)
            setShadowLayer(W * 0.016f, 0f, 0f, Color.argb(215, 0, 0, 0))
        }
        // Uzun ayette yazı küçülür ama seçilen boyutun çok altına inmez; gerekirse blok daha çok yer kaplar.
        var fs = W * 0.044f * k
        val taban = W * 0.044f * k * (if (k > 1f) 0.75f else 0.636f)
        val sinir = H * minOf(0.5f, 0.22f * k)
        var dz: StaticLayout
        while (true) {
            tp.textSize = fs
            dz = StaticLayout.Builder.obtain(meal, 0, meal.length, tp, gen)
                .setAlignment(Layout.Alignment.ALIGN_CENTER).setLineSpacing(0f, 1.25f).build()
            if (dz.height < sinir || (fs <= taban && dz.height + fs * 4 < H * 0.66f) || fs < W * 0.02f) break
            fs *= 0.94f
        }
        val rp = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
            // Küçük satırlar (sure, esma, vakit) uzun ayette bile seçilen boyutta kalsın
            color = Color.rgb(241, 214, 153); textSize = if (k > 1f) maxOf(fs * 0.72f, W * 0.044f * k * 0.72f * 0.9f) else fs * 0.72f; textAlign = Paint.Align.CENTER
            typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
            setShadowLayer(W * 0.012f, 0f, 0f, Color.argb(150, 0, 0, 0))
        }
        val vakit = if (gun.ramazan) Vakit.ramazanSatiri(c) else Vakit.siradaki(c)?.let { "${it.first} ${it.second}" }
        val vp = TextPaint(rp).apply { textSize = rp.textSize * 0.92f; typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.NORMAL) }
        val ep = TextPaint(vp).apply { color = Color.argb(235, 255, 255, 255); typeface = Typeface.create(Typeface.SERIF, Typeface.NORMAL) }
        val esma = gun.esma.ifEmpty { null }; val ustYazi = gun.ust.ifEmpty { null }
        // Esma sığmıyorsa küçültmek yerine iki satıra böl: ad / anlam
        val esSat = when {
            esma == null -> emptyList()
            ep.measureText(esma) > W * 0.9f / 0.85f && esma.contains(" · ") -> esma.split(" · ")
            else -> listOf(esma)
        }
        val ustPay = if (ustYazi != null) rp.textSize * 1.8f else 0f
        val blok = ustPay + dz.height + rp.textSize * 2.2f + esSat.size * vp.textSize * 1.5f + (if (vakit != null) vp.textSize * 1.5f else 0f)
        val merkez = if (Ayar.yer(c) == "alt") H * 0.78f else H * 0.52f
        var ust = merkez - blok / 2; val pay = fs * 2.2f
        if (ust + blok > H * 0.86f) ust = H * 0.86f - blok
        if (ust < H * 0.2f) ust = H * 0.2f // saatin olduğu üst bölgeye çıkmasın
        val bant = Paint().apply {
            shader = LinearGradient(0f, ust - pay, 0f, ust + blok + pay,
                intArrayOf(Color.argb(0, 0, 0, 0), Color.argb(174, 0, 0, 0), Color.argb(174, 0, 0, 0), Color.argb(0, 0, 0, 0)),
                floatArrayOf(0f, .22f, .78f, 1f), Shader.TileMode.CLAMP)
        }
        cv.drawRect(0f, ust - pay, W.toFloat(), ust + blok + pay, bant)
        if (ustYazi != null) cv.drawText(ustYazi, W / 2f, ust + rp.textSize, rp)
        val my = ust + ustPay
        cv.save(); cv.translate((W - gen) / 2f, my); dz.draw(cv); cv.restore()
        var sy = my + dz.height + rp.textSize * 1.6f
        cv.drawText(ref, W / 2f, sy, rp)
        for (e in esSat) { sy += vp.textSize * 1.5f; val ek = TextPaint(ep); while (ek.measureText(e) > W * 0.9f && ek.textSize > 8f) ek.textSize *= 0.95f; cv.drawText(e, W / 2f, sy, ek) }
        if (vakit != null) { sy += vp.textSize * 1.5f; val vk = TextPaint(vp); while (vk.measureText(vakit) > W * 0.9f && vk.textSize > 8f) vk.textSize *= 0.95f; cv.drawText(vakit, W / 2f, sy, vk) }
    }

    fun uygula(c: Context) {
        if (Ayar.canli(c)) return // canlı duvar kağıdı kendi çiziyor
        val bmp = ciz(c)
        val wm = WallpaperManager.getInstance(c)
        wm.setBitmap(bmp, null, true, WallpaperManager.FLAG_LOCK)
        bmp.recycle()
    }
}
