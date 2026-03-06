-- Migration: Add theme preference to users table
-- Date: 2026-03-06
-- Description: Adds a theme column to store user's preferred theme (light/dark)

ALTER TABLE users
ADD COLUMN IF NOT EXISTS theme VARCHAR(10) DEFAULT 'light' NOT NULL;

-- Add a constraint to ensure only valid theme values
ALTER TABLE users
ADD CONSTRAINT check_theme_valid CHECK (theme IN ('light', 'dark'));

-- Create an index for faster theme lookups
CREATE INDEX IF NOT EXISTS idx_users_theme ON users(theme);
