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

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn setup_test_dir(name: &str) -> String {
        let test_dir = format!("/tmp/test_{}", name);
        let _ = fs::remove_dir_all(&test_dir);
        test_dir
    }

    fn cleanup_test_dir(dir: &str) {
        let _ = fs::remove_dir_all(dir);
    }

    #[test]
    fn test_data_collector_new() {
        let test_dir = setup_test_dir("data_collector_new");
        let collector = DataCollector::new(&test_dir);
        
        // Check that directory and JSON file are created
        assert!(std::path::Path::new(&test_dir).exists());
        assert!(collector.json_file.exists());
        
        cleanup_test_dir(&test_dir);
    }

    #[test]
    fn test_log_interaction() {
        let test_dir = setup_test_dir("log_interaction");
        let collector = DataCollector::new(&test_dir);
        
        collector.log_interaction(
            "session123".to_string(),
            Some("test@example.com".to_string()),
            "127.0.0.1".to_string(),
            "Mozilla/5.0".to_string(),
            "What is Arcadia?".to_string(),
            "Arcadia is a university.".to_string(),
            1.234,
        );
        
        // Read the JSON file
        let content = fs::read_to_string(&collector.json_file).expect("Failed to read JSON file");
        let data: Vec<Interaction> = serde_json::from_str(&content).expect("Failed to parse JSON");
        
        assert_eq!(data.len(), 1);
        assert_eq!(data[0].session_id, "session123");
        assert_eq!(data[0].user_email, "test@example.com");
        assert_eq!(data[0].question, "What is Arcadia?");
        assert_eq!(data[0].answer, "Arcadia is a university.");
        assert_eq!(data[0].question_length, 16);
        assert_eq!(data[0].answer_length, 24);
        
        cleanup_test_dir(&test_dir);
    }

    #[test]
    fn test_log_multiple_interactions() {
        let test_dir = setup_test_dir("log_multiple");
        let collector = DataCollector::new(&test_dir);
        
        collector.log_interaction(
            "session1".to_string(),
            Some("user1@example.com".to_string()),
            "127.0.0.1".to_string(),
            "device1".to_string(),
            "Question 1".to_string(),
            "Answer 1".to_string(),
            1.0,
        );
        
        collector.log_interaction(
            "session2".to_string(),
            Some("user2@example.com".to_string()),
            "127.0.0.2".to_string(),
            "device2".to_string(),
            "Question 2".to_string(),
            "Answer 2".to_string(),
            2.0,
        );
        
        let content = fs::read_to_string(&collector.json_file).expect("Failed to read JSON file");
        let data: Vec<Interaction> = serde_json::from_str(&content).expect("Failed to parse JSON");
        
        assert_eq!(data.len(), 2);
        assert_eq!(data[0].session_id, "session1");
        assert_eq!(data[1].session_id, "session2");
        
        cleanup_test_dir(&test_dir);
    }

    #[test]
    fn test_log_interaction_guest_user() {
        let test_dir = setup_test_dir("log_guest");
        let collector = DataCollector::new(&test_dir);
        
        collector.log_interaction(
            "session123".to_string(),
            None, // No user email
            "127.0.0.1".to_string(),
            "device".to_string(),
            "Question".to_string(),
            "Answer".to_string(),
            1.5,
        );
        
        let content = fs::read_to_string(&collector.json_file).expect("Failed to read JSON file");
        let data: Vec<Interaction> = serde_json::from_str(&content).expect("Failed to parse JSON");
        
        assert_eq!(data.len(), 1);
        assert_eq!(data[0].user_email, "guest"); // Should default to "guest"
        
        cleanup_test_dir(&test_dir);
    }

    #[test]
    fn test_generation_time_rounding() {
        let test_dir = setup_test_dir("time_rounding");
        let collector = DataCollector::new(&test_dir);
        
        collector.log_interaction(
            "session".to_string(),
            Some("test@example.com".to_string()),
            "127.0.0.1".to_string(),
            "device".to_string(),
            "Question".to_string(),
            "Answer".to_string(),
            1.23456789, // Should be rounded to 2 decimal places
        );
        
        let content = fs::read_to_string(&collector.json_file).expect("Failed to read JSON file");
        let data: Vec<Interaction> = serde_json::from_str(&content).expect("Failed to parse JSON");
        
        assert_eq!(data[0].generation_time_seconds, 1.23);
        
        cleanup_test_dir(&test_dir);
    }

    #[test]
    fn test_interaction_serialization() {
        let interaction = Interaction {
            timestamp: "2023-01-01T00:00:00Z".to_string(),
            session_id: "test_session".to_string(),
            user_email: "test@example.com".to_string(),
            ip_address: "127.0.0.1".to_string(),
            device_info: "test_device".to_string(),
            question: "test question".to_string(),
            question_length: 13,
            answer: "test answer".to_string(),
            answer_length: 11,
            generation_time_seconds: 1.5,
        };
        
        let json = serde_json::to_string(&interaction).expect("Failed to serialize");
        assert!(json.contains("test_session"));
        assert!(json.contains("test@example.com"));
        
        let deserialized: Interaction = serde_json::from_str(&json).expect("Failed to deserialize");
        assert_eq!(deserialized.session_id, "test_session");
    }

    #[test]
    fn test_persistence_across_instances() {
        let test_dir = setup_test_dir("persistence");
        
        {
            let collector1 = DataCollector::new(&test_dir);
            collector1.log_interaction(
                "session1".to_string(),
                Some("test@example.com".to_string()),
                "127.0.0.1".to_string(),
                "device".to_string(),
                "Question 1".to_string(),
                "Answer 1".to_string(),
                1.0,
            );
        }
        
        // Create a new instance and log another interaction
        {
            let collector2 = DataCollector::new(&test_dir);
            collector2.log_interaction(
                "session2".to_string(),
                Some("test@example.com".to_string()),
                "127.0.0.1".to_string(),
                "device".to_string(),
                "Question 2".to_string(),
                "Answer 2".to_string(),
                2.0,
            );
            
            // Read and verify both interactions are present
            let content = fs::read_to_string(&collector2.json_file).expect("Failed to read JSON file");
            let data: Vec<Interaction> = serde_json::from_str(&content).expect("Failed to parse JSON");
            
            assert_eq!(data.len(), 2);
        }
        
        cleanup_test_dir(&test_dir);
    }
}
