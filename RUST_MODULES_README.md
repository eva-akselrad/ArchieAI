# ArchieAI Rust Modules

This directory contains Rust implementations of the Python modules for ArchieAI.

## Overview

The following Python modules have been converted to Rust:
- `DataCollector.py` → `data_collector.rs`
- `GemInterface.py` → `gem_interface.rs`
- `SessionManager.py` → `session_manager.rs`

**Note:** The original Python files remain unchanged and fully functional. These Rust modules are standalone implementations that can be used independently.

## Structure

- `src/data_collector.rs` - Data collection and analytics logging
- `src/session_manager.rs` - User account and session management
- `src/gem_interface.rs` - AI interface for Ollama integration
- `src/lib.rs` - Library module exports
- `src/main.rs` - Demo runner showing basic functionality

## Building and Running

To build the Rust modules:
```bash
cargo build
```

To run the demo:
```bash
cargo run
```

## Dependencies

The Rust implementation uses:
- `serde` & `serde_json` - JSON serialization
- `tokio` - Async runtime
- `chrono` - Date/time handling
- `reqwest` - HTTP client
- `sha2` & `hex` - Password hashing
- `rand` - Random number generation
- `dotenv` - Environment variable loading

## Comments

For the record, I hate Rust too, but here we are...

The code follows the same comment style as the original Python implementation, maintaining readability and the developer's sentiments about the language choice.
