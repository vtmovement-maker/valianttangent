@echo off
echo Starting local test server...
echo The website will open in your default browser.
echo Keep this window open while you test. Close it when you are done.
echo.
start http://127.0.0.1:8000
py -m http.server 8000
