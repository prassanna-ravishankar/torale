// Local development config
// In production, this file is replaced by Kubernetes ConfigMap mount
// Falls back to .env values when undefined
window.CONFIG = {
  apiUrl: undefined, // Falls back to localhost:8000
  clerkPublishableKey: undefined // Falls back to VITE_CLERK_PUBLISHABLE_KEY from .env
};
