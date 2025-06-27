-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create custom types
CREATE TYPE query_status AS ENUM ('pending_discovery', 'discovering', 'completed', 'failed');
CREATE TYPE source_status AS ENUM ('active', 'paused', 'error', 'deleted');
CREATE TYPE source_type AS ENUM ('website', 'rss', 'youtube');

-- User Queries table
CREATE TABLE user_queries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    raw_query TEXT NOT NULL,
    status query_status DEFAULT 'pending_discovery' NOT NULL,
    config_hints_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Monitored Sources table
CREATE TABLE monitored_sources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    user_query_id UUID REFERENCES user_queries(id) ON DELETE SET NULL,
    url TEXT NOT NULL,
    name TEXT,
    source_type source_type DEFAULT 'website',
    status source_status DEFAULT 'active' NOT NULL,
    check_interval_seconds INTEGER DEFAULT 3600 NOT NULL,
    last_checked_at TIMESTAMPTZ,
    last_content_hash TEXT,
    last_significant_change_at TIMESTAMPTZ,
    last_error TEXT,
    error_count INTEGER DEFAULT 0 NOT NULL,
    keywords_json JSONB,
    config_json JSONB,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT unique_user_url UNIQUE (user_id, url)
);

-- Scraped Content table
CREATE TABLE scraped_contents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    monitored_source_id UUID REFERENCES monitored_sources(id) ON DELETE CASCADE NOT NULL,
    scraped_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    raw_content TEXT NOT NULL,
    processed_text TEXT,
    content_hash TEXT GENERATED ALWAYS AS (encode(digest(raw_content, 'sha256'), 'hex')) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Content Embeddings table with pgvector
CREATE TABLE content_embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scraped_content_id UUID REFERENCES scraped_contents(id) ON DELETE CASCADE NOT NULL UNIQUE,
    embedding_vector vector(1536), -- OpenAI embeddings dimension
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Change Alerts table
CREATE TABLE change_alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    monitored_source_id UUID REFERENCES monitored_sources(id) ON DELETE CASCADE NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    change_summary TEXT,
    change_details JSONB,
    severity TEXT CHECK (severity IN ('low', 'medium', 'high')),
    is_acknowledged BOOLEAN DEFAULT FALSE NOT NULL,
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for better performance
CREATE INDEX idx_user_queries_user_id ON user_queries(user_id);
CREATE INDEX idx_user_queries_status ON user_queries(status);
CREATE INDEX idx_monitored_sources_user_id ON monitored_sources(user_id);
CREATE INDEX idx_monitored_sources_status ON monitored_sources(status);
CREATE INDEX idx_monitored_sources_last_checked ON monitored_sources(last_checked_at);
CREATE INDEX idx_scraped_contents_monitored_source ON scraped_contents(monitored_source_id);
CREATE INDEX idx_scraped_contents_scraped_at ON scraped_contents(scraped_at);
CREATE INDEX idx_content_embeddings_scraped_content ON content_embeddings(scraped_content_id);
CREATE INDEX idx_change_alerts_user_id ON change_alerts(user_id);
CREATE INDEX idx_change_alerts_monitored_source ON change_alerts(monitored_source_id);
CREATE INDEX idx_change_alerts_detected_at ON change_alerts(detected_at);
CREATE INDEX idx_change_alerts_acknowledged ON change_alerts(is_acknowledged);

-- Create vector similarity search index
CREATE INDEX idx_content_embeddings_vector ON content_embeddings 
USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);

-- Enable Row Level Security
ALTER TABLE user_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitored_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraped_contents ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE change_alerts ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_queries
CREATE POLICY "Users can view own queries" ON user_queries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own queries" ON user_queries
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own queries" ON user_queries
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own queries" ON user_queries
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for monitored_sources
CREATE POLICY "Users can view own sources" ON monitored_sources
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own sources" ON monitored_sources
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sources" ON monitored_sources
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own sources" ON monitored_sources
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for scraped_contents (users can view content from their sources)
CREATE POLICY "Users can view content from own sources" ON scraped_contents
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM monitored_sources 
            WHERE monitored_sources.id = scraped_contents.monitored_source_id 
            AND monitored_sources.user_id = auth.uid()
        )
    );

-- Service role can insert/update scraped content
CREATE POLICY "Service role can manage scraped content" ON scraped_contents
    FOR ALL USING (auth.role() = 'service_role');

-- RLS Policies for content_embeddings (similar to scraped_contents)
CREATE POLICY "Users can view embeddings from own sources" ON content_embeddings
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM scraped_contents
            JOIN monitored_sources ON monitored_sources.id = scraped_contents.monitored_source_id
            WHERE scraped_contents.id = content_embeddings.scraped_content_id 
            AND monitored_sources.user_id = auth.uid()
        )
    );

CREATE POLICY "Service role can manage embeddings" ON content_embeddings
    FOR ALL USING (auth.role() = 'service_role');

-- RLS Policies for change_alerts
CREATE POLICY "Users can view own alerts" ON change_alerts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own alerts" ON change_alerts
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role can create alerts" ON change_alerts
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_user_queries_updated_at
    BEFORE UPDATE ON user_queries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_monitored_sources_updated_at
    BEFORE UPDATE ON monitored_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Create function to get similar content
CREATE OR REPLACE FUNCTION get_similar_content(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    scraped_content_id UUID,
    monitored_source_id UUID,
    similarity float
)
LANGUAGE sql STABLE
AS $$
    SELECT 
        ce.scraped_content_id,
        sc.monitored_source_id,
        1 - (ce.embedding_vector <=> query_embedding) as similarity
    FROM content_embeddings ce
    JOIN scraped_contents sc ON sc.id = ce.scraped_content_id
    WHERE 1 - (ce.embedding_vector <=> query_embedding) > match_threshold
    ORDER BY ce.embedding_vector <=> query_embedding
    LIMIT match_count;
$$;

-- Create view for user's active alerts
CREATE OR REPLACE VIEW active_alerts AS
SELECT 
    ca.*,
    ms.name as source_name,
    ms.url as source_url
FROM change_alerts ca
JOIN monitored_sources ms ON ms.id = ca.monitored_source_id
WHERE ca.is_acknowledged = false
AND ms.is_deleted = false;

-- Grant access to the view
GRANT SELECT ON active_alerts TO authenticated;