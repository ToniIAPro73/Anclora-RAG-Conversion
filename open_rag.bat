@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

if exist .env (
  for /f "usebackq tokens=* delims=" %%a in (".env") do (
    set "line=%%a"
    if not "!line!"=="" if not "!line:~0,1!"=="#" (
      for /f "tokens=1* delims==" %%i in ("!line!") do (
        if not "%%i"=="" set "%%i=%%j"
      )
    )
  )
)

if not defined ANCLORA_API_TOKENS if not defined ANCLORA_JWT_SECRET (
  if defined ANCLORA_DEFAULT_API_TOKEN (
    set "ANCLORA_API_TOKENS=%ANCLORA_DEFAULT_API_TOKEN%"
    set "ANCLORA_API_TOKEN=%ANCLORA_DEFAULT_API_TOKEN%"
    >&2 echo [WARN] No se definieron ANCLORA_API_TOKENS ni ANCLORA_JWT_SECRET; se usará el token por defecto.
  ) else (
    >&2 echo [ERROR] Debes definir ANCLORA_API_TOKENS, ANCLORA_JWT_SECRET o ANCLORA_DEFAULT_API_TOKEN antes de iniciar los servicios.
    exit /b 1
  )
)

docker compose %* up -d
endlocal
