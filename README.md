# AnkiSyncDuolingo
Pull your Duolingo vocabulary into Anki, as an Anki plugin This plugin works, but is under development. It is not yet available in the Anki plugin registry, but you can install it manually.

See the [issues](https://github.com/JASchilz/AnkiSyncDuolingo/issues/) for the features I intend to add or fix.

## Installing
To install, unzip the [latest release](https://github.com/JASchilz/AnkiSyncDuolingo/releases/latest/) directly into your Anki plugins directory. After unzipping, the `duolingo_sync.py` file and the `duolingo_sync` directory should both reside directly in your plugins directory.

## Use
Start Anki and select Tools ~> Sync Duolingo. You will be prompted for your Duolingo username and password. If a Duolingo sync deck and card type do not already exist then the plugin will create these for you and begin syncing your Duolingo words into Anki.

Currently, the plugin will only sync cards from your *active* Duolingo language. This is the language that you last selected in Duolingo. To update your active language, log in to Duolingo and select the language that you would sync from your languages menu.

## Getting Involved

Feel free to open pull requests or issues. [GitHub](https://github.com/JASchilz/AnkiSyncDuolingo) is the canonical location of this project.

Here's the general sequence of events for code contribution:

1. Either:
    * Identify an existing issue in the [issue tracker](https://github.com/JASchilz/AnkiSyncDuolingo/issues/) and comment that you'd like to try to resolve it.
    * Open an issue in the [issue tracker](https://github.com/JASchilz/AnkiSyncDuolingo/issues/).
2. Get acknowledgement/concurrence.
3. Submit a pull request to resolve the issue. Include documentation, if appropriate.

