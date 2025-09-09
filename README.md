Binance Futures Trading Bot📝 

Project Description. 

This project is a trading bot designed to interact with the Binance Futures Testnet. It allows users to manage their testnet account and execute trades without risking real money. 
The application provides two interfaces:

1)A user-friendly web interface built with Streamlit.
2)A traditional Command-Line Interface (CLI) for terminal-based interaction.

This project was developed as a skills assignment for an internship application.

✨ Key FeaturesDual Interfaces: Choose between a graphical web UI or a fast command-line interface.

Account Management: View your testnet wallet balance, margin balance, and unrealized PnL.

Order Placement:Place Market orders (BUY/SELL).Place Limit orders (BUY/SELL).Order Management:View all open orders.Cancel specific open orders by their ID.

Real-time Data: Check the current market price for any trading symbol.Secure: Uses a .env file to securely manage your API credentials.

Logging: Logs all major actions and API responses to trading_bot.log for easy debugging.

🛠️ Tech Stack & RequirementsLanguage: Python 3.10+Key 

Libraries:

streamlit: For the web frontend.python-binance: The official Binance API wrapper.pandas: 
For data display in the web UI.
python-dotenv: For managing environment variables.

colorama & tabulate: For styling the CLI output.A complete list of dependencies is available in the requirements.txt file.

🚀 Setup and InstallationFollow these steps to get the bot running on your local machine.1. Clone the Repositorygit clone [https://github.com/Pooja0726/Binance-Bot]
cd [Binance-Bot]

2. Create and Activate a Virtual EnvironmentIt is highly recommended to use a virtual environment.
# Create the environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
3. Install DependenciesInstall all required packages using the requirements.txt file.pip install -r requirements.txt
4. Set Up API CredentialsThe bot requires API keys from the Binance Futures Testnet.

Generate Keys: Go to Binance Futures Testnet to register an account and generate an API Key and Secret Key. 
Ensure that Futures trading permissions are enabled for the key.


Create .env File: In the root of the project folder, create a new file named .env and add your keys to it like this:BINANCE_TESTNET_API_KEY="YOUR_TESTNET_API_KEY_HERE"
BINANCE_TESTNET_API_SECRET="YOUR_TESTNET_API_SECRET_HERE"

▶️ How to Run the BotYou can run either the Streamlit web app or the command-line version.Running the Streamlit Web App (Recommended)Execute the following command in your terminal:

streamlit run app.py

Your default web browser will open with the application's user interface.Running the Command-Line Interface (CLI)Execute the following command in your terminal:streamlit run app.py

The application will start, and you can interact with it directly in the terminal.
