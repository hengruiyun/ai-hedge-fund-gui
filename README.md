# AI Hedge Fund Analysis Software - GUI Extension  [中文](https://github.com/hengruiyun/ai-hedge-fund-gui/blob/main/README_cn.md)

This project provides a Graphical User Interface (GUI) for the AI hedge fund analysis software originally developed by virattt. It aims to simplify interaction with the powerful underlying AI-driven financial analysis tools.


## Features

*   **Graphical User Interface**: An intuitive interface for managing and running financial analyses.
*   **Simplified Workflow**: Easily configure stock tickers, date ranges, API keys, and AI models.
*   **Multi-AI Provider Support**: Compatible with various AI model service providers.


## Installation and Usage

To use this GUI extension, follow these steps:


  **Run the GUI**:
    ```bash
    gui
    ```



## Configuration Notes

API keys and other settings are managed via the `.env` file in the `ai-hedge-fund-gui` directory and through the GUI itself.

*   **Analyst Selection**: Choose the AI analysts to participate in the analysis in the "Analysts" tab.
*   **API Keys**: Enter your API keys in the "API Keys" tab of the GUI or by editing the `.env` file. At least one AI provider key is usually required.
*   **Model Selection**: Select your preferred AI model provider and model name in the "Model Configuration" tab.
*   **Analysis Parameters**: Set stock tickers, date ranges, initial cash, etc., in the "Parameters" tab.


## License

This GUI extension is licensed under the Apache License 2.0. See the `LICENSE` file for more details.

## Acknowledgements

*   This project is an extension of virattt's `ai-hedge-fund` project. We thank them for their original work and for open-sourcing it. You can find the original project at: [https://github.com/virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund).
*   We use `uv`, an extremely fast Python package installer and resolver, written in Rust, developed by Astral. More information at: [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv).


## Contact

Email: 267278466@qq.com


## Disclaimer

This software is intended for educational and research purposes only and does not constitute real trading or investment advice. The creators and contributors of this software are not responsible for any financial losses incurred from its use. Always consult a qualified financial advisor before making investment decisions. 
