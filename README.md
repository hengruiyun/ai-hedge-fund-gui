# AI Hedge Fund Analysis Software - GUI Extension  [中文](https://github.com/hengruiyun/ai-hedge-fund-gui/blob/main/README_cn.md)

This project provides a Graphical User Interface (GUI) for the AI hedge fund analysis software originally developed by virattt. It aims to simplify interaction with the powerful underlying AI-driven financial analysis tools.

OSM: Fully Developed by AI
AI-driven software development represents a significant milestone in technological innovation. Through the complete development of practical tools like OSM using AI, we demonstrate artificial intelligence's exceptional capabilities in code generation, system design, and problem-solving. This development approach not only improves efficiency, reduces human resource costs and time investment in traditional development, but also ensures consistency in code quality. AI can quickly absorb best practices, avoid common errors, and provide innovative solutions. It serves as powerful evidence of the integration between artificial intelligence and software engineering, revealing the direction of paradigm shifts in future development.

![gui](https://github.com/user-attachments/assets/1790abff-ab95-4822-89d8-127cfabec6ca)

## Features

*   **Graphical User Interface**: An intuitive interface for managing and running financial analyses.
*   **Simplified Workflow**: Easily configure stock tickers, date ranges, API keys, and AI models.
*   **Multi-AI Provider Support**: Compatible with various AI model service providers.
*   **Configuration Management**: Save and load your analysis settings.

## Installation and Usage

To use this GUI extension, follow these steps:

1.  **Clone the Original Repository**:
    First, you need to clone the base ai-hedge-fund project from virattt's repository.
    ```bash
    git clone https://github.com/virattt/ai-hedge-fund.git
    ```

2.  **Add GUI Files**:
    Download the latest version of the GUI extension. Place the downloaded files into the `ai-hedge-fund` directory you cloned in the previous step.
    ```bash
    git clone https://github.com/hengruiyun/ai-hedge-fund-gui.git
    copy /y ai-hedge-fund-gui\*.*  ai-hedge-fund
    copy /y ai-hedge-fund-gui\src\*.*  ai-hedge-fund\src
    cd ai-hedge-fund
    ```

3.  **Set Up Environment and Dependencies**:
    It is highly recommended to use a virtual environment.
    ```bash
    uv venv --python=3.10
    .venv\Scripts\activate
    uv pip install -r requirements.txt
    ```

4.  **Configure API Keys**:
    The software requires API keys from AI model providers (e.g., OpenAI, Groq) and potentially API keys for financial data sources.
    *   Copy the `.env.example` file to `.env`:
        ```bash
        copy /y  .env.example .env
        ```
    *   Edit the `.env` file and add your API keys.
    *   Alternatively, you can configure API keys directly in the GUI after launching it. The GUI will help create or update the `.env` file.

5.  **Run the GUI**:
    ```bash
    gui
    ```
    or
    ```bash
    uv run gui_launcher.py
    ```
![a1](https://github.com/user-attachments/assets/14183595-f470-41dc-b5c2-1f902f5cb128)

## Configuration Notes

API keys and other settings are managed via the `.env` file in the root of the `ai-hedge-fund` directory and through the GUI itself.

*   **Analyst Selection**: Choose the AI analysts to participate in the analysis in the "Analysts" tab.
*   **API Keys**: Enter your API keys in the "API Keys" tab of the GUI or by editing the `.env` file. At least one AI provider key is usually required.
*   **Model Selection**: Select your preferred AI model provider and model name in the "Model Configuration" tab.
*   **Analysis Parameters**: Set stock tickers, date ranges, initial cash, etc., in the "Parameters" tab.

Settings configured in the GUI (including API keys) will be saved to the `hedge_fund_config.json` file, and relevant API keys will also be written to the `.env` file.

## Troubleshooting

*   **Missing Dependencies**: Ensure all dependencies in `requirements.txt` are correctly installed in your activated Python environment. Run `python dependency_checker.py` for a quick check.
*   **API Key Errors**: Double-check that your API keys are entered correctly, are valid, and have sufficient quota.
*   **GUI Launch Failure**:
    *   Confirm Python is installed and accessible (Python 3.10+ recommended).
    *   Ensure `tkinter` (usually part of standard Python installations) is available.
    *   Try reinstalling dependencies: `pip install -r requirements.txt --force-reinstall`.

## License

This GUI extension is licensed under the Apache License 2.0. See the `LICENSE` file for more details.

## Acknowledgements

*   This project is an extension of virattt's `ai-hedge-fund` project. We thank them for their original work and for open-sourcing it. You can find the original project at: [https://github.com/virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund).
*   We use `uv`, an extremely fast Python package installer and resolver, written in Rust, developed by Astral. More information at: [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).


## Contact

Gmail: hengruiyun


## Disclaimer

This software is intended for educational and research purposes only and does not constitute real trading or investment advice. The creators and contributors of this software are not responsible for any financial losses incurred from its use. Always consult a qualified financial advisor before making investment decisions. 
