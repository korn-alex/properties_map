cd ..
.env/Scripts/activate.ps1
$env:FLASK_APP = "webserver"
python -m flask run --with-threads
Read-Host -Prompt "Press Enter to exit"