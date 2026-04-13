#!/bin/bash

# Check if version is passed as a command-line argument
if [[ -z "$1" ]]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VERSION="$1"
echo "Building release version: $VERSION"

# Create the dist folder if it doesn't exist
DIST_FOLDER="./dist"
if [[ ! -d "$DIST_FOLDER" ]]; then
    mkdir "$DIST_FOLDER"
fi

# Define the source and destination files
APP_FOLDER="./app/"
OVERWRITE_FOLDER="./overwrite/"
OVERWRITE_PARAMETRIZED_SCRIPTS_FOLDER=$OVERWRITE_FOLDER"parametrized-scripts/"
OVERWRITE_JS_FILES_FOLDER=$OVERWRITE_FOLDER"js-files/"
OVERWRITE_DATASETS_FOLDER=$OVERWRITE_FOLDER"datasets/"
CUSTOM_LOGO_PATH="${OVERWRITE_FOLDER}logo.svg"
SOURCE_FILE="index.html"
SOURCE_FILE_PATH="$APP_FOLDER$SOURCE_FILE"
DEST_FILE="./dist/opla.html"
BUILD_STEP_FOLDER="./dist/build-steps/"
CUSTOMIZATION_STEP_FILE=$BUILD_STEP_FOLDER"customization-step.html"

# Check if the source file exists
if [[ ! -f "$SOURCE_FILE_PATH" ]]; then
    echo "Source file $SOURCE_FILE_PATH does not exist."
    exit 1
fi

# Clean the dist folder if it is not empty
if [[ -d "$DIST_FOLDER" && "$(ls -A $DIST_FOLDER)" ]]; then
    echo "Cleaning existing dist folder..."
    rm -rf "$DIST_FOLDER"/*
fi

# Recreate the build step folder
if [[ -d "$BUILD_STEP_FOLDER" ]]; then
    echo "Cleaning existing build step folder..."
    rm -rf "$BUILD_STEP_FOLDER"
fi
mkdir -p "$BUILD_STEP_FOLDER"


###################
## CUSTOMIZATION ##
###################


while IFS= read -r line; do
    if [[ "$line" =~ \<\!\-\-\[REPLACE\-TAG\|LOGO\]\-\-\> ]]; then
        if [[ -f "$CUSTOM_LOGO_PATH" ]]; then
            echo "<img src=\".${CUSTOM_LOGO_PATH}\"/>" >> $CUSTOMIZATION_STEP_FILE
        else
            echo "$line" >> $CUSTOMIZATION_STEP_FILE
        fi
    elif [[ "$line" =~ \<\!\-\-\[REPLACE\-TAG\|JS_OVERWRITE\]\-\-\> ]]; then
        if [[ -d "$OVERWRITE_JS_FILES_FOLDER" ]]; then
            echo "Found generic overwrite scripts folder. Adding scripts to the build..."
            find "$OVERWRITE_JS_FILES_FOLDER" -type f -name "*.js" | sort | while read -r JS_FILE; do
                echo "-| Adding script: $JS_FILE"
                echo "<script src=\".${JS_FILE}\"></script>" >> $CUSTOMIZATION_STEP_FILE
            done
        fi
    elif [[ "$line" =~ \<\!\-\-\[REPLACE\-TAG\|DATASETS\]\-\-\> ]]; then
        if [[ -d "$OVERWRITE_DATASETS_FOLDER" ]]; then
            echo "Found dataset folder. Adding dataset to the build..."
            find "$OVERWRITE_DATASETS_FOLDER" -type f -name "*.js" | sort | while read -r JS_FILE; do
                echo "-| Adding dataset: $JS_FILE"
                echo "<script src=\".${JS_FILE}\"></script>" >> $CUSTOMIZATION_STEP_FILE
            done
        fi
    elif [[ "$line" =~ \<\!\-\-\[REPLACE\-TAG\|PARAMETRIZED_SCRIPTS\]\-\-\> ]]; then
        if [[ -d "$OVERWRITE_PARAMETRIZED_SCRIPTS_FOLDER" ]]; then
            echo "Found parametrized scripts folder. Adding scripts to the build..."
            find "$OVERWRITE_PARAMETRIZED_SCRIPTS_FOLDER" -type f -name "*.js" | sort | while read -r JS_FILE; do
                echo "-| Adding script: $JS_FILE"
                echo "<script src=\".${JS_FILE}\"></script>" >> $CUSTOMIZATION_STEP_FILE
            done
        fi
    else
        echo "$line" >> $CUSTOMIZATION_STEP_FILE
    fi
done < "$SOURCE_FILE_PATH"


########################
## BUNDLING OF ASSETS ##
########################


while IFS= read -r line; do
    # Manage JavaScript Files
    if [[ "$line" =~ \<script([^\>]*)src=\"([^\"]+)\"([^\>]*)\>\<\/script\> ]]; then
        JS_FILE="${BASH_REMATCH[2]}"
        TAG_PARAMS="${BASH_REMATCH[1]}${BASH_REMATCH[3]}"
        if [[ -f "$APP_FOLDER$JS_FILE" ]]; then
            echo "<!-- Inline script from $JS_FILE -->" >> $DEST_FILE
            if [[ "$TAG_PARAMS" =~ defer ]]; then
                echo "<script ${TAG_PARAMS}>" >> $DEST_FILE
                echo "window.addEventListener('DOMContentLoaded', function() {" >> $DEST_FILE
                sed '' "$APP_FOLDER$JS_FILE" >> $DEST_FILE
                echo "});" >> $DEST_FILE
                echo "</script>" >> $DEST_FILE
            else
                echo "<script ${TAG_PARAMS}>" >> $DEST_FILE
                sed '' "$APP_FOLDER$JS_FILE" >> $DEST_FILE
                echo "</script>" >> $DEST_FILE
            fi
        else
            echo "Warning: JavaScript file $JS_FILE not found. Skipping."
        fi
    # Manage Stylesheets Files
    elif [[ "$line" =~ \<link([^\>]*)rel=\"stylesheet\"([^\>]*)href=\"([^\"]+)\"([^\>]*)\> ]]; then
        CSS_FILE="${BASH_REMATCH[3]}"
        if [[ -f "$APP_FOLDER$CSS_FILE" ]]; then
            echo "<!-- Inline stylesheet from $CSS_FILE -->" >> $DEST_FILE
            echo "<style>" >> $DEST_FILE
            cat "$APP_FOLDER$CSS_FILE" >> $DEST_FILE
            echo "</style>" >> $DEST_FILE
        else
            echo "Warning: CSS file $CSS_FILE not found. Skipping."
        fi
    # Manage SVG Images
    elif [[ "$line" =~ \<img([^\>]*)src=\"([^\"]+\.svg)\"([^\>]*)\> ]]; then
        SVG_FILE="${BASH_REMATCH[2]}"
        if [[ -f "$APP_FOLDER$SVG_FILE" ]]; then
            echo "<!-- Inline SVG from $SVG_FILE -->" >> $DEST_FILE
            cat "$APP_FOLDER$SVG_FILE" >> $DEST_FILE
        else
            echo "Warning: SVG file $SVG_FILE not found. Skipping."
        fi
    else
        echo "$line" >> $DEST_FILE
    fi
done < "$CUSTOMIZATION_STEP_FILE"


##################
## FINALIZATION ##
##################

# Update version placeholder
sed -i "s/version \[develop\]/version $VERSION/g" "$DEST_FILE"

echo "Processed file saved as $DEST_FILE"