# Next-Gen Frontend Plan (Iteration 1 Refocused)

## Overview

This plan details the immediate frontend development required to align with the backend's Iteration 1 services. The focus is on adapting existing UI/logic or building new components to interact with the refactored backend APIs for source discovery, monitored source management, and viewing new change alerts.

## Core Iteration 1 Frontend Tasks (Adaptation & New Development)

### 1. Adapt/Update User Authentication & Profile Context
*   **Goal:** Ensure existing authentication flows correctly secure new routes and new API interactions.
*   **Tasks:**
    *   Review and update route protection to cover new UIs for source discovery, monitored source management, and change alert views.
    *   Ensure API client correctly handles auth tokens for all new backend endpoints.
    *   If not already present, create a minimal profile page to display user context (e.g., email) and a logout mechanism relevant to the new flows.

### 2. Implement Source Discovery UI & Logic
*   **Goal:** Provide UI for users to utilize the backend's `SourceDiscoveryService`.
*   **Backend API:** `/api/v1/source-discovery/`
*   **Tasks:**
    *   Create a new UI section/page for source discovery.
    *   Develop input fields for users to submit raw queries.
    *   Implement API calls to the backend's source discovery endpoint.
    *   Display the list of suggested URLs returned by the backend.
    *   Develop a mechanism for users to select URLs from suggestions to initiate the creation of a `MonitoredSource` (linking to Task 3).

### 3. Refactor/Build Monitored Source Management UI & Logic
*   **Goal:** Adapt existing dashboard components or build new ones for full CRUD operations on `MonitoredSource` entries, replacing any previous alert setup UI.
*   **Backend API:** `/api/v1/monitored-sources/`
*   **Tasks:**
    *   **List View:** Develop/adapt UI to display all active `MonitoredSource` items for the logged-in user (e.g., URL, status, check interval). Fetch data from the new endpoint.
    *   **Create Form:** Develop/adapt UI to allow manual creation of `MonitoredSource` entries (input URL, check interval). This form should be callable from the Source Discovery flow (Task 2).
    *   **Edit Form:** Develop/adapt UI to allow modification of `MonitoredSource` settings.
    *   **Delete Functionality:** Implement UI controls to delete `MonitoredSource` entries.
    *   Ensure all interactions use the new `/api/v1/monitored-sources/` endpoints.

### 4. Refactor/Build Change Alert Display UI & Logic
*   **Goal:** Adapt existing dashboard components or build new ones to display `ChangeAlert` records from the new backend system, replacing any previous alert display.
*   **Backend API:** `/api/v1/alerts/` (for the new `ChangeAlert` model)
*   **Tasks:**
    *   **List View:** Develop/adapt UI to display `ChangeAlert` records. Fetch data from the new endpoint. Implement filtering/sorting as necessary for MVP (e.g., by source, by date).
    *   **Detail View:** Develop/adapt UI to show details of a selected `ChangeAlert`.
    *   **Acknowledge Functionality:** Implement UI and API call to mark `ChangeAlert`s as acknowledged.
    *   Ensure all interactions use the new `/api/v1/alerts/` endpoint.

### 5. Update API Client & State Management for New Endpoints/Entities
*   **Goal:** Ensure the frontend API client and state management can handle the new backend services and data structures.
*   **Tasks:**
    *   Add/update type-safe functions in the API client for:
        *   Source discovery.
        *   `MonitoredSource` CRUD.
        *   `ChangeAlert` retrieval and acknowledgement.
    *   Update or implement state management (e.g., React Query, Zustand, Context) to handle caching, updates, and optimistic updates for `MonitoredSource` and `ChangeAlert` data.
    *   Implement robust error handling and user feedback (loading states, error messages) for all new API interactions.

## Iteration 1: Key Deliverables
*   A user can submit a query and see suggested URLs.
*   A user can select a suggested URL or manually input a URL to create a `MonitoredSource`.
*   A user can view, update, and delete their `MonitoredSource`s.
*   A user can view a list of `ChangeAlert`s generated for their monitored sources.
*   A user can view details of a `ChangeAlert` and acknowledge it.
*   All interactions are secured by authentication and use the new backend Iteration 1 APIs.

*(Superseded sections on general setup, component libraries, or future iterations have been removed to keep this focused on immediate, necessary changes for backend compatibility.)*
