//! A minimal MQTT 3.1.1 client (QoS 0 only), written by hand to show the
//! packet format. Real projects use a library (e.g. rust-mqtt, PubSubClient).

use embedded_io_async::{Read, Write};

/// Fixed header byte = packet type (high nibble) + flags (low nibble).
const CONNECT: u8 = 0x10;
const CONNACK: u8 = 0x20;
const PUBLISH: u8 = 0x30;
const SUBSCRIBE: u8 = 0x82; // flags 0b0010 are mandatory for SUBSCRIBE

#[derive(Debug)]
pub enum Error {
    Io,
    Refused(u8),
    Protocol,
    TooLong,
}

/// Packet builder on a fixed buffer (no heap needed).
struct Packet {
    buf: [u8; 256],
    len: usize,
}

impl Packet {
    fn new() -> Self {
        Packet { buf: [0; 256], len: 0 }
    }
    fn byte(&mut self, b: u8) -> Result<(), Error> {
        *self.buf.get_mut(self.len).ok_or(Error::TooLong)? = b;
        self.len += 1;
        Ok(())
    }
    fn bytes(&mut self, data: &[u8]) -> Result<(), Error> {
        data.iter().try_for_each(|&b| self.byte(b))
    }
    /// UTF-8 string with a 2 byte big endian length prefix.
    fn string(&mut self, s: &str) -> Result<(), Error> {
        self.bytes(&(s.len() as u16).to_be_bytes())?;
        self.bytes(s.as_bytes())
    }
}

/// Send fixed header + "remaining length" (variable length encoding:
/// 7 bit per byte, bit 7 = more bytes follow) + body in ONE write, so the
/// packet leaves in one TCP segment. (Some brokers drop the connection if a
/// CONNECT arrives split into several segments - a bug on their side, but
/// one that real devices have to live with.)
async fn send<S: Write>(sock: &mut S, header: u8, body: &Packet) -> Result<(), Error> {
    let mut packet = Packet::new();
    packet.byte(header)?;
    let mut n = body.len;
    loop {
        let mut digit = (n % 128) as u8;
        n /= 128;
        if n > 0 {
            digit |= 0x80;
        }
        packet.byte(digit)?;
        if n == 0 {
            break;
        }
    }
    packet.bytes(&body.buf[..body.len])?;
    sock.write_all(&packet.buf[..packet.len]).await.map_err(|_| Error::Io)?;
    sock.flush().await.map_err(|_| Error::Io)
}

/// Read one packet; returns (fixed header byte, body length) with the body in `buf`.
pub async fn receive<S: Read>(sock: &mut S, buf: &mut [u8]) -> Result<(u8, usize), Error> {
    let mut b = [0u8; 1];
    sock.read_exact(&mut b).await.map_err(|_| Error::Io)?;
    let header = b[0];
    let (mut len, mut shift) = (0usize, 0);
    loop {
        sock.read_exact(&mut b).await.map_err(|_| Error::Io)?;
        len |= ((b[0] & 0x7f) as usize) << shift;
        if b[0] & 0x80 == 0 {
            break;
        }
        shift += 7;
    }
    let body = buf.get_mut(..len).ok_or(Error::TooLong)?;
    sock.read_exact(body).await.map_err(|_| Error::Io)?;
    Ok((header, len))
}

/// CONNECT and wait for CONNACK.
pub async fn connect<S: Read + Write>(sock: &mut S, client_id: &str) -> Result<(), Error> {
    let mut p = Packet::new();
    p.string("MQTT")?; // protocol name
    p.byte(4)?; // protocol level 4 = MQTT 3.1.1
    p.byte(0x02)?; // connect flags: clean session
    p.bytes(&60u16.to_be_bytes())?; // keep alive 60 s
    p.string(client_id)?; // payload: client identifier
    send(sock, CONNECT, &p).await?;

    let mut buf = [0u8; 4];
    match receive(sock, &mut buf).await? {
        (CONNACK, 2) if buf[1] == 0 => Ok(()),
        (CONNACK, 2) => Err(Error::Refused(buf[1])),
        _ => Err(Error::Protocol),
    }
}

/// SUBSCRIBE to one topic with QoS 0 (the SUBACK is handled by the caller).
pub async fn subscribe<S: Write>(sock: &mut S, topic: &str) -> Result<(), Error> {
    let mut p = Packet::new();
    p.bytes(&1u16.to_be_bytes())?; // packet identifier
    p.string(topic)?;
    p.byte(0)?; // requested QoS
    send(sock, SUBSCRIBE, &p).await
}

/// PUBLISH with QoS 0: topic + payload, no acknowledgement.
pub async fn publish<S: Write>(sock: &mut S, topic: &str, payload: &[u8]) -> Result<(), Error> {
    let mut p = Packet::new();
    p.string(topic)?;
    p.bytes(payload)?;
    send(sock, PUBLISH, &p).await
}

/// Split the body of a received QoS 0 PUBLISH into (topic, payload).
pub fn parse_publish(body: &[u8]) -> Option<(&str, &[u8])> {
    let len = u16::from_be_bytes([*body.first()?, *body.get(1)?]) as usize;
    let topic = core::str::from_utf8(body.get(2..2 + len)?).ok()?;
    Some((topic, &body[2 + len..]))
}

/// Packet type of a fixed header byte (PUBLISH = 3, SUBACK = 9, ...).
pub fn packet_type(header: u8) -> u8 {
    header >> 4
}
