//! TSF 注入 spike：验证 imekit 能否在 Windows 上注册为输入法并在激活时提交文本。
//!
//! 机制：监听本地 TCP(127.0.0.1:8799) 接收要注入的文本；当本 IME 被激活(Activate)时，
//! 通过 imekit 的 commit_string 提交文本。这是「瞬态激活切换」方案的核心验证。

use imekit::{InputMethod, InputMethodEvent};
use std::io::Read;
use std::net::TcpListener;

fn main() -> Result<(), imekit::Error> {
    env_logger::init();

    let mut im = InputMethod::new()?;
    println!("tsf-injector started, waiting for activation...");

    let listener = TcpListener::bind("127.0.0.1:8799").expect("bind 8799");
    listener.set_nonblocking(true).expect("nonblocking");

    let mut pending_text: String = String::new();

    loop {
        // 接收要注入的文本
        match listener.accept() {
            Ok((mut stream, _)) => {
                // Windows 上 listener 非阻塞会传染给 accept 出的 stream，恢复阻塞 + 读超时
                let _ = stream.set_nonblocking(false);
                let _ = stream.set_read_timeout(Some(std::time::Duration::from_secs(1)));
                let mut buf = [0u8; 4096];
                match stream.read(&mut buf) {
                    Ok(n) if n > 0 => {
                        pending_text = String::from_utf8_lossy(&buf[..n]).trim_end().to_string();
                        eprintln!("received text to inject: {pending_text:?}");
                    }
                    Ok(_) => eprintln!("read got 0 bytes"),
                    Err(e) => eprintln!("read error: {e}"),
                }
            }
            Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {}
            Err(e) => eprintln!("accept error: {e}"),
        }

        // 处理 IME 事件
        while let Some(event) = im.next_event() {
            match event {
                InputMethodEvent::Activate { serial } => {
                    println!("IME ACTIVATED (serial {serial})");
                    if !pending_text.is_empty() {
                        eprintln!("committing: {pending_text:?}");
                        im.commit_string(&pending_text)?;
                        im.commit(serial)?;
                        pending_text.clear();
                    }
                }
                InputMethodEvent::Deactivate => println!("IME DEACTIVATED"),
                InputMethodEvent::SurroundingText { text, cursor, .. } => {
                    println!("surrounding text: {text:?} cursor={cursor}");
                }
                InputMethodEvent::Unavailable => {
                    eprintln!("IME protocol unavailable");
                    return Ok(());
                }
                _ => {}
            }
        }

        std::thread::sleep(std::time::Duration::from_millis(10));
    }
}
