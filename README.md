
## Local Development / Docker Deployment

For setup instructions and environment configuration, please check the official [documentation](https://github.com/cgsem/webproject_docs).

## Development Workflow

1. Define the database models (`model`)
2. Define the data validation models (`schema`)
3. Define the API views and routing (`api`)
4. Write business logic (`service`)
5. Implement database operations (`crud`)

## Testing

Testing can be done using `pytest` as follows:

1. Create a test database with utf8mb4 encoding.
2. Use the `backend/sql/create_tables.sql` to create the necessary tables.
3. Initialize test data with the `backend/sql/init_pytest_data.sql`.
4. Execute tests by navigating to the `backend` directory and running:

   ```bash
   cd backend/
   pytest -vs --disable-warnings
