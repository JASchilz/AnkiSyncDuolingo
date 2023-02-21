from .jwt import decode
from pprint import pprint
from aqt import AnkiQt
from aqt.qt import *

def duolingo_display_login_dialog(mw: AnkiQt):
    d = QDialog()
    d.setWindowTitle("Pull from Duolingo")
    d.setWindowModality(Qt.WindowModality.WindowModal)
    d.resize(1024, 768)

    url = "https://www.duolingo.com/"

    token = None
    uuid = None

    def on_cookie_added(cookie) -> None:
        nonlocal token
        nonlocal uuid

        if cookie.name() == b"jwt_token":
            token = bytes(cookie.value()).decode()

        if token is not None:
            d.close()

        return

    webview = QWebEngineView()
    webview.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

    profile = QWebEngineProfile("storage", webview)
    cookie_store = profile.cookieStore()
    cookie_store.deleteAllCookies()  # May want to remove once working
    cookie_store.cookieAdded.connect(on_cookie_added)

    webpage = QWebEnginePage(profile, webview)

    webview.setPage(webpage)
    webview.load(QUrl(url))

    lay = QVBoxLayout()
    lay.addWidget(webview)
    d.setLayout(lay)

    d.show()
    d.exec()

    decoded = decode(token, algorithms=["HS256"], options={"verify_signature": False})
    uuid = decoded["sub"]

    webview.destroy()

    return token, uuid

