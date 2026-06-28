# Rust Local Process Example

This example runs a Rust process that opts into Port
Zero with `PZ_TUNNEL`, binds to port `0`, and serves plain HTTP on the random
port assigned by the OS.

Run it from PowerShell (Windows):

```powershell
git clone https://github.com/PortZeroNetwork/portzero-examples.git
cd portzero-examples\rust
$env:PZ_TUNNEL = "rust-demo.portzero.local:80"
cargo run
```

Run it from a terminal (macOS or Linux):

```bash
git clone https://github.com/PortZeroNetwork/portzero-examples.git
cd portzero-examples/rust
PZ_TUNNEL="rust-demo.portzero.local:80" cargo run
```

After starting the above command, navigate to http://rust-demo.portzero.local or https://rust-demo.portzero.local in your browser to see this example working with PortZero.

