from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List

import requests.exceptions
from anki.utils import splitFields, ids2str

import aqt
from aqt import mw
from aqt.operations import QueryOp
from aqt.qt import *
from aqt.utils import askUser, showWarning
from aqt.utils import showInfo
from .duolingo import Duolingo, LoginFailedException
from .duolingo_display_login_dialog import duolingo_display_login_dialog
from .duolingo_model import get_duolingo_model

WORD_CHUNK_SIZE = 50
ADD_STATUS_TEMPLATE = "Importing from Duolingo: {} of {} complete."


@dataclass
class VocabRetrieveResult:
    success: bool = False
    words_to_add: list = field(default_factory=list)
    language_string: Optional[str] = None
    lingo: Optional[Duolingo] = None


@dataclass
class AddVocabResult:
    notes_added: int = 0
    problem_vocabs: List[str] = field(default_factory=list)


def login_and_retrieve_vocab(username, password) -> VocabRetrieveResult:
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

        lingo = Duolingo(username, password)

        aqt.mw.taskman.run_on_main(
            lambda: aqt.mw.progress.update(
                label=f"Retrieving vocabulary...",
            )
        )
        vocabulary_response = lingo.get_vocabulary()

    except LoginFailedException:
        aqt.mw.taskman.run_on_main(
            lambda: showWarning(
                """
                <p>Logging in to Duolingo failed. Please check your Duolingo credentials.</p>

                <p>Having trouble logging in? You must use your <i>Duolingo</i> username and JWT.
                You <i>can't</i> use your Google or Facebook credentials, even if that's what you use to
                sign in to Duolingo.</p>

                <p>You can find your Duolingo username at
                <a href="https://www.duolingo.com/settings">https://www.duolingo.com/settings</a>.</p>
                """
            )
        )
        return result
    except requests.exceptions.ConnectionError:
        aqt.mw.taskman.run_on_main(
            lambda: showWarning("Could not connect to Duolingo. Please check your internet connection.")
        )
        return result

    language_string = vocabulary_response['language_string']
    vocabs = vocabulary_response['vocab_overview']

    did = mw.col.decks.id("Default")
    mw.col.decks.select(did)

    deck = mw.col.decks.get(did)
    deck['mid'] = model['id']
    mw.col.decks.save(deck)

    words_to_add = [vocab for vocab in vocabs if vocab['id'] not in gids_to_notes]
    result.success = True
    result.words_to_add = words_to_add
    result.language_string = language_string
    result.lingo = lingo

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
    word_chunks = [retrieve_result.words_to_add[x:x + WORD_CHUNK_SIZE] for x in range(0, total_word_count, WORD_CHUNK_SIZE)]
    lingo = retrieve_result.lingo

    aqt.mw.taskman.run_on_main(
        lambda: mw.progress.update(label=ADD_STATUS_TEMPLATE.format(0, total_word_count), value=0, max=total_word_count)
    )

    words_processed = 0
    for word_chunk in word_chunks:
        translations = {
            vocab['word_string']: ["Provide the translation for '{}' from {}.".format(vocab['word_string'], retrieve_result.language_string)]
            for vocab in word_chunk
        }

        for vocab in word_chunk:
            n = mw.col.newNote()

            # Update the underlying dictionary to accept more arguments for more customisable cards
            n._fmap = defaultdict(str, n._fmap)

            n['Gid'] = vocab['id']
            n['Gender'] = vocab['gender'] if vocab['gender'] else ''
            n['Source'] = '; '.join(translations[vocab['word_string']])
            n['Target'] = vocab['word_string']
            n['Pronunciation'] = vocab['normalized_string'].strip()
            n['Target Language'] = retrieve_result.language_string
            n.addTag(retrieve_result.language_string)
            n.addTag('duolingo_sync')

            if vocab['pos']:
                n.addTag(vocab['pos'])

            if vocab['skill']:
                n.addTag(vocab['skill'].replace(" ", "-"))

            num_cards = mw.col.addNote(n)

            if num_cards:
                result.notes_added += 1
            else:
                result.problem_vocabs.append(vocab['word_string'])
            words_processed += 1

            aqt.mw.taskman.run_on_main(
                lambda: mw.progress.update(label=ADD_STATUS_TEMPLATE.format(result.notes_added, total_word_count), value=words_processed, max=total_word_count)
            )

    aqt.mw.taskman.run_on_main(
        lambda: mw.progress.finish()
    )

    return result


def on_retrieve_success(retrieve_result: VocabRetrieveResult):
    if not retrieve_result.success:
        return

    if not retrieve_result.words_to_add:
        showInfo(f"Successfully logged in to Duolingo, but no new words found in {retrieve_result.language_string} language.")
    elif askUser(f"Add {len(retrieve_result.words_to_add)} notes from {retrieve_result.language_string} language?"):
        op = QueryOp(
            parent=mw,
            op=lambda col: add_vocab(retrieve_result),
            success=on_add_success,
        )

        op.with_progress(label=ADD_STATUS_TEMPLATE.format(0, len(retrieve_result.words_to_add))).run_in_background()
        return 1


def sync_duolingo():
    try:
        username, password = duolingo_display_login_dialog(mw)
    except TypeError:
        return

    op = QueryOp(
        parent=mw,
        op=lambda col: login_and_retrieve_vocab(username, password),
        success=on_retrieve_success,
    )

    op.with_progress(label="Logging in...").run_in_background()

action = QAction("Pull from Duolingo", mw)
qconnect(action.triggered, sync_duolingo)
mw.form.menuTools.addAction(action)
