$env:API_SERVER_VERSION="1.0.0-dev"
$env:SYSTEM_VERSION="1.0.1-dev"
$env:DTR_ENV="development"
$env:DTR_DB_CREATE="True"
$env:DTR_DB_PASSWORD="password"
$env:DTR_DB_USER="dtr_user"
$env:DTR_DB_NAME="dtr"

C:\Users\coren\Documents\info\virtual\dtr\api\Scripts\Activate.ps1

flask --app "api:create_app()" run --debug