# Frontend Architecture

## 1. Overview

The AmbiAlert frontend is a Next.js application built with TypeScript, designed to provide a user-friendly interface for interacting with the AmbiAlert backend. It allows users to authenticate, discover potential monitoring sources, manage their monitored sources, and view change alerts.

Key technologies include:
*   **Next.js (App Router):** Framework for server-side rendering, client-side navigation, and API routes (though backend is separate).
*   **TypeScript:** For static typing and improved code quality.
*   **Tailwind CSS:** For utility-first styling.
*   **Supabase:** For user authentication (Supabase Auth via `@supabase/ssr`).
*   **Axios:** For making HTTP requests to the backend API.
*   **TanStack Query (React Query):** For server state management (caching, fetching, mutations).
*   **React Hook Form & Zod:** For form management and validation.
*   **React Hot Toast:** For displaying notifications.

## 2. Core Components and Pages

The frontend is structured around several key pages and reusable components:

### 2.1. Authentication (`src/app/auth/`, `src/middleware.ts`)
*   **Pages:**
    *   Sign-in, Sign-up, Forgot Password, Magic Link callback pages.
*   **`src/middleware.ts`:**
    *   Protects routes (e.g., `/dashboard`, `/discover`, `/sources`, `/alerts`, `/profile`) using `@supabase/ssr` to ensure only authenticated users can access them.
    *   Redirects unauthenticated users to the sign-in page.
*   **Supabase Client (`src/lib/supabase/client.ts`, `src/lib/supabase/server.ts`):**
    *   Provides client-side and server-side Supabase instances for authentication and session management.

### 2.2. Layout (`src/app/layout.tsx`)
*   The main application shell, including global providers like:
    *   `QueryClientProvider` for TanStack Query.
    *   `ToastProvider` for `react-hot-toast`.
    *   Likely includes a persistent navigation bar/sidebar.

### 2.3. API Client (`src/lib/axiosInstance.ts`)
*   A dedicated **Axios instance** configured with:
    *   The backend API base URL.
    *   An **Axios request interceptor** that automatically fetches the active user session/JWT from the Supabase client (`@supabase/ssr` or client-side Supabase instance) and adds it as an `Authorization: Bearer <token>` header to outgoing requests.
*   Contains type-safe functions that encapsulate Axios calls for all backend API endpoints. These functions are then used by TanStack Query hooks.

### 2.4. State Management
*   **TanStack Query (React Query):**
    *   Used for all server state management: fetching, caching, synchronizing, and updating data from the backend.
    *   `useQuery` hooks are used for GET requests (e.g., fetching sources, alerts).
    *   `useMutation` hooks are used for POST, PUT, DELETE requests (e.g., creating/updating/deleting sources, acknowledging alerts), handling loading states, and cache invalidation.
*   **React Hook Form & Zod:**
    *   `react-hook-form` manages form state (inputs, validation, submission).
    *   `zod` defines validation schemas used by `react-hook-form`.
*   **React Context / `useState` / `useReducer`:**
    *   Used for local UI state (e.g., modal visibility, toggles, non-server related state).
*   **`react-hot-toast`:**
    *   Provides user feedback for API call success/failure and other important events.

### 2.5. Pages & Features

*   **Profile Page (`src/app/profile/page.tsx`):
    *   Displays user information from Supabase Auth.
    *   Includes a logout mechanism.

*   **Source Discovery Page (`src/app/discover/page.tsx`):
    *   **UI:** A form with a textarea for users to input a `raw_query`.
    *   **Logic:**
        *   On submit, calls `POST /api/v1/discover-sources/` (via the Axios instance and a `useMutation` hook).
        *   Displays the returned `monitorable_urls` (e.g., as a list).
        *   Allows users to select a URL and navigate to the "Create Monitored Source" page (`/sources/new`) with the URL pre-filled.

*   **Monitored Sources Pages (`src/app/sources/`):
    *   **List View (`/sources/page.tsx`):
        *   Displays a list/table of `MonitoredSourceInDB` items for the logged-in user.
        *   Fetches data using `GET /api/v1/monitored-sources/` (via Axios and `useQuery`).
        *   Includes options to Edit (navigate to edit page) and Delete (using `useMutation`).
    *   **Create Form (`/sources/new/page.tsx`):
        *   A form (using `react-hook-form` and `zod`) for `url` and `check_interval_seconds`.
        *   URL can be pre-filled from the discovery page.
        *   Submits data using `POST /api/v1/monitored-sources/` (via Axios and `useMutation`).
    *   **Edit Form (`/sources/[id]/edit/page.tsx` or `/sources/[id]/page.tsx` depending on routing strategy for edit):
        *   Fetches existing `MonitoredSource` data (via `useQuery`).
        *   Form (using `react-hook-form` and `zod`) to update `url`, `check_interval_seconds`, and `status`.
        *   Submits updates using `PUT /api/v1/monitored-sources/{source_id}` (via Axios and `useMutation`).

*   **Change Alerts Pages (`src/app/alerts/`):
    *   **List View (`/alerts/page.tsx`):
        *   Displays a list/table of `ChangeAlertSchema` records.
        *   Fetches data using `GET /api/v1/alerts/` (via Axios and `useQuery`), with support for filtering (e.g., by `is_acknowledged`).
        *   Displays key alert info (source, summary, timestamp).
        *   Option to navigate to alert detail or acknowledge directly.
    *   **Detail View (`/alerts/[id]/page.tsx`):
        *   Fetches and displays comprehensive details of a selected `ChangeAlertSchema` (via `useQuery`).
        *   Includes fields like `summary`, `details`, `screenshot_url`.
    *   **Acknowledge Functionality:**
        *   Buttons on list/detail views to mark an alert as acknowledged.
        *   Calls `POST /api/v1/alerts/{alert_id}/acknowledge` (via Axios and `useMutation`).
        *   UI updates optimistically or re-fetches/invalidates queries.

### 2.6. Reusable Components (`src/components/`)
*   General UI elements (buttons, inputs, modals, cards, layout components like `Navigation`).
*   Specific feature components (e.g., `UserProfile`, `RawQueryInputForm`, `MonitoredSourceCard`, `AlertListItem`).
*   Provider components (e.g., `QueryProvider.tsx` wrapping `QueryClientProvider`).

## 3. Architecture Diagram (Textual Representation)

```
+-----------------------+      +-----------------------------------+      +---------------------+ 
| User (Browser)        |<---->| Next.js Application (App Router)  |<---->| Supabase (Auth)     |
+-----------------------+      |  - Pages (SSR/CSR)                |      +---------------------+ 
                               |  - Components (React)             |
                               |  - Middleware (Auth Protection)   |
                               +-----------------------------------+
                                     |          ^         |
                                     |          | (State) |
                               (API Calls)      |         |
                                     |          |         V
                                     V          |   +-------------------------+
                           +--------------------+   | Browser Local Storage   |
                           | Axios Instance     |   | (Session, etc.)         |
                           | (src/lib/axiosInstance.ts) |   +-------------------------+
                           | - JWT Interceptor  |         
                           +--------------------+
                                     |
                                     V
                           +-------------------------+
                           | TanStack Query          |
                           | (Server State: Caching, | 
                           |  Fetching, Mutations)   |
                           +-------------------------+
                                     |
                                     V
+------------------------------------------------------------------------------------+
|                                 Backend API (FastAPI)                              |
| (e.g., POST /discover-sources/, GET /monitored-sources/, GET /alerts/, etc.)       |
+------------------------------------------------------------------------------------+

Key Interactions:
- User interacts with React Components within Next.js Pages.
- Next.js Middleware intercepts requests to protected pages, checks Supabase for auth status.
- Components trigger data fetching/mutations via TanStack Query hooks (`useQuery`, `useMutation`).
- TanStack Query hooks use functions that internally call the `axiosInstance`.
- `axiosInstance` adds Supabase JWT to requests and communicates with the Backend API.
- Supabase client libraries (`@supabase/ssr`) are used directly for auth actions (login, logout, session management).
- `react-hook-form` manages form state locally within components.
- `react-hot-toast` displays notifications based on API responses or other events.
```

## 4. Key Libraries & Their Roles

*   **Next.js:** Core framework, routing, rendering.
*   **React:** UI library for building components.
*   **TypeScript:** Type safety.
*   **Tailwind CSS:** Styling.
*   **`@supabase/ssr`:** Supabase authentication helpers for Next.js App Router (client & server).
*   **Axios (`src/lib/axiosInstance.ts`):** HTTP client for backend API communication, with JWT interceptor.
*   **TanStack Query (`react-query`):** Server state management (fetching, caching, mutations, optimistic updates).
*   **React Hook Form:** Form state management.
*   **Zod:** Schema validation for forms.
*   **`react-hot-toast`:** User notifications.
*   **Headless UI / Radix UI (or similar - if used):** For accessible unstyled UI primitives.
*   **Lucide Icons / Heroicons (if used):** SVG icons. 