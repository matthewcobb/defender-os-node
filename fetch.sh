#!/bin/bash

# Load NVM when ran in python subprocess
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Navigate to the git repository directory (replace with your path)
# Needed for python subprocesses to find the git repo
#cd ~/defender-os-node || exit

# Begin update process
echo "[PROGRESS:STEP:git_pull:started] 🔄 Pulling latest changes from repository..."
git_output=$(git pull origin main)
echo "$git_output"
pull_status=$?

# Check if the git pull was successful
if [ $pull_status -eq 0 ]; then
    echo "[PROGRESS:STEP:git_pull:completed] ✅ Successfully pulled the latest changes"

    # Check if the message contains "Already up to date" or similar
    if echo "$git_output" | grep -q "Already up to date" || echo "$git_output" | grep -q "up-to-date"; then
        echo "🔍 No changes detected. System is already up to date."
        echo "[PROGRESS:OVERALL:completed] ✅ No updates needed, system is already up to date"
        exit 0
    fi

    app_changes=false
    python_changes=false

    # Check if there are changes in the app directory
    if echo "$git_output" | grep -q "app/"; then
        app_changes=true
        echo "📦 Changes detected in app directory"
    fi

    if [ "$app_changes" = true ]; then
        # Run npm install
        echo "[PROGRESS:STEP:npm_install:started] 🔄 Installing npm dependencies..."
        cd /home/pi/defender-os-node/app || exit
        npm install
        npm_install_status=$?

        # Check if npm install was successful (ignoring deprecation warnings)
        if [ $npm_install_status -eq 0 ]; then
            echo "[PROGRESS:STEP:npm_install:completed] ✅ npm install completed successfully"

            # Run npm run build
            echo "[PROGRESS:STEP:npm_build:started] 🔄 Building application..."
            npm run build
            npm_build_status=$?

            # Check if npm run build was successful (ignoring deprecation warnings)
            if [ $npm_build_status -eq 0 ]; then
                echo "[PROGRESS:STEP:npm_build:completed] ✅ Build completed successfully"

                echo "[PROGRESS:STEP:restart_app:started] 🔄 Restarting Node.js server..."
                pm2 restart defender-os-server
                restart_status=$?

                if [ $restart_status -eq 0 ]; then
                    echo "[PROGRESS:STEP:restart_app:completed] ✅ Server restart successful"
                else
                    echo "[PROGRESS:STEP:restart_app:failed] ❌ Server restart failed"
                fi
            else
                # Only fail if it's a real error, not just deprecation warnings
                if grep -v "DeprecationWarning" <<< "$(npm run build 2>&1)" | grep -q "ERR!"; then
                    echo "[PROGRESS:STEP:npm_build:failed] ❌ npm run build failed"
                    echo "[PROGRESS:OVERALL:failed] ❌ Update process failed"
                    exit 1
                else
                    echo "[PROGRESS:STEP:npm_build:completed] ✅ Build completed with warnings"
                fi
            fi
        else
            # Only fail if it's a real error, not just deprecation warnings
            if grep -v "DeprecationWarning" <<< "$(npm install 2>&1)" | grep -q "ERR!"; then
                echo "[PROGRESS:STEP:npm_install:failed] ❌ npm install failed"
                echo "[PROGRESS:OVERALL:failed] ❌ Update process failed"
                exit 1
            else
                echo "[PROGRESS:STEP:npm_install:completed] ✅ npm install completed with warnings"
            fi
        fi
    else
        echo "🔍 No changes detected in app directory. Skipping npm install, build and restart."
    fi

    # Check if there are changes in the python directory
    if echo "$git_output" | grep -q "python/"; then
        python_changes=true
        echo "📦 Changes detected in python directory"

        # Navigate to python directory and update dependencies
        echo "[PROGRESS:STEP:python_dependencies:started] 🔄 Updating Python dependencies..."
        cd /home/pi/defender-os-node/python || exit
        source env/bin/activate

        # Install requirements
        pip install -r requirements.txt
        pip_status=$?

        # Check if pip install was successful
        if [ $pip_status -eq 0 ]; then
            echo "[PROGRESS:STEP:python_dependencies:completed] ✅ Python dependencies updated successfully"
        else
            echo "[PROGRESS:STEP:python_dependencies:failed] ❌ Failed to update Python dependencies"
            echo "[PROGRESS:OVERALL:failed] ❌ Update process failed"
            deactivate
            exit 1
        fi

        deactivate
        echo "[PROGRESS:STEP:restart_python:started] 🔄 Restarting Python server..."
        sudo systemctl restart defender-os-utilities-server.service

        # Check if restart was successful
        if sudo systemctl is-active --quiet defender-os-utilities-server.service; then
            echo "[PROGRESS:STEP:restart_python:completed] ✅ Python server restart successful"
        else
            echo "[PROGRESS:STEP:restart_python:failed] ❌ Python server restart failed"
            sudo systemctl status defender-os-utilities-server.service
            echo "[PROGRESS:OVERALL:failed] ❌ Update process failed"
            exit 1
        fi
    else
        echo "🔍 No changes detected in python directory. Skipping dependency updates."
    fi

    # If no changes were detected in either directory but git pull succeeded
    if [ "$app_changes" = false ] && [ "$python_changes" = false ]; then
        echo "🔍 No significant changes detected that require updates."
    fi

    # If we got here without errors, the update was successful
    echo "[PROGRESS:OVERALL:completed] ✅ Update process completed successfully"
else
    echo "[PROGRESS:STEP:git_pull:failed] ❌ Failed to pull the latest changes"
    echo "[PROGRESS:OVERALL:failed] ❌ Update process failed"
    exit 1
fi
