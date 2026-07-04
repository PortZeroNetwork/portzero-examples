use std::env;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::thread;

fn main() -> std::io::Result<()> {
    let tunnel = env::var("PZ_TUNNEL").unwrap_or_else(|_| "rust-process.portzero.local:80".to_string());
    let listener = TcpListener::bind("127.0.0.1:0")?;
    let port = listener.local_addr()?.port();
    let tunnel_host = tunnel.split(':').next().unwrap_or(&tunnel);

    println!(
        "PORTZERO_EXAMPLE_LISTENING language=rust variant=process host=127.0.0.1 port={port} url=http://127.0.0.1:{port}/ tunnel={tunnel} tunnel_url=http://{tunnel_host}/"
    );
    println!(
        "This Rust process was launched with PZ_TUNNEL={tunnel}. It is now listening on localhost port {port}. Port Zero detects programs with PZ_TUNNEL listening on a port; the program does not need to read its own PZ_TUNNEL value or detect what port the OS has assigned to it. Technically the program doesn't even need to listen on port 0, although that is highly recommended because avoiding port conflicts is the whole point of using PortZero. The program asked to listen on port 0, so the OS assigned an available port. Next, PortZero's local daemon will detect PZ_TUNNEL and the listening port, then make it available at http://{tunnel_host}/."
    );

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let tunnel = tunnel.clone();
                thread::spawn(move || {
                    if let Err(err) = handle_client(stream, &tunnel, port) {
                        eprintln!("request failed: {err}");
                    }
                });
            }
            Err(err) => eprintln!("accept failed: {err}"),
        }
    }

    Ok(())
}

fn handle_client(mut stream: TcpStream, tunnel: &str, port: u16) -> std::io::Result<()> {
    let mut buf = [0_u8; 1024];
    let _ = stream.read(&mut buf)?;

    let body = format!(
        "Hello from the PortZero Rust process example.\nPZ_TUNNEL={tunnel}\nlocalhost_port={port}\n"
    );
    let response = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        body.len(),
        body
    );

    stream.write_all(response.as_bytes())?;
    stream.flush()
}
