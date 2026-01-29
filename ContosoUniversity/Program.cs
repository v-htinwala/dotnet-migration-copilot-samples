using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.EntityFrameworkCore;
using ContosoUniversity.Services;
using ContosoUniversity.Data;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSystemWebAdapters()
    .AddWrappedAspNetCoreSession()
    .AddJsonSessionSerializer(options =>
    {
        options.RegisterKey<string>("MachineName");
        options.RegisterKey<string>("SessionStartTime");
    });

// Add services to the container.
builder.Services.AddControllersWithViews();
builder.Services.AddSingleton<NotificationService>();

// Add DbContext with connection string from configuration
builder.Services.AddDbContext<SchoolContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

var app = builder.Build();

// Initialize database
using (var scope = app.Services.CreateScope())
{
    var services = scope.ServiceProvider;
    var context = services.GetRequiredService<SchoolContext>();
    DbInitializer.Initialize(context);
}

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error"); // Global error handler
    app.UseHsts();
}
else
{
    app.UseExceptionHandler("/Home/Error"); // Global error handler for development too
    app.UseDeveloperExceptionPage();
}

app.UseStatusCodePagesWithReExecute("/Home/StatusErrorCode", "?code={0}");

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();
app.UseSession();
app.UseSystemWebAdapters();

app.MapControllers()
    .RequireSystemWebAdapterSession();
app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}")
    .RequireSystemWebAdapterSession();

app.Run();