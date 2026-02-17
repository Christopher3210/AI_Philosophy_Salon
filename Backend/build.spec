# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Azure Speech SDK DLLs
azure_speech_path = os.path.join(
    os.path.dirname(os.path.abspath(SPEC)),
    '..', 'venv310', 'lib', 'site-packages', 'azure', 'cognitiveservices', 'speech'
)
azure_dlls = [(os.path.join(azure_speech_path, f), 'azure/cognitiveservices/speech')
              for f in os.listdir(azure_speech_path) if f.endswith('.dll')]

a = Analysis(
    ['main_unity.py'],
    pathex=[os.path.dirname(os.path.abspath(SPEC))],
    binaries=azure_dlls,
    datas=[
        ('agents/configs', 'agents/configs'),
    ],
    hiddenimports=[
        'azure.cognitiveservices.speech',
        'websockets',
        'websockets.server',
        'websockets.legacy',
        'websockets.legacy.server',
        'openai',
        'yaml',
        'asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhilosophySalonBackend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for debug output
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhilosophySalonBackend',
)
