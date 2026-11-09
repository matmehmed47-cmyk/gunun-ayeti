package net.gununayeti

import android.app.AlarmManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.media.AudioAttributes
import android.media.AudioManager
import android.media.MediaPlayer
import android.media.RingtoneManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.ZoneId

/**
 * Ezan: kullanıcının açtığı vakitlerde (İmsak, Öğle, İkindi, Akşam, Yatsı) seçtiği sesi kısa çalar.
 * Her ezan çalınca bir sonrakinin alarmı kurulur (zincir); vakitler her gün Diyanet verisinden okunur.
 * Telefon sessiz/titreşimdeyse sadece titrer. Güneş vaktinde hiçbir şey olmaz.
 */
object Ezan {
    /** Vakit sıraları (Vakit.ADLAR içinde): 0 İmsak, 2 Öğle, 3 İkindi, 4 Akşam, 5 Yatsı. 1 (Güneş) yok. */
    val VAKITLER = intArrayOf(0, 2, 3, 4, 5)
    const val EN_UZUN_MS = 25_000L      // seçilen ses daha uzunsa burada yavaşça kısılır
    private val TR = ZoneId.of("Europe/Istanbul")
    private fun p(c: Context) = c.getSharedPreferences("ezan", Context.MODE_PRIVATE)

    fun acik(c: Context, i: Int) = p(c).getBoolean("acik$i", false)
    fun acikKoy(c: Context, i: Int, v: Boolean) { p(c).edit().putBoolean("acik$i", v).apply(); kur(c) }
    fun herhangiAcik(c: Context) = VAKITLER.any { acik(c, it) }

    fun sesDosya(c: Context, i: Int) = File(File(c.filesDir, "ezan").apply { mkdirs() }, "$i.ses")
    fun sesAdi(c: Context, i: Int): String = if (sesDosya(c, i).exists()) p(c).getString("ad$i", "Seçilen ses") ?: "" else ""
    fun sesKaydet(c: Context, i: Int, veri: ByteArray, ad: String) { sesDosya(c, i).writeBytes(veri); p(c).edit().putString("ad$i", ad).apply() }
    fun sesSil(c: Context, i: Int) { sesDosya(c, i).delete(); p(c).edit().remove("ad$i").apply() }

    private fun vakitler(c: Context): JSONObject? = try { JSONObject(File(c.filesDir, "vakit.json").readText()).optJSONObject("gunler") } catch (e: Exception) { null }

    /** Açık vakitlerden sıradaki: (vakit sırası, zamanı). Önümüzdeki 3 güne bakar. */
    fun siradaki(c: Context, sonra: LocalDateTime = LocalDateTime.now(TR)): Pair<Int, LocalDateTime>? {
        val g = vakitler(c) ?: return null
        for (ek in 0..3) {
            val gun: LocalDate = sonra.toLocalDate().plusDays(ek.toLong())
            val dz = g.optJSONArray(gun.toString()) ?: continue
            for (i in VAKITLER) {
                if (i >= dz.length() || !acik(c, i)) continue
                val t = gun.atTime(LocalTime.parse(dz.getString(i)))
                if (t.isAfter(sonra)) return i to t
            }
        }
        return null
    }

    private fun alarmNiyeti(c: Context, i: Int = -1, ms: Long = 0) = PendingIntent.getBroadcast(c, 51,
        Intent(c, EzanAlici::class.java).putExtra("vakit", i).putExtra("zaman", ms),
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

    /** Sıradaki ezanın alarmını kurar (öncekini siler). Vakit, ayar ya da şehir değişince ve her ezandan sonra çağrılır. */
    fun kur(c: Context) {
        val am = c.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        am.cancel(alarmNiyeti(c))
        val (i, t) = siradaki(c) ?: return
        val ms = t.atZone(TR).toInstant().toEpochMilli()
        val pi = alarmNiyeti(c, i, ms)
        val tam = Build.VERSION.SDK_INT < 31 || am.canScheduleExactAlarms()
        if (tam) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, ms, pi)
        else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, ms, pi)
    }

    /** Uygulamadaki kart için durum: her vakit açık mı, ses adı ve sıradaki ezan. */
    fun durum(c: Context): String {
        val acik = JSONArray(); val ad = JSONArray()
        for (i in 0..5) { acik.put(acik(c, i)); ad.put(sesAdi(c, i)) }
        val s = siradaki(c)
        return JSONObject().put("acik", acik).put("ad", ad)
            .put("siradaki", if (s == null) "" else "${Vakit.ADLAR[s.first]} ${"%02d:%02d".format(s.second.hour, s.second.minute)}")
            .put("gun", if (s == null) "" else s.second.toLocalDate().toString())
            .toString()
    }

    /** Bugünkü vakit saati "HH:MM" (bildirimde gösterilir). */
    fun bugunSaat(c: Context, i: Int): String? = try { vakitler(c)?.optJSONArray(LocalDate.now(TR).toString())?.getString(i) } catch (e: Exception) { null }

    fun cal(c: Context, i: Int, deneme: Boolean) {
        val n = Intent(c, EzanServisi::class.java).putExtra("vakit", i).putExtra("deneme", deneme)
        if (Build.VERSION.SDK_INT >= 26) c.startForegroundService(n) else c.startService(n)
    }
}

/** Vakit girdi: ezanı çal, sonra sıradakini kur. 10 dakikadan fazla geç kalındıysa (telefon kapalıydı vb.) çalmaz. */
class EzanAlici : BroadcastReceiver() {
    override fun onReceive(c: Context, i: Intent) {
        val v = i.getIntExtra("vakit", -1); val ms = i.getLongExtra("zaman", 0)
        try {
            if (v >= 0 && Ezan.acik(c, v) && System.currentTimeMillis() - ms < 10 * 60_000) Ezan.cal(c, v, false)
        } catch (_: Exception) {
        } finally {
            try { Ezan.kur(c) } catch (_: Exception) {}   // zincir: sıradaki ezanı kur
        }
    }
}

/** Ezanı çalan kısa ömürlü servis: bildirimde "Durdur" düğmesi; ses bitince ya da 25 sn sonra yavaşça kısılıp kapanır. */
class EzanServisi : Service() {
    private var oynatici: MediaPlayer? = null
    private val el = Handler(Looper.getMainLooper())
    private var bitti = false

    override fun onBind(i: Intent?): IBinder? = null

    override fun onStartCommand(i: Intent?, flags: Int, startId: Int): Int {
        if (i?.action == "DURDUR") { kapat(); return START_NOT_STICKY }
        val v = i?.getIntExtra("vakit", 0) ?: 0
        val deneme = i?.getBooleanExtra("deneme", false) ?: false
        bildirimGoster(v, deneme)
        oynatici?.release(); oynatici = null; el.removeCallbacksAndMessages(null); bitti = false
        val am = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        if (!deneme && am.ringerMode != AudioManager.RINGER_MODE_NORMAL) {
            titret(); el.postDelayed({ kapat() }, 4000)
        } else {
            try { cal(v) } catch (_: Exception) { titret(); el.postDelayed({ kapat() }, 4000) }
        }
        return START_NOT_STICKY
    }

    private fun cal(v: Int) {
        val dosya = Ezan.sesDosya(this, v)
        val mp = MediaPlayer()
        mp.setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM)
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
        if (dosya.exists()) mp.setDataSource(dosya.path)
        else mp.setDataSource(this, RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION))
        mp.setWakeMode(this, PowerManager.PARTIAL_WAKE_LOCK)
        mp.setOnCompletionListener { kapat() }
        mp.setOnErrorListener { _, _, _ -> kapat(); true }
        mp.prepare(); mp.start(); oynatici = mp
        // Uzun bir ses seçildiyse 25. saniyede 1,5 sn'de kısılarak dursun
        el.postDelayed({ kis(1f) }, Ezan.EN_UZUN_MS)
    }

    private fun kis(s: Float) {
        val mp = oynatici ?: return
        if (s <= 0f) { kapat(); return }
        try { mp.setVolume(s, s) } catch (_: Exception) {}
        el.postDelayed({ kis(s - 0.07f) }, 100)
    }

    private fun titret() {
        val desen = longArrayOf(0, 500, 250, 500, 250, 900)
        val t: Vibrator = if (Build.VERSION.SDK_INT >= 31) (getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager).defaultVibrator
                          else @Suppress("DEPRECATION") (getSystemService(Context.VIBRATOR_SERVICE) as Vibrator)
        if (Build.VERSION.SDK_INT >= 26) t.vibrate(VibrationEffect.createWaveform(desen, -1)) else @Suppress("DEPRECATION") t.vibrate(desen, -1)
    }

    private fun bildirimGoster(v: Int, deneme: Boolean) {
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= 26 && nm.getNotificationChannel("ezan") == null)
            nm.createNotificationChannel(NotificationChannel("ezan", "Ezan", NotificationManager.IMPORTANCE_HIGH).apply {
                setSound(null, null); enableVibration(false); description = "Vakit girince kısa ezan"
            })
        val durdur = PendingIntent.getService(this, 52, Intent(this, EzanServisi::class.java).setAction("DURDUR"),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val ac = PendingIntent.getActivity(this, 53, Intent(this, AnaEkran::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val vakitSaati = Ezan.bugunSaat(this, v)
        val b = (if (Build.VERSION.SDK_INT >= 26) Notification.Builder(this, "ezan") else @Suppress("DEPRECATION") Notification.Builder(this))
            .setSmallIcon(R.drawable.ic_ezan)
            .setContentTitle("${Vakit.ADLAR[v]} vakti" + if (deneme) " (deneme)" else "")
            .setContentText(vakitSaati ?: "Ezan okunuyor")
            .setContentIntent(ac)
            .setOngoing(true)
            .addAction(Notification.Action.Builder(null, "⏹ Durdur", durdur).build())
        if (Build.VERSION.SDK_INT >= 29) startForeground(54, b.build(), ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK)
        else startForeground(54, b.build())
    }

    private fun kapat() {
        if (bitti) return; bitti = true
        el.removeCallbacksAndMessages(null)
        try { oynatici?.stop() } catch (_: Exception) {}
        oynatici?.release(); oynatici = null
        if (Build.VERSION.SDK_INT >= 24) stopForeground(STOP_FOREGROUND_REMOVE) else @Suppress("DEPRECATION") stopForeground(true)
        stopSelf()
    }

    override fun onDestroy() { el.removeCallbacksAndMessages(null); oynatici?.release(); oynatici = null; super.onDestroy() }
}
