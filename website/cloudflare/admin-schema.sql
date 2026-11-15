CREATE TABLE IF NOT EXISTS forum_post_moderation (post_id TEXT PRIMARY KEY REFERENCES forum_posts(id) ON DELETE CASCADE, hidden INTEGER NOT NULL CHECK(hidden IN (0,1)), updated_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS forum_admin_sessions (id_hash TEXT PRIMARY KEY, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS forum_admin_nonces (nonce TEXT PRIMARY KEY, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS forum_admin_limits (tag TEXT PRIMARY KEY, bucket INTEGER NOT NULL, count INTEGER NOT NULL CHECK(count>=1 AND count<=cap), cap INTEGER NOT NULL, last_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS forum_admin_audit (id TEXT PRIMARY KEY, action TEXT NOT NULL CHECK(action IN ('hide','restore','close','reopen')), target_type TEXT NOT NULL CHECK(target_type IN ('thread','post')), target_id TEXT NOT NULL, created_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS forum_admin_audit_recent ON forum_admin_audit(created_at DESC,id DESC);
