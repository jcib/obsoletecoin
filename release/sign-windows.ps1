param([Parameter(Mandatory=$true)][string]$CertificateThumbprint,[Parameter(Mandatory=$true)][string]$File)
$ErrorActionPreference='Stop'
# Certificate must already exist in the operator's Windows certificate store.
# No private key or password is passed in source or command arguments.
& signtool sign /sha1 $CertificateThumbprint /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $File
if ($LASTEXITCODE -ne 0) { throw 'Signing failed' }
& signtool verify /pa /all $File
if ($LASTEXITCODE -ne 0) { throw 'Signature verification failed' }
