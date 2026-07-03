var tunnel = Environment.GetEnvironmentVariable("PZ_TUNNEL") ?? "csharp-docker.portzero.local:80";

var builder = WebApplication.CreateSlimBuilder(args);
builder.WebHost.UseUrls("http://0.0.0.0:8080");

var app = builder.Build();

app.MapGet("/", () =>
    Results.Text(
        $"Hello from the PortZero C# Docker example.\nPZ_TUNNEL={tunnel}\ncontainer_port=8080\n",
        "text/plain; charset=utf-8"
    )
);

await app.RunAsync();
