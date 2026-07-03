use std::env;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::thread;

fn main() -> std::io::Result<()> {
    let tunnel = env::var("PZ_TUNNEL").unwrap_or_else(|_| "rust-docker.portzero.local:80".to_string());
    let listener = TcpListener::bind("0.0.0.0:8080")?;

    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let tunnel = tunnel.clone();
                thread::spawn(move || {
                    if let Err(err) = handle_client(stream, &tunnel) {
                        eprintln!("request failed: {err}");
                    }
                });
            }
            Err(err) => eprintln!("accept failed: {err}"),
        }
    }

    Ok(())
}

fn handle_client(mut stream: TcpStream, tunnel: &str) -> std::io::Result<()> {
    let mut buf = [0_u8; 1024];
    let _ = stream.read(&mut buf)?;

    let body = format!(
        "Hello from the PortZero Rust Docker example.\nPZ_TUNNEL={tunnel}\ncontainer_port=8080\n"
    );
    let response = format!(
        "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        body.len(),
        body
    );

    stream.write_all(response.as_bytes())?;
    stream.flush()
}
