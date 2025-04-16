#!/bin/bash

# Variables
REPO_OWNER="matthewcobb"  # Replace with your GitHub username or organization
REPO_NAME="defender-os"            # Replace with your repository name
DESTINATION_PATH="/home/pi/defender-os.AppImage"  # Final path to save the AppImage
API_URL="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"

# Function to download the latest AppImage
download_latest_appimage() {
    echo "Fetching latest release info from GitHub..."

    # Get the download URL for the latest AppImage (matches any AppImage file in the release assets)
    DOWNLOAD_URL=$(curl -s $API_URL | grep "browser_download_url.*AppImage" | cut -d '"' -f 4)

    # Check if the download URL was found
    if [ -z "$DOWNLOAD_URL" ]; then
        echo "Error: Could not find the download URL for the latest AppImage."
        exit 1
    fi

    # Extract the filename from the download URL
    APPIMAGE_NAME=$(basename $DOWNLOAD_URL)

    echo "Downloading the latest version: $APPIMAGE_NAME..."

    # Download the AppImage to a temporary location
    curl -L $DOWNLOAD_URL -o /tmp/$APPIMAGE_NAME

    if [ $? -eq 0 ]; then
        echo "Download complete. Replacing the old AppImage..."
        mv /tmp/$APPIMAGE_NAME $DESTINATION_PATH
        chmod +x $DESTINATION_PATH
        echo "$APPIMAGE_NAME has been updated successfully at $DESTINATION_PATH."
    else
        echo "Error: Failed to download $APPIMAGE_NAME."
        exit 1
    fi
}

# Execute the download function
download_latest_appimage
