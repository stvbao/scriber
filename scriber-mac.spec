# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for macOS (Apple Silicon, arm64)
# Produces: dist/Scriber.app  +  dist/Scriber-<ver>-macos-arm64.tar.gz (via CI)

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs, collect_submodules

datas = []
binaries = []
hiddenimports = []

datas += collect_data_files('scriber.gui.assets')

# Full collection for every package that has native extensions or lazy imports
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
        pass  # package not installed (e.g. CUDA-only wheels absent on Mac)

# MLX packages raise during import on headless builders, so collect the files
# directly instead of relying on import-time module discovery.
datas += collect_data_files('mlx', include_py_files=True)
datas += collect_data_files('mlx_whisper', include_py_files=True)
binaries += collect_dynamic_libs('mlx')

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
        'scriber.gui.assets',
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
    upx=False,         # UPX breaks some dylibs on macOS
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,  # uses current arch (arm64 on macos-14 runner)
    codesign_identity=None,
    entitlements_file=None,
    icon='Assets/icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='scriber',
)

app = BUNDLE(
    coll,
    name='Scriber.app',
    icon='Assets/icon.icns',
    bundle_identifier='com.stvbao.scriber',
    info_plist={
        'CFBundleName': 'Scriber',
        'CFBundleDisplayName': 'Scriber',
        'CFBundleShortVersionString': '0.1.1',
        'CFBundleVersion': '0.1.1',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '14.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 stvbao',
        # Allow opening audio files by drag-drop onto the dock icon
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Audio File',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': [
                    'public.mp3', 'public.mpeg-4-audio', 'com.apple.m4a-audio',
                    'public.wav', 'public.aiff-audio', 'public.ogg-audio',
                ],
            }
        ],
    },
)
