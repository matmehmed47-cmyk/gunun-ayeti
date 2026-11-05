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
}

/** Kullanıcının fotoğrafı + bugünün ayeti → kilit ekranı. Web sürümündeki kilitCiz() ile aynı düzen. */
object KilitCizici {
    private fun bugunkuAyet(c: Context): Pair<String, String> {
        val ayar = JSONObject(c.assets.open("www/ayar.json").bufferedReader().readText())
        val liste = JSONArray(c.assets.open("www/sirali.json").bufferedReader().readText())
        val bas = LocalDate.parse(ayar.getString("baslangic"))
        val bugun = LocalDate.now(ZoneId.of("Europe/Istanbul"))
        val gun = maxOf(0L, ChronoUnit.DAYS.between(bas, bugun)).toInt()
        val a = liste.getJSONObject(gun % liste.length())
        val ayetNo = a.getString("ref").substringAfter(':')
        return a.getString("meal") to "${a.getString("sure")} Suresi, $ayetNo. ayet"
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
        val cv = Canvas(bmp)
        val foto = File(c.filesDir, "foto.jpg")
        val im = if (foto.exists()) BitmapFactory.decodeFile(foto.path) else null
        if (im != null) {
            val o = maxOf(W.toFloat() / im.width, H.toFloat() / im.height)
            val w = im.width * o; val h = im.height * o
            cv.drawBitmap(im, null, RectF((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2), Paint(Paint.FILTER_BITMAP_FLAG))
            im.recycle()
        } else {
            val p = Paint().apply { shader = LinearGradient(0f, 0f, 0f, H.toFloat(), Color.rgb(15, 42, 44), Color.rgb(22, 64, 63), Shader.TileMode.CLAMP) }
            cv.drawRect(Rect(0, 0, W, H), p)
        }
        val (meal, ref) = bugunkuAyet(c)
        val gen = (W * 0.8f).toInt()
        val tp = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE; typeface = Typeface.create(Typeface.SERIF, Typeface.BOLD)
            setShadowLayer(W * 0.016f, 0f, 0f, Color.argb(215, 0, 0, 0))
        }
        var fs = W * 0.044f
        var dz: StaticLayout
        while (true) {
            tp.textSize = fs
            dz = StaticLayout.Builder.obtain(meal, 0, meal.length, tp, gen)
                .setAlignment(Layout.Alignment.ALIGN_CENTER).setLineSpacing(0f, 1.25f).build()
            if (dz.height < H * 0.22f || fs < W * 0.028f) break
            fs *= 0.94f
        }
        val rp = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.rgb(241, 214, 153); textSize = fs * 0.72f; textAlign = Paint.Align.CENTER
            typeface = Typeface.create(Typeface.SANS_SERIF, Typeface.BOLD)
            setShadowLayer(W * 0.012f, 0f, 0f, Color.argb(150, 0, 0, 0))
        }
        val blok = dz.height + rp.textSize * 2.2f
        val merkez = if (Ayar.yer(c) == "alt") H * 0.78f else H * 0.52f
        var ust = merkez - blok / 2; val pay = fs * 2.2f
        if (ust + blok > H * 0.86f) ust = H * 0.86f - blok
        val bant = Paint().apply {
            shader = LinearGradient(0f, ust - pay, 0f, ust + blok + pay,
                intArrayOf(Color.argb(0, 0, 0, 0), Color.argb(174, 0, 0, 0), Color.argb(174, 0, 0, 0), Color.argb(0, 0, 0, 0)),
                floatArrayOf(0f, .22f, .78f, 1f), Shader.TileMode.CLAMP)
        }
        cv.drawRect(0f, ust - pay, W.toFloat(), ust + blok + pay, bant)
        cv.save(); cv.translate((W - gen) / 2f, ust); dz.draw(cv); cv.restore()
        cv.drawText(ref, W / 2f, ust + dz.height + rp.textSize * 1.6f, rp)
        return bmp
    }

    fun uygula(c: Context) {
        val bmp = ciz(c)
        val wm = WallpaperManager.getInstance(c)
        wm.setBitmap(bmp, null, true, WallpaperManager.FLAG_LOCK)
        bmp.recycle()
    }
}
