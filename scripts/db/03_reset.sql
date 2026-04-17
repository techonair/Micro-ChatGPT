-- Optional reset script for local development.
-- Example: psql -U postgres -d chatbot -f scripts/db/03_reset.sql
DROP TABLE IF EXISTS conversation_summaries;
DROP TABLE IF EXISTS conversation_turns;
DROP TABLE IF EXISTS users;
