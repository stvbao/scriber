# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the macOS CLI bundle (Apple Silicon, arm64).
# Produces: dist/scriber-cli/  ->  scriber-<ver>-macos-arm64.tar.gz (via CI)

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# Avoid dragging package test suites, examples, and training/debug tools into the
# Homebrew CLI artifact. Runtime package hooks still collect native libraries.
def keep_runtime_submodule(name):
    excluded_parts = (
        '.tests',
        '.testing',
        '._testing',
        '.test_',
        '.examples',
        '.benchmark',
        '.debug',
        '.conftest',
    )
    excluded_prefixes = (
        'torch.testing',
        'torch.utils.benchmark',
        'torch._dynamo.test',
        'torch._inductor.test',
        'sklearn.tests',
        'transformers.commands',
        'transformers.cli',
    )
    return not name.startswith(excluded_prefixes) and not any(part in name for part in excluded_parts)


_COLLECT = [
    'av',
    'ctranslate2',
    'faster_whisper',
    'pyannote.audio',
    'pyannote.core',
    'pyannote.pipeline',
    'pyannote.metrics',
    'speechbrain',
    'asteroid_filterbanks',
    'einops',
    'huggingface_hub',
    'platformdirs',
]

for pkg in _COLLECT:
    try:
        d, b, h = collect_all(pkg, filter_submodules=keep_runtime_submodule)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

a = Analysis(
    ['scriber/__main__.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.sip',
        'scriber',
        'scriber.cli',
        'scriber.app',
        'scriber.core.audio',
        'scriber.core.batch',
        'scriber.core.transcribe',
        'scriber.core.diarize',
        'scriber.core.merge',
        'scriber.core.export',
        'scriber.core.download',
        'scriber.core.model_cache',
        'scriber.core.translate',
        'scriber.gui.icon',
        'scriber.gui.main_window',
        'scriber.gui.worker',
        'scriber.gui.widgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
        'PIL',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='scriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='scriber-cli',
)
