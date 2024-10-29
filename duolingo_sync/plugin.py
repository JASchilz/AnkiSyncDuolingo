from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List
import traceback

import requests.exceptions
from anki.utils import splitFields, ids2str
from anki.decks import DEFAULT_DECK_ID

import aqt
from aqt import mw
from aqt.operations import QueryOp
from aqt.qt import *
from aqt.utils import askUser, showWarning
from aqt.utils import showInfo
from .duolingo import Duolingo
from .duolingo_display_login_dialog import duolingo_display_login_dialog
from .duolingo_model import get_duolingo_model

import os
import requests

WORD_CHUNK_SIZE = 50
ADD_STATUS_TEMPLATE = "Importing from Duolingo: {} of {} complete."


@dataclass
class VocabResult:
    identifier: str
    text: str
    audioURL: str
    isNew: bool
    translations: List[str] = field(default_factory=list)


@dataclass
class VocabRetrieveResult:
    words_to_add: List[VocabResult]
    success: bool = False
    language_string: Optional[str] = None
    lingo: Optional[Duolingo] = None


@dataclass
class AddVocabResult:
    notes_added: int = 0
    problem_vocabs: List[str] = field(default_factory=list)


def login_and_retrieve_vocab(jwt) -> VocabRetrieveResult:
    result = VocabRetrieveResult(success=False, words_to_add=[])

    model = get_duolingo_model(aqt)

    note_ids = mw.col.findNotes('tag:duolingo_sync')
    notes = mw.col.db.list("select flds from notes where id in {}".format(ids2str(note_ids)))
    gids_to_notes = {splitFields(note)[0]: note for note in notes}

    try:
        aqt.mw.taskman.run_on_main(
            lambda: aqt.mw.progress.update(
                label=f"Logging in...",
            )
        )

        lingo = Duolingo(jwt=jwt)

        aqt.mw.taskman.run_on_main(
            lambda: aqt.mw.progress.update(
                label=f"Retrieving vocabulary...",
            )
        )

    except requests.exceptions.ConnectionError:
        aqt.mw.taskman.run_on_main(
            lambda: showWarning("Could not connect to Duolingo. Please check your internet connection.")
        )
        return result

    current_language = lingo.get_user_info()['learning_language_string']
    language_abbreviation = lingo.get_abbreviation_of(current_language)
    vocabulary_response = lingo.get_vocabulary(language_abbreviation)

    did = mw.col.decks.get(DEFAULT_DECK_ID)['id']
    mw.col.decks.select(did)

    deck = mw.col.decks.get(did)
    deck['mid'] = model['id']
    mw.col.decks.save(deck)

    words_to_add_models = []
    for vocab in vocabulary_response:
        id = vocab['text'] + "-" + language_abbreviation
        if id not in gids_to_notes:
            words_to_add_models.append(VocabResult(identifier=id, text=vocab["text"], audioURL=vocab["audioURL"], isNew=vocab["isNew"],
                                             translations=vocab["translations"]))

    result.words_to_add = words_to_add_models
    result.success = True
    result.language_string = current_language

    return result


def on_add_success(add_result: AddVocabResult) -> None:
    message = "{} notes added.".format(add_result.notes_added)

    if add_result.problem_vocabs:
        message += " Failed to add: " + ", ".join(add_result.problem_vocabs)

    showInfo(message)
    mw.moveToState("deckBrowser")


def add_vocab(retrieve_result: VocabRetrieveResult) -> AddVocabResult:
    result = AddVocabResult()

    total_word_count = len(retrieve_result.words_to_add)

    aqt.mw.taskman.run_on_main(
        lambda: mw.progress.update(label=ADD_STATUS_TEMPLATE.format(0, total_word_count), value=0, max=total_word_count)
    )

    words_processed = 0
    for vocabResult in retrieve_result.words_to_add:
        n = mw.col.newNote()

        # Update the underlying dictionary to accept more arguments for more customisable cards
        n._fmap = defaultdict(str, n._fmap)

        n['Gid'] = vocabResult.identifier
        n['Gender'] = ''
        n['Source'] = '; '.join(vocabResult.translations)
        n['Pronunciation'] = ''
        n['Target Language'] = retrieve_result.language_string
        n.addTag(retrieve_result.language_string)
        n.addTag('duolingo_sync')

        # Add audio file to the target, this autoplays. I'm not sure if theres a better way to attach
        # audio, as replay audio controls do not work
        audio_filename = '{0}.mp3'.format(vocabResult.text)
        audio_path = os.path.join(mw.col.media.dir(), audio_filename)  # Path in Anki's media folder
        audio_tag = f'<br><br><audio class="custom-audio" controls autoplay><source src="{audio_filename}" type="audio/mpeg"></audio>'
        download_audio_from_url(vocabResult.audioURL, audio_path)

        n['Target'] = vocabResult.text + audio_tag
        css = """
          <style>
          .custom-audio {
              height: 60px; /* Adjust height as needed */
          }
          </style>
          """
        note_model = n.model()
        note_model['css'] += css

        num_cards = mw.col.addNote(n)

        if num_cards:
            result.notes_added += 1
        else:
            result.problem_vocabs.append(vocabResult.text)
        words_processed += 1

        aqt.mw.taskman.run_on_main(
            lambda: mw.progress.update(label=ADD_STATUS_TEMPLATE.format(result.notes_added, total_word_count),
                                       value=words_processed, max=total_word_count)
        )

    aqt.mw.taskman.run_on_main(
        lambda: mw.progress.finish()
    )

    return result


# Downloads audio from a given URL and saves it on the file system
# used to then embed the audio links from the duolingo API to cards
def download_audio_from_url(url, save_path):
    # Function to download audio file from URL
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def on_retrieve_success(retrieve_result: VocabRetrieveResult):
    if not retrieve_result.success:
        return

    if not retrieve_result.words_to_add:
        showInfo(
            f"Successfully logged in to Duolingo, but no new words found in {retrieve_result.language_string} language.")
    elif askUser(f"Add {len(retrieve_result.words_to_add)} notes from {retrieve_result.language_string} language?"):
        op = QueryOp(
            parent=mw,
            op=lambda col: add_vocab(retrieve_result),
            success=on_add_success,
        )

        op.with_progress(label=ADD_STATUS_TEMPLATE.format(0, len(retrieve_result.words_to_add))).run_in_background()
        return 1


def sync_duolingo():
    aqt.mw.taskman.run_on_main(
        lambda: showWarning(
            """
            <p>Duolingo has been making breaking changes to their API every year or so. Duolingo does not officially
            support any third party programs like this one, and I have found it more and more difficult to keep up with
            their changes. Additionally, I don't use this plugin myself. I would therefore consider this add-on 
            <u><span style="color: red">unsupported</span></u>. Specifically:
            <ul>
            <li>Any further changes by Duolingo which break this add-on might go unfixed.</li>
            <li>Any release that I do make in response to a change by Duolingo might have disruptive changes. For example,
            Duolingo might make some kind of information unavailable to this plugin which previously was available on its cards.</li>
            <li>This add-on is only available for manual install from <a href="https://github.com/JASchilz/AnkiSyncDuolingo/releases">
            https://github.com/JASchilz/AnkiSyncDuolingo/releases</a> and not the AnkiWeb site.</li>
            <li>I'm inviting any programmer who uses this themselves and has an interest in maintaining it to take 
            ownership at <a href="https://github.com/JASchilz/AnkiSyncDuolingo/issues/78">https://github.com/JASchilz/AnkiSyncDuolingo/issues/78</a>.</li>
            </p>
            
            <p>To see any issues or open a new issue, see <a href="https://github.com/JASchilz/AnkiSyncDuolingo/issues">
            the issue tracker</a>.</p>
            
            <p>Click "OK" to log in to Duolingo. This plugin will then pull words from <u>whatever language you have most
            recently studied</u>.</p>
            """
        )
    )
    try:
        jwt = duolingo_display_login_dialog(mw)
    except TypeError:
        return

    op = QueryOp(
        parent=mw,
        op=lambda col: login_and_retrieve_vocab(jwt),
        success=on_retrieve_success,
    )

    op.with_progress(label="Logging in...").run_in_background()


action = QAction("Pull from Duolingo", mw)
qconnect(action.triggered, sync_duolingo)
mw.form.menuTools.addAction(action)
