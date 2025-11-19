// Session and user management for ArchieAI.
// Handles user accounts, session storage, and chat history.

use chrono::Utc;
use rand::Rng;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct User {
    pub email: String,
    pub password_hash: String,
    pub created_at: String,
    pub ip_address: String,
    pub device_info: String,
    pub sessions: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Message {
    pub role: String,
    pub content: String,
    pub timestamp: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SessionData {
    pub session_id: String,
    pub user_email: Option<String>,
    pub created_at: String,
    pub messages: Vec<Message>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SessionPreview {
    pub session_id: String,
    pub created_at: String,
    pub preview: String,
    pub message_count: usize,
}

pub struct SessionManager {
    data_dir: PathBuf,
    users_file: PathBuf,
    sessions_dir: PathBuf,
}

impl SessionManager {
    /// Manages user accounts and chat sessions with JSON file storage.
    pub fn new(data_dir: &str) -> Self {
        let data_dir = PathBuf::from(data_dir);
        let users_file = data_dir.join("users.json");
        let sessions_dir = data_dir.join("sessions");

        // Ensure directories exist
        fs::create_dir_all(&sessions_dir).expect("Failed to create sessions directory");

        // Initialize users file if it doesn't exist
        if !users_file.exists() {
            let empty_users: HashMap<String, User> = HashMap::new();
            let json_str =
                serde_json::to_string(&empty_users).expect("Failed to serialize empty users");
            fs::write(&users_file, json_str).expect("Failed to write users file");
        }

        SessionManager {
            data_dir,
            users_file,
            sessions_dir,
        }
    }

    fn load_users(&self) -> HashMap<String, User> {
        match fs::read_to_string(&self.users_file) {
            Ok(content) => serde_json::from_str(&content).unwrap_or_else(|e| {
                eprintln!("Warning: users.json is corrupted: {}", e);
                HashMap::new()
            }),
            Err(_) => HashMap::new(),
        }
    }

    fn save_users(&self, users: &HashMap<String, User>) {
        let json_str = serde_json::to_string_pretty(users).expect("Failed to serialize users");
        fs::write(&self.users_file, json_str).expect("Failed to write users file");
    }

    /// Create a new user account.
    pub fn create_user(
        &self,
        email: String,
        password: String,
        ip_address: String,
        device_info: String,
    ) -> bool {
        let mut users = self.load_users();

        if users.contains_key(&email) {
            return false;
        }

        let password_hash = self.generate_password_hash(&password);

        let user = User {
            email: email.clone(),
            password_hash,
            created_at: Utc::now().to_rfc3339(),
            ip_address,
            device_info,
            sessions: Vec::new(),
        };

        users.insert(email, user);
        self.save_users(&users);
        true
    }

    fn generate_password_hash(&self, password: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(password.as_bytes());
        let result = hasher.finalize();
        hex::encode(result)
    }

    fn check_password_hash(&self, password: &str, hash: &str) -> bool {
        let computed_hash = self.generate_password_hash(password);
        computed_hash == hash
    }

    /// Authenticate a user with email and password.
    pub fn authenticate_user(&self, email: &str, password: &str) -> bool {
        let users = self.load_users();

        match users.get(email) {
            Some(user) => self.check_password_hash(password, &user.password_hash),
            None => false,
        }
    }

    fn is_valid_session_id(&self, session_id: &str) -> bool {
        // Only allow alphanumeric, dash, and underscore characters
        session_id.len() <= 64
            && session_id
                .chars()
                .all(|c| c.is_alphanumeric() || c == '-' || c == '_')
    }

    /// Get all session IDs for a user.
    pub fn get_user_sessions(&self, email: &str) -> Vec<String> {
        let users = self.load_users();

        match users.get(email) {
            Some(user) => user.sessions.clone(),
            None => Vec::new(),
        }
    }

    /// Create a new chat session with a unique ID.
    pub fn create_session(&self, user_email: Option<String>) -> String {
        let session_id = self.generate_session_id();

        let session_data = SessionData {
            session_id: session_id.clone(),
            user_email: user_email.clone(),
            created_at: Utc::now().to_rfc3339(),
            messages: Vec::new(),
        };

        let session_file = self.sessions_dir.join(format!("{}.json", session_id));
        let json_str =
            serde_json::to_string_pretty(&session_data).expect("Failed to serialize session data");
        fs::write(session_file, json_str).expect("Failed to write session file");

        // Add session to user's session list if user is logged in
        if let Some(email) = user_email {
            let mut users = self.load_users();
            if let Some(user) = users.get_mut(&email) {
                user.sessions.push(session_id.clone());
                self.save_users(&users);
            }
        }

        session_id
    }

    fn generate_session_id(&self) -> String {
        let mut rng = rand::thread_rng();
        let bytes: Vec<u8> = (0..32).map(|_| rng.gen()).collect();
        base64::encode_config(&bytes, base64::URL_SAFE_NO_PAD)
    }

    /// Load a session from file.
    pub fn get_session(&self, session_id: &str) -> Option<SessionData> {
        if !self.is_valid_session_id(session_id) {
            eprintln!("Warning: invalid session_id format: {}", session_id);
            return None;
        }

        let session_file = self.sessions_dir.join(format!("{}.json", session_id));

        if !session_file.exists() {
            return None;
        }

        match fs::read_to_string(session_file) {
            Ok(content) => serde_json::from_str(&content).ok(),
            Err(_) => None,
        }
    }

    /// Save session data to file.
    pub fn save_session(&self, session_id: &str, session_data: &SessionData) -> Result<(), String> {
        if !self.is_valid_session_id(session_id) {
            return Err(format!("Invalid session_id format: {}", session_id));
        }

        let session_file = self.sessions_dir.join(format!("{}.json", session_id));
        let json_str = serde_json::to_string_pretty(session_data)
            .map_err(|e| format!("Failed to serialize session data: {}", e))?;
        fs::write(session_file, json_str)
            .map_err(|e| format!("Failed to write session file: {}", e))?;
        Ok(())
    }

    /// Add a message to a session.
    pub fn add_message(&self, session_id: &str, role: String, content: String) {
        let mut session_data = self.get_session(session_id).unwrap_or_else(|| {
            // Create new session if it doesn't exist
            SessionData {
                session_id: session_id.to_string(),
                user_email: None,
                created_at: Utc::now().to_rfc3339(),
                messages: Vec::new(),
            }
        });

        let message = Message {
            role,
            content,
            timestamp: Utc::now().to_rfc3339(),
        };

        session_data.messages.push(message);
        self.save_session(session_id, &session_data)
            .expect("Failed to save session");
    }

    /// Get conversation history for a session.
    pub fn get_conversation_history(&self, session_id: &str) -> Vec<Message> {
        match self.get_session(session_id) {
            Some(session_data) => {
                let messages = session_data.messages;
                // Return last 10 messages
                if messages.len() > 10 {
                    messages[messages.len() - 10..].to_vec()
                } else {
                    messages
                }
            }
            None => Vec::new(),
        }
    }

    /// Delete a chat session.
    pub fn delete_session(&self, session_id: &str, user_email: Option<String>) -> bool {
        if !self.is_valid_session_id(session_id) {
            eprintln!("Warning: invalid session_id format: {}", session_id);
            return false;
        }

        let session_file = self.sessions_dir.join(format!("{}.json", session_id));

        if !session_file.exists() {
            return false;
        }

        // Remove from user's session list if applicable
        // At the time i wrote this i wasnt sure if i would be allowing guest sessions or not
        // For the sake of time (and my sanity) i am keeping this in
        if let Some(email) = user_email {
            let mut users = self.load_users();
            if let Some(user) = users.get_mut(&email) {
                user.sessions.retain(|s| s != session_id);
                self.save_users(&users);
            }
        }

        // Delete the session file
        fs::remove_file(session_file).is_ok()
    }

    /// Get all sessions for a user with message preview.
    pub fn get_all_user_sessions_with_preview(&self, email: &str) -> Vec<SessionPreview> {
        let session_ids = self.get_user_sessions(email);
        let mut sessions = Vec::new();

        for session_id in session_ids {
            if let Some(session_data) = self.get_session(&session_id) {
                let messages = &session_data.messages;
                let preview = messages
                    .iter()
                    .find(|msg| msg.role == "user")
                    .map(|msg| {
                        let content = &msg.content;
                        if content.len() > 100 {
                            content[..100].to_string()
                        } else {
                            content.clone()
                        }
                    })
                    .unwrap_or_default();

                sessions.push(SessionPreview {
                    session_id,
                    created_at: session_data.created_at,
                    preview,
                    message_count: messages.len(),
                });
            }
        }

        sessions
    }
}

// Helper module for base64 encoding (all credit to copilot for this one)
mod base64 {
    const CHARSET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

    pub fn encode_config(input: &[u8], _config: u8) -> String {
        let mut result = String::new();
        let mut i = 0;

        while i < input.len() {
            let b1 = input[i];
            let b2 = if i + 1 < input.len() { input[i + 1] } else { 0 };
            let b3 = if i + 2 < input.len() { input[i + 2] } else { 0 };

            result.push(CHARSET[(b1 >> 2) as usize] as char);
            result.push(CHARSET[(((b1 & 0x03) << 4) | (b2 >> 4)) as usize] as char);

            if i + 1 < input.len() {
                result.push(CHARSET[(((b2 & 0x0f) << 2) | (b3 >> 6)) as usize] as char);
            }

            if i + 2 < input.len() {
                result.push(CHARSET[(b3 & 0x3f) as usize] as char);
            }

            i += 3;
        }

        result
    }

    pub const URL_SAFE_NO_PAD: u8 = 0;
}
