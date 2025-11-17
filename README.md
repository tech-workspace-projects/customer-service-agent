E-commerce AI Agent POC (with Gemini)

This project is a runnable Proof of Concept for an AI Agent. It consists of a Flask web application that serves a chat interface and a `pytest` suite that runs validation test cases.

This version is enhanced with two features powered by the Gemini API:
1. Outfit Suggester: Suggests an outfit for in-stock products.
2. Email Drafter: Drafts a support email for delayed orders.

### How to Run the Application

1. Install uv using pip or brew:
```commandline
pip3 install uv
```
2. Sync uv packages for environment setup:
```commandline
uv sync
```
4. Run the Flask application:
```commandline
uv run app.py
```
The application will be running at `http://127.0.0.1:5001`. Open this URL in your browser to interact with the chatbot.

### How to Run the Test Suite

Make sure the application is not running. (The test suite will start its own instance).

From your terminal, in the project directory, run pytest:
```commandline
pytest
```


pytest will automatically discover the `test_app.py` file, execute all 34 test cases, and give you a detailed report of passes and failures. This report is the final "Validation Report" deliverable.