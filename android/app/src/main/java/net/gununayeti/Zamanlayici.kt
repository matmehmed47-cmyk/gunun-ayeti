package net.gununayeti

import android.content.Context
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.Worker
import androidx.work.WorkerParameters
import java.time.Duration
import java.time.LocalDateTime
import java.time.LocalTime
import java.util.concurrent.TimeUnit

/** Her sabah 07:00'de kilit ekranını yeniler. */
class KilitIsci(c: Context, p: WorkerParameters) : Worker(c, p) {
    override fun doWork(): Result = try {
        Vakit.gerekirseIndir(applicationContext)
        Icerik.gerekirseIndir(applicationContext)
        if (Ayar.canli(applicationContext)) FotoHavuz.yenile(applicationContext)
        if (Ayar.otomatik(applicationContext)) KilitCizici.uygula(applicationContext)
        Vakit.alarmKur(applicationContext)
        Result.success()
    } catch (e: Exception) { Result.retry() }
}

object Zamanlayici {
    private const val AD = "gunluk-kilit"
    fun kur(c: Context) {
        val wm = WorkManager.getInstance(c)
        if (!Ayar.otomatik(c) && !Ayar.canli(c)) { wm.cancelUniqueWork(AD); return }
        val simdi = LocalDateTime.now()
        var hedef = simdi.toLocalDate().atTime(LocalTime.of(7, 0))
        if (!hedef.isAfter(simdi)) hedef = hedef.plusDays(1)
        val gecikme = Duration.between(simdi, hedef).toMinutes()
        val is_ = PeriodicWorkRequestBuilder<KilitIsci>(24, TimeUnit.HOURS)
            .setInitialDelay(gecikme, TimeUnit.MINUTES)
            .build()
        wm.enqueueUniquePeriodicWork(AD, ExistingPeriodicWorkPolicy.UPDATE, is_)
    }
}
