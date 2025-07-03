# BillSmart API Integration Guide for Frontend

## Overview
This guide provides instructions for integrating your Next.js frontend with the BillSmart FastAPI backend. The backend uses JWT authentication and provides RESTful endpoints for managing shops, products, customers, bills, and udharo (credit) transactions.

## 🔧 Base Configuration

### API Setup
- **Base URL**: `http://localhost:8000/api/v1`
- **Authentication**: JWT Bearer token in localStorage
- **Headers**: Always include `Authorization: Bearer <token>` for authenticated requests

### Error Handling
- Parse validation errors from array format
- Handle both simple string errors and detailed validation errors
- Display meaningful error messages to users

## 🚀 Critical Requirements

### 1. Authentication
- **Login**: Use form-data with `username` field (actually email) and `password`
- **Token Storage**: Store JWT in localStorage as `access_token`
- **Token Expiry**: 30 minutes - handle expiration gracefully
- **Headers**: Include `Authorization: Bearer <token>` in all authenticated requests

### 2. Bill Creation (CRITICAL - Fixes 422 Error)
Your previous 422 errors were caused by missing required fields. The backend requires:

- **`bill_number`**: Auto-generate with format `BILL-{year}-{timestamp}`
- **`total_price`**: Calculate for each item as `unit_price * quantity`
- **`paid_amount`**: Use this field (not `amount_paid`)
- **`payment_status`**: Must be `'paid'`, `'pending'`, or `'partial'`

**Bill Creation Helper Functions Needed:**
```typescript
// Auto-generate bill number
generateBillNumber(): string {
  const year = new Date().getFullYear();
  const timestamp = Date.now().toString().slice(-6);
  return `BILL-${year}-${timestamp}`;
}

// Calculate item total
calculateItemTotal(unitPrice: number, quantity: number): number {
  return unitPrice * quantity;
}

// Determine payment status
calculatePaymentStatus(totalAmount: number, paidAmount: number): string {
  if (paidAmount >= totalAmount) return 'paid';
  if (paidAmount > 0) return 'partial';
  return 'pending';
}
```

### 3. Product Management
- **Stock Display**: Use `current_stock` field (alias for `stock_quantity`)
- **Required Fields**: Support `cost_price`, `min_stock_level`, `sku`
- **Filtering**: Support search by name/category and low stock filtering

### 4. Customer Management
- **Udharo Integration**: Track `udharo_balance` for credit management
- **Search**: Support search by name and phone number
- **Optional Fields**: Handle email and address as optional

## 📍 API Endpoints Structure

### Endpoint Pattern
Use the simplified pattern without shop_id (backend auto-detects user's shop):
- ✅ `GET /products/` (recommended)
- ✅ `GET /customers/` (recommended)
- ✅ `GET /bills/` (recommended)

### Authentication Endpoints
- `POST /auth/login` - Login with form-data
- `POST /auth/register` - Register new user
- `GET /auth/me` - Get current user info

### Resource Endpoints
- **Products**: `/products/` - Full CRUD operations
- **Customers**: `/customers/` - Full CRUD operations  
- **Bills**: `/bills/` - Create, read, update operations
- **Udharo**: `/udharo/summary` - Credit balance summary
- **Dashboard**: `/dashboard/stats` - Analytics data

## 🎯 Frontend Implementation Requirements

### 1. TypeScript Interfaces
Create interfaces that match the backend schemas exactly:
- `Product` - Include all fields including `current_stock`
- `Customer` - Include `udharo_balance`
- `Bill` - Include `bill_number`, `paid_amount`, `payment_status`
- `BillItem` - Include `total_price` calculation

### 2. Service Classes
Implement singleton service classes for:
- `AuthService` - Authentication and user management
- `ProductService` - Product CRUD operations
- `CustomerService` - Customer CRUD operations
- `BillService` - Bill creation and management (with helper functions)
- `UdharoService` - Credit transaction handling
- `DashboardService` - Statistics and analytics

### 3. Bill Service Implementation
Your bill service must:
- Auto-generate bill numbers
- Calculate total_price for each item
- Calculate total_amount from items
- Determine payment_status automatically
- Handle backend validation requirements

### 4. Error Handling
Implement robust error handling for:
- 401 Unauthorized (token expired)
- 422 Validation errors (field validation)
- 404 Not Found (resource not found)
- 500 Internal Server Error

## 🔑 Key Business Logic

### Bill Creation Flow
1. **Collect**: Basic bill info (customer, items, payment)
2. **Generate**: Auto-generate bill_number
3. **Calculate**: total_price for each item
4. **Calculate**: total_amount from all items
5. **Determine**: payment_status based on paid_amount
6. **Submit**: Complete bill data to backend

### Stock Management
- Stock automatically decreases when bills are created
- Use `current_stock` for display purposes
- Support stock updates via PATCH endpoint

### Udharo (Credit) Logic
- Automatically creates credit transactions for unpaid bills
- Track customer credit balances
- Handle payment updates that affect credit

### Authentication Flow
1. **Login**: Form-data to `/auth/login`
2. **Store**: JWT token in localStorage
3. **Include**: Bearer token in all requests
4. **Handle**: Token expiration (30 minutes)

## 📋 Required Frontend Files

Create these service files with the specified functionality:
- `services/auth-service.ts` - Authentication management
- `services/product-service.ts` - Product operations
- `services/customer-service.ts` - Customer operations
- `services/bill-service.ts` - Bill creation and management
- `services/udharo-service.ts` - Credit transaction handling
- `services/dashboard-service.ts` - Statistics and analytics
- `config/api.ts` - Base configuration
- `types/api.ts` - TypeScript interfaces

## ⚠️ Important Notes

1. **Bill Creation**: This was the main issue causing 422 errors. The backend requires specific fields that were missing in your previous implementation.

2. **Authentication**: Use form-data for login, JSON for all other requests.

3. **Shop Context**: All operations are automatically scoped to the current user's shop - no need to pass shop_id.

4. **Stock Management**: Product stock is automatically updated when bills are created.

5. **Udharo Logic**: Credit transactions are automatically created for pending payments.

## 🎉 Success Criteria

After implementing these requirements, you should be able to:
- ✅ Successfully login and manage authentication
- ✅ Create products with all required fields
- ✅ Manage customers with udharo tracking
- ✅ Create bills without 422 validation errors
- ✅ Handle credit transactions automatically
- ✅ Display dashboard statistics
- ✅ Handle errors gracefully

This integration guide ensures your frontend will work seamlessly with the BillSmart API backend without the 422 validation errors you were experiencing.

## Key Requirements

### 1. Authentication
- Store JWT token in localStorage
- Include `Authorization: Bearer <token>` header in all requests
- Handle token expiration (30 minutes)

### 2. Bill Creation Logic (CRITICAL)
- Always generate `bill_number` using `generateBillNumber()`
- Calculate `total_price` for each item: `unit_price * quantity`
- Use `paid_amount` field (not `amount_paid`)
- Set `payment_status` based on payment: `'paid'`, `'pending'`, `'partial'`

### 3. Product Management
- Use `current_stock` field for display (same as `stock_quantity`)
- Support all fields: `cost_price`, `min_stock_level`, `sku`
- Handle low stock filtering with `low_stock=true` parameter

### 4. Customer Management
- Support udharo balance tracking
- Handle search by name or phone
- Use optional fields appropriately

### 5. Error Handling
- Parse validation errors from arrays
- Display meaningful error messages
- Handle different HTTP status codes

### 6. API Endpoints
- Use `/resource/` pattern (without shop_id) for simplicity
- Backend automatically uses current user's shop
- All endpoints require authentication

## API Endpoints Summary

### Authentication
- `POST /auth/login` - Login with email/password
- `POST /auth/register` - Register new user
- `GET /auth/me` - Get current user info

### Products
- `GET /products/` - Get all products
- `POST /products/` - Create product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product
- `PATCH /products/{id}/stock` - Update stock

### Customers
- `GET /customers/` - Get all customers
- `POST /customers/` - Create customer
- `PUT /customers/{id}` - Update customer
- `DELETE /customers/{id}` - Delete customer

### Bills
- `GET /bills/` - Get all bills
- `POST /bills/` - Create bill
- `GET /bills/{id}` - Get bill details
- `PUT /bills/{id}` - Update bill

### Udharo
- `GET /udharo/summary` - Get udharo summary
- `GET /customers/{id}/udharo` - Get customer udharo transactions

### Dashboard
- `GET /dashboard/stats` - Get dashboard statistics

## Important Notes

1. **Bill Creation**: This was the main issue causing 422 errors. The backend requires `bill_number` and `total_price` for each item.

2. **Authentication**: Use form-data for login, JSON for other requests.

3. **Shop Context**: All operations are automatically scoped to the current user's shop.

4. **Stock Management**: Product stock is automatically updated when bills are created.

5. **Udharo Logic**: Credit transactions are automatically created for pending payments.

This integration guide ensures your frontend will work seamlessly with the BillSmart API backend.
