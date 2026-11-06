package net.gununayeti

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.ZoneId

/** Diyanet namaz vakitleri: telefonda filesDir/vakit.json olarak saklanır (web uygulaması ya da indir() yazar). */
object Vakit {
    val ADLAR = arrayOf("İmsak", "Güneş", "Öğle", "İkindi", "Akşam", "Yatsı")
    private const val KAYNAK = "https://matmehmed47-cmyk.github.io/gunun-ayeti/vakitler/"
    private val TR = ZoneId.of("Europe/Istanbul")
    private fun dosya(c: Context) = File(c.filesDir, "vakit.json")

    fun kaydet(c: Context, json: String) {
        if (json.isEmpty()) { dosya(c).delete(); return }
        JSONObject(json) // bozuksa hata versin
        dosya(c).writeText(json)
    }

    private fun oku(c: Context): JSONObject? = try { JSONObject(dosya(c).readText()) } catch (e: Exception) { null }

    /** Kayıtlı şehrin vakitlerini sunucudan yeniler (arka planda çağrılır). */
    fun indir(c: Context) {
        val id = oku(c)?.optString("id") ?: return
        val b = URL("$KAYNAK$id.json").openConnection() as HttpURLConnection
        b.connectTimeout = 15000; b.readTimeout = 15000
        try { if (b.responseCode == 200) kaydet(c, b.inputStream.bufferedReader().readText()) } finally { b.disconnect() }
    }

    /** Birkaç günlük veri kaldıysa yenile. */
    fun gerekirseIndir(c: Context) {
        val g = oku(c)?.optJSONObject("gunler") ?: return
        if (!g.has(LocalDate.now(TR).plusDays(5).toString())) try { indir(c) } catch (_: Exception) {}
    }

    /** Sıradaki vakit: (ad, "HH:MM", ne zaman). Veri yoksa null. */
    fun siradaki(c: Context): Triple<String, String, LocalDateTime>? {
        val g = oku(c)?.optJSONObject("gunler") ?: return null
        val simdi = LocalDateTime.now(TR)
        for (ek in 0..1) {
            val gun = simdi.toLocalDate().plusDays(ek.toLong())
            val dz = g.optJSONArray(gun.toString()) ?: continue
            for (i in 0 until minOf(6, dz.length())) {
                val t = gun.atTime(LocalTime.parse(dz.getString(i)))
                if (t.isAfter(simdi)) return Triple(ADLAR[i], dz.getString(i), t)
            }
        }
        return null
    }

    /** Ramazan satırı: "İmsak 05:48 · İftar 17:42" (iftar geçtiyse ertesi günün). Veri yoksa null. */
    fun ramazanSatiri(c: Context): String? {
        val g = oku(c)?.optJSONObject("gunler") ?: return null
        val simdi = LocalDateTime.now(TR)
        for (ek in 0..1) {
            val gun = simdi.toLocalDate().plusDays(ek.toLong())
            val dz = g.optJSONArray(gun.toString()) ?: continue
            if (dz.length() < 5) continue
            if (ek == 0 && !gun.atTime(LocalTime.parse(dz.getString(4))).isAfter(simdi)) continue
            return "İmsak ${dz.getString(0)} · İftar ${dz.getString(4)}"
        }
        return null
    }

    /** Gösterilen vakit girdiğinde kilit ekranını yeniden çizmek için alarm kur. */
    fun alarmKur(c: Context) {
        val am = c.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        val pi = PendingIntent.getBroadcast(c, 41, Intent(c, VakitAlici::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        am.cancel(pi)
        if (!Ayar.otomatik(c)) return
        val s = siradaki(c) ?: return
        val ms = s.third.atZone(TR).toInstant().toEpochMilli() + 3000
        val tam = Build.VERSION.SDK_INT < 31 || am.canScheduleExactAlarms()
        if (tam) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, ms, pi)
        else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, ms, pi)
    }
}

/** Vakit girdi: kilit ekranını yenile, bir sonraki vakte alarm kur. */
class VakitAlici : BroadcastReceiver() {
    override fun onReceive(c: Context, i: Intent) {
        val p = goAsync()
        Thread {
            try {
                Vakit.gerekirseIndir(c); Icerik.gerekirseIndir(c)
                if (Ayar.otomatik(c)) KilitCizici.uygula(c)
            } catch (_: Exception) {
            } finally {
                Vakit.alarmKur(c); p.finish()
            }
        }.start()
    }
}

/** Telefon yeniden başlayınca alarmlar silinir; yeniden kur. */
class AcilisAlici : BroadcastReceiver() {
    override fun onReceive(c: Context, i: Intent) {
        Zamanlayici.kur(c); Vakit.alarmKur(c)
    }
}
