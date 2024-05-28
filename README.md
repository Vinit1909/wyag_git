
# WYAG-GIT

## Introduction
This is a Web UI for a simplified Git implementation in Python.

## Setup Instructions

1. **Clone the Repository**
   ```sh
   git clone https://github.com/Vinit1909/wyag_git.git
   cd wyag_git
   ```

2. **Install Dependencies**
   
   Install the required dependencies from `requirements.txt`:
   ```sh
   pip install -r requirements.txt
   ```

3. **Make `wyag` Executable**

   #### On Linux

   Make the `wyag` file executable:

      ```bash
      chmod +x wyag
      ```

   #### On Windows
   No specific command is required to make the file executable. Just ensure you have the necessary permissions to run it.


4. **Run the Application**
   
   Run the `app.py` file to start the Flask application:
   ```sh
   python app.py
   ```

   If the above command doesn't work, you may need to use:
   ```sh
   python3 app.py
   ```

4. **Access the Application**
   
   Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Common Operations

- **Adding a File**: Enter the filename and content, then click "Add File".
- **Committing Changes**: Enter a commit message and click "Commit".
- **Checking Status**: Click "Check Status" to see the current repository status.
- **Viewing Logs**: Click "Check Log" to see the commit logs.
- **Reading a File**: Enter the filename and click "Read File" to view its content.
- **Modifying a File**: Enter the filename and new content, then click "Modify File".
- **Deleting a File**: Enter the filename and click "Delete File" to remove it.
- **Merging Branches**: Enter the branch name and click "Merge" to merge branches.


## NOTE
The backend git functions were implemented by referring to this excellent guide on building git from scratch: https://wyag.thb.lt/