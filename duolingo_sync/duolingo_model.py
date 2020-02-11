from aqt.utils import askUser, showInfo

_field_names = ["Gid", "Gender", "Source", "Target", "Target Language", "Pronunciation"]
_model_name = "Duolingo Sync"


def create_model(mw):
    mm = mw.col.models
    m = mm.new(_(_model_name))

    for field_name in _field_names:
        fm = mm.newField(_(field_name))
        mm.addField(m, fm)  

    t = mm.newTemplate("Card 1")
    t['qfmt'] = "{{Source}}<br>\n<br>\nTo {{Target Language}}:\n\n<hr id=answer>"
    t['afmt'] = "{{FrontSide}}\n\n<br><br>{{Target}}"
    mm.addTemplate(m, t)

    t = mm.newTemplate("Card 2")
    t['qfmt'] = "{{Target}}<br>\n<br>\nFrom {{Target Language}}:\n\n<hr id=answer>"
    t['afmt'] = "{{FrontSide}}\n\n<br><br>{{Source}}"
    mm.addTemplate(m, t)

    mm.add(m)
    mw.col.models.save(m)
    return m


def get_duolingo_model(mw):
    m = mw.col.models.byName(_model_name)
    if not m:
        showInfo("Duolingo Sync note type not found. Creating.")
        m = create_model(mw)

    # Add new fields if they don't exist yet
    fields_to_add = [field_name for field_name in _field_names if field_name not in mw.col.models.fieldNames(m)]
    if fields_to_add:
        showInfo("""
        <p>The Duolingo Sync plugin has recently been upgraded to include the following attributes: {}</p>
        <p>This change will require a full-sync of your card database to your Anki-Web account.</p>
        """.format(", ".join(fields_to_add)))
        for field_name in fields_to_add:
            pass
            fm = mw.col.models.newField(_(field_name))
            mw.col.models.addField(m, fm)
            mw.col.models.save(m)

    return m


