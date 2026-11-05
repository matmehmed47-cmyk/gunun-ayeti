# "Günün Ayeti Değiştir" kestirmesi: menüden ilçe ya da fotoğraf kaydını siler, sonra "Günün Ayeti"ni çalıştırır (yeniden sorar).
import plistlib, sys, uuid
sys.path.insert(0, __import__('os').path.dirname(__file__))
U = lambda: str(uuid.uuid4()).upper()
FOTO, ILCE = 'gunun-ayeti-fotograf.jpg', 'gunun-ayeti-ilce.txt'   # olustur.py ile aynı olmalı
def e(k, **p): return {'WFWorkflowActionIdentifier': k, 'WFWorkflowActionParameters': p}
def cikti(uid, ad): return {'Value': {'OutputUUID': uid, 'Type': 'ActionOutput', 'OutputName': ad}, 'WFSerializationType': 'WFTextTokenAttachment'}
g = U(); f1, f2 = U(), U()
SECENEK = ['📍 İlçeyi değiştir', '🖼️ Fotoğrafı değiştir']
eylemler = [
    e('is.workflow.actions.choosefrommenu', GroupingIdentifier=g, WFControlFlowMode=0, WFMenuPrompt='Neyi değiştirmek istersin?',
      WFMenuItems=[{'WFItemType': 0, 'WFValue': s} for s in SECENEK]),
    e('is.workflow.actions.choosefrommenu', GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemAttributedTitle=SECENEK[0], WFMenuItemTitle=SECENEK[0]),
    e('is.workflow.actions.documentpicker.open', UUID=f1, WFGetFilePath=ILCE, WFFileErrorIfNotFound=False),
    e('is.workflow.actions.file.delete', WFInput=cikti(f1, 'Dosya'), WFDeleteImmediatelyDelete=True, WFDeleteFileConfirmDeletion=False),
    e('is.workflow.actions.choosefrommenu', GroupingIdentifier=g, WFControlFlowMode=1, WFMenuItemAttributedTitle=SECENEK[1], WFMenuItemTitle=SECENEK[1]),
    e('is.workflow.actions.documentpicker.open', UUID=f2, WFGetFilePath=FOTO, WFFileErrorIfNotFound=False),
    e('is.workflow.actions.file.delete', WFInput=cikti(f2, 'Dosya'), WFDeleteImmediatelyDelete=True, WFDeleteFileConfirmDeletion=False),
    e('is.workflow.actions.choosefrommenu', GroupingIdentifier=g, WFControlFlowMode=2, UUID=U()),
    e('is.workflow.actions.runworkflow', WFWorkflowName='Günün Ayeti', WFShowWorkflow=False),
]
plistlib.dump({
    'WFWorkflowName': 'Günün Ayeti Değiştir', 'WFWorkflowActions': eylemler,
    'WFWorkflowClientVersion': '2605.0.5', 'WFWorkflowMinimumClientVersion': 900, 'WFWorkflowMinimumClientVersionString': '900',
    'WFWorkflowIcon': {'WFWorkflowIconStartColor': 431817727, 'WFWorkflowIconGlyphNumber': 59446},
    'WFWorkflowTypes': [], 'WFWorkflowInputContentItemClasses': [], 'WFWorkflowImportQuestions': [],
}, open(sys.argv[1], 'wb'), fmt=plistlib.FMT_BINARY)
print('yazıldı', len(eylemler), 'eylem')
