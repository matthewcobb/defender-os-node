#!/bin/bash

# Load NVM when ran in python subprocess
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Navigate to the git repository directory (replace with your path)
# Needed for python subprocesses to find the git repo
#cd ~/defender-os-node || exit

# Pull the latest changes from the remote repository
echo "Pulling the latest changes from the repository..."
git_output=$(git pull origin main)
echo "$git_output"
pull_status=$?

# Check if the git pull was successful
if [ $pull_status -eq 0 ]; then
    echo "✅ Successfully pulled the latest changes."

    # Check if there are changes in the app directory
    if echo "$git_output" | grep -q "app/"; then
        echo "📦 Changes detected in app directory."

        # Run npm install
        echo "Running npm install..."
        cd /home/pi/defender-os-node/app || exit
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
        echo "🔍 No changes detected in app directory. Skipping npm install, build and restart."
    fi

    if echo "$git_output" | grep -q "python/"; then
        echo "📦 Changes detected in python directory."

        # Navigate to python directory and update dependencies
        echo "Updating Python dependencies..."
        cd /home/pi/defender-os-node/python || exit
        source env/bin/activate

        # Install requirements
        pip install -r requirements.txt

        # Check if pip install was successful
        if [ $? -eq 0 ]; then
            echo "✅ Python dependencies updated successfully."
        else
            echo "🛑 Failed to update Python dependencies."
        fi

        deactivate
        echo "✨ Restarting server"
        sudo systemctl restart defender-os-utilities-server.service

        # Check if restart was successful
        if sudo systemctl is-active --quiet defender-os-utilities-server.service; then
            echo "✅ Server restart successful"
        else
            echo "🛑 Server restart failed"
            sudo systemctl status defender-os-utilities-server.service
            exit 1
        fi
    else
        echo "🔍 No changes detected in python directory. Skipping dependency updates."
    fi
else
    echo "🛑 Failed to pull the latest changes."
    exit 1
fi
