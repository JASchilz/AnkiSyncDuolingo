from aqt.utils import askUser


def create_model(mw):
    mm = mw.col.models
    m = mm.new(_("Duolingo Sync"))

    for fieldName in ["Gid", "Gender", "Source", "Target", "Target Language", "Pronunciation"]:
        fm = mm.newField(_(fieldName))
        mm.addField(m, fm)  

    t = mm.newTemplate("Card 1")
    t['qfmt'] = "{{Source}}<br>\n<br>\nTo {{Target Language}}:\n\n<hr id=answer>"
    t['afmt'] = "{{FrontSide}}\n\n<br><br>{{Target}} ({{Pronunciation}})"
    mm.addTemplate(m, t)

    t = mm.newTemplate("Card 2")
    t['qfmt'] = "{{Target}}<br>\n<br>\nFrom {{Target Language}}:\n\n<hr id=answer>"
    t['afmt'] = "{{FrontSide}}\n\n<br><br>{{Source}}"
    mm.addTemplate(m, t)

    mm.add(m)
    mw.col.models.save(m)
    return m

def get_duolingo_model(mw):
    m = mw.col.models.byName("Duolingo Sync")
    if not m:
        if askUser("Duolingo Sync note type not found. Create?"):
            m = create_model(mw)
    return m

def get_duolingo_model_with_pronunciation(mw):
    m = create_model(mw)
    return m