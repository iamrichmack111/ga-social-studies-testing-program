# Georgia Social Studies Testing Program

Adaptive Georgia social studies assessment for Grades 3 through 8.

## Grade coverage

- Grade 3: Georgia communities, geography, civics, economics, and historical figures
- Grade 4: U.S. history from exploration through Reconstruction
- Grade 5: U.S. history from the late 1800s through modern America
- Grade 6: World Area Studies — Europe, Latin America, Canada, and Australia
- Grade 7: World Area Studies — Africa and Asia
- Grade 8: Georgia history, geography, government, civics, and economics

## Features

- Adaptive diagnostic
- Automatic grading
- Standards stored with every answer
- Parent PIN portal
- CSV export
- Separate SQLite database
- Federation-ready schema
- Pop!_OS desktop installer

## Install on macOS

    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    .venv/bin/python app.py

Open http://127.0.0.1:5085

## Install on Pop!_OS

    chmod +x install-desktop.sh start-desktop.sh
    ./install-desktop.sh
    ./start-desktop.sh

Default parent PIN: 2468

Database:

    ~/KIDS-HW/grades/ga_social_studies_testing_program/ga_social_studies_testing_program.db
