# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the macOS CLI bundle (Apple Silicon, arm64).
# Produces: dist/scriber-cli/  ->  scriber-<ver>-macos-arm64.tar.gz (via CI)

from pathlib import PurePosixPath

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs

datas = []
binaries = []
hiddenimports = []

datas += collect_data_files('scriber.gui.assets')

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
        'av.__main__',
        'av.datasets',
        'huggingface_hub._hot_reload',
        'huggingface_hub.cli',
        'huggingface_hub.inference._mcp',
        'platformdirs.__main__',
        'pyannote.audio.__main__',
        'pyannote.audio.models.separation',
        'pyannote.audio.pipelines.pyannoteai',
        'pyannote.audio.sample',
        'pyannote.audio.tasks.separation',
        'pyannote.metrics.cli',
        'pyannote.metrics.plot',
        'pyannote.pipeline.experiment',
        'torch.testing',
        'torch.utils.benchmark',
        'torch._dynamo.test',
        'torch._inductor.test',
        'sklearn.tests',
        'transformers.commands',
        'transformers.cli',
    )
    return not name.startswith(excluded_prefixes) and not any(part in name for part in excluded_parts)


def keep_runtime_collected_path(src: str, dest: str) -> bool:
    norm_src = src.replace("\\", "/")
    norm_dest = dest.replace("\\", "/")
    combined = f"{norm_dest}/{PurePosixPath(norm_src).name}"
    excluded_fragments = (
        "/tests/",
        "/testing/",
        "/examples/",
        "/benchmark/",
        "/debug/",
        "/conftest",
        "/sample/",
        "/commands/",
        "/cli/",
        "/_mcp/",
        "/pyannoteai/",
        "/separation/",
    )
    return not any(fragment in norm_src or fragment in norm_dest or fragment in combined for fragment in excluded_fragments)


def trim_collected(datas, binaries, hiddenimports):
    datas = [item for item in datas if keep_runtime_collected_path(item[0], item[1])]
    binaries = [item for item in binaries if keep_runtime_collected_path(item[0], item[1])]
    hiddenimports = [name for name in hiddenimports if keep_runtime_submodule(name)]
    return datas, binaries, hiddenimports


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
        d, b, h = trim_collected(d, b, h)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

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
        'av.__main__',
        'av.datasets',
        'huggingface_hub._hot_reload',
        'huggingface_hub.cli',
        'huggingface_hub.inference._mcp',
        'platformdirs.__main__',
        'pyannote.audio.__main__',
        'pyannote.audio.models.separation',
        'pyannote.audio.pipelines.pyannoteai',
        'pyannote.audio.sample',
        'pyannote.audio.tasks.separation',
        'pyannote.metrics.cli',
        'pyannote.metrics.plot',
        'pyannote.pipeline.experiment',
        'torch.testing',
        'torch.testing._internal',
        'torch.utils.benchmark',
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
