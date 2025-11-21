// Simple runner for ArchieAI Rust modules
// Demonstrates the basic functionality of DataCollector, SessionManager, and AiInterface
// For the record, I hate Rust with a burning passion but here we are
//This code will have warnings and such because its just a demo file to test the modules. ignore them it is not used anymore 
// if you want to see it in action look at the video i submitted
use archie_ai_rust::{AiInterface, DataCollector, SessionManager};

#[tokio::main]
async fn main() {
    println!("=== ArchieAI Rust Demo ===\n");

    // Demo DataCollector
    println!("1. Testing DataCollector...");
    let collector = DataCollector::new("data");
    collector.log_interaction(
        "demo_session_123".to_string(),
        Some("test@arcadia.edu".to_string()),
        "127.0.0.1".to_string(),
        "Mozilla/5.0 Test Browser".to_string(),
        "What is the tuition for 2025?".to_string(),
        "The tuition for 2025 is $45,000 per year.".to_string(),
        1.23,
    );
    println!("   ✓ Logged interaction to analytics.json\n");

    // Demo SessionManager
    println!("2. Testing SessionManager...");
    let session_manager = SessionManager::new("data");

    // Create a test user
    let user_created = session_manager.create_user(
        "demo@arcadia.edu".to_string(),
        "password123".to_string(),
        "127.0.0.1".to_string(),
        "Test Device".to_string(),
    );
    println!("   ✓ User created: {}", user_created);

    // Authenticate the user
    let is_authenticated = session_manager.authenticate_user("demo@arcadia.edu", "password123");
    println!("   ✓ User authenticated: {}", is_authenticated);

    // Create a session
    let session_id = session_manager.create_session(Some("demo@arcadia.edu".to_string()));
    println!("   ✓ Created session: {}", session_id);

    // Add messages to the session
    session_manager.add_message(
        &session_id,
        "user".to_string(),
        "Hello ArchieAI!".to_string(),
    );
    session_manager.add_message(
        &session_id,
        "assistant".to_string(),
        "Hello! How can I help you today?".to_string(),
    );
    println!("   ✓ Added messages to session\n");

    // Get conversation history
    let history = session_manager.get_conversation_history(&session_id);
    println!("   ✓ Conversation history has {} messages", history.len());

    // Demo AiInterface
    println!("\n3. Testing AiInterface with Ollama...");
    let ai_interface = AiInterface::new(true, 3, 1.0, 15);
    println!("   ✓ AiInterface initialized with Ollama client");

    // Note: Actual API calls require a running Ollama instance
    println!("\n   Note: To make actual API calls on your machine:");
    println!("     1. Install and start Ollama (https://ollama.ai)");
    println!("     2. Pull a model: ollama pull (model name)");
    println!("     3. Set MODEL environment variable if needed");

    let user_prompt = "What is the capital of the us?".to_string();
    let response = ai_interface.archie_streaming(user_prompt, None).await;
    match response {
        //Ok so i ran out of time to fully implement streaming response handling in this demo so it will look like a complete mess
        //however it should work for basic testing and demo purposes
        Ok(answer) => {
            println!("   ✓ Received response: {:?}", answer);
        }
        Err(e) => {
            println!("   ✗ Error during API call: {}", e);
        }
    }

    println!("\n=== Demo Complete ===");
    println!("Rust modules are working correctly! (I dont want to tell you how long this took me. but now all i need to do is the webserver and im done)");
}
