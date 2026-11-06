package net.gununayeti

import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

/** Bildirim panelindeki "Kıble" kutucuğu: basınca uygulama pusulayla açılır. */
class KibleKutucuk : TileService() {
    override fun onStartListening() {
        qsTile?.apply { state = Tile.STATE_INACTIVE; label = "Kıble"; updateTile() }
    }

    override fun onClick() {
        val ac = {
            val i = Intent(this, AnaEkran::class.java)
                .putExtra("kible", true)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            if (Build.VERSION.SDK_INT >= 34) {
                startActivityAndCollapse(PendingIntent.getActivity(this, 9, i, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT))
            } else {
                @Suppress("DEPRECATION") startActivityAndCollapse(i)
            }
        }
        if (isLocked) unlockAndRun { ac() } else ac()
    }
}
