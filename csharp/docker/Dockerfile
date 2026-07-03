FROM mcr.microsoft.com/dotnet/sdk:10.0-preview AS build
WORKDIR /app
COPY PortZeroCSharpDockerExample.csproj .
RUN dotnet restore
COPY Program.cs .
RUN dotnet publish -c Release -o /out --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0-preview
WORKDIR /app
COPY --from=build /out .
EXPOSE 8080
CMD ["dotnet", "PortZeroCSharpDockerExample.dll"]
