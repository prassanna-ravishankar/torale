#!/bin/bash
set -e

# Simple deploy script - assumes gcloud is set up
if [ ! -f .env ]; then
    echo "Create .env from .env.example first"
    exit 1
fi

export $(cat .env | grep -v '^#' | xargs)

gcloud builds submit --config=cloudbuild.yaml \
    --substitutions=_SUPABASE_URL="$SUPABASE_URL",_SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY",_SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY",_TEMPORAL_HOST="$TEMPORAL_HOST",_OPENAI_API_KEY="$OPENAI_API_KEY",_ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"