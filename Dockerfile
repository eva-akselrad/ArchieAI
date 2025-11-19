# Multi-stage build for ArchieAI Rust application
FROM rust:1.83 AS builder

# Create app directory
WORKDIR /app

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Copy source code
COPY src ./src

# Build the application in release mode
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Install required runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and data directory
WORKDIR /app

# Create data directory for persistent storage
RUN mkdir -p /app/data/sessions

# Copy the binary from builder
COPY --from=builder /app/target/release/archie-ai-rust /app/

# Copy templates and static files
COPY src/templates ./src/templates
COPY src/static ./src/static

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV RUST_BACKTRACE=1

# Run the binary
CMD ["/app/archie-ai-rust"]
