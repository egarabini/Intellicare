---
dem: DEM-012
titulo: Gestor Frontend — Especificação Técnica
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-012 · 02 — Especificação Técnica

## Estrutura

```
frontend/GestorUI/
├── GestorUI.csproj
├── Program.cs
├── appsettings.json
├── Pages/
│   ├── Dashboard.razor
│   ├── UserList.razor
│   ├── UserInvite.razor
│   ├── DocumentList.razor
│   ├── DocumentUpload.razor
│   ├── UnitProfile.razor
│   └── UsageReport.razor
├── Services/
│   └── GestorApiService.cs
└── Models/
    ├── DocumentDto.cs
    ├── GestorUserDto.cs
    └── UsageReportDto.cs
```

## BLOCO 1 — `frontend/GestorUI/GestorUI.csproj`

```xml
<Project Sdk="Microsoft.NET.Sdk.BlazorWebAssembly">
  <PropertyGroup>
    <TargetFramework>net9.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Components.WebAssembly" Version="9.0.0" />
    <PackageReference Include="Microsoft.AspNetCore.Components.WebAssembly.Authentication" Version="9.0.0" />
    <PackageReference Include="MudBlazor" Version="7.*" />
  </ItemGroup>
</Project>
```

## BLOCO 2 — `frontend/GestorUI/Services/GestorApiService.cs`

```csharp
using System.Net.Http.Json;

namespace GestorUI.Services;

public class GestorApiService(HttpClient http)
{
    public Task<List<GestorUserDto>> GetUsersAsync()
        => http.GetFromJsonAsync<List<GestorUserDto>>("gestor/users")
           .ContinueWith(t => t.Result ?? []);

    public async Task InviteUserAsync(string email, string name, string role)
        => (await http.PostAsJsonAsync("gestor/users/invite",
            new { Email = email, Name = name, Role = role })).EnsureSuccessStatusCode();

    public Task<List<DocumentDto>> GetDocumentsAsync()
        => http.GetFromJsonAsync<List<DocumentDto>>("gestor/documents")
           .ContinueWith(t => t.Result ?? []);

    public async Task<IngestResult?> UploadDocumentAsync(IBrowserFile file)
    {
        using var content = new MultipartFormDataContent();
        var stream = file.OpenReadStream(maxAllowedSize: 50 * 1024 * 1024);
        content.Add(new StreamContent(stream), "file", file.Name);
        var resp = await http.PostAsync("gestor/documents/upload", content);
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<IngestResult>();
    }

    public Task<UsageReportDto?> GetUsageReportAsync(int days = 30)
        => http.GetFromJsonAsync<UsageReportDto>($"gestor/reports/usage?days={days}");

    public Task<UnitProfileDto?> GetProfileAsync()
        => http.GetFromJsonAsync<UnitProfileDto>("gestor/profile");

    public async Task<UnitProfileDto?> UpdateProfileAsync(UnitProfileDto profile)
    {
        var resp = await http.PutAsJsonAsync("gestor/profile", profile);
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<UnitProfileDto>();
    }
}
```

## BLOCO 3 — `frontend/GestorUI/Pages/DocumentUpload.razor`

```razor
@page "/documents/upload"
@attribute [Authorize(Roles = "TENANT_GESTOR")]
@inject GestorApiService Api
@inject ISnackbar Snackbar

<MudText Typo="Typo.h6" Class="mb-4">Upload de Documento</MudText>

<MudFileUpload T="IBrowserFile" FilesChanged="OnFileSelected" Accept=".pdf,.md,.txt">
    <ActivatorContent>
        <MudButton Variant="Variant.Filled" Color="Color.Primary">Selecionar Arquivo</MudButton>
    </ActivatorContent>
</MudFileUpload>

@if (_file is not null)
{
    <MudText Class="mt-2">@_file.Name (@(_file.Size / 1024) KB)</MudText>
    <MudButton Class="mt-2" Variant="Variant.Filled" Color="Color.Success"
               Disabled="_uploading" OnClick="Upload">
        @(_uploading ? "Enviando..." : "Enviar e Ingerir")
    </MudButton>
}

@if (_result is not null)
{
    <MudAlert Severity="Severity.Success" Class="mt-3">
        Ingerido: @_result.ChunkCount chunks em @_result.DurationMs ms
    </MudAlert>
}

@code {
    private IBrowserFile? _file;
    private IngestResult? _result;
    private bool _uploading;

    void OnFileSelected(IBrowserFile file) => _file = file;

    async Task Upload()
    {
        if (_file is null) return;
        _uploading = true;
        try { _result = await Api.UploadDocumentAsync(_file);
              Snackbar.Add($"Ingerido: {_result?.ChunkCount} chunks", Severity.Success); }
        catch (Exception ex) { Snackbar.Add($"Erro: {ex.Message}", Severity.Error); }
        finally { _uploading = false; }
    }
}
```

## BLOCO 4 — `tools/scripts/build_gestor_ui.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
cd frontend/GestorUI
dotnet publish -c Release -o /tmp/gestor-ui-publish
rm -rf ../../intellicare_core/static/gestor-ui
cp -r /tmp/gestor-ui-publish/wwwroot ../../intellicare_core/static/gestor-ui
echo "Gestor UI build concluido"
```

Registrar no FastAPI (`intellicare_core/main.py`):

```python
GESTOR_UI = pathlib.Path(__file__).parent / "static" / "gestor-ui"
if GESTOR_UI.exists():
    app.mount("/gestor-ui", StaticFiles(directory=str(GESTOR_UI), html=True), name="gestor-ui")
```

## BLOCO 5 — Commit

```bash
git add frontend/GestorUI/ tools/scripts/build_gestor_ui.sh docs/demandas/DEM-012_GESTOR_FRONTEND/
git commit -m "DEM-012: Gestor Frontend Blazor - usuarios, documentos RAG, relatorio uso"
git push origin main
```
