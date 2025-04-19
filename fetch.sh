#!/bin/bash

# Navigate to the git repository directory (replace with your path)
cd ~/defender-os-node || exit

# Pull the latest changes from the remote repository
echo "Pulling the latest changes from the repository..."
git pull origin main

# Check if the git pull was successful
if [ $? -eq 0 ]; then
    echo "✅ Successfully pulled the latest changes."

    # Run npm install
    echo "Running npm install..."
    cd app || exit
    npm install

    # Check if npm install was successful
    if [ $? -eq 0 ]; then
        echo "✅ npm install completed successfully."

        # Run npm run build
        echo "Running npm run build..."
        npm run build

        # Check if npm run build was successful
        if [ $? -eq 0 ]; then
            echo "✅ Build completed successfully."
            pm2 restart defender-os-server
        else
            echo "🛑 npm run build failed."
            exit 1
        fi
    else
        echo "🛑 npm install failed."
        exit 1
    fi
else
    echo "🛑 Failed to pull the latest changes."
    exit 1
fi
