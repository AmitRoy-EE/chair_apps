**Preparation**

- Install miniconda from https://docs.conda.io/en/latest/miniconda.html
- Install Git from https://git-scm.com/downloads
- Start Visual Code 
- Open the folder, in  which you want to save your project
- Open your terminal 
- Click on arrow right to `+` on the right side of the terminal window
    - by default this should be PowerShell
        - to be able to utilise conda in PowerShell, [execution policies](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy?view=powershell-7.2) have to be changed by typing `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` 
    - initialise your terminal by typing `conda init powershell` (replace `powershell` with the shell you are using)
- type `git clone https://git.noc.ruhr-uni-bochum.de/ee/mcda-dashboard.git` into your terminal
- then open the project, by typing `code mcda-dashboard` into your terminal


**How to set up the environment:**


- create an environment by using the `environment.yml` file
    - type `conda env create -f environment.yml`
    - all required packages should be installed after a while
    - activate your environment by using `conda activate mcda`
- for more information about using conda click https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html

**How to run the app:**

- make sure that the path shown in the terminal is the path of the **app.py** file on your machine
    - if not use `cd foldername` to get to the right path
- type:  `streamlit run streamlit_app.py` into the terminal
- click on the https link, which is shown in your terminal
- now you can use the webtool in the webbrowser

**Additional information**

- the data frame, which is shown in the terminal, has been added for a better understanding of the code
