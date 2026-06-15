from pathlib import Path


def test_site_files_exist():
    root = Path("site")
    required = [
        root / "index.html",
        root / "app.html",
        root / "styles.css",
        root / "app.js",
        root / "ui_copy.js",
        root / "site_data.js",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert missing == []


def test_site_includes_blueprint_and_asset_explorer_hooks():
    html = Path("site/index.html").read_text(encoding="utf-8")
    app_html = Path("site/app.html").read_text(encoding="utf-8") if Path("site/app.html").exists() else ""
    js = Path("site/app.js").read_text(encoding="utf-8")

    assert 'id="blueprint-section"' in html
    assert "asset_explorer_rows" in js
    assert "CURRENT_LOCALE" in js
    assert 'id="compare-asset-filter"' in html
    assert 'id="narrative-pulse"' in html
    assert "narrative_explorer_rows" in js
    assert 'id="explorer-mode-assets"' in html
    assert 'id="explorer-mode-narratives"' in html
    assert "narrativeList" in js
    assert 'href="./app.html"' in html
    assert 'id="nav-link-language"' in html
    assert 'id="roadmap-grid"' in html
    assert 'id="app-shell"' in app_html
    assert 'id="app-link-language"' in app_html
    assert 'id="app-hero-title"' in app_html
    assert 'id="app-signal-strip"' in app_html
    assert 'id="app-insight-grid"' in app_html
    assert "renderAppInsights" in js
    assert 'id="app-leaderboard"' in app_html
    assert 'id="app-rotation-board"' in app_html
    assert 'id="app-alerts"' in app_html
    assert "renderAppCommandCenter" in js
    assert 'id="app-attention-bars"' in app_html
    assert 'id="app-narrative-bars"' in app_html
    assert 'id="app-rs-bars"' in app_html
    assert "renderAppVisuals" in js
    assert 'id="app-refresh-note"' in app_html
    assert "renderAppRefreshStatus" in js
    assert "run_metadata" in js
    assert "driver_mix" in js
    assert "narrative_health" in js
    assert "formatDriverSummary" in js
    assert "formatManifestPath" in js
