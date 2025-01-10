# Coderr Backend

The Coderr backend is a RESTful API built with **Django** and **Django REST Framework**. It supports the frontend by providing essential functionalities such as user registration, login, and the management of offers, orders, and reviews.

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Technologies](#technologies)
4. [Installation](#installation)
5. [API Endpoints](#api-endpoints)
6. [Helper Functions](#helper-functions)
7. [Contributing](#contributing)
8. [License](#license)

---

## Overview

The Coderr backend is designed to handle data management and business-specific logic for the Coderr platform. It provides RESTful APIs to manage user profiles, offers, orders, reviews, and related statistics.

---

## Features

- **User Authentication**:
  - User registration and login.
  - Role-based access control (Customer and Provider).
- **Offer Management**:
  - Create, update, delete, and retrieve offers.
  - Filter and search offers.
- **Order Management**:
  - Place and manage orders.
  - Manage order statuses.
- **Review Management**:
  - Add, edit, delete, and view reviews.
- **Statistics**:
  - View completed orders and review counts.
- **Pagination**:
  - Paginated endpoints for efficient data access.

---

## Technologies

- **Programming Language**: Python
- **Framework**: Django, Django REST Framework
- **Database**: SQLite
- **Dependencies**: 
  - `django-cors-headers`
  - `django-filter`
  - `pillow`
  - For a complete list, refer to the `requirements.txt` file.


## Tests

In diesem Projekt sind insgesamt 73 Tests implementiert, um die Funktionalität und Stabilität der Anwendung sicherzustellen. Die Tests decken verschiedene Aspekte der Anwendung ab, einschließlich:

- **Modelle**: Tests für die Validierung und die Methoden der Modelle.
- **Serializer**: Tests für die Serializer, um sicherzustellen, dass die Daten korrekt validiert und verarbeitet werden.
- **Admin-Oberflächen**: Tests für die Admin-Interfaces, um sicherzustellen, dass sie korrekt funktionieren.

### Ausführen der Tests

Um die Tests auszuführen, stelle sicher, dass du die erforderlichen Abhängigkeiten installiert hast und führe den folgenden Befehl im Terminal aus:

```bash
python manage.py test

---

## Installation

### Prerequisites
- Python 3.10+
- Git

### Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Seldir193/coderr-backend.git
   cd coderr-backend
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   python -m venv env
   source env/bin/activate  # For Linux/macOS
   env\Scripts\activate     # For Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Migrate the Database**:
   ```bash
   python manage.py migrate
   ```

5. **Start the Development Server**:
   ```bash
   python manage.py runserver
   ```

---

## API Endpoints

### Authentication
- **POST** `/registration/`  
  Registers a new user.
- **POST** `/login/`  
  Logs in a user.

### Profiles
- **GET** `/profile/<int:user_id>/`  
  Retrieves the profile of a specific user.
- **GET** `/profiles/business/<int:user_id>/`  
  Retrieves a specific business profile.
- **GET** `/profiles/business/`  
  Retrieves all business profiles.
- **GET** `/profiles/customer/<int:user_id>/`  
  Retrieves a specific customer profile.
- **GET** `/profiles/customer/`  
  Retrieves all customer profiles.

### Reviews
- **GET** `/reviews/`  
  Retrieves all reviews.
- **GET** `/reviews/<int:pk>/`  
  Retrieves a specific review.
- **POST** `/reviews/`  
  Creates a new review.
- **PUT** `/reviews/<int:pk>/`  
  Updates a specific review.
- **DELETE** `/reviews/<int:pk>/`  
  Deletes a specific review.

### Orders
- **GET** `/orders/`  
  Retrieves all orders.
- **GET** `/orders/<int:order_id>/`  
  Retrieves the details of a specific order.
- **POST** `/orders/`  
  Creates a new order.
- **GET** `/order-count/<int:offer_id>/`  
  Retrieves the count of in-progress orders for a specific offer.
- **GET** `/completed-order-count/<int:user_id>/`  
  Retrieves the count of completed orders for a specific user.


### Offers
- **GET** `/offers/`  
  Retrieves all offers.
- **GET** `/offers/<int:id>/`  
  Retrieves the details of a specific offer.
- **POST** `/offers/`  
  Creates a new offer.
- **GET** `/offerdetails/<int:id>/`
  Retrieves the details of a specific offer.

### Base Information
- **GET** `/base-info/`  
  Retrieves base information about the system.

---


## Helper Functions

The backend includes several helper functions for different purposes:

### `functions.py`
Contains logic for reusable functionalities like:

- `get_customer_profile_or_error(user)`: Retrieves customer profiles or returns an error if not found.
- `get_user_or_error(user_id)`: Fetches a user by ID or returns an error.
- `create_or_update_details(offer, details_data)`: Handles offer details, creating or updating them as needed.
- `handle_permission_denied(exception)`: Handles `PermissionDenied` exceptions.
- `format_profile_response(user, profile, profile_type)`: Formats profile data for responses.

### `profile_helpers.py`
Helper functions for profile-related operations:

- `get_user_type(obj)`: Returns the type of the user (superuser, business, customer, or unknown).
- `get_user_profile_image(obj)`: Retrieves the profile image URL based on the user's profile type.
- `validate_username_exists(username, errors)`: Validates if a username already exists.
- `validate_email_exists(email, errors)`: Validates if an email already exists.
- `validate_password_match(password, repeated_password, errors)`: Checks if the password and repeated password match.
- `create_new_user(validated_data)`: Creates a new user and sets their password.
- `create_user_profile(user, profile_type, validated_data)`: Creates the appropriate profile for the user based on the profile type.

### `serializers_helpers.py`
Includes utilities for serializers:

- `calculate_min_price(offer)`: Calculates the minimum price for an offer.
- `calculate_min_delivery_time(offer)`: Calculates the minimum delivery time for an offer.
- `extract_user_details(obj)`: Extracts user details for an offer.
- `create_offer_details(offer, details_data)`: Creates offer details for an offer.
- `update_main_instance(instance, validated_data)`: Updates the main instance of an offer.
- `update_offer_details(instance, details_data)`: Updates the offer details of an offer.
- `calculate_avg_rating(obj)`: Calculates the average rating for a business profile.
- `count_pending_orders(obj)`: Counts the number of pending orders for a business profile.

### `utils.py`
Utility functions like string formatting and data manipulation:

- `set_order_defaults(order)`: Sets default values for an order before saving.
- `authenticate_user(username, password)`: Authenticates a user using username and password.
- `create_token_for_user(user)`: Creates or retrieves an authentication token for a user.

---

## Contributing

Contributions are welcome! Fork the repository, create a new branch, and submit a pull request. 

Please ensure that your code adheres to the following standards:
- **Clean Code principles**: Write simple, understandable, and maintainable code.
- **PEP 8 style guide**: Follow Python's official style guide to ensure consistency and readability.

---

## License

This project is licensed under the MIT License. For more details, see the [LICENSE](LICENSE) file.


































































