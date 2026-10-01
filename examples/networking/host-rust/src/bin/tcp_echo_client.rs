//! TCP client: connect to the echo server, send a line, print the answer.
//! Run: cargo run --bin tcp_echo_client -- 127.0.0.1:5000 hello
use std::io::{Read, Write};
use std::net::TcpStream;

fn main() -> std::io::Result<()> {
    let mut args = std::env::args().skip(1);
    let server = args.next().unwrap_or_else(|| "127.0.0.1:5000".into());
    let msg = args.next().unwrap_or_else(|| "hello".into());

    // connect(): name resolution + three-way handshake
    let mut stream = TcpStream::connect(&server)?;
    stream.write_all(msg.as_bytes())?;

    let mut buf = [0u8; 256];
    let n = stream.read(&mut buf)?;
    println!("answer: {}", String::from_utf8_lossy(&buf[..n]));
    Ok(()) // the stream is closed (FIN) when it goes out of scope
}
