# Next-Gen Frontend Plan (Iteration 1 Refocused - API Aligned)

## Overview

This plan details the immediate frontend development required to align with the backend's Iteration 1 services, as defined by the provided OpenAPI schema. The focus is on adapting existing UI/logic or building new components to interact with the backend APIs for source discovery, monitored source management, and viewing change alerts.

## Core Iteration 1 Frontend Tasks (Adaptation & New Development)

### 1. Adapt/Update User Authentication & Profile Context
*   **Goal:** Ensure existing authentication flows correctly secure new routes and new API interactions.
*   **Tasks:**
    *   Utilize **Next.js Middleware** (e.g., `middleware.ts` at the root or in `src/`) in conjunction with `@supabase/auth-helpers-nextjs` to protect the new UI routes: `/discover`, `/sources`, and `/alerts`.
    *   Configure a dedicated **Axios instance** for API calls. Implement an **Axios request interceptor** to automatically fetch the active user session/JWT from the Supabase client (`@supabase/supabase-js`) and add it as an `Authorization` header (e.g., `Bearer <token>`) to all outgoing requests to your backend.
    *   Ensure the existing profile page (or create one at `/profile`) displays user information from Supabase Auth and provides a logout mechanism using Supabase client functions.

### 2. Implement Source Discovery UI & Logic
*   **Goal:** Provide UI for users to utilize the backend's `SourceDiscoveryService`.
*   **Backend API Endpoint:** `POST /api/v1/discover-sources/`
    *   **Request Body Schema:** `RawQueryInput` (containing `raw_query: string`)
    *   **Response Body Schema:** `MonitoredURLOutput` (containing `monitorable_urls: array[uri-string]`)
*   **Tasks:**
    *   Create a new page/route (e.g., `/discover`) for source discovery.
    *   Develop a form with a text input field (e.g., `<textarea>`) for users to submit the `raw_query` and a submit button.
    *   Implement API calls to the `POST /api/v1/discover-sources/` endpoint using the configured **Axios instance**.
    *   Display the `monitorable_urls` list returned by the backend (e.g., as a list of selectable items, potentially with checkboxes or "Add" buttons).
    *   Develop a mechanism for users to select one or more URLs from the suggestions to initiate the creation of `MonitoredSource`(s) (linking to Task 3.2), pre-populating the `url` field in the creation form.

### 3. Refactor/Build Monitored Source Management UI & Logic
*   **Goal:** Adapt existing dashboard components or build new ones for full CRUD operations on `MonitoredSource` entries, replacing any previous alert setup UI.
*   **Backend API Endpoints & Schemas:**
    *   `POST /api/v1/monitored-sources/`
        *   **Request Body Schema:** `MonitoredSourceCreate` (`url: uri-string`, `check_interval_seconds?: integer`)
        *   **Response Body Schema:** `MonitoredSourceInDB`
    *   `GET /api/v1/monitored-sources/`
        *   **Query Parameters:** `skip?: integer`, `limit?: integer`
        *   **Response Body Schema:** `array[MonitoredSourceInDB]`
    *   `GET /api/v1/monitored-sources/{source_id}`
        *   **Path Parameter:** `source_id: integer`
        *   **Response Body Schema:** `MonitoredSourceInDB`
    *   `PUT /api/v1/monitored-sources/{source_id}`
        *   **Path Parameter:** `source_id: integer`
        *   **Request Body Schema:** `MonitoredSourceUpdate` (`url?: uri-string`, `check_interval_seconds?: integer`, `status?: string`)
        *   **Response Body Schema:** `MonitoredSourceInDB`
    *   `DELETE /api/v1/monitored-sources/{source_id}`
        *   **Path Parameter:** `source_id: integer`
        *   **Response:** `204 No Content`
*   **Tasks:**
    *   **List View (e.g., `/sources` page):**
        *   Develop/adapt UI (e.g., a table or card layout) to display `MonitoredSourceInDB` items for the logged-in user.
        *   Fetch data using `GET /api/v1/monitored-sources/` via the **Axios instance**. Manage this server state (caching, refetching, etc.) using **TanStack Query (React Query)** by wrapping the Axios call in a `useQuery` hook.
        *   Include options for each item to "Edit" and "Delete".
        *   Display key information such as URL, check interval, and status.
    *   **Create Form (e.g., modal dialog or dedicated `/sources/new` page):**
        *   Develop/adapt UI with input fields for `url` (pre-fillable from Task 2.5) and `check_interval_seconds`, using `react-hook-form` for form state and `zod` for validation.
        *   Use `POST /api/v1/monitored-sources/` with a `MonitoredSourceCreate` payload, sent via the **Axios instance**. Manage this mutation using **TanStack Query's** `useMutation` hook for handling submission, loading states, and cache invalidation.
        *   Provide clear user feedback on success or failure (e.g., using `react-hot-toast`).
    *   **Edit Form (e.g., modal dialog or dedicated `/sources/[id]/edit` page):**
        *   Develop/adapt UI pre-filled with existing `MonitoredSource` data (fetched via **TanStack Query**).
        *   Allow modification of `url`, `check_interval_seconds`, and `status`, using `react-hook-form` and `zod`.
        *   Use `PUT /api/v1/monitored-sources/{source_id}` with a `MonitoredSourceUpdate` payload, sent via the **Axios instance**. Manage this mutation with **TanStack Query's** `useMutation`.
    *   **Delete Functionality:**
        *   Implement UI controls (e.g., a "Delete" button with a confirmation dialog) to delete `MonitoredSource` entries.
        *   Use `DELETE /api/v1/monitored-sources/{source_id}` via the **Axios instance**, managed by a **TanStack Query** `useMutation` hook.

### 4. Refactor/Build Change Alert Display UI & Logic
*   **Goal:** Adapt existing dashboard components or build new ones to display `ChangeAlert` records from the new backend system.
*   **Backend API Endpoints & Schemas:**
    *   `GET /api/v1/alerts/`
        *   **Query Parameters:** `skip?: integer`, `limit?: integer`, `monitored_source_id?: integer`, `is_acknowledged?: boolean`
        *   **Response Body Schema:** `array[ChangeAlertSchema]`
    *   `GET /api/v1/alerts/{alert_id}`
        *   **Path Parameter:** `alert_id: integer`
        *   **Response Body Schema:** `ChangeAlertSchema`
    *   `POST /api/v1/alerts/{alert_id}/acknowledge`
        *   **Path Parameter:** `alert_id: integer`
        *   **Response Body Schema:** `ChangeAlertSchema` (updated)
*   **Tasks:**
    *   **List View (e.g., `/alerts` page or a section on the main dashboard):**
        *   Develop/adapt UI (e.g., a table or list) to display `ChangeAlertSchema` records.
        *   Fetch data using `GET /api/v1/alerts/` via the **Axios instance**, managed by a **TanStack Query** `useQuery` hook, including support for query parameters for filtering.
        *   Implement client-side or server-side filtering options (e.g., dropdowns or input fields) for `monitored_source_id` and `is_acknowledged`.
        *   Implement sorting options (e.g., by date, source).
        *   Display key alert information: source URL (or name), detected change summary, timestamp, acknowledged status.
    *   **Detail View (e.g., modal dialog or dedicated `/alerts/[id]` page):**
        *   Develop/adapt UI to show comprehensive details of a selected `ChangeAlertSchema` (fetched via `GET /api/v1/alerts/{alert_id}` using the **Axios instance** and **TanStack Query's** `useQuery` if not all data is present in the list view).
        *   Display fields like `summary`, `details`, `screenshot_url` (if available, render the image), `old_value`, `new_value`.
    *   **Acknowledge Functionality:**
        *   Implement UI controls (e.g., an "Acknowledge" button) on list items or in the detail view.
        *   Call `POST /api/v1/alerts/{alert_id}/acknowledge` via the **Axios instance**, managed by a **TanStack Query** `useMutation` hook.
        *   Update the UI optimistically or re-fetch/invalidate queries using TanStack Query to reflect the change in `is_acknowledged` status.

### 5. Update API Client & State Management for New Endpoints/Entities
*   **Goal:** Ensure the frontend API client and state management can handle the new backend services and data structures as defined in the OpenAPI schema.
*   **Tasks:**
    *   Create and configure a dedicated **Axios instance** (e.g., in `src/lib/axiosInstance.ts`) with the backend base URL and the request interceptor for Supabase JWT authentication. Add type-safe functions in this or a related API service module for all specified backend endpoints. These functions will encapsulate Axios calls and be used by TanStack Query hooks.
    *   Integrate **TanStack Query (React Query)** for managing server state. This involves setting up a `QueryClientProvider` in your `_app.tsx`. Use `useQuery` for data fetching (GET requests) and `useMutation` for data modifications (POST, PUT, DELETE requests) for `MonitoredSourceInDB` and `ChangeAlertSchema` entities. This will handle caching, background updates, stale-while-revalidate, and optimistic updates.
    *   For client-side UI state (e.g., modal visibility, local component state), continue to use React's built-in `useState`, `useReducer`, and Context API as appropriate. `react-hook-form` will continue to manage form-specific state.
    *   Implement robust error handling within TanStack Query's `onError` callbacks and Axios interceptors (for global error handling like 401s). Provide user feedback using `react-hot-toast` for errors and success messages. Ensure TypeScript types from your OpenAPI schema are used for request/response payloads with Axios and TanStack Query.

### Recommended Implementation Order

To ensure a smooth development process, the following implementation order is recommended:

1.  **Foundational Setup (Prerequisites):**
    *   Complete **Task 1 (User Authentication & Profile Context)**: Solidify authentication, route protection using Next.js Middleware with Supabase, and profile basics.
    *   Perform initial setup from **Task 5 (API Client & State Management)**: 
        *   Create and configure the dedicated Axios instance (`src/lib/axiosInstance.ts`) with the Supabase JWT interceptor.
        *   Integrate TanStack Query by setting up its `QueryClientProvider` in `_app.tsx`.

2.  **Feature Development (Sequential):**
    *   **Task 2 (Source Discovery UI & Logic):** Implement the source discovery page and API interaction.
    *   **Task 3 (Monitored Source Management UI & Logic):** Develop CRUD operations for monitored sources. The "Create" functionality will directly use outputs from Task 2.
    *   **Task 4 (Change Alert Display UI & Logic):** Implement the UI for viewing and acknowledging alerts.

3.  **Ongoing Task During Feature Development:**
    *   **Task 5 (API Client & State Management - Detailed Implementation):** As each feature (Tasks 2, 3, 4) is developed, implement the specific API client functions (using the Axios instance) and the corresponding TanStack Query hooks (`useQuery`, `useMutation`) for data fetching, caching, and mutations. Continuously implement error handling and user feedback mechanisms.

## Iteration 1: Key Deliverables
*   A user can navigate to a `/discover` page, submit a query via a form using the `RawQueryInput` schema to `POST /api/v1/discover-sources/` (via the **Axios instance**), and see the returned `monitorable_urls` displayed as a selectable list.
*   From the discovery results, a user can select a URL to initiate the creation of a `MonitoredSource`, which pre-populates a `react-hook-form`. The user can complete and submit this form (using `MonitoredSourceCreate` payload) via `POST /api/v1/monitored-sources/` (using **Axios** and **TanStack Query's** `useMutation`).
*   A user can navigate to a `/sources` page to view their `MonitoredSourceInDB` items, fetched and managed by **TanStack Query**. From this view, they can initiate actions to update (via a `react-hook-form`, **Axios**, and `useMutation`) and delete (via **Axios** and `useMutation`) their monitored sources.
*   A user can navigate to an `/alerts` page to view a list of their `ChangeAlertSchema` items, fetched and managed by **TanStack Query**, with options to filter.
*   A user can view details of a specific `ChangeAlertSchema` and acknowledge it using a button that triggers an API call via **Axios** and **TanStack Query's** `useMutation`.
*   All interactions are secured by **Next.js Middleware** using **Supabase Auth**. All API calls utilize the new backend Iteration 1 APIs via the configured **Axios instance**, with **TanStack Query** managing server state and mutations.
*   The **Axios instance** is set up with interceptors for auth. **TanStack Query** is configured. TypeScript types are used throughout the API and state management layers.

*(Superseded sections on general setup, component libraries, or future iterations have been removed to keep this focused on immediate, necessary changes for backend compatibility.)*
