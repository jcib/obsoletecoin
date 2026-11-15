PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS public_state (name TEXT PRIMARY KEY, observed INTEGER NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS forum_threads (id TEXT PRIMARY KEY, title TEXT NOT NULL CHECK(length(title) BETWEEN 3 AND 120), created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, replies INTEGER NOT NULL DEFAULT 0, locked INTEGER NOT NULL DEFAULT 0, hidden INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS forum_threads_recent ON forum_threads(hidden, updated_at DESC, id);
CREATE TABLE IF NOT EXISTS forum_posts (id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES forum_threads(id) ON DELETE CASCADE, alias TEXT NOT NULL CHECK(length(alias) BETWEEN 1 AND 32), body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 5000), created_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS forum_posts_thread ON forum_posts(thread_id, created_at, id);
CREATE TABLE IF NOT EXISTS forum_nonces (nonce TEXT PRIMARY KEY, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS forum_limits (tag TEXT PRIMARY KEY, bucket INTEGER NOT NULL, count INTEGER NOT NULL CHECK(count>=1 AND count<=cap), cap INTEGER NOT NULL, last_at INTEGER NOT NULL);
CREATE TRIGGER IF NOT EXISTS forum_accept_post BEFORE INSERT ON forum_posts BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM forum_threads WHERE id=NEW.thread_id AND hidden=0 AND locked=0) THEN RAISE(ABORT,'thread unavailable') END;
 SELECT CASE WHEN (SELECT COUNT(*) FROM forum_posts WHERE thread_id=NEW.thread_id)>=1000 THEN RAISE(ABORT,'thread full') END;
END;
CREATE TRIGGER IF NOT EXISTS forum_update_thread AFTER INSERT ON forum_posts BEGIN
 UPDATE forum_threads SET updated_at=MAX(updated_at,NEW.created_at), replies=replies+1 WHERE id=NEW.thread_id;
END;

CREATE TABLE IF NOT EXISTS forum_post_moderation (post_id TEXT PRIMARY KEY REFERENCES forum_posts(id) ON DELETE CASCADE, hidden INTEGER NOT NULL CHECK(hidden IN (0,1)), updated_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS forum_admin_sessions (id_hash TEXT PRIMARY KEY, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS forum_admin_nonces (nonce TEXT PRIMARY KEY, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS forum_admin_limits (tag TEXT PRIMARY KEY, bucket INTEGER NOT NULL, count INTEGER NOT NULL CHECK(count>=1 AND count<=cap), cap INTEGER NOT NULL, last_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS forum_admin_audit (id TEXT PRIMARY KEY, action TEXT NOT NULL CHECK(action IN ('hide','restore','close','reopen')), target_type TEXT NOT NULL CHECK(target_type IN ('thread','post')), target_id TEXT NOT NULL, created_at INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS forum_admin_audit_recent ON forum_admin_audit(created_at DESC,id DESC);
