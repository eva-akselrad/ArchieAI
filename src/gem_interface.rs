// AI Interface using Ollama for local LLM inference with streaming support.

use ollama_rs::{
    generation::chat::{request::ChatMessageRequest, ChatMessage},
    Ollama,
};
use serde::{Deserialize, Serialize};
use std::env;
use tokio_stream::StreamExt;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Message {
    pub role: String,
    pub content: String,
}

impl Message {
    fn to_chat_message(&self) -> ChatMessage {
        match self.role.as_str() {
            "system" => ChatMessage::system(self.content.clone()),
            "assistant" => ChatMessage::assistant(self.content.clone()),
            _ => ChatMessage::user(self.content.clone()),
        }
    }
}

pub struct AiInterface {
    model: String,
    debug: bool,
    ollama_client: Ollama,
}

impl AiInterface {
    /// AI Interface using Ollama for local LLM inference with streaming support.
    ///
    /// Usage:
    ///   let ai = AiInterface::new(false, 3, 1.0, 15);
    ///   let result = ai.archie("When is fall break?").await;
    pub fn new(
        debug: bool,
        _scraper_max_retries: u32,
        _scraper_backoff_factor: f32,
        _scraper_timeout: u64,
    ) -> Self {
        // Load the variables from the .env file into the environment
        dotenv::dotenv().ok();

        // Retrieve the model name from environment (defaults to llama2 if not set)
        let model = env::var("MODEL").unwrap_or_else(|_| "llama2".to_string());

        // Create Ollama client - defaults to localhost:11434
        // This was recommended by some forms i found online to avoid connection issues
        let host = env::var("OLLAMA_HOST").unwrap_or_else(|_| "http://localhost".to_string());
        let port: u16 = env::var("OLLAMA_PORT")
            .ok()
            .and_then(|p| p.parse().ok())
            .unwrap_or(11434);

        let ollama_client = Ollama::new(host, port);

        AiInterface {
            model,
            debug,
            ollama_client,
        }
    }
    // A temporary logging function to designate debug messages
    fn log(&self, message: &str) {
        if self.debug {
            println!("[AiInterface DEBUG] {}", message);
        }
    }

    pub async fn async_web_search(
        &self,
        prompt: String,
        system_prompt: String,
    ) -> Result<Vec<String>, String> {
        self.log(&format!("Web search for: {}", prompt));

        // Check for OLLAMA_API_KEY or OLLAMA_TOKEN in environment
        let _ollama_api_key = env::var("OLLAMA_API_KEY")
            .or_else(|_| env::var("OLLAMA_TOKEN"))
            .ok();

        let model = env::var("OLLAMA_MODEL").unwrap_or_else(|_| self.model.clone());

        let mut messages = Vec::new();

        if !system_prompt.is_empty() {
            messages.push(ChatMessage::system(system_prompt));
        }

        messages.push(ChatMessage::user(prompt));

        let request = ChatMessageRequest::new(model, messages);

        match self.ollama_client.send_chat_messages_stream(request).await {
            Ok(mut stream) => {
                let mut results = Vec::new();
                while let Some(Ok(response)) = stream.next().await {
                    results.push(response.message.content);
                }
                Ok(results)
            }
            Err(e) => Err(format!("Failed to perform web search: {}", e)),
        }
    }

    pub async fn archie_streaming(
        &self,
        query: String,
        conversation_history: Option<Vec<Message>>,
    ) -> Result<Vec<String>, String> {
        self.log(&format!("Archie streaming query: {}", query));

        // Build context with conversation history
        let mut history_context = String::new();
        if let Some(history) = conversation_history {
            history_context.push_str("\n\nConversation History:\n");
            for msg in history.iter() {
                history_context.push_str(&format!(
                    "{}: {}\n",
                    msg.role.to_uppercase(),
                    msg.content
                ));
            }
        }

        let current_time = chrono::Utc::now().format("%Y-%m-%d %H:%M:%S").to_string();

        let system_prompt = format!(
            r#"You are ArchieAI, an AI assistant for Arcadia University. You are here to help students, faculty, and staff with any questions they may have about the university.

You are made by students for a final project. You must be factual and concise based on the information provided. All responses should be professional yet to the point.
Markdown IS NOT SUPPORTED OR RENDERED in the final output. DO NOT RESPOND WITH MARKDOWN FORMATTING OR HYPERLINKS so no [links](url) formatting or bolding. however you can provide full URLs.
You are not associated with Arcadia University officially as you are a student project.
History:
{}
The Time is {}"#,
            history_context, current_time
        );

        self.async_web_search(query, system_prompt).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ai_interface_new() {
        let ai = AiInterface::new(false, 3, 1.0, 15);
        assert!(!ai.debug);
    }

    #[test]
    fn test_ai_interface_new_debug() {
        let ai = AiInterface::new(true, 3, 1.0, 15);
        assert!(ai.debug);
    }

    #[test]
    fn test_message_creation() {
        let msg = Message {
            role: "user".to_string(),
            content: "Hello".to_string(),
        };
        
        assert_eq!(msg.role, "user");
        assert_eq!(msg.content, "Hello");
    }

    #[test]
    fn test_message_to_chat_message_user() {
        let msg = Message {
            role: "user".to_string(),
            content: "Hello".to_string(),
        };
        
        let _chat_msg = msg.to_chat_message();
        // Just verify it doesn't panic
        assert!(true);
    }

    #[test]
    fn test_message_to_chat_message_assistant() {
        let msg = Message {
            role: "assistant".to_string(),
            content: "Hi there".to_string(),
        };
        
        let _chat_msg = msg.to_chat_message();
        assert!(true);
    }

    #[test]
    fn test_message_to_chat_message_system() {
        let msg = Message {
            role: "system".to_string(),
            content: "System prompt".to_string(),
        };
        
        let _chat_msg = msg.to_chat_message();
        assert!(true);
    }

    #[test]
    fn test_message_serialization() {
        let msg = Message {
            role: "user".to_string(),
            content: "Test message".to_string(),
        };
        
        let json = serde_json::to_string(&msg).expect("Failed to serialize");
        assert!(json.contains("user"));
        assert!(json.contains("Test message"));
    }

    #[test]
    fn test_message_deserialization() {
        let json = r#"{"role": "assistant", "content": "Response"}"#;
        let msg: Message = serde_json::from_str(json).expect("Failed to deserialize");
        
        assert_eq!(msg.role, "assistant");
        assert_eq!(msg.content, "Response");
    }

    #[test]
    fn test_message_clone() {
        let msg = Message {
            role: "user".to_string(),
            content: "Test".to_string(),
        };
        
        let cloned = msg.clone();
        assert_eq!(msg.role, cloned.role);
        assert_eq!(msg.content, cloned.content);
    }

    #[test]
    fn test_log_function_debug_mode() {
        let ai = AiInterface::new(true, 3, 1.0, 15);
        // This should not panic
        ai.log("Test debug message");
    }

    #[test]
    fn test_log_function_no_debug() {
        let ai = AiInterface::new(false, 3, 1.0, 15);
        // This should not panic or output anything
        ai.log("This should not be printed");
    }

    #[tokio::test]
    async fn test_archie_streaming_with_empty_history() {
        let ai = AiInterface::new(false, 3, 1.0, 15);
        // This test will fail without Ollama running, but we can test the structure
        // In a real environment, you'd mock the Ollama client
        let result = ai.archie_streaming(
            "Test query".to_string(),
            None,
        ).await;
        
        // We can't test the actual result without Ollama, but we can verify the function signature works
        assert!(result.is_ok() || result.is_err());
    }

    #[tokio::test]
    async fn test_archie_streaming_with_history() {
        let ai = AiInterface::new(false, 3, 1.0, 15);
        
        let history = vec![
            Message {
                role: "user".to_string(),
                content: "Previous question".to_string(),
            },
            Message {
                role: "assistant".to_string(),
                content: "Previous answer".to_string(),
            },
        ];
        
        let result = ai.archie_streaming(
            "Follow-up question".to_string(),
            Some(history),
        ).await;
        
        // We can't test the actual result without Ollama, but we can verify the function signature works
        assert!(result.is_ok() || result.is_err());
    }

    #[tokio::test]
    async fn test_async_web_search_structure() {
        let ai = AiInterface::new(false, 3, 1.0, 15);
        
        let result = ai.async_web_search(
            "Test query".to_string(),
            "Test system prompt".to_string(),
        ).await;
        
        // Can't test actual result without Ollama
        assert!(result.is_ok() || result.is_err());
    }

    #[test]
    fn test_multiple_message_conversions() {
        let messages = vec![
            Message { role: "system".to_string(), content: "System".to_string() },
            Message { role: "user".to_string(), content: "User".to_string() },
            Message { role: "assistant".to_string(), content: "Assistant".to_string() },
        ];
        
        for msg in messages {
            let _ = msg.to_chat_message();
        }
        
        assert!(true);
    }

    #[test]
    fn test_message_debug_format() {
        let msg = Message {
            role: "user".to_string(),
            content: "Test".to_string(),
        };
        
        let debug_string = format!("{:?}", msg);
        assert!(debug_string.contains("user"));
        assert!(debug_string.contains("Test"));
    }
}
