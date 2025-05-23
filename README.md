# Personal Context Server

![context-server](https://github.com/Maclean-D/context-server/raw/main/context-server.png)

Server converting Limitless AI lifelogs into indexed markdown, searchable via REST API and web UI

## Features

- Fetches Lifelog entries
- Persistent vector database using FAISS
- Multiple retrieval modes:
  - Day: Search across entire days
  - Memory: Search within specific memories
  - Section: Search within sections of memories
  - Line: Search individual lines/quotes
- Recency-weighted search results
- Web UI for settings and queries
- REST API for integration

## First Time Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Maclean-D/context-server.git
   cd context-server
   ```

2. Get a [Limitless API key](https://app.limitless.ai) (Account > Developers)

3. Enter it in `config.json`

3. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Start the server:
   ```bash
   python main.py
   ```

6. Continute to `Starting The Server`

## Starting The Server

1. Activate a virtual environment:
   ```bash
   # Windows
   .\venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

2. Start the server:
   ```bash
   python main.py
   ```

3. 6. View server status and change settings at http://localhost:5712

## Running with Docker

This section provides instructions for running the application using Docker. This is generally recommended as it handles dependencies and environment setup consistently.

Prerequisites:
*   Install Docker: Follow the official instructions for your operating system.
    *   [Install Docker Engine](https://docs.docker.com/engine/install/)
    *   If you plan to use `docker-compose`, also [Install Docker Compose](https://docs.docker.com/compose/install/) (Docker Desktop for Windows/Mac usually includes it).

Clone the repository (if you haven't already):
```bash
git clone https://github.com/Maclean-D/context-server.git
cd context-server
```

### Option 1: Using Docker Compose (Recommended)

Docker Compose simplifies the management of multi-container applications and is convenient for development and deployment.

1.  Configure API Key:
    Create a file named `.env` in the root of the project directory (alongside `docker-compose.yml`) with the following content:
    ```env
    LIMITLESS_API_KEY=your_actual_api_key_here
    ```
    Replace `your_actual_api_key_here` with your actual Limitless API key. If this variable is not set or is empty, the application will attempt to use the API key specified in `config.json`.

2.  Build and run the application:
    To start the services:
    ```bash
    docker-compose up
    ```
    If you have made changes to the application code or the `Dockerfile` and want to ensure the docker image is rebuilt, use:
    ```bash
    docker-compose up --build
    ```
    To run in detached mode (in the background), add the `-d` flag:
    ```bash
    docker-compose up -d 
    # or with an explicit rebuild
    docker-compose up --build -d
    ```

3.  Access the application:
    Open your browser and go to `http://localhost:5712`.

4.  Stopping the application:
    If running in the foreground, press `Ctrl+C`.
    If running in detached mode:
    ```bash
    docker-compose down
    ```

### Option 2: Using Docker CLI (`docker run`)

If you prefer not to use Docker Compose, you can build and run the container using Docker CLI commands directly.

1.  Prepare Configuration and Directories:
    *   Ensure you have a `config.json` file in the project root. You can copy the provided `config.json` example or create your own.
    *   Create the `./notes` and `./faiss_index` directories in your project root if they don't exist:
        ```bash
        mkdir -p notes faiss_index
        ```
        If `config.json` does not exist in your project root when you run the container with a volume mount, Docker might create an empty directory instead of a file. It's best to have `config.json` present.

2.  Build the Docker image:
    Navigate to the project's root directory (where the `Dockerfile` is located) and run:
    ```bash
    docker build -t context-server-image .
    ```
    (You can choose any name for `context-server-image`).

3.  Run the Docker container:
    ```bash
    docker run -d \
      --name context-server-app \
      -p 5712:5712 \
      -v "./data/notes":/app/notes \
      -v "./data/faiss_index":/app/faiss_index \
      -v "./data/config.json":/app/config.json \
      -e LIMITLESS_API_KEY="your_actual_api_key_here" \
      -e UVICORN_RELOAD="false" \
      --restart unless-stopped \
      context-server-image
    ```
    Explanation of flags:
    *   `-d`: Run in detached mode (background).
    *   `--name context-server-app`: Assign a name to the container.
    *   `-p 5712:5712`: Map port 5712 on the host to port 5712 in the container.
    *   `-v "$./data/notes":/app/notes`: Mount the local `notes` directory to `/app/notes` in the container.
    *   `-v "$./data/faiss_index":/app/faiss_index`: Mount the local `faiss_index` directory to `/app/faiss_index` in the container.
    *   `-v "$./data/config.json":/app/config.json`: Mount the local `config.json` file to `/app/config.json` in the container.
    *   `-e LIMITLESS_API_KEY="your_actual_api_key_here"`: Set the Limitless API key. Replace with your actual key or omit if you want to rely solely on `config.json` (though setting it here is recommended for `docker run`).
    *   `-e UVICORN_RELOAD="false"`: Ensure Uvicorn's auto-reload is disabled.
    *   `--restart unless-stopped`: Configure the container to restart automatically unless manually stopped.
    *   `context-server-image`: The name of the image you built.

    Replace `"your_actual_api_key_here"` with your actual Limitless API key.

4.  Access the application:
    Open your browser and go to `http://localhost:5712`.

5.  Viewing logs:
    ```bash
    docker logs context-server-app
    ```

6.  Stopping the container:
    ```bash
    docker stop context-server-app
    ```

7.  Removing the container:
    ```bash
    docker rm context-server-app
    ```

Data Persistence (for both options):
The setup ensures that your data is persisted on your host machine in the following locations within your project directory:
*   `./notes`: Stores the downloaded markdown lifelogs.
*   `./faiss_index`: Stores the FAISS vector index.
*   `./config.json`: Stores your application configuration (when mounted).

These folders will be created in your project directory on your host machine if they don't already exist (though for `config.json` with `docker run`, it's best if it exists beforehand).

## Using the API

Once your server is started visit http://localhost:5712/docs#/ to view documentation.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Maclean-D/context-server&type=Date)](https://star-history.com/#Maclean-D/context-server&Date)

## Contributors

<a href="https://github.com/Maclean-D/context-server/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Maclean-D/context-server" />
</a>
