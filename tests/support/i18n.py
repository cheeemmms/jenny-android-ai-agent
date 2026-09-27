"""Quali lingue ha la WebUI, e come si leggono i suoi file.

Le chiavi delle traduzioni vivono in un posto che nessun modello legge
(``jenny/templates/ui/assets/i18n/``): l'unico consumatore sono l'interfaccia e
i test, quindi una chiave mancante non fallisce da nessuna parte — ``i18n.t()``
ritorna la chiave grezza e l'utente legge ``settings.someKey`` a schermo.

La lista delle lingue sta qui una volta sola perche' i test che controllano
"tutte le lingue" sono una ventina, e ognuno se la riscriveva a mano: una lingua
nuova finiva cosi' in quelli aggiornati e spariva da tutti gli altri, che
continuavano a passare **ignorandola**. Con una lista sola, chi la dimentica la
dimentica in un punto solo.
"""

from __future__ import annotations

import json
from pathlib import Path

I18N_DIR = (
    Path(__file__).resolve().parents[2] / "jenny" / "templates" / "ui" / "assets" / "i18n"
)

#: La lingua di riferimento: il codice e' scritto in inglese e le chiavi delle
#: altre lingue si confrontano con le sue, non fra loro.
REFERENCE_LOCALE = "en"

#: Ogni lingua che la WebUI sa mostrare.
LOCALES: tuple[str, ...] = ("en", "it", "zh")


def load_locale(locale: str) -> dict:
    """Il file di ``locale``, letto come lo legge il browser (UTF-8)."""
    return json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))
