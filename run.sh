#!/bin/bash

# Reset
Color_Off='\033[0m' # Text Reset

# Regular Colors
Red='\033[0;31m'    # Red
Green='\033[0;32m'  # Green
Yellow='\033[0;33m' # Yellow
Blue='\033[0;34m'   # Blue
Cyan='\033[0;36m'   # Cyan

# Function to check if a package is installed
is_package_installed() {
    python -c "import pkg_resources; pkg_resources.require('$1')" &>/dev/null
}

# Function to install dependencies from requirements.txt
install_requirements() {
    if [ -f "requirements.txt" ]; then
        printf "${Yellow}Checking dependencies...\n"
        SECONDS=0
        while read -r line; do
            package=$(printf "$line" | cut -d'=' -f1) # Get the package name
            if ! is_package_installed "$package"; then
                printf "${Yellow}$package is not installed. Installing...\n"
                pip install "$line" # Install the package with its version
            else
                printf "${Green}$package is already installed.\n"
            fi
        done <requirements.txt
        printf "${Green}Dependencies installed in %s seconds.\n" "$SECONDS"
    else
        printf "${Red}requirements.txt not found!\n"
        deactivate
        exit 1
    fi
}

# Check if virtual environment exists, if not create it and install requirements
if [ ! -d "venv" ]; then
    printf "${Blue}Virtual enviroment not found, creating...\n"
    SECONDS=0
    python3 -m venv venv
    source venv/bin/activate
    printf "${Green}Virtual enviroment created in %s seconds.\n" "$SECONDS"
    printf "${Cyan}Installing requirements...\n"
    printf "${Cyan}This may take a minute...\n"
    install_requirements
else
    printf "${Blue}Virtual enviroment found, activating...\n"
    SECONDS=0
    source venv/bin/activate
    printf "${Green}Virtual enviroment activated in %s seconds.\n" "$SECONDS"
fi

# Check if the "repair" argument was passed to the script
if [ "$1" == "repair" ]; then
    printf "${Yellow}Running repair to check/install requirements...\n"
    install_requirements
fi

printf "${Green}Starting web interface...\n"
# Run the Python script (replace script.py with your script name)
SECONDS=0
python webapp/main.py
printf "${Green}Web interface ran for %s seconds.\n" "$SECONDS"

printf "${Red}Exiting...\n"

# Deactivate the virtual environment
deactivate
