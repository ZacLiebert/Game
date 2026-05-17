## Build as EXE

The game can be built into a Windows `.exe` file using PyInstaller.

Run:

```bat
build_exe.bat
```

The output file will be created here:

```text
dist\MutationRPG.exe
```

To build manually:

```bat
py -3 -m pip install -r requirements.txt
py -3 -m pip install -r requirements-build.txt
py -3 build_exe.py
```

Note: The `dist` folder and `.exe` file are generated build files, so they are not included in the GitHub repository.
