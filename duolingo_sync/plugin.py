import requests.exceptions
import time
from collections import defaultdict

from aqt import mw
from aqt.utils import showInfo, askUser, showWarning
from aqt.qt import *

from anki.utils import splitFields, ids2str

from .duolingo_dialog import duolingo_dialog
from .duolingo import Duolingo, LoginFailedException
from .duolingo_model import get_duolingo_model
from .duolingo_thread import DuolingoThread


def sync_duolingo():
    model = get_duolingo_model(mw)

    if not model:
        showWarning("Could not find or create Duolingo Sync note type.")
        return

    note_ids = mw.col.findNotes('tag:duolingo_sync')
    notes = mw.col.db.list("select flds from notes where id in {}".format(ids2str(note_ids)))
    gids_to_notes = {splitFields(note)[0]: note for note in notes}
    try:
        username, password = duolingo_dialog(mw)
    except TypeError:
        return

    if username and password:
        try:
            mw.progress.start(immediate=True, label="Logging in...")

            login_thread = DuolingoThread(target=Duolingo, args=(username, password))
            login_thread.start()
            while login_thread.is_alive():
                time.sleep(.02)
                mw.progress.update()
            lingo = login_thread.join()

            vocabulary_thread = DuolingoThread(target=lingo.get_vocabulary)
            vocabulary_thread.start()
            mw.progress.update(label="Retrieving vocabulary...")
            while vocabulary_thread.is_alive():
                time.sleep(.02)
                mw.progress.update()
            vocabulary_response = vocabulary_thread.join()

        except LoginFailedException:
            showWarning(
                """
                <p>Logging in to Duolingo failed. Please check your Duolingo credentials.</p>
                
                <p>Having trouble logging in? You must use your <i>Duolingo</i> username and password.
                You <i>can't</i> use your Google or Facebook credentials, even if that's what you use to
                sign in to Duolingo.</p>
                
                <p>You can find your Duolingo username at
                <a href="https://www.duolingo.com/settings">https://www.duolingo.com/settings</a> and you
                can create or set your Duolingo password at
                <a href="https://www.duolingo.com/settings/password">https://www.duolingo.com/settings/password</a>.</p>
                """
            )
            return
        except requests.exceptions.ConnectionError:
            showWarning("Could not connect to Duolingo. Please check your internet connection.")
            return
        finally:
            mw.progress.finish()

        language_string = vocabulary_response['language_string']
        vocabs = vocabulary_response['vocab_overview']

        did = mw.col.decks.id("Default")
        mw.col.decks.select(did)

        deck = mw.col.decks.get(did)
        deck['mid'] = model['id']
        mw.col.decks.save(deck)

        words_to_add = [vocab for vocab in vocabs if vocab['id'] not in gids_to_notes]

        if not words_to_add:
            showInfo("Successfully logged in to Duolingo, but no new words found in {} language.".format(language_string))
        elif askUser("Add {} notes from {} language?".format(len(words_to_add), language_string)):

            word_chunks = [words_to_add[x:x + 50] for x in range(0, len(words_to_add), 50)]

            mw.progress.start(immediate=True, label="Importing from Duolingo...", max=len(words_to_add))
            notes_added = 0
            problem_vocabs = []
            for word_chunk in word_chunks:
                translations = lingo.get_translations([vocab['word_string'] for vocab in word_chunk])

                for vocab in word_chunk:
                    
                    n = mw.col.newNote()
                    
                    # Update the underlying dictionary to accept more arguments for more customisable cards 
                    n._fmap = defaultdict(str, n._fmap)

                    n['Gid'] = vocab['id']
                    n['Gender'] = vocab['gender'] if vocab['gender'] else ''
                    n['Source'] = '; '.join(translations[vocab['word_string']])
                    n['Target'] = vocab['word_string']
                    n['Pronunciation'] = vocab['normalized_string'].strip()
                    n['Target Language'] = language_string
                    n.addTag(language_string)
                    n.addTag('duolingo_sync')

                    if vocab['pos']:
                        n.addTag(vocab['pos'])

                    if vocab['skill']:
                        n.addTag(vocab['skill'].replace(" ", "-"))

                    num_cards = mw.col.addNote(n)

                    if num_cards:
                        notes_added += 1
                    else:
                        problem_vocabs.append(vocab['word_string'])

                    mw.progress.update(value=notes_added)

            message = "{} notes added.".format(notes_added)

            if problem_vocabs:
                message += " Failed to add: " + ", ".join(problem_vocabs)

            mw.progress.finish()

            showInfo(message)

            mw.moveToState("deckBrowser")


action = QAction("Pull from Duolingo", mw)
action.triggered.connect(sync_duolingo)
mw.form.menuTools.addAction(action)


