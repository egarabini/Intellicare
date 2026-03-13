---
dem: DEM-006
titulo: Admin Frontend — Especificação Técnica
tipo: TECNICA
status: aprovado
criado: 2026-03-13
---

# DEM-006 · 02 — Especificação Técnica

## Estrutura de Projeto

```
frontend/
└── AdminUI/                          # Projeto Blazor WASM
    ├── AdminUI.csproj
    ├── Program.cs
    ├── appsettings.json              # OIDC config (lida em runtime)
    ├── wwwroot/
    │   └── index.html
    ├── Pages/
    │   ├── Dashboard.razor
    │   ├── TenantList.razor
    │   ├── TenantForm.razor
    │   └── TenantDetail.razor
    ├── Components/
    │   ├── StatusBadge.razor
    │   ├── ConfirmModal.razor
    │   └── ToastService.cs
    ├── Services/
    │   ├── TenantApiService.cs       # wrapper HttpClient → /admin/tenants
    │   └── AuthService.cs
    └── Models/
        ├── TenantDto.cs
        └── PagedResult.cs

# Após build, `publish/wwwroot/` é copiado para intellicare_core/static/admin-ui/
# e servido pelo FastAPI (ver BLOCO 8)
```

---

## BLOCO 1 — `frontend/AdminUI/AdminUI.csproj`

```xml
<Project Sdk="Microsoft.NET.Sdk.BlazorWebAssembly">
  <PropertyGroup>
    <TargetFramework>net9.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <ServiceWorkerAssetsManifest>service-worker-assets.js</ServiceWorkerAssetsManifest>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Components.WebAssembly"
                      Version="9.0.0" />
    <PackageReference Include="Microsoft.AspNetCore.Components.WebAssembly.Authentication"
                      Version="9.0.0" />
    <PackageReference Include="MudBlazor"
                      Version="7.*" />
  </ItemGroup>
</Project>
```

---

## BLOCO 2 — `frontend/AdminUI/Program.cs`

```csharp
using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.Components.WebAssembly.Hosting;
using Microsoft.AspNetCore.Components.WebAssembly.Authentication;
using MudBlazor.Services;
using AdminUI;
using AdminUI.Services;

var builder = WebAssemblyHostBuilder.CreateDefault(args);
builder.RootComponents.Add<App>("#app");
builder.RootComponents.Add<HeadOutlet>("head::after");

// OIDC — Keycloak
builder.Services.AddOidcAuthentication(options =>
{
    builder.Configuration.Bind("Oidc", options.ProviderOptions);
    options.ProviderOptions.ResponseType = "code";
    options.ProviderOptions.DefaultScopes.Add("openid");
    options.ProviderOptions.DefaultScopes.Add("profile");
    options.ProviderOptions.DefaultScopes.Add("email");
});

// HttpClient autenticado → aponta para FastAPI
builder.Services.AddHttpClient<TenantApiService>(client =>
{
    client.BaseAddress = new Uri(
        builder.Configuration["ApiBaseUrl"] ?? "http://localhost:8000/"
    );
}).AddHttpMessageHandler<BaseAddressAuthorizationMessageHandler>();

// MudBlazor
builder.Services.AddMudServices();

await builder.Build().RunAsync();
```

---

## BLOCO 3 — `frontend/AdminUI/appsettings.json`

```json
{
  "ApiBaseUrl": "http://localhost:8000/",
  "Oidc": {
    "Authority":    "http://localhost:8080/realms/intellicare",
    "ClientId":     "intellicare-frontend",
    "ResponseType": "code"
  }
}
```

> **Em produção**: substitua `localhost` pelos hostnames reais e configure via variável de ambiente
> ou `appsettings.Production.json` (não commitar segredos).

---

## BLOCO 4 — `frontend/AdminUI/Models/TenantDto.cs`

```csharp
namespace AdminUI.Models;

public record TenantDto(
    Guid   Id,
    string Slug,
    string Name,
    string Status,
    DateTime CreatedAt,
    DateTime UpdatedAt
);

public record PagedResult<T>(
    List<T> Items,
    int     Total,
    int     Page,
    int     Size
);

public record TenantCreateRequest(
    string Slug,
    string Name,
    string GestorEmail
);

public record TenantStatusUpdate(string Status);

public record TenantUserDto(
    string       KeycloakId,
    string       Username,
    string       Email,
    List<string> Roles,
    bool         Enabled
);
```

---

## BLOCO 5 — `frontend/AdminUI/Services/TenantApiService.cs`

```csharp
using System.Net.Http.Json;
using AdminUI.Models;

namespace AdminUI.Services;

public class TenantApiService(HttpClient http)
{
    public async Task<PagedResult<TenantDto>> ListTenantsAsync(int page = 1, int size = 20)
    {
        var result = await http.GetFromJsonAsync<PagedResult<TenantDto>>(
            $"admin/tenants?page={page}&size={size}"
        );
        return result ?? new PagedResult<TenantDto>([], 0, page, size);
    }

    public async Task<TenantDto?> GetTenantAsync(string slug)
        => await http.GetFromJsonAsync<TenantDto>($"admin/tenants/{slug}");

    public async Task<TenantDto?> CreateTenantAsync(TenantCreateRequest request)
    {
        var resp = await http.PostAsJsonAsync("admin/tenants", request);
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<TenantDto>();
    }

    public async Task<TenantDto?> UpdateStatusAsync(string slug, string status)
    {
        var resp = await http.PatchAsJsonAsync(
            $"admin/tenants/{slug}/status",
            new TenantStatusUpdate(status)
        );
        resp.EnsureSuccessStatusCode();
        return await resp.Content.ReadFromJsonAsync<TenantDto>();
    }

    public async Task<List<TenantUserDto>> GetUsersAsync(string slug)
    {
        var resp = await http.GetFromJsonAsync<TenantUsersResponse>($"admin/tenants/{slug}/users");
        return resp?.Users ?? [];
    }

    private record TenantUsersResponse(string TenantSlug, List<TenantUserDto> Users, int Total);
}
```

---

## BLOCO 6 — `frontend/AdminUI/Pages/TenantList.razor`

```razor
@page "/tenants"
@attribute [Authorize(Roles = "PLATFORM_ADMIN")]
@inject TenantApiService Api
@inject NavigationManager Nav
@inject ISnackbar Snackbar

<MudText Typo="Typo.h5" Class="mb-4">Tenants</MudText>

<MudButton Variant="Variant.Filled" Color="Color.Primary"
           OnClick='() => Nav.NavigateTo("/tenants/new")'
           Class="mb-4">
    Novo Tenant
</MudButton>

@if (_loading)
{
    <MudSkeleton SkeletonType="SkeletonType.Rectangle" Height="300px" />
}
else
{
    <MudTable Items="_tenants" Hover="true" Dense="true" OnRowClick="OnRowClick">
        <HeaderContent>
            <MudTh>Slug</MudTh>
            <MudTh>Nome</MudTh>
            <MudTh>Status</MudTh>
            <MudTh>Criado em</MudTh>
            <MudTh>Ações</MudTh>
        </HeaderContent>
        <RowTemplate>
            <MudTd>@context.Slug</MudTd>
            <MudTd>@context.Name</MudTd>
            <MudTd><StatusBadge Status="@context.Status" /></MudTd>
            <MudTd>@context.CreatedAt.ToString("dd/MM/yyyy")</MudTd>
            <MudTd>
                @if (context.Status == "active")
                {
                    <MudButton Size="Size.Small" Color="Color.Warning"
                               OnClick="() => ToggleStatus(context, \"suspended\")">
                        Suspender
                    </MudButton>
                }
                else if (context.Status == "suspended")
                {
                    <MudButton Size="Size.Small" Color="Color.Success"
                               OnClick="() => ToggleStatus(context, \"active\")">
                        Reativar
                    </MudButton>
                }
            </MudTd>
        </RowTemplate>
    </MudTable>

    <MudPagination Count="_totalPages" @bind-Selected="_currentPage"
                   Class="mt-4" />
}

@code {
    private List<TenantDto> _tenants = [];
    private bool _loading = true;
    private int _currentPage = 1;
    private int _totalPages = 1;
    private const int PageSize = 20;

    protected override async Task OnInitializedAsync() => await LoadAsync();

    private async Task LoadAsync()
    {
        _loading = true;
        var result = await Api.ListTenantsAsync(_currentPage, PageSize);
        _tenants    = result.Items;
        _totalPages = (int)Math.Ceiling((double)result.Total / PageSize);
        _loading    = false;
    }

    private void OnRowClick(TableRowClickEventArgs<TenantDto> args)
        => Nav.NavigateTo($"/tenants/{args.Item.Slug}");

    private async Task ToggleStatus(TenantDto tenant, string newStatus)
    {
        await Api.UpdateStatusAsync(tenant.Slug, newStatus);
        Snackbar.Add($"Tenant '{tenant.Name}' atualizado para {newStatus}", Severity.Success);
        await LoadAsync();
    }
}
```

---

## BLOCO 7 — `frontend/AdminUI/Pages/TenantForm.razor`

```razor
@page "/tenants/new"
@attribute [Authorize(Roles = "PLATFORM_ADMIN")]
@inject TenantApiService Api
@inject NavigationManager Nav
@inject ISnackbar Snackbar
@using System.Text.RegularExpressions

<MudText Typo="Typo.h5" Class="mb-4">Novo Tenant</MudText>

<MudForm @ref="_form" @bind-IsValid="_isValid">
    <MudTextField @bind-Value="_name"
                  Label="Nome"
                  Required="true"
                  RequiredError="Nome é obrigatório"
                  OnInput="OnNameInput"
                  Class="mb-3" />

    <MudTextField @bind-Value="_slug"
                  Label="Slug (gerado automaticamente)"
                  Required="true"
                  Validation="@(new Func<string, string?>(ValidateSlug))"
                  Class="mb-3" />

    <MudTextField @bind-Value="_gestorEmail"
                  Label="Email do Gestor"
                  Required="true"
                  InputType="InputType.Email"
                  Class="mb-3" />

    <MudButton Variant="Variant.Filled" Color="Color.Primary"
               Disabled="!_isValid || _submitting"
               OnClick="Submit">
        @(_submitting ? "Criando..." : "Criar Tenant")
    </MudButton>
    <MudButton Variant="Variant.Text" OnClick='() => Nav.NavigateTo("/tenants")'
               Class="ml-2">
        Cancelar
    </MudButton>
</MudForm>

@code {
    private MudForm _form = null!;
    private string _name        = "";
    private string _slug        = "";
    private string _gestorEmail = "";
    private bool   _isValid;
    private bool   _submitting;

    private static readonly Regex SlugRegex = new(@"^[a-z0-9_]{3,30}$");

    private void OnNameInput()
    {
        _slug = Regex.Replace(_name.ToLowerInvariant().Trim(), @"[^a-z0-9]+", "_")
                     .Trim('_');
        if (_slug.Length > 30) _slug = _slug[..30];
    }

    private string? ValidateSlug(string v)
        => SlugRegex.IsMatch(v) ? null : "Slug: 3-30 chars [a-z0-9_]";

    private async Task Submit()
    {
        await _form.Validate();
        if (!_isValid) return;

        _submitting = true;
        try
        {
            await Api.CreateTenantAsync(new(_slug, _name, _gestorEmail));
            Snackbar.Add($"Tenant '{_name}' criado com sucesso!", Severity.Success);
            Nav.NavigateTo("/tenants");
        }
        catch (HttpRequestException ex) when (ex.StatusCode == System.Net.HttpStatusCode.Conflict)
        {
            Snackbar.Add($"Slug '{_slug}' já existe. Escolha outro.", Severity.Error);
        }
        catch (Exception ex)
        {
            Snackbar.Add($"Erro: {ex.Message}", Severity.Error);
        }
        finally { _submitting = false; }
    }
}
```

---

## BLOCO 8 — Integração com FastAPI (`intellicare_core/main.py` trecho)

Após `dotnet publish` do projeto Blazor, copiar `wwwroot/` para `intellicare_core/static/admin-ui/`.
O FastAPI serve como arquivos estáticos:

```python
from fastapi.staticfiles import StaticFiles
import pathlib

STATIC_DIR = pathlib.Path(__file__).parent / "static" / "admin-ui"

if STATIC_DIR.exists():
    app.mount(
        "/admin-ui",
        StaticFiles(directory=str(STATIC_DIR), html=True),
        name="admin-ui",
    )
```

Script de build/copy (adicionar ao `Makefile` ou `tools/scripts/build_frontend.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Build Admin UI ==="
cd frontend/AdminUI
dotnet publish -c Release -o /tmp/admin-ui-publish

echo "=== Copiando wwwroot ==="
rm -rf ../../intellicare_core/static/admin-ui
cp -r /tmp/admin-ui-publish/wwwroot ../../intellicare_core/static/admin-ui

echo "=== Build concluído ==="
```

---

## BLOCO 9 — Componente `StatusBadge.razor`

```razor
@* Components/StatusBadge.razor *@

<MudChip T="string"
         Color="@GetColor()"
         Size="Size.Small"
         Label="true">
    @Status
</MudChip>

@code {
    [Parameter] public string Status { get; set; } = "";

    private Color GetColor() => Status switch
    {
        "active"     => Color.Success,
        "suspended"  => Color.Warning,
        "terminated" => Color.Default,
        _            => Color.Default,
    };
}
```

---

## BLOCO 10 — Commit

```bash
git add frontend/AdminUI/ \
        intellicare_core/static/ \
        tools/scripts/build_frontend.sh \
        docs/demandas/DEM-006_ADMIN_FRONTEND/

git commit -m "DEM-006: Admin Frontend Blazor WASM - OIDC Keycloak, CRUD tenants, MudBlazor"
git push origin main
```

---

## Critérios de Aceite (técnicos)

| # | Critério | Como verificar |
|---|---|---|
| AC-1 | `/admin-ui/` redireciona para Keycloak se não autenticado | Abrir em navegação anônima |
| AC-2 | Login com `platform-admin` → Dashboard com contadores | Login flow completo |
| AC-3 | Login com `gestor-dev` → rota bloqueada | `[Authorize(Roles="PLATFORM_ADMIN")]` |
| AC-4 | Criar tenant via formulário → POST bem-sucedido | Network tab → POST `/admin/tenants` 201 |
| AC-5 | Slug gerado a partir do nome | Digitar "Clínica São José" → slug `clinica_sao_jose` |
| AC-6 | Slug inválido → erro inline antes de enviar | Digitar "AB" → erro exibido |
| AC-7 | Suspender → badge muda para amarelo sem reload | Clicar "Suspender" → tabela atualizada |
| AC-8 | `dotnet publish` → `wwwroot/` copiado → FastAPI serve `/admin-ui` | `curl http://localhost:8000/admin-ui/` → HTML |
| AC-9 | Token renovado automaticamente | Aguardar 5min (TTL do token) → ação ainda funciona |
