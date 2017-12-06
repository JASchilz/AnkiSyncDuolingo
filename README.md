# AnkiSyncDuolingo
Pull your Duolingo vocabulary into Anki, as an Anki plugin This plugin works, but is under development. It is not yet available in the Anki plugin registry, but you can install it manually.

See the [issues](https://github.com/JASchilz/AnkiSyncDuolingo/issues/) for the features I intend to add or fix.

The connection to Duolingo's API is provided by [KartikTalwar's](https://github.com/KartikTalwar/) [Duolingo-API Python library](https://github.com/KartikTalwar/Duolingo/). Because of packaging requirements for Anki plugins, a modified version of that library is provided in this repository.

## Installing
To install, unzip the [latest release](https://github.com/JASchilz/AnkiSyncDuolingo/releases/latest/) directly into your Anki plugins directory. After unzipping, the `duolingo_sync.py` file and the `duolingo_sync` directory should both reside directly in your plugins directory.

## Use
Start Anki and select Tools ~> Sync Duolingo. You will be prompted for your Duolingo username and password. If a Duolingo note type does not already exist then the plugin will create this for you and begin syncing your Duolingo vocabulary into Anki. The synced notes will appear as cards in your "Default" deck. 

At this point, you can move the cards to another deck of your choice. The cards are tagged with "duolingo_sync". This tag, plus the unique "GID" field on each note is what allows the plugin to identify all of the vocabulary that have already been retrieved from Duolingo. Do not remove the tag, or change the GID.

Currently, the plugin will only sync cards from your *active* Duolingo language. This is the language that you last selected in Duolingo. To change your active language, log in to Duolingo and select from the languages menu the language that you wish to sync to Anki.

## Getting Involved

Feel free to open pull requests or issues. [GitHub](https://github.com/JASchilz/AnkiSyncDuolingo) is the canonical location of this project.

Here's the general sequence of events for code contribution:

1. Either:
    * Identify an existing issue in the [issue tracker](https://github.com/JASchilz/AnkiSyncDuolingo/issues/) and comment that you'd like to try to resolve it.
    * Open an issue in the [issue tracker](https://github.com/JASchilz/AnkiSyncDuolingo/issues/).
2. Get acknowledgement/concurrence.
3. Submit a pull request to resolve the issue. Include documentation, if appropriate.

