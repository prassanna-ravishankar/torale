import { createBrowserClient } from '@supabase/ssr';
import type { Database } from '@/types/supabase'; // Ensure this path is correct for your types

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl) {
  throw new Error("NEXT_PUBLIC_SUPABASE_URL is not set in .env.local or environment variables");
}

if (!supabaseAnonKey) {
  throw new Error("NEXT_PUBLIC_SUPABASE_ANON_KEY is not set in .env.local or environment variables");
}

export const supabase = createBrowserClient<Database>(supabaseUrl, supabaseAnonKey); 