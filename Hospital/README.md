# Hospital Management System

A comprehensive hospital management system built with Flask.

## Features

- Patient management
- Doctor management
- Appointment scheduling
- Room management for admitted patients
- User authentication (admin and patient roles)
- Responsive design

## Deployment Instructions for PythonAnywhere

1. Sign up for a free account at [PythonAnywhere](https://www.pythonanywhere.com/)

2. Upload your files:
   - Go to the Files tab in your PythonAnywhere dashboard
   - Create a new directory (e.g., `hospital`)
   - Upload all the files from your Hospital directory

3. Set up a virtual environment:
   ```bash
   mkvirtualenv --python=python3.9 hospital-env
   ```

4. Install dependencies:
   ```bash
   cd ~/hospital
   pip install -r requirements.txt
   ```

5. Set up MySQL database:
   - Go to the Databases tab in PythonAnywhere
   - Create a new MySQL database
   - Update the .env file with the database credentials:
     ```
     DATABASE_URI=mysql://username:password@hostname/database_name
     ```

6. Run the database initialization script:
   ```bash
   cd ~/hospital
   python init_database.py
   ```

7. Configure the web app:
   - Go to the Web tab in PythonAnywhere
   - Click "Add a new web app"
   - Choose "Manual configuration" and select Python 3.9
   - Set the source code directory to `/home/yourusername/hospital`
   - Set the WSGI configuration file to point to your wsgi.py
   - Update the WSGI file with the correct path to your application
   - Add the following environment variables:
     - SECRET_KEY=your_secret_key
     - DATABASE_URI=mysql://username:password@hostname/database_name
     - DEBUG=False

8. Restart your web app and it should be live at `https://yourusername.pythonanywhere.com`

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in .env file
4. Run the app: `python app.py`

## License

This project is licensed under the MIT License. 