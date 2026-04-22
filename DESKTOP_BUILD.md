# CocoAIStudy Desktop Build

## macOS

1. Activate the project virtual environment.
2. Run:

```bash
./build_macos_app.sh
```

Output:

```text
dist/CocoAIStudy.app
```

## Windows EXE

Build the Windows executable on a Windows machine from the same project folder:

```bat
build_windows_exe.bat
```

Output:

```text
dist\CocoAIStudy\CocoAIStudy.exe
```

## Notes

- The desktop app starts the local Streamlit server in the background and opens it in a native desktop window.
- User uploads, chat history, and problem banks are stored in the OS app data folder:
  - macOS: `~/Library/Application Support/CocoAIStudy`
  - Windows: `%APPDATA%\CocoAIStudy`
  - Linux: `~/.local/share/CocoAIStudy`
- The bundled app keeps code/assets inside the executable package and writes study data outside the app bundle.
- Windows `.exe` should be built on Windows. macOS cannot reliably produce a native Windows executable in this setup.
