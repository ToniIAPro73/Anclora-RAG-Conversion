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
  echo [ERROR] Debes definir ANCLORA_API_TOKENS o ANCLORA_JWT_SECRET antes de iniciar los servicios.
  exit /b 1
)

docker compose %* up -d
endlocal
