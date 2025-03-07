# Cliques Web Application

A web-based social networking application where users are automatically put into group chats whenever cliques form between them.

Built with Flask.

## Setup

1. Clone the repository.
2. Create a virtual environment and install dependencies:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. Configure the environment:
   - Copy `.env.example` to `.env`
   - Edit `.env` and fill in your configuration values:
     - Generate a secure random key for `FLASK_SECRET_KEY`
     - Configure your mail server settings
     - Set up your database credentials
     - Configure your application domain

4. Initialize the database:
   - Create a MySQL database with the name specified in your `.env`
   - Import the database schema (schema file location TBD)

5. Run the application:

    ```bash
    python -m flask run
    ```

## Environment Variables

The application requires several environment variables to be set. These can be configured in the `.env` file:

### Flask Configuration

- `FLASK_SECRET_KEY`: Secret key for session security
- `FLASK_SESSION_TYPE`: Session storage type (default: filesystem)
- `FLASK_PERMANENT_SESSION_LIFETIME`: Session lifetime in days (default: 30)
- `FLASK_SEND_FILE_MAX_AGE`: Static file cache lifetime in hours (default: 1)

### Mail Configuration

- `MAIL_DEFAULT_SENDER`: Default email sender address
- `MAIL_USE_TLS`: Whether to use TLS for email (default: True)
- `MAIL_USERNAME`: SMTP server username
- `MAIL_PASSWORD`: SMTP server password
- `MAIL_HOST`: SMTP server hostname

### Database Configuration

- `DB_HOST`: MySQL server hostname (default: localhost)
- `DB_USER`: MySQL username
- `DB_PASSWORD`: MySQL password
- `DB_NAME`: MySQL database name
- `DB_CHARSET`: MySQL charset (default: utf8mb4)

### Application Configuration

- `APP_DOMAIN`: Your application's domain name
- `APP_SCHEME`: URL scheme (http/https, default: https)

## Security Notes

1. Never commit your `.env` file to version control
2. Use strong, unique passwords for all services
3. Keep your secret key secure and never share it
4. Regularly update dependencies to patch security vulnerabilities
5. Use HTTPS in production

## License

This project is licensed under the terms specified in the LICENSE file.

## Author

Created by Ali Mahouk.
