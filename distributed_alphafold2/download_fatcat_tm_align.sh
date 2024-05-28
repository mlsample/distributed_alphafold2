#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define installation directory
INSTALL_DIR=$(pwd)/fatcat_tmalign

# Create and navigate to the installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Clone the necessary repositories
git clone https://github.com/GodzikLab/FATCAT-dist.git
git clone https://github.com/pylelab/USalign.git

# Build USalign
cd USalign
make

# Install FATCAT
cd ../FATCAT-dist
./Install

# Setup environment variables
echo "Setting up the environment for FATCAT..."

# Determine the shell type
SHELL_TYPE=$(basename "$SHELL")

if [[ "$SHELL_TYPE" == "bash" ]]; then
    SHELL_CONFIG_FILE="$HOME/.bashrc"
elif [[ "$SHELL_TYPE" == "csh" || "$SHELL_TYPE" == "tcsh" ]]; then
    SHELL_CONFIG_FILE="$HOME/.cshrc"
else
    echo "Unsupported shell type: $SHELL_TYPE"
    exit 1
fi

# Add environment variable settings to the shell config file
FATCAT_DIR="$INSTALL_DIR/FATCAT-dist"
FATCAT_MAIN_DIR="$FATCAT_DIR/FATCATMain"

if [[ "$SHELL_TYPE" == "bash" ]]; then
    {
        echo "export FATCAT=$FATCAT_DIR"
        echo "export PATH=\$PATH:$FATCAT_MAIN_DIR"
    } >> "$SHELL_CONFIG_FILE"
elif [[ "$SHELL_TYPE" == "csh" || "$SHELL_TYPE" == "tcsh" ]]; then
    {
        echo "setenv FATCAT $FATCAT_DIR"
        echo "set path = ( \$path $FATCAT_MAIN_DIR )"
    } >> "$SHELL_CONFIG_FILE"
fi

# Source the shell config file to apply changes
source "$SHELL_CONFIG_FILE"

echo "FATCAT environment setup complete. Please restart your terminal or run 'source $SHELL_CONFIG_FILE' to apply the changes."
