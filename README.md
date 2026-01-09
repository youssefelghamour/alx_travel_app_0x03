# alx_travel_app_0x02

Django backend for a travel booking platform with **Listings**, **Bookings**, **Reviews**, and **Payments**. Provides RESTful APIs via **Django REST Framework (DRF)** and includes a **database seeder** to populate sample data.  

This service handles core booking logic, user interactions (hosts and guests), and secure payment processing via **Chapa API**. It can be extended to integrate into a **microservices architecture** in the future, using tools like **RabbitMQ** for inter-service communication with our messaging, notification and authentication services that we have created earlier.

## Features

- Manage Listings, Bookings, and Reviews via API  
- Nested user information for hosts and guests  
- Role-based validations (guests vs hosts)  
- Public endpoints for browsing listings and reviews  
- Payment integration with **Chapa API** (initiation and verification)  
- Payment workflow:  
    - Booking creation triggers Payment row creation  
    - API returns `payment_url` to complete payment  
    - Payment verification updates status (`Pending`, `Completed`, `Failed`)  
- Seeder to populate the database with sample data  

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

This project builds on and extends [alx_travel_app_0x01](https://github.com/youssefelghamour/alx_travel_app_0x01)