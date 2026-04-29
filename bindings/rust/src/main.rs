use lifecourse_contract::build_command;
use std::env;

fn main() {
    let mut request_path: Option<String> = None;
    let mut output_path: Option<String> = None;
    let mut args = env::args().skip(1);

    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--request" => request_path = args.next(),
            "--output" => output_path = args.next(),
            _ => {}
        }
    }

    let Some(request_path) = request_path else {
        eprintln!("--request is required");
        std::process::exit(2);
    };

    let mut command = build_command(request_path, output_path);
    let status = command.status().expect("failed to start python3");
    std::process::exit(status.code().unwrap_or(1));
}
