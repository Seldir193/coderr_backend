# Backend Documentation for the Coderr Project

## Table of Contents
1. [Introduction](#introduction)
2. [Technologies Used](#technologies-used)
3. [Setup and Installation](#setup-and-installation)
4. [Database Structure](#database-structure)
5. [API Endpoints](#api-endpoints)
6. [Helper Functions](#helper-functions)
7. [Pagination and Filtering](#pagination-and-filtering)
8. [Error Handling](#error-handling)
9. [Tests](#tests)
10. [Contributing](#contributing)
11. [License](#license)

---

## Introduction

The Coderr backend is a RESTful API developed using **Django** and **Django REST Framework**. It provides features like user registration, login, offer management, order processing, and reviews. This document details the setup, usage, and extension of the backend.

---

## Technologies Used

- **Programming Language**: Python
- **Frameworks**:
  - Django
  - Django REST Framework
- **Database**: SQLite (default for local development)
- **Additional Libraries**:
  - `django-cors-headers`: Manage Cross-Origin Resource Sharing (CORS).
  - `django-filter`: Queryset filtering for APIs.
  - `pillow`: Image processing.
- **CustomPagination**: A custom class for API pagination.

---

## Setup and Installation

### Prerequisites
- Python 3.10 or higher
- Git
- Virtual environment (recommended)

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Seldir193/coderr-backend.git
   cd coderr-backend
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv env
   source env/bin/activate  # For Linux/macOS
   env\Scripts\activate     # For Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Database Migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Start the Development Server**:
   ```bash
   python manage.py runserver
   ```

---

## Database Structure

### Key Tables

1. **Users**:
   - Fields: `id`, `username`, `email`, `password`, `is_business`, `date_joined`.
   - Purpose: Stores user credentials.

2. **Offers**:
   - Fields: `id`, `title`, `description`, `price`, `creator`, `created_at`, `updated_at`.
   - Purpose: Manages offers created by business users.

3. **Orders**:
   - Fields: `id`, `offer`, `user`, `status`, `created_at`.
   - Purpose: Tracks orders placed by customers.

4. **Reviews**:
   - Fields: `id`, `rating`, `description`, `business_user`, `reviewer`, `created_at`.
   - Purpose: Stores user reviews.

---

## API Endpoints

### Authentication
- **POST** `/registration/`  
  Registers a new user.

- **POST** `/login/`  
  Logs in a user.

### Profiles
- **GET** `/profiles/business/<int:user_id>/`  
  Retrieve a business profile.
- **GET** `/profiles/customer/<int:user_id>/`  
  Retrieve a customer profile.

### Offers
- **GET** `/offers/`  
  Retrieve all offers.
- **POST** `/offers/`  
  Create a new offer.
- **GET** `/offers/<int:id>/`  
  Retrieve offer details.
- **GET** `/offerdetails/<int:id>/`
  Retrieves the details of a specific offer.

### Orders
- **GET** `/orders/`  
  Retrieve all orders.
- **POST** `/orders/`  
  Create a new order.
- **GET** `/order-count/<int:offer_id>/`  
  Count in-progress orders for an offer.
- **GET** `/completed-order-count/<int:user_id>/`  
  Count completed orders for a user.

### Reviews
- **GET** `/reviews/`  
  Retrieve all reviews.
- **POST** `/reviews/`  
  Create a new review.
- **PUT** `/reviews/<int:pk>/`  
  Edit a review.
- **DELETE** `/reviews/<int:pk>/`  
  Delete a review.

### Base Information
- **GET** `/base-info/`  
  Retrieve application base information.

---

## Helper Functions

The backend includes several helper files to streamline and organize the logic:

- **`profile_helpers.py`**: Contains validation and processing logic for user profiles.
- **`utils.py`**: General utilities like string formatting or date conversion.
- **`functions.py`**: Business-specific logic used across various views.
- **`serializers_helpers.py`**: Helper functions for serializing data.

For detailed explanations of each helper function, including their purpose and usage, please refer to the **[README.md](README.md)** file.

---

## Pagination and Filtering

The backend employs:
- **DjangoFilterBackend**: Allows filtering based on fields like `price` or `date`.
- **CustomPagination**: A flexible pagination system for API endpoints.
- **FilterOrder**: Enables sorting results, e.g., by `created_at` or `price`.

---

## Error Handling

### Common Issues

1. **Database Errors**:
   - Cause: Missing migrations.
   - Solution: Run `python manage.py makemigrations && python manage.py migrate`.

2. **Authentication Errors**:
   - Cause: Missing or invalid tokens.
   - Solution: Verify request headers.

3. **Endpoint Errors**:
   - Cause: Incorrect URL or method.
   - Solution: Confirm endpoint definitions.

---

## Tests

### Running Tests
```bash
python manage.py test
```

- Tests cover authentication, endpoint functionality, and database integrity.
- Use tools like `coverage` to check test coverage.

---

## Contributing

Contributions are welcome! Fork the repository, create a new branch, and submit a pull request. 

Please ensure that your code adheres to the following standards:
- **Clean Code principles**: Write simple, understandable, and maintainable code.
- **PEP 8 style guide**: Follow Python's official style guide to ensure consistency and readability.

---

## License

This project is licensed under the MIT License. For more details, see the [LICENSE](LICENSE) file.
