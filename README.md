# UI String Translator & GitHub Integrator

A Streamlit application for creating localization files with context-aware translations powered by Google's Gemini API. This tool allows you to upload JSON or XML files, or connect to GitHub to automatically scan repositories for translatable strings.

## Features

- Upload JSON or XML files for translation
- GitHub repository integration to scan and translate strings.xml files
- Context-aware translations using Google's Gemini API
- Support for multiple languages
- Review and edit translations
- Export translations to various formats

## Docker Setup

### Prerequisites

- Docker and Docker Compose installed on your machine
- Google Gemini API key
- GitHub API token (for GitHub repository scanning)

### Configuration

1. Clone this repository:
   ```bash
   git clone <your-repository-url>
   cd <repository-directory>
   ```

2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and add your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   GITHUB_TOKEN=your_github_token_here
   ```

### Running with Docker Compose

Build and start the container:

```bash
docker-compose up -d
```

The Streamlit application will be available at http://localhost:8501

To stop the container:

```bash
docker-compose down
```

### Running with Docker Directly

Build the Docker image:

```bash
docker build -t ui-translator .
```

Run the container:

```bash
docker run -p 8501:8501 --env-file .env ui-translator
```

## Usage

1. Create a new project from the Dashboard tab
2. Upload files or connect to a GitHub repository
3. Select languages for translation
4. Review and edit translations
5. Export translations in your desired format

## Notes

- For large repositories, scanning might take some time
- The application uses batched API calls for large translation jobs to avoid API limits
- Make sure your API keys have the necessary permissions