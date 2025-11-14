// AI Interface using Ollama for local LLM inference with streaming support.
// Keeps the original synchronous web scraper (requests + BeautifulSoup) but improves it
// by adding a requests.Session with browser-like headers and a retry strategy to reduce
// 403/429/5xx failures. Everything else remains async-friendly by running blocking
// operations in a threadpool.

use serde::{Deserialize, Serialize};
use std::env;
use ollama_rs::{
    Ollama,
    generation::chat::{request::ChatMessageRequest, ChatMessage},
};
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
    
    fn log(&self, message: &str) {
        if self.debug {
            println!("[AiInterface DEBUG] {}", message);
        }
    }
    
    // I dont think this is used anywhere but im keeping it just in case
    pub async fn generate_text_streaming(
        &self,
        prompt: String,
        system_prompt: String,
    ) -> Result<Vec<String>, String> {
        self.log(&format!("Generating text for prompt: {}", prompt));
        
        let mut messages = Vec::new();
        
        if !system_prompt.is_empty() {
            messages.push(ChatMessage::system(system_prompt));
        }
        
        messages.push(ChatMessage::user(prompt));
        
        let request = ChatMessageRequest::new(self.model.clone(), messages);
        
        match self.ollama_client.send_chat_messages_stream(request).await {
            Ok(mut stream) => {
                let mut result = Vec::new();
                while let Some(Ok(response)) = stream.next().await {
                    result.push(response.message.content);
                }
                Ok(result)
            }
            Err(e) => Err(format!("Failed to generate text: {}", e)),
        }
    }
    
    // I dont think this is used anywhere but im keeping it just in case
    pub async fn archie(
        &self,
        query: String,
        conversation_history: Option<Vec<Message>>,
    ) -> Result<String, String> {
        self.log(&format!("Archie query: {}", query));
        
        // Load scraped data from JSON file
        let scrape_results = match tokio::fs::read_to_string("data/scrape_results.json").await {
            Ok(content) => content,
            Err(e) => {
                self.log(&format!("Warning: Could not read scrape_results.json: {}", e));
                "{}".to_string()
            }
        };
        
        let mut messages = Vec::new();
        
        let system_content = format!(
            r#"You are ArchieAI, an AI assistant for Arcadia University. You are here to help students, faculty, and staff with any questions they may have about the university.

You are made by students for a final project. You must be factual and accurate based on the information provided.

Respond based on your knowledge up to 2025.

Use the following university data to answer questions:
{}

If the university data doesn't contain the information needed, or if the query requires current/real-time information, you can use the search_web tool to find additional information."#,
            scrape_results
        );
        
        messages.push(ChatMessage::system(system_content));
        
        // Add conversation history
        if let Some(history) = conversation_history {
            for msg in history.iter().rev().take(5).rev() {
                messages.push(msg.to_chat_message());
            }
        }
        
        // Add current query
        messages.push(ChatMessage::user(query));
        
        let request = ChatMessageRequest::new(self.model.clone(), messages);
        
        match self.ollama_client.send_chat_messages(request).await {
            Ok(response) => {
                Ok(response.message.content)
            }
            Err(e) => Err(format!("Failed to get response from Archie AI: {}", e)),
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
                history_context.push_str(&format!("{}: {}\n", msg.role.to_uppercase(), msg.content));
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
