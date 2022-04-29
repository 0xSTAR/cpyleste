import sys

assert sys.platform == "win32", sys.exit(
                                """
        This build script is only for Windows users.
        You are on {}.
                                """.format(
                                    sys
                                     .platform
                                     .upper()
                                    )
                                )

assert (
    sys.version_info.major == 3 and
    sys.version_info
        .minor >= 7
),sys.exit(
"""
Must be on a Python of version 3.7 or newer.
You are on Python version {} ...
""".format(sys.version.split(" ")[0])
)

try:
    from cx_Freeze import setup, Executable
except ModuleNotFoundError:
    import subprocess
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            "cx-Freeze"
        ]
    )

    # re-import
    try:
        from cx_Freeze import setup,Executable
    except ImportError:
        sys.exit("Re-run the build script.")

build_exe_opts = {
    "packages":[
        "os","sys","math","dataclasses","io","functools","pygame","hagia","hagia.utils",
        "numpy","llvmlite","numba"
    ],
    "excludes": [
        "tkinter","PyInstaller","email","http",
        "html","urllib","xml","xmlrpc"
    ],
}

base = None if sys.platform != "win32" else "Win32GUI"

setup(
    name="cpyleste",
    version="0.1",
    description="Celeste Classic Python Port.",
    author="https://github.com/0xSTAR/",
    options={"build_exe":build_exe_opts},
    executables=[Executable("cpyleste.py",base=base)]
)
