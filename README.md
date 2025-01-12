# Basic Flask Application for 3rd Year Gymnasium Students as part of their Maturity Project [24-25]

## Author
Johan Jobin, Collège du Sud.

## Description
The current directory is a basic Flask application template connected to an SQLite database, serving as a starting point for 3rd-year students at Collège du Sud as part of their Maturity Project. With pedagogical objectives in mind, and to provide a fundamental grasp of web application architecture, the project intentionally omits any Object-Relational Mapping (ORM) or data validation modules.

## How to run the project
1. **Create a virtual environment**
   - Using the command line:

      ```bash
      python -m venv <VIRTUAL-ENVIRONMENT-NAME>
      ``` 
      
   - Using Visual Studio Code:
     - Type `Ctrl + Maj + P` and enter `Python: Create environment` into the search bar at the top of the window **This requires that the official [Python extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-python.python) is installed.**
     - Choose `venv` to create a `.venv` virtual environment in the current workspace.
     - Choose the version of the Python interpreter to use.


2. **Activate the virtual environment**
   
   - Using the command line:
  
     - Windows users:
  
      ```bash
      <VIRTUAL_ENVIRONMENT_NAME>\Scripts\activate
      ```

      - MacOS users:
  
      ```bash
      source <VIRTUAL_ENVIRONMENT_NAME>/bin/activate
      ```

   - Using Visual Studio Code:
     - The virtual environment should automatically activate. If this is not the case or if you want to use another environment, type `Python: select interpreter` into the search bar at the top of the window and select the one to activate.

3. **Install the dependencies that are in *requirements.txt* file**
   - Using the command line:
  
      ```bash
      pip install -r requirements.txt
      ```

   - Using Visual Studio Code:
     - In the search bar at the top of the window, tick the *requirements.txt* box to install all the dependencies that are in the file.

4. **Add the configuration to the project**
     - Duplicate the *empty-config.py* file, rename it to *config.py* and modify its content according to your own configuration. 
     - Example:
         ```bash
         SECRET_KEY="YOUR_SECRET_KEY"
         DATABASE="NAME_OF_THE_DATABASE_FILE.DB"
         EMAIL_HOST="SMTP_SERVER_NAME (FOR EXAMPLE smtp.office365.com)"
         EMAIL_PORT="SMTP_SERVER_PORT (FOR EXAMPLE 587)"
         EMAIL_ADDRESS="EMAIL_ADRESS_FROM_WHICH_THE_EMAIL_ARE_SENT_(NEEDS TO BE ...@outlook.com)"
         EMAIL_PASSWORD="PASSWORD"
         ```
  
5. **Run the project**

    - Using the command line:
   
      ```bash
      python -m flask run --debug
      ```

    - Using Visual Studio Code:
      - Open the *run.py* file and click on the small triangle at the top right of the window.
  
   - If everything worked fine, you should see the application running:
      ```bash
            * Serving Flask app 'app'
            * Debug mode: on
            WARNING: This is a development server. Do not use it in a production deployment...
            * Running on http://127.0.0.1:5000
         Press CTRL+C to quit
            * Restarting with stat
            * Debugger is active!
            * Debugger PIN: 107-190-651
      ```