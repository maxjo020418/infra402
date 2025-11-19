# GEMINI.md

## Project Overview

This project is a monorepo containing a Python-based backend and an empty frontend. The backend is a FastAPI server that demonstrates how to use the `x402` library to implement a paywall for API endpoints.

The `x402` library is a client for a remote facilitator service that handles payment verification and settlement. It supports per-request payments on EVM-compatible blockchains. The library is designed to be integrated into web frameworks like FastAPI and Flask.

The project is structured as follows:

-   `backend/`: The FastAPI server.
    -   `main.py`: The main entry point of the server.
    -   `x402/`: The source code for the `x402` library.
        -   `src/x402/`: The source code for the `x402` library.
            -   `facilitator.py`: The client for the x402 facilitator service.
            -   `paywall.py`: The logic for generating the HTML paywall.
            -   `fastapi/`: The FastAPI integration.
            -   `flask/`: The Flask integration.
-   `frontend/`: An empty directory.

## Building and Running

### Backend

To run the backend server, follow these steps:

1.  Navigate to the `backend/` directory:

    ```bash
    cd backend
    ```

2.  Create a `.env` file and add your Ethereum address:

    ```bash
    cp .env-local .env
    ```

3.  Install the dependencies:

    ```bash
    uv sync
    ```

4.  Run the server:

    ```bash
    uv run python main.py
    ```

The server will be available at `http://localhost:4021`.

## Development Conventions

The project uses `uv` for dependency management. The `x402` library is being developed locally as an editable install. The code is written in Python and uses type hints. Tests are located in the `backend/x402/tests/` directory and can be run with `pytest`.
