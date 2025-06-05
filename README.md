# STORE

## Overview
This project is a web application built using **Python** (Django Framework). It includes functionality for managing customers and products, with APIs implemented using Django REST Framework (DRF). The project is containerized using Docker and supports deployment in Kubernetes (K8s).

---

## Prerequisites
- **Python**: Ensure Python 3.12 or higher is installed.
- **Docker**: Install Docker for containerization.
- **Kubernetes**: Install `kubectl` and a Kubernetes cluster (e.g., Minikube or a cloud provider like AWS EKS, GCP GKE, or Azure AKS).

---

## Development Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2.  Set Environment Variables
Create a .env file in the project root with the following variables:
```bash
SECRET_KEY=your_secret_key
DEBUG=True # Set to False in production
ALLOWED_HOSTS=*
SECRET_KEY=uisdfaebyusjhfgwevbdjhacev

DB_NAME=<DATABASE_NAME>
DB_USER=<DATABASE_USER>
DB_PASSWORD=<DATABASE_PASSWORD>
DB_HOST=<DATABASE_HOST>

GOOGLE_OAUTH2_CLIENT_ID=<GOOGLE_OAUTH2_CLIENT_ID>
GOOGLE_OAUTH2_CLIENT_SECRET=<GOOGLE_OAUTH2_CLIENT_SECRET>

AFRICAS_TALKING_SENDER_ID=<AFRICAS_TALKING_SENDER_ID>
AFRICAS_TALKING_API_KEY=<AFRICAS_TALKING_API_KEY>
AFRICAS_TALKING_USERNAME=<AFRICAS_TALKING_USERNAME>

ADMIN_EMAIL=<ADMIN_EMAIL>
EMAIL_HOST=<EMAIL_HOST>
EMAIL_PORT=<EMAIL_PORT>
EMAIL_HOST_USER=<EMAIL_HOST_USER>
EMAIL_HOST_PASSWORD=<EMAIL_HOST_PASSWORD>
EMAIL_USE_TLS=True
EMAIL_USE_SSL=True
EMAIL_BACKEND=<EMAIL_BACKEND> e.g., django.core.mail.backends.smtp.EmailBackend
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Server
```bash
# Apply migrations
python manage.py migrate
python manage.py runserver
```
Access the application at http://localhost:8000.<hr></hr>

### 5. Running with Docker
1. Build the Docker image:
    ```bash
    docker build -t <image-name>:<tag> .
    ```
2. Run the Docker container:
    ```bash
    docker run -p 8000:8000 --env-file .env <image-name>:<tag>
    ```

<hr>

### 6. Deployment in Kubernetes

1.Prepare Kubernetes Deployment Files
Ensure the following files are available in the deployment/ directory:
- `deployment.yaml`: Defines the deployment configuration.
- `service.yaml`: Defines the service configuration.
- `configmap.yaml`: Contains configuration settings.
- `secret.yaml`: Contains sensitive information (e.g., database credentials).

2.Apply Deployment Files
```bash
kubectl apply -f configmap
kubectl apply -f secret
kubectl apply -f deployment
kubectl apply -f service
```
3.Verify Deployment
Check the status of the pods and services:
```bash
kubectl get pods
kubectl get services
```
Access the application using the service's external IP:
e,g on minikube
```bash
minikube service store-service
```

<hr>

### 6. Testing the APIs
You can test the APIs using tools like Postman or cURL. The following endpoints are available:
- `GET /api/customer/`: Returns current authenticated customer.
- `PUT /api/customers/{id}/`: Updates an existing customer by ID.
- `GET /api/products/`: Lists all products.
- `GET /api/products/{id}/`: Retrieves a specific product by ID.
- `POST /api/products/`: Creates a new product.
- `PUT /api/products/{id}/`: Updates an existing product by ID.
- `DELETE /api/products/{id}/`: Deletes a product by ID.
- `POST /api/oders/`: Creates a new order.
- `GET /api/orders/`: Lists all orders associated with the authenticated customer.
- `GET /api/orders/{id}/`: Retrieves a specific order by ID.
- `POST /api/orders/{id}/`: Updates an existing order by ID.
- `DELETE /api/orders/{id}/`: Deletes an order by ID.
### 7. Running Tests
```bash
python manage.py test
```
### 8. Notes
- Ensure the requirements.txt file is included in the build context for Docker.
- Update the Kubernetes deployment files to match your cluster configuration (e.g., image name, environment variables, and resource limits).
- For production, configure a persistent database and external storage
- Consider using a reverse proxy (e.g., Nginx) for better performance and security.
- Use a CI/CD pipeline for automated testing and deployment.
- For OAuth2 authentication, ensure you have set up the Google OAuth2 credentials correctly and that the redirect URIs are configured in the Google Developer Console. 
- For email functionality, ensure the email backend is correctly configured in the Django settings and that the email server is accessible.

#### License
This project is licensed under the [MIT License](LICENSE).

<hr></hr> This README provides a basic guide for development and deployment. Adjust configurations as needed for your environment.