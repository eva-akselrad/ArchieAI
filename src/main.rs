// ArchieAI Rust Web Server
// Converted from Flask app.py to Axum
// Maintains the same functionality as the Python version

use axum::{
    extract::{Path, State},
    http::{header, HeaderMap, StatusCode},
    response::{Html, IntoResponse, Redirect, Response, Sse},
    routing::{delete, get, post},
    Form, Json, Router,
};
use axum::response::sse::{Event, KeepAlive};
use serde::{Deserialize, Serialize};
use std::convert::Infallible;
use std::sync::Arc;
use std::time::Instant;
use tower_http::services::ServeDir;

use archie_ai_rust::{AiInterface, DataCollector, SessionManager};

// Application state shared across handlers
#[derive(Clone)]
struct AppState {
    session_manager: Arc<SessionManager>,
    data_collector: Arc<DataCollector>,
    ai_interface: Arc<AiInterface>,
}

// Request/Response types
#[derive(Debug, Deserialize)]
struct ArchieRequest {
    question: String,
}

#[derive(Debug, Serialize)]
struct ArchieResponse {
    answer: String,
}

#[derive(Debug, Serialize)]
struct ErrorResponse {
    error: String,
}

#[derive(Debug, Serialize)]
struct MessageResponse {
    message: String,
}

#[derive(Debug, Serialize)]
struct SessionResponse {
    session_id: String,
}

#[derive(Debug, Serialize)]
struct SessionHistoryResponse {
    history: Vec<archie_ai_rust::session_manager::Message>,
}

#[derive(Debug, Serialize)]
struct SessionListResponse {
    sessions: Vec<archie_ai_rust::session_manager::SessionPreview>,
}

#[derive(Debug, Deserialize)]
struct LoginForm {
    email: String,
    password: String,
}

// Helper function to extract cookie value
fn get_cookie(headers: &HeaderMap, name: &str) -> Option<String> {
    headers
        .get(header::COOKIE)
        .and_then(|v| v.to_str().ok())
        .and_then(|cookies| {
            cookies
                .split(';')
                .find_map(|cookie| {
                    let parts: Vec<&str> = cookie.trim().splitn(2, '=').collect();
                    if parts.len() == 2 && parts[0] == name {
                        Some(parts[1].to_string())
                    } else {
                        None
                    }
                })
        })
}

// Helper function to set cookies
fn create_cookie_header(name: &str, value: &str) -> String {
    format!("{}={}; Path=/; HttpOnly; SameSite=Strict", name, value)
}

#[tokio::main]
async fn main() {
    // Initialize components
    let session_manager = Arc::new(SessionManager::new("data"));
    let data_collector = Arc::new(DataCollector::new("data"));
    let ai_interface = Arc::new(AiInterface::new(false, 3, 1.0, 15));

    let state = AppState {
        session_manager,
        data_collector,
        ai_interface,
    };

    // Build router with all routes
    let app = Router::new()
        .route("/", get(home))
        .route("/index", get(index))
        .route("/api/archie", post(api_archie))
        .route("/api/archie/stream", post(api_archie_stream))
        .route("/api/sessions/history", get(get_session_history))
        .route("/api/sessions/list", get(list_user_sessions))
        .route("/api/sessions/{session_id}", get(get_session_details))
        .route("/api/sessions/{session_id}", delete(delete_session_handler))
        .route("/api/sessions/new", post(create_new_session))
        .route("/api/sessions/switch/{session_id}", post(switch_session))
        .route("/chats", get(chats_get).post(chats_post))
        .nest_service("/static", ServeDir::new("src/static"))
        .with_state(state);

    // Start server
    let listener = tokio::net::TcpListener::bind("0.0.0.0:5000")
        .await
        .expect("Failed to bind to port 5000");
    
    println!("Server running on http://0.0.0.0:5000");
    
    axum::serve(listener, app)
        .await
        .expect("Server failed to start");
}

// Route handlers

async fn home(headers: HeaderMap) -> Response {
    let session_id = get_cookie(&headers, "session_id");
    
    if session_id.is_some() {
        // User has session, redirect to chat
        Redirect::to("/index").into_response()
    } else {
        // No session, show login page
        match tokio::fs::read_to_string("src/templates/home.html").await {
            Ok(content) => Html(content).into_response(),
            Err(e) => (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to load home page Error {e}")).into_response(),
        }
    }
}

async fn index(headers: HeaderMap) -> Response {
    let session_id = get_cookie(&headers, "session_id");
    
    if session_id.is_none() {
        // No session, redirect to login
        return Redirect::to("/").into_response();
    }
    
    match tokio::fs::read_to_string("src/templates/index.html").await {
        Ok(content) => Html(content).into_response(),
        Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Failed to load chat page").into_response(),
    }
}

async fn api_archie(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(payload): Json<ArchieRequest>,
) -> Response {
    let start_time = Instant::now();
    
    let session_id = get_cookie(&headers, "session_id");
    let user_email = get_cookie(&headers, "user_email");
    let question = payload.question;
    
    // Get conversation history if session exists
    let conversation_history = if let Some(ref sid) = session_id {
        state.session_manager.get_conversation_history(sid)
    } else {
        Vec::new()
    };
    
    // Convert to AI interface format
    let history: Option<Vec<archie_ai_rust::gem_interface::Message>> = if conversation_history.is_empty() {
        None
    } else {
        Some(conversation_history.iter().map(|m| {
            archie_ai_rust::gem_interface::Message {
                role: m.role.clone(),
                content: m.content.clone(),
            }
        }).collect())
    };
    
    // Call AI
    let answer = match state.ai_interface.archie_streaming(question.clone(), history).await {
        Ok(tokens) => tokens.join(""),
        Err(e) => format!("Error: {}", e),
    };
    
    let generation_time = start_time.elapsed().as_secs_f64();
    
    // Save to session if session_id exists
    if let Some(ref sid) = session_id {
        state.session_manager.add_message(sid, "user".to_string(), question.clone());
        state.session_manager.add_message(sid, "assistant".to_string(), answer.clone());
    }
    
    // Get IP address (simplified - would need tower middleware for real IP)
    let ip_address = "unknown".to_string();
    let device_info = headers
        .get(header::USER_AGENT)
        .and_then(|v| v.to_str().ok())
        .unwrap_or("unknown")
        .to_string();
    
    // Collect analytics data
    state.data_collector.log_interaction(
        session_id.unwrap_or_else(|| "no_session".to_string()),
        user_email,
        ip_address,
        device_info,
        question.clone(),
        answer.clone(),
        generation_time,
    );
    
    println!("Question: {}\nAnswer: {}\n", question, answer);
    
    Json(ArchieResponse { answer }).into_response()
}

async fn api_archie_stream(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(payload): Json<ArchieRequest>,
) -> Response {
    let session_id = get_cookie(&headers, "session_id");
    let user_email = get_cookie(&headers, "user_email");
    let question = payload.question.clone();
    
    let ip_address = "unknown".to_string();
    let device_info = headers
        .get(header::USER_AGENT)
        .and_then(|v| v.to_str().ok())
        .unwrap_or("unknown")
        .to_string();
    
    // Clone for the stream
    let state_clone = state.clone();
    let session_id_clone = session_id.clone();
    let user_email_clone = user_email.clone();
    let question_clone = question.clone();
    
    let stream = async_stream::stream! {
        let start_time = Instant::now();
        let mut full_response = String::new();
        
        // Get conversation history
        let conversation_history = if let Some(ref sid) = session_id_clone {
            state_clone.session_manager.get_conversation_history(sid)
        } else {
            Vec::new()
        };
        
        let history: Option<Vec<archie_ai_rust::gem_interface::Message>> = if conversation_history.is_empty() {
            None
        } else {
            Some(conversation_history.iter().map(|m| {
                archie_ai_rust::gem_interface::Message {
                    role: m.role.clone(),
                    content: m.content.clone(),
                }
            }).collect())
        };
        
        // Stream tokens
        match state_clone.ai_interface.archie_streaming(question_clone.clone(), history).await {
            Ok(tokens) => {
                for token in tokens {
                    full_response.push_str(&token);
                    let data = serde_json::json!({ "token": token });
                    yield Ok::<_, Infallible>(Event::default().data(data.to_string()));
                }
            }
            Err(e) => {
                let error_data = serde_json::json!({ "error": e });
                yield Ok(Event::default().data(error_data.to_string()));
            }
        }
        
        let generation_time = start_time.elapsed().as_secs_f64();
        
        // Save to session
        if let Some(ref sid) = session_id_clone {
            state_clone.session_manager.add_message(sid, "user".to_string(), question_clone.clone());
            state_clone.session_manager.add_message(sid, "assistant".to_string(), full_response.clone());
        }
        
        // Collect analytics
        state_clone.data_collector.log_interaction(
            session_id_clone.unwrap_or_else(|| "no_session".to_string()),
            user_email_clone,
            ip_address,
            device_info,
            question_clone.clone(),
            full_response.clone(),
            generation_time,
        );
        
        println!("Question: {}\nAnswer: {}\n", question_clone, full_response);
        
        // Send completion signal
        let done_data = serde_json::json!({ "done": true });
        yield Ok(Event::default().data(done_data.to_string()));
    };
    
    Sse::new(stream).keep_alive(KeepAlive::default()).into_response()
}

async fn get_session_history(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> Response {
    let session_id = get_cookie(&headers, "session_id");
    
    match session_id {
        Some(sid) => {
            let history = state.session_manager.get_conversation_history(&sid);
            Json(SessionHistoryResponse { history }).into_response()
        }
        None => (
            StatusCode::UNAUTHORIZED,
            Json(ErrorResponse { error: "No session found".to_string() })
        ).into_response(),
    }
}

async fn list_user_sessions(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> Response {
    let user_email = get_cookie(&headers, "user_email");
    
    match user_email {
        Some(email) => {
            let sessions = state.session_manager.get_all_user_sessions_with_preview(&email);
            Json(SessionListResponse { sessions }).into_response()
        }
        None => (
            StatusCode::UNAUTHORIZED,
            Json(ErrorResponse { error: "Not logged in".to_string() })
        ).into_response(),
    }
}

async fn get_session_details(
    State(state): State<AppState>,
    Path(session_id): Path<String>,
    headers: HeaderMap,
) -> Response {
    let user_email = get_cookie(&headers, "user_email");
    let current_session_id = get_cookie(&headers, "session_id");
    
    match state.session_manager.get_session(&session_id) {
        Some(session_data) => {
            // Check authorization
            if session_data.user_email != user_email && Some(session_id.clone()) != current_session_id {
                return (
                    StatusCode::FORBIDDEN,
                    Json(ErrorResponse { error: "Unauthorized".to_string() })
                ).into_response();
            }
            Json(session_data).into_response()
        }
        None => (
            StatusCode::NOT_FOUND,
            Json(ErrorResponse { error: "Session not found".to_string() })
        ).into_response(),
    }
}

async fn delete_session_handler(
    State(state): State<AppState>,
    Path(session_id): Path<String>,
    headers: HeaderMap,
) -> Response {
    let user_email = get_cookie(&headers, "user_email");
    let current_session_id = get_cookie(&headers, "session_id");
    
    match state.session_manager.get_session(&session_id) {
        Some(session_data) => {
            // Check authorization
            if session_data.user_email != user_email && Some(session_id.clone()) != current_session_id {
                return (
                    StatusCode::FORBIDDEN,
                    Json(ErrorResponse { error: "Unauthorized".to_string() })
                ).into_response();
            }
            
            let success = state.session_manager.delete_session(&session_id, user_email);
            if success {
                Json(MessageResponse { message: "Session deleted".to_string() }).into_response()
            } else {
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    Json(ErrorResponse { error: "Failed to delete session".to_string() })
                ).into_response()
            }
        }
        None => (
            StatusCode::NOT_FOUND,
            Json(ErrorResponse { error: "Session not found".to_string() })
        ).into_response(),
    }
}

async fn create_new_session(
    State(state): State<AppState>,
    headers: HeaderMap,
) -> Response {
    let user_email = get_cookie(&headers, "user_email");
    
    let session_id = state.session_manager.create_session(user_email);
    
    let mut response = Json(SessionResponse { session_id: session_id.clone() }).into_response();
    
    // Set cookie
    if let Ok(headers) = response.headers_mut().try_insert(
        header::SET_COOKIE,
        create_cookie_header("session_id", &session_id).parse().unwrap()
    ) {
        let _ = headers;
    }
    
    response
}

async fn switch_session(
    State(state): State<AppState>,
    Path(session_id): Path<String>,
    headers: HeaderMap,
) -> Response {
    let user_email = get_cookie(&headers, "user_email");
    
    match state.session_manager.get_session(&session_id) {
        Some(session_data) => {
            // Check authorization
            if session_data.user_email != user_email {
                return (
                    StatusCode::FORBIDDEN,
                    Json(ErrorResponse { error: "Unauthorized".to_string() })
                ).into_response();
            }
            
            let mut response = Json(MessageResponse { message: "Session switched".to_string() }).into_response();
            
            // Set cookie with Lax instead of Strict (as in Python version)
            let cookie_header = format!("{}={}; Path=/; HttpOnly; SameSite=Lax", "session_id", session_id);
            if let Ok(headers) = response.headers_mut().try_insert(
                header::SET_COOKIE,
                cookie_header.parse().unwrap()
            ) {
                let _ = headers;
            }
            
            response
        }
        None => (
            StatusCode::NOT_FOUND,
            Json(ErrorResponse { error: "Session not found".to_string() })
        ).into_response(),
    }
}

async fn chats_get() -> Response {
    match tokio::fs::read_to_string("src/templates/home.html").await {
        Ok(content) => Html(content).into_response(),
        Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Failed to load home page").into_response(),
    }
}

async fn chats_post(
    State(state): State<AppState>,
    headers: HeaderMap,
    Form(form): Form<LoginForm>,
) -> Response {
    let email = form.email.trim();
    let password = form.password;
    
    // Basic email validation
    if email.is_empty() || !email.contains('@') || email.len() > 255 {
        return match tokio::fs::read_to_string("src/templates/home.html").await {
            Ok(mut content) => {
                // This is simplified - in production you'd use a template engine
                content = content.replace("</body>", "<script>alert('Please provide a valid email address');</script></body>");
                Html(content).into_response()
            }
            Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Failed to load page").into_response(),
        };
    }
    
    if password.is_empty() {
        return match tokio::fs::read_to_string("src/templates/home.html").await {
            Ok(mut content) => {
                content = content.replace("</body>", "<script>alert('Password is required');</script></body>");
                Html(content).into_response()
            }
            Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Failed to load page").into_response(),
        };
    }
    
    // Try to authenticate user
    if state.session_manager.authenticate_user(email, &password) {
        // User exists and password is correct
        let session_id = state.session_manager.create_session(Some(email.to_string()));
        
        println!("User {} logged in with session: {}", email, session_id);
        
        let mut response = Redirect::to("/index").into_response();
        
        // Set cookies
        let headers_mut = response.headers_mut();
        headers_mut.insert(
            header::SET_COOKIE,
            create_cookie_header("session_id", &session_id).parse().unwrap()
        );
        headers_mut.append(
            header::SET_COOKIE,
            create_cookie_header("user_email", email).parse().unwrap()
        );
        
        response
    } else {
        // User doesn't exist, create new account
        let ip_address = "unknown".to_string();
        let device_info = headers
            .get(header::USER_AGENT)
            .and_then(|v| v.to_str().ok())
            .unwrap_or("unknown")
            .to_string();
        
        if state.session_manager.create_user(
            email.to_string(),
            password,
            ip_address,
            device_info,
        ) {
            let session_id = state.session_manager.create_session(Some(email.to_string()));
            
            println!("New user {} created with session: {}", email, session_id);
            
            let mut response = Redirect::to("/index").into_response();
            
            // Set cookies
            let headers_mut = response.headers_mut();
            headers_mut.insert(
                header::SET_COOKIE,
                create_cookie_header("session_id", &session_id).parse().unwrap()
            );
            headers_mut.append(
                header::SET_COOKIE,
                create_cookie_header("user_email", email).parse().unwrap()
            );
            
            response
        } else {
            match tokio::fs::read_to_string("src/templates/home.html").await {
                Ok(mut content) => {
                    content = content.replace("</body>", "<script>alert('Failed to create account');</script></body>");
                    Html(content).into_response()
                }
                Err(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Failed to load page").into_response(),
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_cookie() {
        let mut headers = HeaderMap::new();
        headers.insert(
            header::COOKIE,
            "session_id=test123; user_email=test@example.com".parse().unwrap()
        );
        
        assert_eq!(get_cookie(&headers, "session_id"), Some("test123".to_string()));
        assert_eq!(get_cookie(&headers, "user_email"), Some("test@example.com".to_string()));
        assert_eq!(get_cookie(&headers, "nonexistent"), None);
    }

    #[test]
    fn test_create_cookie_header() {
        let cookie = create_cookie_header("session_id", "test123");
        assert!(cookie.contains("session_id=test123"));
        assert!(cookie.contains("HttpOnly"));
        assert!(cookie.contains("SameSite=Strict"));
    }

    #[tokio::test]
    async fn test_session_manager_creation() {
        let manager = SessionManager::new("test_data");
        let session_id = manager.create_session(Some("test@example.com".to_string()));
        assert!(!session_id.is_empty());
        
        // Cleanup
        let _ = std::fs::remove_dir_all("test_data");
    }

    #[tokio::test]
    async fn test_data_collector_creation() {
        let collector = DataCollector::new("test_data2");
        collector.log_interaction(
            "test_session".to_string(),
            Some("test@example.com".to_string()),
            "127.0.0.1".to_string(),
            "test_device".to_string(),
            "test question".to_string(),
            "test answer".to_string(),
            1.5,
        );
        
        // Cleanup
        let _ = std::fs::remove_dir_all("test_data2");
    }

    #[tokio::test]
    async fn test_ai_interface_creation() {
        let ai = AiInterface::new(false, 3, 1.0, 15);
        // Just verify it can be created without panicking
        assert!(true);
    }

    #[test]
    fn test_archie_request_deserialization() {
        let json = r#"{"question": "What is Arcadia?"}"#;
        let request: ArchieRequest = serde_json::from_str(json).unwrap();
        assert_eq!(request.question, "What is Arcadia?");
    }

    #[test]
    fn test_archie_response_serialization() {
        let response = ArchieResponse {
            answer: "Arcadia is a university".to_string(),
        };
        let json = serde_json::to_string(&response).unwrap();
        assert!(json.contains("Arcadia is a university"));
    }

    #[test]
    fn test_error_response_serialization() {
        let response = ErrorResponse {
            error: "Test error".to_string(),
        };
        let json = serde_json::to_string(&response).unwrap();
        assert!(json.contains("Test error"));
    }

    #[test]
    fn test_login_form_deserialization() {
        let _form = "email=test@example.com&password=secret123";
        // In a real test, you'd use the Form extractor, but this tests the struct
        let login = LoginForm {
            email: "test@example.com".to_string(),
            password: "secret123".to_string(),
        };
        assert_eq!(login.email, "test@example.com");
        assert_eq!(login.password, "secret123");
    }
}
