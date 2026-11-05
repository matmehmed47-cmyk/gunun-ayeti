# "Günün Ayeti" iPhone kestirmesini (imzasız plist) üretir. İmzayı GitHub'ın Mac'i atar (shortcuts sign).
# Akış: ilçe kodu (içe aktarma sorusu) → fotoğraf (ilk seferde seçtirir, Kestirmeler klasörüne kaydeder)
#       → 1290x2796'ya kırp → ayet resmini bindir → ilçe vakit satırını bindir → kilit ekranı duvar kağıdı.
import plistlib, sys, uuid

SITE = 'https://matmehmed47-cmyk.github.io/gunun-ayeti/iphone/'
FOTO = 'gunun-ayeti-fotograf.jpg'  # ad değişti: eski (bozuk sürümden kalan) kayıt kullanılmaz
ILCE = 'gunun-ayeti-ilce.txt'
U = lambda: str(uuid.uuid4()).upper()

def cikti(uid, ad):  # bir eylemin çıktısına başvuru
    return {'Value': {'OutputUUID': uid, 'Type': 'ActionOutput', 'OutputName': ad}, 'WFSerializationType': 'WFTextTokenAttachment'}

def metin(parcalar):  # ['sabit', (uid, ad), 'sabit'] → WFTextTokenString
    s, ek = '', {}
    for p in parcalar:
        if isinstance(p, str): s += p
        else:
            ek[f'{{{len(s.encode("utf-16-le")) // 2}, 1}}'] = {'OutputUUID': p[0], 'Type': 'ActionOutput', 'OutputName': p[1]}
            s += '￼'
    return {'Value': {'string': s, 'attachmentsByRange': ek}, 'WFSerializationType': 'WFTextTokenString'}

def eylem(kimlik, **p):
    return {'WFWorkflowActionIdentifier': kimlik, 'WFWorkflowActionParameters': p}

ilce, dosya1, sec, kaydet, dosya2, boyut, kirp, ayet, bindir1, vakit, bindir2 = (U() for _ in range(11))
grup = U()
jpg = U()
gen, yuk, carp, bol, yuvar = (U() for _ in range(5))
idosya1, isor, ikaydet, idosya2 = (U() for _ in range(4)); igrup = U()
u1, b1, s1, u2, k1, u3, b2, s2, u4, kodmetin = (U() for _ in range(10))

# Gündüz elle açılınca menü (gece otomasyonda saat < 6 olduğu için sorulmaz)
def menu_blogu():
    tarih, saat, sayi, eg, mg = U(), U(), U(), U(), U()
    u1, b1, s1, u2, k1, u3, b2, s2, u4, kod, km, sec, jpg = (U() for _ in range(13))
    S = ['🔄 Kilit ekranını yenile', '📍 İlçeyi değiştir', '🖼️ Fotoğrafı değiştir']
    return [
        eylem('is.workflow.actions.date', UUID=tarih, WFDateActionMode='Current Date'),
        eylem('is.workflow.actions.format.date', UUID=saat, WFDate=cikti(tarih, 'Tarih'), WFDateFormatStyle='Custom', WFDateFormat='H', WFTimeFormatStyle='None'),
        eylem('is.workflow.actions.detect.number', UUID=sayi, WFInput=cikti(saat, 'Biçimlendirilmiş Tarih')),
        eylem('is.workflow.actions.conditional', GroupingIdentifier=eg, WFControlFlowMode=0, WFCondition=3, WFNumberValue='6',
              WFInput={'Type': 'Variable', 'Variable': cikti(sayi, 'Sayılar')}),
        eylem('is.workflow.actions.choosefrommenu', GroupingIdentifier=mg, WFControlFlowMode=0, WFMenuPrompt='Günün Ayeti',
              WFMenuItems=[{'WFItemType': 0, 'WFValue': s} for s in S]),
        eylem('is.workflow.actions.choosefrommenu', GroupingIdentifier=mg, WFControlFlowMode=1, WFMenuItemAttributedTitle=S[0], WFMenuItemTitle=S[0]),
        eylem('is.workflow.actions.choosefrommenu', GroupingIdentifier=mg, WFControlFlowMode=1, WFMenuItemAttributedTitle=S[1], WFMenuItemTitle=S[1]),
        eylem('is.workflow.actions.downloadurl', UUID=u1, WFURL=SITE + 'iller.txt'),
        eylem('is.workflow.actions.text.split', UUID=b1, text=cikti(u1, 'URL İçeriği'), WFTextSeparator='New Lines'),
        eylem('is.workflow.actions.choosefromlist', UUID=s1, WFInput=cikti(b1, 'Bölünmüş Metin'), WFChooseFromListActionPrompt='İlini seç'),
        eylem('is.workflow.actions.downloadurl', UUID=u2, WFURL=SITE + 'iller.json'),
        eylem('is.workflow.actions.getvalueforkey', UUID=k1, WFInput=cikti(u2, 'URL İçeriği'), WFGetDictionaryValueType='Value', WFDictionaryKey=metin([(s1, 'Seçilen Öge')])),
        eylem('is.workflow.actions.downloadurl', UUID=u3, WFURL=metin([SITE + 'ilce/', (k1, 'Sözlük Değeri'), '.txt'])),
        eylem('is.workflow.actions.text.split', UUID=b2, text=cikti(u3, 'URL İçeriği'), WFTextSeparator='New Lines'),
        eylem('is.workflow.actions.choosefromlist', UUID=s2, WFInput=cikti(b2, 'Bölünmüş Metin'), WFChooseFromListActionPrompt='İlçeni seç'),
        eylem('is.workflow.actions.downloadurl', UUID=u4, WFURL=metin([SITE + 'ilce/', (k1, 'Sözlük Değeri'), '.json'])),
        eylem('is.workflow.actions.getvalueforkey', UUID=kod, WFInput=cikti(u4, 'URL İçeriği'), WFGetDictionaryValueType='Value', WFDictionaryKey=metin([(s2, 'Seçilen Öge')])),
        eylem('is.workflow.actions.gettext', UUID=km, WFTextActionText=metin([(kod, 'Sözlük Değeri')])),
        eylem('is.workflow.actions.documentpicker.save', WFInput=cikti(km, 'Metin'), WFAskWhereToSave=False, WFFileDestinationPath=ILCE, WFSaveFileOverwrite=True),
        eylem('is.workflow.actions.choosefrommenu', GroupingIdentifier=mg, WFControlFlowMode=1, WFMenuItemAttributedTitle=S[2], WFMenuItemTitle=S[2]),
        eylem('is.workflow.actions.selectphoto', UUID=sec, WFPhotoPickerTypes=['Images']),
        eylem('is.workflow.actions.image.convert', UUID=jpg, WFInput=cikti(sec, 'Fotoğraflar'), WFImageFormat='JPEG', WFImageCompressionQuality=0.92, WFImagePreserveMetadata=True),
        eylem('is.workflow.actions.documentpicker.save', WFInput=cikti(jpg, 'Dönüştürülmüş Görüntü'), WFAskWhereToSave=False, WFFileDestinationPath=FOTO, WFSaveFileOverwrite=True),
        eylem('is.workflow.actions.choosefrommenu', GroupingIdentifier=mg, WFControlFlowMode=2, UUID=U()),
        eylem('is.workflow.actions.conditional', GroupingIdentifier=eg, WFControlFlowMode=2),
    ]

eylemler = menu_blogu() + [
    # İlçe kodu: ilk çalışmada sorulur, Kestirmeler klasörüne kaydedilir
    eylem('is.workflow.actions.documentpicker.open', UUID=idosya1, WFGetFilePath=ILCE, WFFileErrorIfNotFound=False, WFShowFilePicker=False),
    eylem('is.workflow.actions.conditional', GroupingIdentifier=igrup, WFControlFlowMode=0, WFCondition=101, WFInput={'Type': 'Variable', 'Variable': cikti(idosya1, 'Dosya')}),
    eylem('is.workflow.actions.downloadurl', UUID=u1, WFURL=SITE + 'iller.txt'),
    eylem('is.workflow.actions.text.split', UUID=b1, text=cikti(u1, 'URL İçeriği'), WFTextSeparator='New Lines'),
    eylem('is.workflow.actions.choosefromlist', UUID=s1, WFInput=cikti(b1, 'Bölünmüş Metin'), WFChooseFromListActionPrompt='İlini seç (namaz vakitleri için)'),
    eylem('is.workflow.actions.downloadurl', UUID=u2, WFURL=SITE + 'iller.json'),
    eylem('is.workflow.actions.getvalueforkey', UUID=k1, WFInput=cikti(u2, 'URL İçeriği'), WFGetDictionaryValueType='Value', WFDictionaryKey=metin([(s1, 'Seçilen Öge')])),
    eylem('is.workflow.actions.downloadurl', UUID=u3, WFURL=metin([SITE + 'ilce/', (k1, 'Sözlük Değeri'), '.txt'])),
    eylem('is.workflow.actions.text.split', UUID=b2, text=cikti(u3, 'URL İçeriği'), WFTextSeparator='New Lines'),
    eylem('is.workflow.actions.choosefromlist', UUID=s2, WFInput=cikti(b2, 'Bölünmüş Metin'), WFChooseFromListActionPrompt='İlçeni seç'),
    eylem('is.workflow.actions.downloadurl', UUID=u4, WFURL=metin([SITE + 'ilce/', (k1, 'Sözlük Değeri'), '.json'])),
    eylem('is.workflow.actions.getvalueforkey', UUID=isor, WFInput=cikti(u4, 'URL İçeriği'), WFGetDictionaryValueType='Value', WFDictionaryKey=metin([(s2, 'Seçilen Öge')])),
    eylem('is.workflow.actions.gettext', UUID=kodmetin, WFTextActionText=metin([(isor, 'Sözlük Değeri')])),
    eylem('is.workflow.actions.documentpicker.save', UUID=ikaydet, WFInput=cikti(kodmetin, 'Metin'), WFAskWhereToSave=False,
          WFFileDestinationPath=ILCE, WFSaveFileOverwrite=True),
    eylem('is.workflow.actions.conditional', GroupingIdentifier=igrup, WFControlFlowMode=2),
    eylem('is.workflow.actions.documentpicker.open', UUID=idosya2, WFGetFilePath=ILCE, WFFileErrorIfNotFound=True, WFShowFilePicker=False),
    eylem('is.workflow.actions.gettext', UUID=ilce, WFTextActionText=metin([(idosya2, 'Dosya')])),
    eylem('is.workflow.actions.documentpicker.open', UUID=dosya1, WFGetFilePath=FOTO, WFFileErrorIfNotFound=False, WFShowFilePicker=False),
    eylem('is.workflow.actions.conditional', GroupingIdentifier=grup, WFControlFlowMode=0, WFCondition=101, WFInput={'Type': 'Variable', 'Variable': cikti(dosya1, 'Dosya')}),
    eylem('is.workflow.actions.selectphoto', UUID=sec, WFPhotoPickerTypes=['Images']),
    eylem('is.workflow.actions.image.convert', UUID=jpg, WFInput=cikti(sec, 'Fotoğraflar'), WFImageFormat='JPEG', WFImageCompressionQuality=0.92, WFImagePreserveMetadata=True),
    eylem('is.workflow.actions.documentpicker.save', UUID=kaydet, WFInput=cikti(jpg, 'Dönüştürülmüş Görüntü'), WFAskWhereToSave=False,
          WFFileDestinationPath=FOTO, WFSaveFileOverwrite=True),
    eylem('is.workflow.actions.conditional', GroupingIdentifier=grup, WFControlFlowMode=2),
    eylem('is.workflow.actions.documentpicker.open', UUID=dosya2, WFGetFilePath=FOTO, WFFileErrorIfNotFound=True, WFShowFilePicker=False),
    # Oran korunarak boya göre ölçekle: yeni genişlik = genişlik × 2796 / yükseklik (yuvarlanır)
    eylem('is.workflow.actions.properties.images', UUID=gen, WFInput=cikti(dosya2, 'Dosya'), WFContentItemPropertyName='Width'),
    eylem('is.workflow.actions.properties.images', UUID=yuk, WFInput=cikti(dosya2, 'Dosya'), WFContentItemPropertyName='Height'),
    eylem('is.workflow.actions.math', UUID=carp, WFInput=cikti(gen, 'Genişlik'), WFMathOperation='×', WFMathOperand='2796'),
    eylem('is.workflow.actions.math', UUID=bol, WFInput=cikti(carp, 'Hesaplama Sonucu'), WFMathOperation='÷', WFMathOperand=cikti(yuk, 'Yükseklik')),
    eylem('is.workflow.actions.round', UUID=yuvar, WFInput=cikti(bol, 'Hesaplama Sonucu'), WFRoundMode='Normal', WFRoundTo='Integer'),
    eylem('is.workflow.actions.image.resize', UUID=boyut, WFImage=cikti(dosya2, 'Dosya'), WFImageResizeKey='Size',
          WFImageResizeWidth=metin([(yuvar, 'Yuvarlanmış Sayı')]), WFImageResizeHeight='2796'),
    eylem('is.workflow.actions.image.crop', UUID=kirp, WFInput=cikti(boyut, 'Yeniden Boyutlandırılmış Görüntü'),
          WFImageCropPosition='Center', WFImageCropWidth='1290', WFImageCropHeight='2796'),
    eylem('is.workflow.actions.downloadurl', UUID=ayet, WFURL=SITE + 'bugun-alt.png'),
    eylem('is.workflow.actions.overlayimageonimage', UUID=bindir1, WFInput=cikti(kirp, 'Kırpılmış Görüntü'), WFImage=cikti(ayet, 'URL İçeriği'),
          WFShouldShowImageEditor=False, WFImagePosition='Center', WFImageWidth='1290', WFImageHeight='2796'),
    eylem('is.workflow.actions.downloadurl', UUID=vakit, WFURL=metin([SITE + 'vakit/', (ilce, 'Metin'), '-alt.png'])),
    eylem('is.workflow.actions.overlayimageonimage', UUID=bindir2, WFInput=cikti(bindir1, 'Üst Üste Bindirilmiş Görüntü'), WFImage=cikti(vakit, 'URL İçeriği'),
          WFShouldShowImageEditor=False, WFImagePosition='Center', WFImageWidth='1290', WFImageHeight='2796'),
    eylem('is.workflow.actions.wallpaper.set', WFInput=cikti(bindir2, 'Üst Üste Bindirilmiş Görüntü'),
          WFWallpaperLocation=['Lock Screen'], WFWallpaperShowPreview=False,
          WFWallpaperSmartCrop=False, WFWallpaperLegibilityBlur=False, WFWallpaperPerspectiveZoom=False),
]
kestirme = {
    'WFWorkflowName': 'Günün Ayeti',
    'WFWorkflowActions': eylemler,
    'WFWorkflowClientVersion': '2605.0.5',
    'WFWorkflowMinimumClientVersion': 900,
    'WFWorkflowMinimumClientVersionString': '900',
    'WFWorkflowIcon': {'WFWorkflowIconStartColor': 431817727, 'WFWorkflowIconGlyphNumber': 59511},
    'WFWorkflowTypes': [],
    'WFWorkflowInputContentItemClasses': [],
    'WFWorkflowImportQuestions': [],
}
plistlib.dump(kestirme, open(sys.argv[1], 'wb'), fmt=plistlib.FMT_BINARY)
print('yazıldı', sys.argv[1], len(eylemler), 'eylem')
