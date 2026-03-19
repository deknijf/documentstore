# Docstore Android Mobile App (MVP)

This is a first native Android implementation for Docstore, designed specifically for the mobile pain points that the web app cannot solve well:

- reliable document capture on phone
- local caching when the backend is temporarily unavailable
- automatic background upload retries
- a tighter scan-to-upload flow inspired by apps such as FairScan, Paperless Mobile and Immich

## Why native

A native Android app adds concrete reliability and UX benefits over the current mobile web UI:

- native document scanner (Google ML Kit document scanner)
- local queue for scans and uploads
- background retry with WorkManager when the server is reachable again
- no dependency on fragile browser camera behavior
- direct authenticated connection to `https://docstore.deknijf.eu`

## First version scope

This MVP includes:

- login against `POST /api/auth/login`
- persisted session token and user info via DataStore
- document list via `GET /api/documents`
- document detail via `GET /api/documents/{id}`
- native scan flow using Google ML Kit Document Scanner
- offline-first upload queue in Room
- automatic background upload retry using WorkManager
- queue overview for pending/failed/completed uploads
- document/open-original actions through authenticated backend URLs

## Architecture

- **UI**: Jetpack Compose
- **Networking**: Retrofit + OkHttp
- **Local state**: DataStore (session), Room (pending uploads)
- **Background jobs**: WorkManager
- **Scanner**: Google ML Kit Document Scanner

## Backend target

The app is configured to use:

- `https://docstore.deknijf.eu/`

This is injected via `BuildConfig.DOCSTORE_BASE_URL`.

## Important behavior

### Scan caching

Every scan is first copied to app-local storage under:

- `files/pending_uploads/`

Then it is inserted into the local Room queue.

Only after that does the app try to upload it.

This means:

- if the backend is down
- if the network is flaky
- if the app goes to the background

…the scan is still safely retained and retried later.

### Upload strategy

WorkManager handles uploads only when a network connection is available.

States:

- `PENDING`
- `UPLOADING`
- `FAILED`
- `COMPLETE`

## Build prerequisites

This repository does **not** contain a Gradle wrapper yet. To build the app, use Android Studio or generate a wrapper locally.

Required:

- Android Studio Hedgehog or newer
- JDK 17
- Android SDK 35
- Google Play Services available on the test device for ML Kit scanner

## Open in Android Studio

Open:

- `mobile/android`

Then let Android Studio sync the Gradle project.

## What still needs follow-up

This is a first working foundation, not full feature parity with the web app yet.

Recommended next steps:

1. native PDF/image preview inside the app instead of opening the browser for the document file
2. profile screen and logout flow
3. direct upload progress UI per queued item
4. tenant switch for superadmin users
5. document detail editing and OCR/AI reprocess actions
6. budget read-only screens and later category editing
7. push or local notifications for completed OCR jobs and failed uploads
