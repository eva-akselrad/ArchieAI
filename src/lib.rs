// ArchieAI Rust Library
// This module provides Rust implementations of the Python modules:
// - DataCollector: For collecting interaction analytics
// - SessionManager: For managing user sessions and chat history
// - GemInterface: For AI interface with Ollama

pub mod data_collector;
pub mod gem_interface;
pub mod session_manager;

pub use data_collector::DataCollector;
pub use gem_interface::AiInterface;
pub use session_manager::SessionManager;
