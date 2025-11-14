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
- `src/gem_interface.rs` - AI interface for Ollama integration with **actual API calls**
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

## Ollama Integration

The `gem_interface.rs` module now includes **real Ollama API calls** using the `ollama-rs` crate:

- **Streaming support** - Real-time token streaming from Ollama
- **Chat messages** - Full conversation history support
- **Async/await** - Fully asynchronous implementation with Tokio

### Using the Ollama Interface

```rust
use archie_ai_rust::AiInterface;

let ai = AiInterface::new(true, 3, 1.0, 15);

// Non-streaming chat
let response = ai.archie("What are the office hours?".to_string(), None).await?;

// Streaming chat (returns Vec of content chunks)
let chunks = ai.generate_text_streaming(
    "Tell me about Arcadia".to_string(),
    "You are a helpful assistant".to_string()
).await?;
```

### Prerequisites for Actual API Calls

1. Install Ollama: https://ollama.ai
2. Start the Ollama service
3. Pull a model: `ollama pull llama2` (or any other model)
4. Set environment variables (optional):
   - `MODEL` - Model name (default: llama2)
   - `OLLAMA_HOST` - Ollama host URL (default: http://localhost)
   - `OLLAMA_PORT` - Ollama port (default: 11434)

## Dependencies

The Rust implementation uses:
- `serde` & `serde_json` - JSON serialization
- `tokio` - Async runtime
- `chrono` - Date/time handling
- `reqwest` - HTTP client
- `sha2` & `hex` - Password hashing
- `rand` - Random number generation
- `dotenv` - Environment variable loading
- **`ollama-rs`** - Ollama API client with streaming support
- **`tokio-stream`** - Async stream utilities

## Comments

For the record, I hate Rust too, but here we are...

The code follows the same comment style as the original Python implementation, maintaining readability and the developer's sentiments about the language choice.
