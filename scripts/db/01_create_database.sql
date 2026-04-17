-- Run this in psql connected to the default postgres database.
-- Example: psql -U postgres -d postgres -f scripts/db/01_create_database.sql
SELECT 'CREATE DATABASE chatbot'
WHERE NOT EXISTS (
  SELECT 1 FROM pg_database WHERE datname = 'chatbot'
)\gexec
