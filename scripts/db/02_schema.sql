-- Run this in psql against chatbot database.
-- Example: psql -U postgres -d chatbot -f scripts/db/02_schema.sql

CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(36) PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS conversation_turns (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id VARCHAR(36) NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  provider VARCHAR(50) NOT NULL,
  model VARCHAR(100) NOT NULL,
  input_text TEXT NOT NULL,
  output_text TEXT NOT NULL,
  prompt_tokens INTEGER NOT NULL DEFAULT 0,
  completion_tokens INTEGER NOT NULL DEFAULT 0,
  total_tokens INTEGER NOT NULL DEFAULT 0,
  estimated_cost DOUBLE PRECISION NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_conversation_turns_user_id ON conversation_turns (user_id);
CREATE INDEX IF NOT EXISTS ix_conversation_turns_session_id ON conversation_turns (session_id);
CREATE INDEX IF NOT EXISTS ix_conversation_turns_timestamp ON conversation_turns (timestamp);
CREATE INDEX IF NOT EXISTS ix_conversation_turns_provider ON conversation_turns (provider);

CREATE TABLE IF NOT EXISTS conversation_summaries (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id VARCHAR(36) NOT NULL,
  summary_text TEXT NOT NULL,
  covered_until TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_conversation_summaries_user_id ON conversation_summaries (user_id);
CREATE INDEX IF NOT EXISTS ix_conversation_summaries_session_id ON conversation_summaries (session_id);
CREATE INDEX IF NOT EXISTS ix_conversation_summaries_covered_until ON conversation_summaries (covered_until);

CREATE TABLE IF NOT EXISTS documents (
  id VARCHAR(36) PRIMARY KEY,
  title VARCHAR(255),
  content TEXT NOT NULL,
  metadata TEXT,
  embedding TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_documents_created_at ON documents (created_at);
