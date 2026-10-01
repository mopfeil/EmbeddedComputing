//! TCP echo server: every received byte is sent back.
//! A thread per client, so several clients can be served at the same time.
//! Run: cargo run --bin tcp_echo_server -- 5000
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::thread;

fn handle(mut stream: TcpStream) -> std::io::Result<()> {
    let peer = stream.peer_addr()?;
    println!("client {peer} connected");
    let mut buf = [0u8; 256];
    loop {
        let n = stream.read(&mut buf)?; // TCP is a byte stream, not messages
        if n == 0 {
            break; // the client has closed its side (FIN)
        }
        stream.write_all(&buf[..n])?;
    }
    println!("client {peer} disconnected");
    Ok(())
}

fn main() -> std::io::Result<()> {
    let port = std::env::args().nth(1).unwrap_or_else(|| "5000".into());
    // bind() + listen() in one step
    let listener = TcpListener::bind(format!("0.0.0.0:{port}"))?;
    println!("listening on port {port}");
    for stream in listener.incoming() {
        // accept(): one new stream per connection
        let stream = stream?;
        thread::spawn(move || {
            if let Err(e) = handle(stream) {
                eprintln!("error: {e}");
            }
        });
    }
    Ok(())
}
