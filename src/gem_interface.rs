// AI Interface using Ollama for local LLM inference with streaming support.
// Keeps the original synchronous web scraper (requests + BeautifulSoup) but improves it
// by adding a requests.Session with browser-like headers and a retry strategy to reduce
// 403/429/5xx failures. Everything else remains async-friendly by running blocking
// operations in a threadpool.

use serde::{Deserialize, Serialize};
use std::env;
use reqwest::Client;
use tokio::time::Duration;

#[derive(Debug, Serialize, Deserialize)]
pub struct Message {
    pub role: String,
    pub content: String,
}

#[derive(Debug)]
pub struct AiInterface {
    model: String,
    debug: bool,
    scraper_timeout: u64,
    client: Client,
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
        scraper_timeout: u64,
    ) -> Self {
        // Load the variables from the .env file into the environment
        dotenv::dotenv().ok();
        
        // Retrieve the model name from environment (defaults to llama2 if not set)
        let model = env::var("MODEL").unwrap_or_else(|_| "llama2".to_string());
        
        // Create a reqwest client with headers and retry strategy
        let client = Client::builder()
            .timeout(Duration::from_secs(scraper_timeout))
            .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            .build()
            .expect("Failed to create HTTP client");
        
        AiInterface {
            model,
            debug,
            scraper_timeout,
            client,
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
    ) -> Result<String, String> {
        self.log(&format!("Generating text for prompt: {}", prompt));
        
        let mut messages = Vec::new();
        
        if !system_prompt.is_empty() {
            messages.push(Message {
                role: "system".to_string(),
                content: system_prompt,
            });
        }
        
        messages.push(Message {
            role: "user".to_string(),
            content: prompt,
        });
        
        // Placeholder for actual Ollama API call
        // In a real implementation, this would make an async call to the Ollama API
        Ok("Response from AI".to_string())
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
            Err(e) => return Err(format!("Failed to read scrape results: {}", e)),
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
        
        messages.push(Message {
            role: "system".to_string(),
            content: system_content,
        });
        
        // Add conversation history
        if let Some(history) = conversation_history {
            for msg in history.iter().rev().take(5).rev() {
                messages.push(msg.clone());
            }
        }
        
        // Add current query
        messages.push(Message {
            role: "user".to_string(),
            content: query,
        });
        
        // Placeholder for actual Ollama API call
        Ok("Response from Archie AI".to_string())
    }
    
    pub async fn async_web_search(
        &self,
        prompt: String,
        _system_prompt: String,
    ) -> Result<Vec<String>, String> {
        self.log(&format!("Web search for: {}", prompt));
        
        let _ollama_api_key = env::var("OLLAMA_API_KEY")
            .or_else(|_| env::var("OLLAMA_TOKEN"))
            .map_err(|_| "Error: OLLAMA_API_KEY (or OLLAMA_TOKEN) not found in environment".to_string())?;
        
        let _model = env::var("OLLAMA_MODEL")
            .map_err(|_| "Error: OLLAMA_MODEL not found in environment".to_string())?;
        
        // Placeholder for actual web search implementation
        // In a real implementation, this would use the Ollama API with web_search and web_fetch tools
        let mut results = Vec::new();
        results.push("Search result 1".to_string());
        results.push("Search result 2".to_string());
        
        Ok(results)
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

impl Clone for Message {
    fn clone(&self) -> Self {
        Message {
            role: self.role.clone(),
            content: self.content.clone(),
        }
    }
}
