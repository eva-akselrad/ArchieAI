// Data collection module for ArchieAI analytics.
// Collects interaction data and saves to JSON for later analysis.
// For the data science class I will probably remove this when the semester ends but for now it will help me collect data on how people are using ArchieAI
// and i will manipulate the data to find trends for my project

use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
pub struct Interaction {
    pub timestamp: String,
    pub session_id: String,
    pub user_email: String,
    pub ip_address: String,
    pub device_info: String,
    pub question: String,
    pub question_length: usize,
    pub answer: String,
    pub answer_length: usize,
    pub generation_time_seconds: f64,
}

pub struct DataCollector {
    data_dir: PathBuf,
    json_file: PathBuf,
}

impl DataCollector {
    /// Collects and logs interaction data to JSON file.
    pub fn new(data_dir: &str) -> Self {
        let data_dir = PathBuf::from(data_dir);
        let json_file = data_dir.join("analytics.json");

        // Ensure data directory exists
        fs::create_dir_all(&data_dir).expect("Failed to create data directory");

        // Initialize JSON file with empty array if it doesn't exist
        if !json_file.exists() {
            Self::create_json_file(&json_file);
        }

        DataCollector {
            data_dir,
            json_file,
        }
    }

    fn create_json_file(json_file: &PathBuf) {
        // Create JSON file with empty array
        let empty_array: Vec<Interaction> = Vec::new();
        let json_str =
            serde_json::to_string_pretty(&empty_array).expect("Failed to serialize empty array");
        fs::write(json_file, json_str).expect("Failed to write JSON file");
    }

    /// Log a user interaction to the JSON file.
    pub fn log_interaction(
        &self,
        session_id: String,
        user_email: Option<String>,
        ip_address: String,
        device_info: String,
        question: String,
        answer: String,
        generation_time_seconds: f64,
    ) {
        let timestamp = Utc::now().to_rfc3339();
        let question_length = question.len();
        let answer_length = answer.len();

        let interaction = Interaction {
            timestamp,
            session_id,
            user_email: user_email.unwrap_or_else(|| "guest".to_string()),
            ip_address,
            device_info,
            question,
            question_length,
            answer,
            answer_length,
            generation_time_seconds: (generation_time_seconds * 100.0).round() / 100.0,
        };

        // Read existing data
        let mut data: Vec<Interaction> = match fs::read_to_string(&self.json_file) {
            Ok(content) => serde_json::from_str(&content).unwrap_or_else(|_| Vec::new()),
            Err(_) => Vec::new(),
        };

        // Append new interaction
        data.push(interaction);

        // Write back to file
        let json_str =
            serde_json::to_string_pretty(&data).expect("Failed to serialize interactions");
        fs::write(&self.json_file, json_str).expect("Failed to write JSON file");
    }
}
