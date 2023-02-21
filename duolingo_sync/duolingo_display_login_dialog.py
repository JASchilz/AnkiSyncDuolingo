from aqt.qt import *


def duolingo_display_login_dialog(mw):
    d = QDialog(mw)
    d.setWindowTitle("Pull from Duolingo")
    d.setWindowModality(Qt.WindowModal)
    vbox = QVBoxLayout()
    l = QLabel("""
    <p>This plugin will make Anki notes and cards from the words you've learned in 
    your <strong>active</strong> Duolingo language. As you learn more words in Duolingo, use
    this tool again to pull those words into Anki.</p>
    
    <p>The cards and notes created by this plugin are customizable, and some languages may
    include <u>pronunciation</u> or <u>gender</u> that you can add to your cards. See the
    <a href="https://github.com/JASchilz/AnkiSyncDuolingo/">project page</a> for more information.</p>
    
    <p>Encounter a problem? Sometimes Duolingo makes changes to its servers that might require you to
    upgrade the plugin. See the list of <a href="https://github.com/JASchilz/AnkiSyncDuolingo/issues?q=is%3Aissue+is%3Aclosed">
    solved</a> and <a href="https://github.com/JASchilz/AnkiSyncDuolingo/issues">unsolved</a> issues. If you're having
    a language with a translations in a specific language, see the list of <a href="https://github.com/JASchilz/AnkiSyncDuolingo/labels/language-specific">
    language specific</a> issues. You can also see a list of <a href="https://github.com/JASchilz/AnkiSyncDuolingo/labels/feature-request">feature requests</a>.
    You're invited to comment or add new issues.</p>
    
    <p><strong>Due to recent changes in the Duolingo service, this plugin is unable to provide translations for your vocabulary.</strong>
    You can edit in the translations on your first review. See <a href="https://github.com/JASchilz/AnkiSyncDuolingo/issues/61">this support issue</a>
    for more information.</p>

    <p>Due to changes to the Duolingo service, you must enter your JWT to authenticate with Duolingo. See <a href="https://github.com/JASchilz/AnkiSyncDuolingo/issues/64">
    this support issue</a> for more information on authentication.</p>

    <p>You can retrieve your JWT by logging into Duolingo in a browser and then pasting the following script into your browser's
    developer console on <a href="https://www.duolingo.com/">www.duolingo.com</a>:</p>

    <pre>
(() => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; jwt_token=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
})()
    </pre>
    
    <hr>

    <p>Please enter your <strong>Duolingo</strong> username and JWT.</p>
    """)
    l.setTextInteractionFlags(Qt.TextSelectableByMouse)
    l.setOpenExternalLinks(True)
    l.setWordWrap(True)
    vbox.addWidget(l)
    vbox.addSpacing(20)
    g = QGridLayout()
    l1 = QLabel(_("Duolingo Username:"))
    g.addWidget(l1, 0, 0)
    user = QLineEdit()
    g.addWidget(user, 0, 1)
    l2 = QLabel(_("Duolingo JWT:"))
    g.addWidget(l2, 1, 0)
    passwd = QLineEdit()
    passwd.setEchoMode(QLineEdit.Password)
    g.addWidget(passwd, 1, 1)
    vbox.addLayout(g)
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.button(QDialogButtonBox.Ok).setAutoDefault(True)
    bb.accepted.connect(d.accept)
    bb.rejected.connect(d.reject)
    vbox.addWidget(bb)
    d.setLayout(vbox)
    d.show()
    accepted = d.exec_()
    u = user.text()
    p = passwd.text()
    if not accepted or not u or not p:
        return
    return (u, p)
