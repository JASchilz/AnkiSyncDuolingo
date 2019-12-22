import urllib.request, urllib.error, urllib.parse
import requests.exceptions

from aqt import mw
from aqt.utils import showInfo, getText, askUser, showWarning
from aqt.qt import *

from anki.lang import _
from anki.utils import splitFields, ids2str

from .lib import duolingo, duolingo_dialog, LoginFailedException


def get_duolingo_model():

    m = mw.col.models.byName("Duolingo Sync")

    if not m:
        if askUser("Duolingo Sync note type not found. Create?"):

            mm = mw.col.models
            m = mm.new(_("Duolingo Sync"))

            for fieldName in ["Gid", "Gender", "Source", "Target", "Target Language"]:
                fm = mm.newField(_(fieldName))
                mm.addField(m, fm)

            t = mm.newTemplate(_("Card 1"))
            t['qfmt'] = "{{" + _("Source") + "}}"
            t['afmt'] = "{{FrontSide}}\n\n<hr id=answer>\n\n" + "{{" + _("Target") + "}}"
            mm.addTemplate(m, t)
            mm.add(m)

            mw.col.models.save(m)

    return m


def sync_duolingo():

    model = get_duolingo_model()

    note_ids = mw.col.findNotes('tag:duolingo_sync')
    notes = mw.col.db.list("select flds from notes where id in {}".format(ids2str(note_ids)))
    duolingo_gids = [splitFields(note)[0] for note in notes]

    try:
        username, password = duolingo_dialog(mw)
    except TypeError:
        return

    if username and password:

        try:
            lingo = duolingo.Duolingo(username, password=password)
        except LoginFailedException:
            showWarning("Loging in to Duolingo failed. Please check your Duolingo credentials.")
            return
        except requests.exceptions.ConnectionError:
            showWarning("Could not connect to Duolingo. Please check your internet connection.")
            return

        response = lingo.get_vocabulary()
        language_string = response['language_string']
        vocabs = response['vocab_overview']

        did = mw.col.decks.id("Default")
        mw.col.decks.select(did)

        deck = mw.col.decks.get(did)
        deck['mid'] = model['id']
        mw.col.decks.save(deck)

        words_to_add = []
        for vocab in vocabs:

            if vocab['id'] not in duolingo_gids:
                words_to_add.append(vocab)
        if not words_to_add:
            showInfo("Successfully logged in to Duolingo, but no new words found in {} language.".format(language_string))
        elif askUser("Add {} notes from {} language?".format(len(words_to_add), language_string)):

            word_chunks = [words_to_add[x:x + 50] for x in range(0, len(words_to_add), 50)]

            mw.progress.start(immediate=True, label="Importing from Duolingo...", max=len(words_to_add))
            notes_added = 0
            for word_chunk in word_chunks:
                translations = lingo.get_translations([vocab['word_string'] for vocab in word_chunk])

                for vocab in word_chunk:
                    n = mw.col.newNote()

                    n['Gid'] = vocab['id']
                    n['Gender'] = vocab['gender'] if vocab['gender'] else ''
                    n['Source'] = '; '.join(translations[vocab['word_string']])
                    n['Target'] = vocab['word_string']
                    n['Target Language'] = language_string

                    n.addTag(language_string)
                    n.addTag('duolingo_sync')

                    if vocab['pos']:
                        n.addTag(vocab['pos'])

                    if vocab['skill']:
                        n.addTag(vocab['skill'])

                    mw.col.addNote(n)
                    notes_added += 1

                    mw.progress.update(value=notes_added)

            showInfo("{} notes added".format(notes_added))
            mw.moveToState("deckBrowser")

            mw.progress.finish()

action = QAction("Sync Duolingo", mw)
action.triggered.connect(sync_duolingo)
mw.form.menuTools.addAction(action)


