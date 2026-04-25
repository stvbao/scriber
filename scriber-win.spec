# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows (x86_64)
# Produces: dist/Scriber/  →  Scriber-<ver>-windows.zip (via CI)

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

datas = []
binaries = []
hiddenimports = []

# Full collection for every package that has native extensions or lazy imports
# mlx / mlx_whisper intentionally omitted (Apple Silicon only)
_COLLECT = [
    'av',
    'ctranslate2',
    'faster_whisper',
    'torch',
    'torchaudio',
    'pyannote.audio',
    'pyannote.core',
    'pyannote.pipeline',
    'pyannote.metrics',
    'speechbrain',
    'asteroid_filterbanks',
    'einops',
    'transformers',
    'tokenizers',
    'sentencepiece',
    'huggingface_hub',
    'numpy',
    'scipy',
    'sklearn',
    'soundfile',
    'librosa',
    'platformdirs',
]

for pkg in _COLLECT:
    try:
        d, b, h = collect_all(pkg)
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
        'scriber.core.transcribe',
        'scriber.core.diarize',
        'scriber.core.merge',
        'scriber.core.export',
        'scriber.core.download',
        'scriber.core.translate',
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
        'mlx',
        'mlx_whisper',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Scriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # console=False: no terminal window on double-click; stdout still works
    # when launched from cmd.exe / PowerShell because the parent console is
    # inherited. This gives a clean GUI experience AND a working CLI.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,          # TODO: add Assets/icon.ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Scriber',
)
