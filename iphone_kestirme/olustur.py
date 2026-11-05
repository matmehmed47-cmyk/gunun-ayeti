# "Günün Ayeti" iPhone kestirmesini (imzasız plist) üretir. İmza: iphone_kestirme/imzala.py (HubSign).
# Sürüm 2 akışı:
#   Girdi "ilce"  → il/ilçe listeden seçtirir, kaydeder (sonra yeniler)
#   Girdi "foto"  → fotoğraf seçtirir, JPEG'e çevirip kaydeder (sonra yeniler)
#   Girdi "yenile"→ hemen yeniler
#   Girdi yok (otomasyon: 01:00, 07:00, Wi-Fi) → bugün zaten yenilendiyse sessizce çıkar, değilse yeniler
#   İlk çalışmada ilçe/fotoğraf kaydı yoksa sorar. Sonunda yeni kestirme sürümü varsa bildirim gösterir.
# NOT: iPhone, dosya adını kestirme adı yapıyor → kestirmenin adı "Gunun-Ayeti". Site düğmeleri bu adla çağırır.
import plistlib, sys, uuid

SURUM = 2  # site/iphone-surum.txt bundan büyükse "yeni sürüm var" bildirimi
SITE = 'https://matmehmed47-cmyk.github.io/gunun-ayeti/iphone/'
KOK = 'https://matmehmed47-cmyk.github.io/gunun-ayeti/'
FOTO, ILCE, SON = 'gunun-ayeti-fotograf.jpg', 'gunun-ayeti-ilce.txt', 'gunun-ayeti-son.txt'
U = lambda: str(uuid.uuid4()).upper()

def cikti(uid, ad):
    return {'Value': {'OutputUUID': uid, 'Type': 'ActionOutput', 'OutputName': ad}, 'WFSerializationType': 'WFTextTokenAttachment'}
GIRDI = {'Value': {'Type': 'ExtensionInput'}, 'WFSerializationType': 'WFTextTokenAttachment'}
def degisken(v): return {'Type': 'Variable', 'Variable': v}

def metin(parcalar):  # ['sabit', (uid, ad), 'sabit'] → WFTextTokenString
    s, ek = '', {}
    for p in parcalar:
        if isinstance(p, str): s += p
        else:
            ek[f'{{{len(s.encode("utf-16-le")) // 2}, 1}}'] = {'OutputUUID': p[0], 'Type': 'ActionOutput', 'OutputName': p[1]}
            s += '￼'
    return {'Value': {'string': s, 'attachmentsByRange': ek}, 'WFSerializationType': 'WFTextTokenString'}

def eylem(kimlik, **p): return {'WFWorkflowActionIdentifier': kimlik, 'WFWorkflowActionParameters': p}
def eger(grup, kosul, girdi, **ek): return eylem('is.workflow.actions.conditional', GroupingIdentifier=grup, WFControlFlowMode=0, WFCondition=kosul, WFInput=girdi, **ek)
def bitir(grup): return eylem('is.workflow.actions.conditional', GroupingIdentifier=grup, WFControlFlowMode=2)
def dosya_al(uid, ad, hata=False): return eylem('is.workflow.actions.documentpicker.open', UUID=uid, WFGetFilePath=ad, WFFileErrorIfNotFound=hata)
def kaydet(girdi, ad): return eylem('is.workflow.actions.documentpicker.save', WFInput=girdi, WFAskWhereToSave=False, WFFileDestinationPath=ad, WFSaveFileOverwrite=True)

def il_ilce_sec():
    u1, b1, s1, u2, k1, u3, b2, s2, u4, kod, km = (U() for _ in range(11))
    return [
        eylem('is.workflow.actions.downloadurl', UUID=u1, WFURL=SITE + 'iller.txt'),
        eylem('is.workflow.actions.text.split', UUID=b1, text=cikti(u1, 'URL İçeriği'), WFTextSeparator='New Lines'),
        eylem('is.workflow.actions.choosefromlist', UUID=s1, WFInput=cikti(b1, 'Bölünmüş Metin'), WFChooseFromListActionPrompt='İlini seç (namaz vakitleri için)'),
        eylem('is.workflow.actions.downloadurl', UUID=u2, WFURL=SITE + 'iller.json'),
        eylem('is.workflow.actions.getvalueforkey', UUID=k1, WFInput=cikti(u2, 'URL İçeriği'), WFGetDictionaryValueType='Value', WFDictionaryKey=metin([(s1, 'Seçilen Öge')])),
        eylem('is.workflow.actions.downloadurl', UUID=u3, WFURL=metin([SITE + 'ilce/', (k1, 'Sözlük Değeri'), '.txt'])),
        eylem('is.workflow.actions.text.split', UUID=b2, text=cikti(u3, 'URL İçeriği'), WFTextSeparator='New Lines'),
        eylem('is.workflow.actions.choosefromlist', UUID=s2, WFInput=cikti(b2, 'Bölünmüş Metin'), WFChooseFromListActionPrompt='İlçeni seç'),
        eylem('is.workflow.actions.downloadurl', UUID=u4, WFURL=metin([SITE + 'ilce/', (k1, 'Sözlük Değeri'), '.json'])),
        eylem('is.workflow.actions.getvalueforkey', UUID=kod, WFInput=cikti(u4, 'URL İçeriği'), WFGetDictionaryValueType='Value', WFDictionaryKey=metin([(s2, 'Seçilen Öge')])),
        eylem('is.workflow.actions.gettext', UUID=km, WFTextActionText=metin([(kod, 'Sözlük Değeri')])),
        kaydet(cikti(km, 'Metin'), ILCE),
    ]

def foto_sec():
    sec, jpg = U(), U()
    return [
        eylem('is.workflow.actions.selectphoto', UUID=sec, WFPhotoPickerTypes=['Images']),
        eylem('is.workflow.actions.image.convert', UUID=jpg, WFInput=cikti(sec, 'Fotoğraflar'), WFImageFormat='JPEG', WFImageCompressionQuality=0.92, WFImagePreserveMetadata=True),
        kaydet(cikti(jpg, 'Dönüştürülmüş Görüntü'), FOTO),
    ]

g_ilce, g_foto, g_bos, g_ayni, g_ik, g_fk, g_surum = (U() for _ in range(7))
sonm = U()
tarih, gun, son, ik, fk, ilce_d, ilce, foto_d, gen, yuk, carp, bol, yuvar, boyut, kirp, ayet, b1, vakit, b2, gunmetin, sur, surs = (U() for _ in range(22))
eylemler = [
    # 1) Siteden gelen komutlar
    eger(g_ilce, 99, degisken(GIRDI), WFConditionalActionString='ilce'), *il_ilce_sec(), bitir(g_ilce),
    eger(g_foto, 99, degisken(GIRDI), WFConditionalActionString='foto'), *foto_sec(), bitir(g_foto),
    # 2) Bugünün tarihi; otomasyonda (girdi yok) bugün zaten yenilendiyse çık
    eylem('is.workflow.actions.date', UUID=tarih, WFDateActionMode='Current Date'),
    eylem('is.workflow.actions.format.date', UUID=gun, WFDate=cikti(tarih, 'Tarih'), WFDateFormatStyle='Custom', WFDateFormat='yyyy-MM-dd', WFTimeFormatStyle='None'),
    eger(g_bos, 101, degisken(GIRDI)),
    dosya_al(son, SON),
    eylem('is.workflow.actions.gettext', UUID=sonm, WFTextActionText=metin([(son, 'Dosya')])),
    eger(g_ayni, 4, degisken(cikti(sonm, 'Metin')), WFConditionalActionString=metin([(gun, 'Biçimlendirilmiş Tarih')])),
    eylem('is.workflow.actions.exit'),
    bitir(g_ayni),
    bitir(g_bos),
    # 3) İlk çalışma: kayıt yoksa sor
    dosya_al(ik, ILCE), eger(g_ik, 101, degisken(cikti(ik, 'Dosya'))), *il_ilce_sec(), bitir(g_ik),
    dosya_al(fk, FOTO), eger(g_fk, 101, degisken(cikti(fk, 'Dosya'))), *foto_sec(), bitir(g_fk),
    # 4) Kayıtları oku
    dosya_al(ilce_d, ILCE, True),
    eylem('is.workflow.actions.gettext', UUID=ilce, WFTextActionText=metin([(ilce_d, 'Dosya')])),
    dosya_al(foto_d, FOTO, True),
    # 5) Fotoğraf: oran korunarak boya göre ölçekle (genişlik × 2796 / yükseklik), ortadan 1290×2796 kırp
    eylem('is.workflow.actions.properties.images', UUID=gen, WFInput=cikti(foto_d, 'Dosya'), WFContentItemPropertyName='Width'),
    eylem('is.workflow.actions.properties.images', UUID=yuk, WFInput=cikti(foto_d, 'Dosya'), WFContentItemPropertyName='Height'),
    eylem('is.workflow.actions.math', UUID=carp, WFInput=cikti(gen, 'Genişlik'), WFMathOperation='×', WFMathOperand='2796'),
    eylem('is.workflow.actions.math', UUID=bol, WFInput=cikti(carp, 'Hesaplama Sonucu'), WFMathOperation='÷', WFMathOperand=cikti(yuk, 'Yükseklik')),
    eylem('is.workflow.actions.round', UUID=yuvar, WFInput=cikti(bol, 'Hesaplama Sonucu'), WFRoundMode='Normal', WFRoundTo='Integer'),
    eylem('is.workflow.actions.image.resize', UUID=boyut, WFImage=cikti(foto_d, 'Dosya'), WFImageResizeKey='Size',
          WFImageResizeWidth=metin([(yuvar, 'Yuvarlanmış Sayı')]), WFImageResizeHeight='2796'),
    eylem('is.workflow.actions.image.crop', UUID=kirp, WFInput=cikti(boyut, 'Yeniden Boyutlandırılmış Görüntü'),
          WFImageCropPosition='Center', WFImageCropWidth='1290', WFImageCropHeight='2796'),
    # 6) Ayet ve vakit katmanları
    eylem('is.workflow.actions.downloadurl', UUID=ayet, WFURL=SITE + 'bugun-alt.png'),
    eylem('is.workflow.actions.overlayimageonimage', UUID=b1, WFInput=cikti(kirp, 'Kırpılmış Görüntü'), WFImage=cikti(ayet, 'URL İçeriği'),
          WFShouldShowImageEditor=False, WFImagePosition='Center', WFImageWidth='1290', WFImageHeight='2796'),
    eylem('is.workflow.actions.downloadurl', UUID=vakit, WFURL=metin([SITE + 'vakit/', (ilce, 'Metin'), '-alt.png'])),
    eylem('is.workflow.actions.overlayimageonimage', UUID=b2, WFInput=cikti(b1, 'Üst Üste Bindirilmiş Görüntü'), WFImage=cikti(vakit, 'URL İçeriği'),
          WFShouldShowImageEditor=False, WFImagePosition='Center', WFImageWidth='1290', WFImageHeight='2796'),
    # 7) Kilit ekranı (iOS'un kendi kırpma/bulanıklaştırma/yakınlaştırması kapalı)
    eylem('is.workflow.actions.wallpaper.set', WFInput=cikti(b2, 'Üst Üste Bindirilmiş Görüntü'), WFWallpaperLocation=['Lock Screen'],
          WFWallpaperShowPreview=False, WFWallpaperSmartCrop=False, WFWallpaperLegibilityBlur=False, WFWallpaperPerspectiveZoom=False),
    # 8) Bugün yenilendi
    eylem('is.workflow.actions.gettext', UUID=gunmetin, WFTextActionText=metin([(gun, 'Biçimlendirilmiş Tarih')])),
    kaydet(cikti(gunmetin, 'Metin'), SON),
    # 9) Yeni kestirme sürümü var mı?
    eylem('is.workflow.actions.downloadurl', UUID=sur, WFURL=KOK + 'iphone-surum.txt'),
    eylem('is.workflow.actions.detect.number', UUID=surs, WFInput=cikti(sur, 'URL İçeriği')),
    eger(g_surum, 2, degisken(cikti(surs, 'Sayılar')), WFNumberValue=str(SURUM)),
    eylem('is.workflow.actions.notification', WFNotificationActionTitle='Günün Ayeti: yeni sürüm var',
          WFNotificationActionBody='Siteye gir, "iPhone için indir"e bas ve yeni kestirmeyi ekle. Ayarların silinmez.', WFNotificationActionSound=False),
    bitir(g_surum),
]
kestirme = {
    'WFWorkflowName': 'Gunun-Ayeti',
    'WFWorkflowActions': eylemler,
    'WFWorkflowClientVersion': '2605.0.5',
    'WFWorkflowMinimumClientVersion': 900,
    'WFWorkflowMinimumClientVersionString': '900',
    'WFWorkflowIcon': {'WFWorkflowIconStartColor': 431817727, 'WFWorkflowIconGlyphNumber': 59511},
    'WFWorkflowTypes': [],
    'WFWorkflowInputContentItemClasses': ['WFStringContentItem'],
    'WFWorkflowImportQuestions': [],
}
plistlib.dump(kestirme, open(sys.argv[1], 'wb'), fmt=plistlib.FMT_BINARY)
print('yazıldı', sys.argv[1], len(eylemler), 'eylem')
