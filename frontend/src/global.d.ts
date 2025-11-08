// Global type declarations for the frontend

declare global {
  interface Window {
    CONFIG?: {
      apiUrl?: string;
      clerkPublishableKey?: string;
    };
  }
}

export {};
