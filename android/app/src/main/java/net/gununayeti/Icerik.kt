package net.gununayeti

import android.content.Context
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.time.LocalDate
import java.time.ZoneId

/**
 * Kilit ekranına ne yazılacağını siteden öğrenir (kilit.json: 60 günlük ayet, esma, özel gün etiketi, Ramazan bilgisi).
 * Böylece yeni eklemeler uygulamayı güncellemeden gelir. İnternet yoksa son kaydedilen kullanılır.
 */
object Icerik {
    private const val KAYNAK = "https://matmehmed47-cmyk.github.io/gunun-ayeti/kilit.json"
    private val TR = ZoneId.of("Europe/Istanbul")
    private fun dosya(c: Context) = File(c.filesDir, "kilit.json")

    private fun gunler(c: Context): JSONObject? =
        try { JSONObject(dosya(c).readText()).getJSONObject("gunler") } catch (e: Exception) { null }

    /** Bugünün bilgisi: meal, ref, esma, ust, ramazan. Yoksa null (o zaman uygulamanın içindeki liste kullanılır). */
    fun bugun(c: Context): JSONObject? = gunler(c)?.optJSONObject(LocalDate.now(TR).toString())

    /** Veri eskiyse (6 saatten eski ya da birkaç günlük kaldıysa) yeniler. Yenilendiyse true. Arka planda çağrılır. */
    fun gerekirseIndir(c: Context): Boolean {
        val f = dosya(c)
        val g = gunler(c)
        val taze = f.exists() && System.currentTimeMillis() - f.lastModified() < 6 * 3600_000L
        if (taze && g != null && g.has(LocalDate.now(TR).plusDays(3).toString())) return false
        return try {
            val b = URL(KAYNAK + "?r=" + System.currentTimeMillis()).openConnection() as HttpURLConnection
            b.connectTimeout = 15000; b.readTimeout = 15000; b.useCaches = false
            try {
                if (b.responseCode != 200) return false
                val metin = b.inputStream.bufferedReader().readText()
                JSONObject(metin).getJSONObject("gunler") // bozuksa kaydetme
                val eski = if (f.exists()) f.readText() else ""
                f.writeText(metin)
                eski != metin
            } finally { b.disconnect() }
        } catch (e: Exception) { false }
    }
}
