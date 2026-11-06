package net.gununayeti

import android.content.Context
import org.json.JSONArray
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/** Canlı duvar kağıdı fotoğrafları: sitedeki 100 fotoğraftan 30'u telefonda durur, her gün birkaçı yenilenir. */
object FotoHavuz {
    private const val KAYNAK = "https://matmehmed47-cmyk.github.io/gunun-ayeti/fotograflar/"
    private const val ADET = 30
    private const val GUNLUK = 4
    private fun klasor(c: Context) = File(c.filesDir, "havuz").apply { mkdirs() }

    fun dosyalar(c: Context): List<File> =
        klasor(c).listFiles { f -> f.name.endsWith(".jpg") }?.sortedBy { it.name } ?: emptyList()

    private fun al(adres: String): ByteArray? = try {
        val b = URL(adres).openConnection() as HttpURLConnection
        b.connectTimeout = 15000; b.readTimeout = 30000
        try { if (b.responseCode == 200) b.inputStream.readBytes() else null } finally { b.disconnect() }
    } catch (e: Exception) { null }

    /** Eksikleri tamamlar; ilkBasta=false ise (günlük) en eski birkaç fotoğrafı yenileriyle değiştirir. */
    fun yenile(c: Context, ilkBasta: Boolean = false) {
        val liste = al(KAYNAK + "liste.json")?.let { JSONArray(String(it)) } ?: return
        val adlar = (0 until liste.length()).map { liste.getJSONObject(it).getString("dosya") }
        val k = klasor(c)
        var mevcut = dosyalar(c)
        if (!ilkBasta && mevcut.size >= ADET) {
            mevcut.sortedBy { it.lastModified() }.take(GUNLUK).forEach { it.delete() }
            mevcut = dosyalar(c)
        }
        val yeni = (adlar - mevcut.map { it.name }.toSet()).shuffled()
        for (ad in yeni.take(maxOf(0, ADET - mevcut.size))) {
            val b = al(KAYNAK + ad) ?: continue
            val gecici = File(k, "$ad.tmp"); gecici.writeBytes(b); gecici.renameTo(File(k, ad))
        }
    }
}
