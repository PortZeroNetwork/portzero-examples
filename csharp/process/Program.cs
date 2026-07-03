using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;

var tunnel = Environment.GetEnvironmentVariable("PZ_TUNNEL") ?? "csharp-process.portzero.local:80";
var tunnelHost = tunnel.Split(':', 2)[0];

var builder = WebApplication.CreateSlimBuilder(args);
builder.WebHost.UseUrls("http://127.0.0.1:0");

var app = builder.Build();

app.MapGet("/", () =>
{
    var address = app.Urls.FirstOrDefault() ?? "http://127.0.0.1:0";
    var port = new Uri(address).Port;
    return Results.Text(
        $"Hello from the PortZero C# process example.\nPZ_TUNNEL={tunnel}\nlocalhost_port={port}\n",
        "text/plain; charset=utf-8"
    );
});

await app.StartAsync();

var listenerAddress = app.Services.GetRequiredService<IServer>().Features.Get<IServerAddressesFeature>()!.Addresses.Single();
var listenerPort = new Uri(listenerAddress).Port;

Console.WriteLine(
    $"PORTZERO_EXAMPLE_LISTENING language=csharp variant=process host=127.0.0.1 port={listenerPort} url=http://127.0.0.1:{listenerPort}/ tunnel={tunnel} tunnel_url=http://{tunnelHost}/"
);
Console.WriteLine(
    $"This C# process was launched with PZ_TUNNEL={tunnel}. It is now listening on localhost port {listenerPort}. Port Zero detects programs with PZ_TUNNEL listening on a port; the program does not need to read its own PZ_TUNNEL value or detect what port the OS has assigned to it. Technically the program doesn't even need to listen on port 0, although that is highly recommended because avoiding port conflicts is the whole point of using PortZero. The program asked to listen on port 0, so the OS assigned an available port. Next, portzero-local's local daemon will detect PZ_TUNNEL and the listening port, then make it available at http://{tunnelHost}/."
);

await app.WaitForShutdownAsync();
