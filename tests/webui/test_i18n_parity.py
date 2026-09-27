"""Parità delle chiavi fra i file i18n della WebUI.

Una chiave presente in una lingua e assente in un'altra non fallisce da nessuna
parte: ``i18n.t()`` ritorna la chiave grezza, e l'utente di quella lingua si
ritrova ``subagents.relaunch`` stampato nell'interfaccia. Questo test è il posto
dove quella divergenza si nota.

Le lingue non si nominano qui: sono quelle di ``tests/support/i18n.py``, così una
lingua nuova entra nei controlli anche di tutti gli altri file della suite.
"""

from __future__ import annotations

import re

from support.i18n import I18N_DIR, LOCALES, REFERENCE_LOCALE, load_locale


def _flatten(value: dict, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    for key, child in value.items():
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(child, dict):
            keys |= _flatten(child, full)
        else:
            keys.add(full)
    return keys


def _flat_strings(value: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, child in value.items():
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(child, dict):
            out.update(_flat_strings(child, full))
        elif isinstance(child, str):
            out[full] = child
    return out


def test_every_locale_has_the_same_keys_as_the_reference() -> None:
    """Ogni lingua ha le chiavi della lingua di riferimento, e viceversa."""
    reference = _flatten(load_locale(REFERENCE_LOCALE))
    for locale in LOCALES:
        keys = _flatten(load_locale(locale))
        assert keys - reference == set(), f"chiavi presenti solo in {locale}.json"
        assert reference - keys == set(), f"chiavi assenti da {locale}.json"


def test_subagent_panel_strings_exist_in_every_locale() -> None:
    """Il pannello subagent non deve avere stringhe hardcoded nel JS."""
    expected = {
        "subagents.title",
        # Nessuna intestazione "RUNNING"/"RECENT": in carosello il conteggio
        # dell'header e il colore di stato delle card le rendevano superflue.
        # Due varianti del conteggio: senza card terminali "0 appena conclusi"
        # sarebbe rumore, ed è il caso normale.
        "subagents.headCount",
        "subagents.headCountFinished",
        "subagents.untitled",
        "subagents.openDetail",
        "subagents.idle",
        "subagents.attempt",
        "subagents.stalledHint",
        "subagents.autoCapReached",
        "subagents.stop",
        "subagents.relaunch",
        "subagents.stopped",
        "subagents.relaunched",
        "subagents.actionFailed",
    }
    # Nessuna chiave "subagents.empty": il pannello non ha più uno stato vuoto —
    # zero card significa elemento `hidden`, non un placeholder.
    # Etichette della modale di dettaglio: la card mostra una riga, il resto è lì.
    # Manca chi ha perso la sua etichetta nel telaio: stato e orologi stanno nel
    # riepilogo, dove il senso è nell'accostamento e non in una chiave incolonnata
    # ("in corso · 4m 10s · fermo 2s"), e la coda tool non è più un blocco a sé.
    expected |= {
        f"subagents.detail.{field}"
        for field in (
            "type", "attempt", "phase", "iteration", "stopReason",
            "task", "diagnostics", "outcome",
        )
    }
    # Ogni stato e ogni fase che il backend può mandare ha la sua etichetta.
    expected |= {
        f"subagents.state.{state}"
        for state in ("running", "stalled", "done", "failed", "cancelled")
    }
    expected |= {
        f"subagents.phase.{phase}"
        for phase in (
            "initializing",
            "awaiting_tools",
            "tools_completed",
            "final_response",
            "done",
            "error",
        )
    }
    for locale in LOCALES:
        keys = _flatten(load_locale(locale))
        assert expected <= keys, f"chiavi mancanti in {locale}.json: {sorted(expected - keys)}"


def test_workspace_file_help_strings_exist_in_every_locale() -> None:
    """La spiegazione dei file del workspace non vive più dentro i file.

    ``AGENTS.md``, ``USER.md``, ``memory/MEMORY.md`` e ``HEARTBEAT.md`` nascono
    vuoti: a cosa servono — e cosa *non* ci va scritto — lo dice lo sheet della
    WebUI. ``SOUL.md`` nasce pieno, ma è la destinazione indicata da tre di
    quei quattro testi, quindi la sua voce non è meno obbligatoria delle altre.
    La parità fra le due lingue non basta a proteggerlo: una chiave
    cancellata in tutt'e due resta simmetrica, e l'unico segno sarebbe uno
    sheet che non compare più. Qui l'elenco è esplicito.
    """
    expected = {
        # Azione primaria: lo sheet spiega, ma l'editor deve restare raggiungibile.
        "workspace.fileHelp.open",
        "workspace.fileHelp.agents",
        "workspace.fileHelp.user",
        "workspace.fileHelp.soul",
        "workspace.fileHelp.memory",
        "workspace.fileHelp.heartbeat",
    }
    for locale in LOCALES:
        keys = _flatten(load_locale(locale))
        assert expected <= keys, f"chiavi mancanti in {locale}.json: {sorted(expected - keys)}"


def test_workspace_file_help_map_points_at_existing_keys() -> None:
    """Il mapping path→chiave nel JS e i due JSON devono dire la stessa cosa.

    ``fileHelpText()`` ripiega su stringa vuota quando la chiave non esiste, e
    una chiave sbagliata quindi non rompe niente: fa sparire lo sheet in
    silenzio. Questo test la vede.
    """
    import re

    js = (I18N_DIR.parent / "mobile-workspace.js").read_text(encoding="utf-8")
    block = re.search(r"const FILE_HELP_KEYS = \{(.*?)\n\};", js, re.S)
    assert block is not None, "FILE_HELP_KEYS non trovato in mobile-workspace.js"
    mapping = dict(re.findall(r"'([^']+)':\s*'([^']+)'", block.group(1)))

    assert set(mapping) == {"AGENTS.md", "USER.md", "SOUL.md", "HEARTBEAT.md", "memory/MEMORY.md"}
    for locale in LOCALES:
        keys = _flatten(load_locale(locale))
        missing = set(mapping.values()) - keys
        assert missing == set(), f"chiavi referenziate dal JS ma assenti in {locale}.json: {sorted(missing)}"


def test_dead_subagent_keys_are_gone_from_every_locale() -> None:
    """Una chiave che nessuno legge più è debito: la parità la terrebbe in vita.

    ``subagents.empty`` serviva al placeholder di un pannello vuoto, che non
    esiste più (zero card = elemento ``hidden``). Le quattro etichette della
    modale sono cadute con il telaio: stato e orologi vivono accostati nel
    riepilogo, senza chiave davanti, e "Tool recenti" non è più un blocco perché
    la coda dello snapshot è diventata il ripiego della lista di attività.
    """
    ui_assets = I18N_DIR.parent
    chat_js = (ui_assets / "mobile-chat.js").read_text(encoding="utf-8")
    for dead in ("subagents.empty", "subagents.detail.state", "subagents.detail.elapsed",
                 "subagents.detail.idle", "subagents.detail.toolEvents"):
        assert dead not in chat_js
        for locale in LOCALES:
            assert dead not in _flatten(load_locale(locale)), f"{dead} è ancora in {locale}.json"


def test_placeholders_match_the_reference_locale() -> None:
    """Gli stessi ``{segnaposto}`` in ogni lingua: uno mancante stampa ``{n}``.

    Il confronto è con l'inglese, non fra le lingue a coppie: basta che due
    traduzioni sbaglino lo stesso segnaposto perché un confronto incrociato lo
    trovi simmetrico, mentre lo schermo mostra comunque ``{n}``.
    """

    def placeholders(text: str) -> set[str]:
        return set(re.findall(r"\{(\w+)\}", text))

    reference = _flat_strings(load_locale(REFERENCE_LOCALE))
    mismatched = [
        f"{locale}.{key}"
        for locale in LOCALES
        for key, text in _flat_strings(load_locale(locale)).items()
        if key in reference and placeholders(text) != placeholders(reference[key])
    ]
    assert mismatched == []
