# alx_travel_app_0x03

Django backend for a travel booking platform with **Listings**, **Bookings**, **Reviews**, and **Payments**.  
Provides RESTful APIs via **Django REST Framework (DRF)** and supports **asynchronous background task processing** using **Celery with RabbitMQ**.

The service handles core booking logic, user interactions (hosts and guests), secure payment processing via **Chapa API**, and **email notifications executed asynchronously**.

## Features

- Manage Listings, Bookings, and Reviews via API  
- Nested user information for hosts and guests  
- Role-based validations (guests vs hosts)  
- Public endpoints for browsing listings and reviews  
- Payment integration with **Chapa API** (initiation and verification)  

### Booking & Payment Workflow
- Booking creation calculates total price automatically  
- Booking creation triggers:
  - Payment row creation
  - **Asynchronous email notification** using Celery  
- API returns `payment_url` to complete payment  
- Payment verification updates status (`Pending`, `Completed`, `Failed`)  

### Background Task Management
- **Celery** configured for background task execution  
- **RabbitMQ** used as the message broker  
- Email notifications are sent asynchronously on booking creation  
- Email backend configured for development (console or file-based output)
- Email task is triggered using delay() on booking creation

### Utilities
- Database seeder to populate sample data  
- Swagger documentation for API exploration

## Tech Stack

- Django / Django REST Framework  
- Celery  
- RabbitMQ  
- Docker (RabbitMQ service)  
- MySQL
- Chapa Payment API  

## Next Steps / Work in Progress

- Integration with **other microservices** for notifications, authenticaion and messaging  
- Event-driven communication using **RabbitMQ**
- Integration with **frontend** to handle Chapa `return_url` and display payment status  
- Enhanced permissions and filtering for payments
- Token-based authentication for production-ready API  

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed  # populate sample data
```

- Start RabbitMQ with Docker:

```bash
docker-compose up -d
```
RabbitMQ Management UI: http://localhost:15672
- user: guest
- password: guest

- Start Celery worker:

```bash
celery -A alx_travel_app worker -l info --pool=solo
```

- Run the Django server in another terminal:
```bash
python manage.py runserver
```

## API Endpoints

- `/api/listings/` - list, retrieve, create, update, delete listings
- `/api/listings/<listing_id>/reviews/` - list, retrieve, create, update, delete reviews
- `/api/bookings/` - list, retrieve, create, update, delete bookings
- `/api/bookings/?listing=<listing_id>/` - list all bookings for a specific listing
- `/api/payments/` - list all payments and their status  
- `/api/payments/initiate/ `- initiate payment for a booking  
- `/api/payments/verify/?tx_ref=<booking_id>` - verify payment status 
- `/swagger/` - interactive API documentation

This project builds on and extends [alx_travel_app_0x02](https://github.com/youssefelghamour/alx_travel_app_0x02)