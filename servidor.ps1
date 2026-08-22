param(
    [int]$Port = 8787
)

$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath($PSScriptRoot)
$rootWithSeparator = $root.TrimEnd('\') + '\'
$mimeTypes = @{
    '.css' = 'text/css; charset=utf-8'; '.html' = 'text/html; charset=utf-8'; '.js' = 'text/javascript; charset=utf-8';
    '.svg' = 'image/svg+xml'; '.png' = 'image/png'; '.jpg' = 'image/jpeg'; '.jpeg' = 'image/jpeg'; '.ico' = 'image/x-icon';
    '.exe' = 'application/octet-stream'; '.json' = 'application/json; charset=utf-8'; '.txt' = 'text/plain; charset=utf-8'
}

function Send-Response {
    param(
        [System.IO.Stream]$Stream,
        [int]$StatusCode,
        [string]$StatusText,
        [string]$ContentType,
        [byte[]]$Bytes,
        [string]$FilePath,
        [bool]$SendBody,
        [string]$ContentDisposition
    )

    $length = if ($FilePath) { (Get-Item -LiteralPath $FilePath).Length } elseif ($Bytes) { $Bytes.Length } else { 0 }
    $headers = "HTTP/1.1 $StatusCode $StatusText`r`nContent-Type: $ContentType`r`nContent-Length: $length`r`nConnection: close`r`n"
    if ($ContentDisposition) { $headers += "Content-Disposition: $ContentDisposition`r`n" }
    $headers += "X-Content-Type-Options: nosniff`r`n`r`n"
    $headerBytes = [System.Text.Encoding]::ASCII.GetBytes($headers)
    $Stream.Write($headerBytes, 0, $headerBytes.Length)

    if ($SendBody) {
        if ($FilePath) {
            $file = [System.IO.File]::OpenRead($FilePath)
            try { $file.CopyTo($Stream) } finally { $file.Dispose() }
        } elseif ($Bytes) {
            $Stream.Write($Bytes, 0, $Bytes.Length)
        }
    }
}

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
try {
    $listener.Start()
} catch {
    # Another copy is probably already serving the page on this computer.
    exit 0
}

try {
    while ($true) {
        $client = $listener.AcceptTcpClient()
        try {
            $stream = $client.GetStream()
            $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::ASCII, $false, 8192, $true)
            $requestLine = $reader.ReadLine()
            while (($line = $reader.ReadLine()) -ne $null -and $line.Length -gt 0) { }

            if ([string]::IsNullOrWhiteSpace($requestLine)) { continue }
            $request = $requestLine.Split(' ')
            $method = $request[0].ToUpperInvariant()
            if ($request.Length -lt 2 -or ($method -ne 'GET' -and $method -ne 'HEAD')) {
                Send-Response -Stream $stream -StatusCode 405 -StatusText 'Method Not Allowed' -ContentType 'text/plain; charset=utf-8' -Bytes ([System.Text.Encoding]::UTF8.GetBytes('Método no permitido.')) -SendBody $true
                continue
            }

            $path = $request[1].Split('?')[0]
            $relative = [System.Uri]::UnescapeDataString($path).TrimStart('/').Replace('/', '\')
            if ([string]::IsNullOrWhiteSpace($relative)) { $relative = 'index.html' }
            $requestedFile = [System.IO.Path]::GetFullPath((Join-Path $root $relative))
            if (-not $requestedFile.StartsWith($rootWithSeparator, [System.StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $requestedFile -PathType Leaf)) {
                Send-Response -Stream $stream -StatusCode 404 -StatusText 'Not Found' -ContentType 'text/plain; charset=utf-8' -Bytes ([System.Text.Encoding]::UTF8.GetBytes('Archivo no encontrado.')) -SendBody ($method -eq 'GET')
                continue
            }

            $extension = [System.IO.Path]::GetExtension($requestedFile).ToLowerInvariant()
            $contentType = if ($mimeTypes.ContainsKey($extension)) { $mimeTypes[$extension] } else { 'application/octet-stream' }
            $disposition = if ($extension -eq '.exe') { 'attachment; filename="YouTube a MP3.exe"' } else { $null }
            Send-Response -Stream $stream -StatusCode 200 -StatusText 'OK' -ContentType $contentType -FilePath $requestedFile -SendBody ($method -eq 'GET') -ContentDisposition $disposition
        } catch {
            try {
                Send-Response -Stream $stream -StatusCode 500 -StatusText 'Internal Server Error' -ContentType 'text/plain; charset=utf-8' -Bytes ([System.Text.Encoding]::UTF8.GetBytes('Error interno.')) -SendBody $true
            } catch { }
        } finally {
            if ($reader) { $reader.Dispose() }
            if ($client) { $client.Close() }
        }
    }
} finally {
    $listener.Stop()
}
