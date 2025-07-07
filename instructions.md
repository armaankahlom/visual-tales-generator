# Project Setup and Execution Instructions

1. **API Keys Setup**
    - Enter your API key for Replicate.
    - Enter your API key for OpenAI.

2. **Input Data**
    - Place the input JSON received from GPT inside the file: `input_sentence.json`.

3. **Create Virtual Environment**
    - Create a new virtual environment by running:
      ```
      python -m venv venv
      ```
    - Activate the virtual environment:
      - On macOS/Linux:
        ```
        source venv/bin/activate
        ```
      - On Windows:
        ```
        .\venv\Scripts\activate
        ```

4. **Install Dependencies**
    - Install required packages by running:
      ```
      pip install -r requirements.txt
      ```

5. **Run the Application**
    - Execute the program using:
      ```
      python main.py
      ```
