# "Günün Ayeti Değiştir" kestirmesi: menüden ilçe ya da fotoğraf seçtirir, kaydı ÜZERİNE YAZAR, sonra ana kestirmeyi çalıştırır.
# (Silme yöntemi iPhone'da güvenilir değildi.) Dosya adları olustur.py ile aynı olmalı.
import plistlib, sys, uuid
SITE = 'https://matmehmed47-cmyk.github.io/gunun-ayeti/iphone/'
FOTO, ILCE = 'gunun-ayeti-fotograf.jpg', 'gunun-ayeti-ilce.txt'
U = lambda: str(uuid.uuid4()).upper()
def e(k, **p): return {'WFWorkflowActionIdentifier': k, 'WFWorkflowActionParameters': p}
def cikti(uid, ad): return {'Value': {'OutputUUID': uid, 'Type': 'ActionOutput', 'OutputName': ad}, 'WFSerializationType': 'WFTextTokenAttachment'}
def metin(parcalar):
    s, ek = '', {}
    for p in parcalar:
        if isinstance(p, str): s += p
        else: ek[f'{{{len(s.encode("utf-16-le")) // 2}, 1}}'] = {'OutputUUID': p[0], 'Type': 'ActionOutput', 'OutputName': p[1]}; s += '￼'
    return {'Value': {'string': s, 'attachmentsByRange': ek}, 'WFSerializationType': 'WFTextTokenString'}
g = U(); u1, b1, s1, u2, k1, u3, b2, s2, u4, kod, km, sec, jpg = (U() for _ in range(13))
SECENEK = ['📍 İlçeyi değiştir', '🖼️ Fotoğrafı değiştir']
eylemler = [
    e('is.workflow.actions.choosefrommenu', GroupingIdentifier=g, WFControlFlowMode=0, WFMenuPrompt='Neyi değiştirmek istersin?',
      WFMenuItems=[{'WFItemType': 0, 'WFValue': s} for s in SECENEK]),
    e('is.workflow.actions.choosefrommenu', GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemAttributedTitle=SECENEK[0], WFMenuItemTitle=SECENEK[0]),
    e('is.workflow.actions.downloadurl', UUID=u1, WFURL=SITE + 'iller.txt'),
    e('is.workflow.actions.text.split', UUID=b1, text=cikti(u1, 'URL İçeriği'), WFTextSeparator='New Lines'),
    e('is.workflow.actions.choosefromlist', UUID=s1, WFInput=cikti(b1, 'Bölünmüş Metin'), WFChooseFromListActionPrompt='İlini seç'),
    e('is.workflow.actions.downloadurl', UUID=u2, WFURL=SITE + 'iller.json'),
    e('is.workflow.actions.getvalueforkey', UUID=k1, WFInput=cikti(u2, 'URL İçeriği'), WFGetDictionaryValueType='Value', WFDictionaryKey=metin([(s1, 'Seçilen Öge')])),
    e('is.workflow.actions.downloadurl', UUID=u3, WFURL=metin([SITE + 'ilce/', (k1, 'Sözlük Değeri'), '.txt'])),
    e('is.workflow.actions.text.split', UUID=b2, text=cikti(u3, 'URL İçeriği'), WFTextSeparator='New Lines'),
    e('is.workflow.actions.choosefromlist', UUID=s2, WFInput=cikti(b2, 'Bölünmüş Metin'), WFChooseFromListActionPrompt='İlçeni seç'),
    e('is.workflow.actions.downloadurl', UUID=u4, WFURL=metin([SITE + 'ilce/', (k1, 'Sözlük Değeri'), '.json'])),
    e('is.workflow.actions.getvalueforkey', UUID=kod, WFInput=cikti(u4, 'URL İçeriği'), WFGetDictionaryValueType='Value', WFDictionaryKey=metin([(s2, 'Seçilen Öge')])),
    e('is.workflow.actions.gettext', UUID=km, WFTextActionText=metin([(kod, 'Sözlük Değeri')])),
    e('is.workflow.actions.documentpicker.save', WFInput=cikti(km, 'Metin'), WFAskWhereToSave=False, WFFileDestinationPath=ILCE, WFSaveFileOverwrite=True),
    e('is.workflow.actions.choosefrommenu', GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemAttributedTitle=SECENEK[1], WFMenuItemTitle=SECENEK[1]),
    e('is.workflow.actions.selectphoto', UUID=sec, WFPhotoPickerTypes=['Images']),
    e('is.workflow.actions.image.convert', UUID=jpg, WFInput=cikti(sec, 'Fotoğraflar'), WFImageFormat='JPEG', WFImageCompressionQuality=0.92, WFImagePreserveMetadata=True),
    e('is.workflow.actions.documentpicker.save', WFInput=cikti(jpg, 'Dönüştürülmüş Görüntü'), WFAskWhereToSave=False, WFFileDestinationPath=FOTO, WFSaveFileOverwrite=True),
    e('is.workflow.actions.choosefrommenu', GroupingIdentifier=g, WFControlFlowMode=2, UUID=U()),
    e('is.workflow.actions.runworkflow', WFWorkflowName='Gunun-Ayeti', WFShowWorkflow=False),  # iPhone dosya adını kestirme adı yapıyor
]
plistlib.dump({
    'WFWorkflowName': 'Günün Ayeti Değiştir', 'WFWorkflowActions': eylemler,
    'WFWorkflowClientVersion': '2605.0.5', 'WFWorkflowMinimumClientVersion': 900, 'WFWorkflowMinimumClientVersionString': '900',
    'WFWorkflowIcon': {'WFWorkflowIconStartColor': 431817727, 'WFWorkflowIconGlyphNumber': 59446},
    'WFWorkflowTypes': [], 'WFWorkflowInputContentItemClasses': [], 'WFWorkflowImportQuestions': [],
}, open(sys.argv[1], 'wb'), fmt=plistlib.FMT_BINARY)
print('yazıldı', len(eylemler), 'eylem')
