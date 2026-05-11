# .NET 8.0 Upgrade Plan

## Execution Steps

Execute steps below sequentially one by one in the order they are listed.

1. Validate that a .NET 8.0 SDK required for this upgrade is installed on the machine and if not, help to get it installed.
2. Ensure that the SDK version specified in global.json files is compatible with the .NET 8.0 upgrade.
3. Upgrade ContosoUniversity.csproj to .NET 8.0

## Settings

This section contains settings and data used by execution steps.

### Aggregate NuGet packages modifications across all projects

NuGet packages used across all selected projects or their dependencies that need version update in projects that reference them.

| Package Name                                      | Current Version | New Version | Description                                                    |
|:--------------------------------------------------|:---------------:|:-----------:|:---------------------------------------------------------------|
| Antlr                                             | 3.4.1.9004      |             | Replace with Antlr4 4.6.6                                      |
| Antlr4                                            |                 | 4.6.6       | Replacement for Antlr                                          |
| Microsoft.AspNet.Mvc                              | 5.2.9           |             | Functionality included with new framework reference            |
| Microsoft.AspNet.Razor                            | 3.2.9           |             | Functionality included with new framework reference            |
| Microsoft.AspNet.Web.Optimization                 | 1.1.3           |             | Not supported in .NET Core, remove                             |
| Microsoft.AspNet.WebPages                         | 3.2.9           |             | Functionality included with new framework reference            |
| Microsoft.Bcl.AsyncInterfaces                     | 1.1.1           | 8.0.0       | Recommended for .NET 8.0                                       |
| Microsoft.Bcl.HashCode                            | 1.1.1           | 6.0.0       | Recommended for .NET 8.0                                       |
| Microsoft.CodeDom.Providers.DotNetCompilerPlatform| 2.0.1           |             | Functionality included with new framework reference            |
| Microsoft.Data.SqlClient                          | 2.1.4           | 6.1.4       | Security vulnerability (CVE-2024-0056)                         |
| Microsoft.EntityFrameworkCore                     | 3.1.32          | 8.0.23      | Recommended for .NET 8.0                                       |
| Microsoft.EntityFrameworkCore.Abstractions        | 3.1.32          | 8.0.23      | Recommended for .NET 8.0                                       |
| Microsoft.EntityFrameworkCore.Analyzers           | 3.1.32          | 8.0.23      | Recommended for .NET 8.0                                       |
| Microsoft.EntityFrameworkCore.Relational          | 3.1.32          | 8.0.23      | Recommended for .NET 8.0                                       |
| Microsoft.EntityFrameworkCore.SqlServer           | 3.1.32          | 8.0.23      | Recommended for .NET 8.0                                       |
| Microsoft.EntityFrameworkCore.Tools               | 3.1.32          | 8.0.23      | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.Caching.Abstractions         | 3.1.32          | 8.0.0       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.Caching.Memory               | 3.1.32          | 8.0.1       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.Configuration                | 3.1.32          | 8.0.0       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.Configuration.Abstractions   | 3.1.32          | 8.0.0       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.Configuration.Binder         | 3.1.32          | 8.0.2       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.DependencyInjection          | 3.1.32          | 8.0.1       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.DependencyInjection.Abstractions | 3.1.32      | 8.0.2       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.Logging                      | 3.1.32          | 8.0.1       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.Logging.Abstractions         | 3.1.32          | 8.0.3       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.Options                      | 3.1.32          | 8.0.2       | Recommended for .NET 8.0                                       |
| Microsoft.Extensions.Primitives                   | 3.1.32          | 8.0.0       | Recommended for .NET 8.0                                       |
| Microsoft.Identity.Client                         | 4.21.1          | 4.81.0      | Security vulnerability, deprecated version                     |
| Microsoft.Web.Infrastructure                      | 2.0.1           |             | Functionality included with new framework reference            |
| NETStandard.Library                               | 2.0.3           |             | Functionality included with new framework reference            |
| Newtonsoft.Json                                   | 13.0.3          | 13.0.4      | Recommended for .NET 8.0                                       |
| System.Buffers                                    | 4.5.1           |             | Functionality included with new framework reference            |
| System.Collections.Immutable                      | 1.7.1           | 8.0.0       | Recommended for .NET 8.0                                       |
| System.ComponentModel.Annotations                 | 4.7.0           |             | Functionality included with new framework reference            |
| System.Diagnostics.DiagnosticSource               | 4.7.1           | 8.0.1       | Recommended for .NET 8.0                                       |
| System.Memory                                     | 4.5.4           |             | Functionality included with new framework reference            |
| System.Numerics.Vectors                           | 4.5.0           |             | Functionality included with new framework reference            |
| System.Runtime.CompilerServices.Unsafe            | 4.5.3           | 6.1.2       | Recommended for .NET 8.0                                       |
| System.Threading.Tasks.Extensions                 | 4.5.4           |             | Functionality included with new framework reference            |

### Project upgrade details

This section contains details about each project upgrade and modifications that need to be done in the project.

#### ContosoUniversity.csproj modifications

Project properties changes:
  - Project file needs to be converted to SDK-style
  - Target framework should be changed from `net48` to `net8.0`

NuGet packages changes:
  - Antlr should be removed and replaced with Antlr4 4.6.6
  - Microsoft.AspNet.Mvc should be removed (*functionality included with new framework reference*)
  - Microsoft.AspNet.Razor should be removed (*functionality included with new framework reference*)
  - Microsoft.AspNet.Web.Optimization should be removed (*not supported in .NET Core*)
  - Microsoft.AspNet.WebPages should be removed (*functionality included with new framework reference*)
  - Microsoft.Bcl.AsyncInterfaces should be updated from `1.1.1` to `8.0.0` (*recommended for .NET 8.0*)
  - Microsoft.Bcl.HashCode should be updated from `1.1.1` to `6.0.0` (*recommended for .NET 8.0*)
  - Microsoft.CodeDom.Providers.DotNetCompilerPlatform should be removed (*functionality included with new framework reference*)
  - Microsoft.Data.SqlClient should be updated from `2.1.4` to `6.1.4` (*security vulnerability CVE-2024-0056*)
  - Microsoft.EntityFrameworkCore should be updated from `3.1.32` to `8.0.23` (*recommended for .NET 8.0*)
  - Microsoft.EntityFrameworkCore.Abstractions should be updated from `3.1.32` to `8.0.23` (*recommended for .NET 8.0*)
  - Microsoft.EntityFrameworkCore.Analyzers should be updated from `3.1.32` to `8.0.23` (*recommended for .NET 8.0*)
  - Microsoft.EntityFrameworkCore.Relational should be updated from `3.1.32` to `8.0.23` (*recommended for .NET 8.0*)
  - Microsoft.EntityFrameworkCore.SqlServer should be updated from `3.1.32` to `8.0.23` (*recommended for .NET 8.0*)
  - Microsoft.EntityFrameworkCore.Tools should be updated from `3.1.32` to `8.0.23` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.Caching.Abstractions should be updated from `3.1.32` to `8.0.0` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.Caching.Memory should be updated from `3.1.32` to `8.0.1` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.Configuration should be updated from `3.1.32` to `8.0.0` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.Configuration.Abstractions should be updated from `3.1.32` to `8.0.0` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.Configuration.Binder should be updated from `3.1.32` to `8.0.2` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.DependencyInjection should be updated from `3.1.32` to `8.0.1` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.DependencyInjection.Abstractions should be updated from `3.1.32` to `8.0.2` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.Logging should be updated from `3.1.32` to `8.0.1` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.Logging.Abstractions should be updated from `3.1.32` to `8.0.3` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.Options should be updated from `3.1.32` to `8.0.2` (*recommended for .NET 8.0*)
  - Microsoft.Extensions.Primitives should be updated from `3.1.32` to `8.0.0` (*recommended for .NET 8.0*)
  - Microsoft.Identity.Client should be updated from `4.21.1` to `4.81.0` (*security vulnerability, deprecated version*)
  - Microsoft.Web.Infrastructure should be removed (*functionality included with new framework reference*)
  - NETStandard.Library should be removed (*functionality included with new framework reference*)
  - Newtonsoft.Json should be updated from `13.0.3` to `13.0.4` (*recommended for .NET 8.0*)
  - System.Buffers should be removed (*functionality included with new framework reference*)
  - System.Collections.Immutable should be updated from `1.7.1` to `8.0.0` (*recommended for .NET 8.0*)
  - System.ComponentModel.Annotations should be removed (*functionality included with new framework reference*)
  - System.Diagnostics.DiagnosticSource should be updated from `4.7.1` to `8.0.1` (*recommended for .NET 8.0*)
  - System.Memory should be removed (*functionality included with new framework reference*)
  - System.Numerics.Vectors should be removed (*functionality included with new framework reference*)
  - System.Runtime.CompilerServices.Unsafe should be updated from `4.5.3` to `6.1.2` (*recommended for .NET 8.0*)
  - System.Threading.Tasks.Extensions should be removed (*functionality included with new framework reference*)

Feature upgrades:
  - System.Web.Optimization bundling and minification is not supported in .NET Core and should be replaced with actual html tags pointing to content files. Remove BundleConfig.cs and update views to reference static files directly.
  - Routes registration via RouteCollection is not supported in .NET Core and needs to be converted to the route mappings on the application object. Migrate RouteConfig.cs to Program.cs.
  - GlobalFilterCollection is not supported in .NET Core and needs to be converted to the corresponding middleware registrations on the application object. Migrate FilterConfig.cs to Program.cs.
  - Convert System.Messaging to MSMQ in .NET Core or use alternative message queue libraries.
  - Convert application initialization code from Global.asax.cs to .NET Core Program.cs and remove Global.asax.cs.

Other changes:
  - Update controller base types from System.Web.Mvc.Controller to Microsoft.AspNetCore.Mvc.Controller
  - Replace System.Web.Mvc namespace references with Microsoft.AspNetCore.Mvc
  - Update action result types (e.g., HttpStatusCodeResult to StatusCodeResult, HttpNotFound to NotFound)
  - Update model binding attributes (e.g., [Bind] attribute syntax)
  - Replace TryUpdateModel with manual model binding or use model binding attributes
  - Update views to use ASP.NET Core Razor syntax where necessary
  - Remove System.Messaging references or replace with compatible messaging library
