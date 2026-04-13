# Retail Enterprise Data Schema Reference
## Version: 1.0 | Storage: Azure SQL + Azure Blob Storage
## Generated: January 2026

---

## STORAGE DISTRIBUTION

### Azure SQL Database Tables (28 Tables)
All transactional and dimensional data

### Azure Blob Storage Tables (2 Tables)
- `raw_customer_feedback` - Unstructured feedback data (JSON/CSV)
- `raw_product_images` - Product image metadata and paths

---

## DOMAIN COVERAGE

This dataset covers the following business domains:

1. **Store Operations** - Store management, registers, daily operations
2. **Product Management** - Products, categories, brands, pricing
3. **Inventory Management** - Stock levels, movements, warehouses
4. **Customer Management** - Customer profiles, segments, loyalty
5. **Sales & Transactions** - POS transactions, payments, line items
6. **Order Management** - E-commerce orders, fulfillment, shipping
7. **Supply Chain** - Suppliers, purchase orders, goods receipt
8. **Human Resources** - Employees, schedules, payroll
9. **Finance & Accounting** - GL accounts, budgets, AP/AR
10. **Marketing & Promotions** - Campaigns, promotions, coupons
11. **Customer Service** - Returns, complaints, feedback
12. **Analytics & Reporting** - Aggregated metrics, KPIs

---

## TABLE SCHEMAS

### 1. DIM_REGION
**Purpose**: Geographic regions for store grouping and reporting

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| region_id | INT | PK, IDENTITY | Unique identifier for each region |
| region_code | VARCHAR(10) | UNIQUE, NOT NULL | Short code for region (e.g., 'NA-EAST') |
| region_name | VARCHAR(100) | NOT NULL | Full descriptive name of the region |
| country | VARCHAR(100) | | Country where region is located |
| timezone | VARCHAR(50) | | Standard timezone identifier (e.g., 'America/New_York') |
| currency_code | VARCHAR(3) | | ISO 4217 currency code |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 2. DIM_STORE
**Purpose**: Physical retail store locations

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| store_id | INT | PK, IDENTITY | Unique identifier for each store |
| store_code | VARCHAR(20) | UNIQUE, NOT NULL | Business identifier code (e.g., 'STR-NYC-001') |
| store_name | VARCHAR(200) | NOT NULL | Official store name |
| region_id | INT | FK → dim_region | Reference to parent region |
| store_type | VARCHAR(50) | | Classification: Flagship, Standard, Express, Outlet |
| address_line1 | VARCHAR(255) | | Primary street address |
| address_line2 | VARCHAR(255) | | Secondary address info (suite, floor) |
| city | VARCHAR(100) | | City name |
| state | VARCHAR(100) | | State or province |
| postal_code | VARCHAR(20) | | ZIP or postal code |
| phone | VARCHAR(20) | | Primary contact phone |
| email | VARCHAR(100) | | Store email address |
| square_footage | DECIMAL(10,2) | | Total retail floor space in sq ft |
| opening_date | DATE | | Date store opened for business |
| status | VARCHAR(20) | | Operational status: Active, Closed, Renovation |
| manager_employee_id | INT | FK → dim_employee | Store manager reference |
| latitude | DECIMAL(9,6) | | GPS latitude coordinate |
| longitude | DECIMAL(9,6) | | GPS longitude coordinate |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 3. DIM_CATEGORY
**Purpose**: Product category hierarchy

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| category_id | INT | PK, IDENTITY | Unique category identifier |
| category_code | VARCHAR(20) | UNIQUE, NOT NULL | Business code for category |
| category_name | VARCHAR(100) | NOT NULL | Display name of category |
| parent_category_id | INT | FK → dim_category | Self-reference for hierarchy |
| category_level | INT | | Depth in hierarchy (1=top, 2=sub, 3=leaf) |
| category_path | VARCHAR(500) | | Full path (e.g., 'Electronics > Phones > Smartphones') |
| is_active | BIT | DEFAULT 1 | Whether category is currently active |
| display_order | INT | | Sort order for UI display |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 4. DIM_BRAND
**Purpose**: Product brand master data

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| brand_id | INT | PK, IDENTITY | Unique brand identifier |
| brand_code | VARCHAR(20) | UNIQUE, NOT NULL | Short brand code |
| brand_name | VARCHAR(100) | NOT NULL | Official brand name |
| brand_logo_url | VARCHAR(500) | | URL to brand logo image |
| manufacturer | VARCHAR(200) | | Manufacturing company name |
| country_of_origin | VARCHAR(100) | | Brand's country of origin |
| is_private_label | BIT | DEFAULT 0 | Whether this is a store-owned brand |
| website | VARCHAR(255) | | Brand official website |
| is_active | BIT | DEFAULT 1 | Whether brand is currently active |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 5. DIM_PRODUCT
**Purpose**: Product master data

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| product_id | INT | PK, IDENTITY | Unique product identifier |
| sku | VARCHAR(50) | UNIQUE, NOT NULL | Stock Keeping Unit - internal product code |
| upc | VARCHAR(20) | | Universal Product Code - barcode |
| product_name | VARCHAR(300) | NOT NULL | Full product display name |
| product_description | NVARCHAR(MAX) | | Detailed product description |
| category_id | INT | FK → dim_category | Product category reference |
| brand_id | INT | FK → dim_brand | Product brand reference |
| unit_cost | DECIMAL(12,2) | | Cost to acquire/produce product |
| unit_price | DECIMAL(12,2) | | Standard retail price |
| msrp | DECIMAL(12,2) | | Manufacturer Suggested Retail Price |
| weight | DECIMAL(10,3) | | Product weight |
| weight_unit | VARCHAR(10) | | Weight unit (kg, lb, oz) |
| dimensions | VARCHAR(50) | | LxWxH dimensions |
| color | VARCHAR(50) | | Primary color |
| size | VARCHAR(30) | | Size designation |
| is_perishable | BIT | DEFAULT 0 | Whether product is perishable |
| shelf_life_days | INT | | Days until expiration |
| reorder_level | INT | | Minimum stock before reorder |
| reorder_quantity | INT | | Standard reorder quantity |
| is_active | BIT | DEFAULT 1 | Whether product is currently sold |
| tax_category | VARCHAR(50) | | Tax classification code |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 6. DIM_CUSTOMER
**Purpose**: Customer master data

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| customer_id | BIGINT | PK, IDENTITY | Unique customer identifier |
| customer_code | VARCHAR(30) | UNIQUE | External customer reference code |
| first_name | VARCHAR(100) | | Customer first name |
| last_name | VARCHAR(100) | | Customer last name |
| email | VARCHAR(200) | | Primary email address |
| phone | VARCHAR(20) | | Primary phone number |
| date_of_birth | DATE | | Customer date of birth |
| gender | VARCHAR(20) | | Gender identity |
| address_line1 | VARCHAR(255) | | Primary street address |
| address_line2 | VARCHAR(255) | | Secondary address info |
| city | VARCHAR(100) | | City name |
| state | VARCHAR(100) | | State or province |
| postal_code | VARCHAR(20) | | ZIP or postal code |
| country | VARCHAR(100) | | Country name |
| customer_segment_id | INT | FK → dim_customer_segment | Segment classification |
| loyalty_tier_id | INT | FK → dim_loyalty_tier | Loyalty program tier |
| loyalty_points_balance | INT | DEFAULT 0 | Current loyalty points |
| acquisition_source | VARCHAR(50) | | How customer was acquired |
| acquisition_date | DATE | | Date customer first registered |
| preferred_store_id | INT | FK → dim_store | Customer's preferred store |
| preferred_contact_method | VARCHAR(30) | | Email, Phone, SMS, Mail |
| opt_in_email | BIT | DEFAULT 0 | Email marketing consent |
| opt_in_sms | BIT | DEFAULT 0 | SMS marketing consent |
| is_active | BIT | DEFAULT 1 | Whether customer account is active |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 7. DIM_CUSTOMER_SEGMENT
**Purpose**: Customer segmentation classification

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| segment_id | INT | PK, IDENTITY | Unique segment identifier |
| segment_code | VARCHAR(20) | UNIQUE, NOT NULL | Segment short code |
| segment_name | VARCHAR(100) | NOT NULL | Display name (e.g., 'High Value', 'At Risk') |
| segment_description | VARCHAR(500) | | Detailed segment criteria description |
| min_annual_spend | DECIMAL(12,2) | | Minimum annual spend threshold |
| max_annual_spend | DECIMAL(12,2) | | Maximum annual spend threshold |
| min_purchase_frequency | INT | | Minimum purchases per year |
| is_active | BIT | DEFAULT 1 | Whether segment is currently used |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 8. DIM_LOYALTY_TIER
**Purpose**: Customer loyalty program tiers

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| tier_id | INT | PK, IDENTITY | Unique tier identifier |
| tier_code | VARCHAR(20) | UNIQUE, NOT NULL | Tier short code |
| tier_name | VARCHAR(50) | NOT NULL | Display name (Bronze, Silver, Gold, Platinum) |
| min_points | INT | NOT NULL | Minimum points to qualify |
| max_points | INT | | Maximum points in tier |
| discount_percentage | DECIMAL(5,2) | | Standard tier discount |
| points_multiplier | DECIMAL(3,2) | DEFAULT 1.0 | Points earning multiplier |
| benefits_description | NVARCHAR(MAX) | | Full benefits description |
| is_active | BIT | DEFAULT 1 | Whether tier is currently active |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 9. DIM_EMPLOYEE
**Purpose**: Employee master data

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| employee_id | INT | PK, IDENTITY | Unique employee identifier |
| employee_code | VARCHAR(20) | UNIQUE, NOT NULL | Employee ID badge number |
| first_name | VARCHAR(100) | NOT NULL | Employee first name |
| last_name | VARCHAR(100) | NOT NULL | Employee last name |
| email | VARCHAR(200) | | Work email address |
| phone | VARCHAR(20) | | Contact phone number |
| date_of_birth | DATE | | Employee date of birth |
| gender | VARCHAR(20) | | Gender identity |
| hire_date | DATE | NOT NULL | Employment start date |
| termination_date | DATE | | Employment end date (if applicable) |
| job_title_id | INT | FK → dim_job_title | Current job title |
| department_id | INT | FK → dim_department | Current department |
| store_id | INT | FK → dim_store | Primary work location (store) |
| warehouse_id | INT | FK → dim_warehouse | Primary work location (warehouse) |
| manager_id | INT | FK → dim_employee | Reporting manager (self-ref) |
| employment_type | VARCHAR(30) | | Full-Time, Part-Time, Contract, Seasonal |
| status | VARCHAR(20) | | Active, On Leave, Terminated |
| hourly_rate | DECIMAL(10,2) | | Hourly pay rate |
| salary | DECIMAL(12,2) | | Annual salary |
| commission_rate | DECIMAL(5,2) | | Sales commission percentage |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 10. DIM_DEPARTMENT
**Purpose**: Organizational departments

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| department_id | INT | PK, IDENTITY | Unique department identifier |
| department_code | VARCHAR(20) | UNIQUE, NOT NULL | Department short code |
| department_name | VARCHAR(100) | NOT NULL | Full department name |
| parent_department_id | INT | FK → dim_department | Parent department (self-ref) |
| cost_center_code | VARCHAR(20) | | Associated cost center |
| is_active | BIT | DEFAULT 1 | Whether department is active |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 11. DIM_JOB_TITLE
**Purpose**: Job title definitions

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| job_title_id | INT | PK, IDENTITY | Unique job title identifier |
| title_code | VARCHAR(20) | UNIQUE, NOT NULL | Job code |
| title_name | VARCHAR(100) | NOT NULL | Full job title |
| department_id | INT | FK → dim_department | Associated department |
| job_level | INT | | Organizational level (1-10) |
| min_salary | DECIMAL(12,2) | | Minimum salary for position |
| max_salary | DECIMAL(12,2) | | Maximum salary for position |
| is_management | BIT | DEFAULT 0 | Whether this is a management role |
| requires_commission | BIT | DEFAULT 0 | Whether role earns commission |
| is_active | BIT | DEFAULT 1 | Whether job title is currently used |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 12. DIM_SUPPLIER
**Purpose**: Vendor/supplier master data

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| supplier_id | INT | PK, IDENTITY | Unique supplier identifier |
| supplier_code | VARCHAR(30) | UNIQUE, NOT NULL | External supplier code |
| supplier_name | VARCHAR(200) | NOT NULL | Legal company name |
| contact_name | VARCHAR(100) | | Primary contact person |
| contact_email | VARCHAR(200) | | Contact email address |
| contact_phone | VARCHAR(20) | | Contact phone number |
| address_line1 | VARCHAR(255) | | Primary address |
| address_line2 | VARCHAR(255) | | Secondary address |
| city | VARCHAR(100) | | City name |
| state | VARCHAR(100) | | State or province |
| postal_code | VARCHAR(20) | | ZIP or postal code |
| country | VARCHAR(100) | | Country name |
| payment_terms | VARCHAR(50) | | Payment terms (Net 30, Net 60, etc.) |
| lead_time_days | INT | | Standard delivery lead time |
| minimum_order_value | DECIMAL(12,2) | | Minimum order amount |
| rating | DECIMAL(3,2) | | Supplier performance rating (0-5) |
| tax_id | VARCHAR(50) | | Tax identification number |
| is_active | BIT | DEFAULT 1 | Whether supplier is active |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 13. DIM_WAREHOUSE
**Purpose**: Warehouse/distribution center locations

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| warehouse_id | INT | PK, IDENTITY | Unique warehouse identifier |
| warehouse_code | VARCHAR(20) | UNIQUE, NOT NULL | Warehouse short code |
| warehouse_name | VARCHAR(200) | NOT NULL | Warehouse name |
| region_id | INT | FK → dim_region | Geographic region |
| address_line1 | VARCHAR(255) | | Primary address |
| address_line2 | VARCHAR(255) | | Secondary address |
| city | VARCHAR(100) | | City name |
| state | VARCHAR(100) | | State or province |
| postal_code | VARCHAR(20) | | ZIP or postal code |
| country | VARCHAR(100) | | Country name |
| capacity_sqft | DECIMAL(12,2) | | Total storage capacity in sq ft |
| warehouse_type | VARCHAR(50) | | Distribution, Fulfillment, Cold Storage, Cross-Dock |
| is_active | BIT | DEFAULT 1 | Whether warehouse is operational |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 14. DIM_PAYMENT_METHOD
**Purpose**: Payment method reference

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| payment_method_id | INT | PK, IDENTITY | Unique payment method identifier |
| method_code | VARCHAR(20) | UNIQUE, NOT NULL | Method short code |
| method_name | VARCHAR(50) | NOT NULL | Display name (Cash, Visa, PayPal, etc.) |
| method_type | VARCHAR(30) | | Category: Cash, Credit, Debit, Digital, GiftCard |
| processing_fee_pct | DECIMAL(5,3) | | Transaction fee percentage |
| is_active | BIT | DEFAULT 1 | Whether method is accepted |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 15. DIM_PROMOTION
**Purpose**: Promotion and discount definitions

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| promotion_id | INT | PK, IDENTITY | Unique promotion identifier |
| promotion_code | VARCHAR(30) | UNIQUE, NOT NULL | Promo code for redemption |
| promotion_name | VARCHAR(200) | NOT NULL | Promotional offer name |
| promotion_type | VARCHAR(50) | | Percentage, FixedAmount, BOGO, Bundle, FreeShipping |
| discount_value | DECIMAL(10,2) | | Discount amount or percentage |
| min_purchase_amount | DECIMAL(10,2) | | Minimum purchase to qualify |
| max_discount_amount | DECIMAL(10,2) | | Maximum discount cap |
| start_date | DATE | NOT NULL | Promotion start date |
| end_date | DATE | NOT NULL | Promotion end date |
| is_stackable | BIT | DEFAULT 0 | Whether combinable with other promos |
| usage_limit | INT | | Maximum total uses allowed |
| usage_per_customer | INT | | Maximum uses per customer |
| usage_count | INT | DEFAULT 0 | Current usage count |
| applicable_channel | VARCHAR(50) | | All, Online, InStore |
| is_active | BIT | DEFAULT 1 | Whether promotion is active |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 16. DIM_REGISTER
**Purpose**: Point of sale terminal reference

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| register_id | INT | PK, IDENTITY | Unique register identifier |
| register_code | VARCHAR(20) | UNIQUE, NOT NULL | Register identifier code |
| store_id | INT | FK → dim_store, NOT NULL | Store where register is located |
| register_type | VARCHAR(30) | | POS, Self-Checkout, Mobile, Kiosk |
| hardware_model | VARCHAR(100) | | Hardware model information |
| ip_address | VARCHAR(50) | | Network IP address |
| status | VARCHAR(20) | | Active, Inactive, Maintenance |
| install_date | DATE | | Installation date |
| last_maintenance_date | DATE | | Last maintenance date |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 17. DIM_SHIPPING_METHOD
**Purpose**: Shipping/delivery method reference

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| shipping_method_id | INT | PK, IDENTITY | Unique shipping method identifier |
| method_code | VARCHAR(20) | UNIQUE, NOT NULL | Shipping method code |
| method_name | VARCHAR(100) | NOT NULL | Display name (Standard, Express, Same Day) |
| carrier | VARCHAR(100) | | Carrier name (UPS, FedEx, USPS) |
| estimated_days_min | INT | | Minimum delivery days |
| estimated_days_max | INT | | Maximum delivery days |
| base_cost | DECIMAL(10,2) | | Base shipping cost |
| cost_per_pound | DECIMAL(8,4) | | Additional cost per pound |
| is_active | BIT | DEFAULT 1 | Whether method is available |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 18. DIM_RETURN_REASON
**Purpose**: Product return reason codes

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| reason_id | INT | PK, IDENTITY | Unique reason identifier |
| reason_code | VARCHAR(20) | UNIQUE, NOT NULL | Reason short code |
| reason_description | VARCHAR(200) | NOT NULL | Full reason description |
| reason_category | VARCHAR(50) | | Category: Quality, Fit, Changed Mind, Defective |
| is_defect | BIT | DEFAULT 0 | Whether this indicates product defect |
| restocking_fee_pct | DECIMAL(5,2) | | Applicable restocking fee percentage |
| is_active | BIT | DEFAULT 1 | Whether reason is currently used |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 19. FACT_SALES_TRANSACTION
**Purpose**: Point of sale transaction headers

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| transaction_id | BIGINT | PK, IDENTITY | Unique transaction identifier |
| transaction_number | VARCHAR(50) | UNIQUE, NOT NULL | Receipt/transaction number |
| store_id | INT | FK → dim_store, NOT NULL | Store where transaction occurred |
| register_id | INT | FK → dim_register | POS terminal used |
| customer_id | BIGINT | FK → dim_customer | Customer (if identified) |
| employee_id | INT | FK → dim_employee | Cashier/associate |
| transaction_date | DATETIME | NOT NULL | Transaction timestamp |
| transaction_type | VARCHAR(20) | | Sale, Return, Exchange, Void |
| subtotal | DECIMAL(12,2) | | Total before tax and discounts |
| discount_amount | DECIMAL(12,2) | DEFAULT 0 | Total discounts applied |
| tax_amount | DECIMAL(12,2) | | Total tax amount |
| total_amount | DECIMAL(12,2) | | Final transaction total |
| payment_method_id | INT | FK → dim_payment_method | Primary payment method |
| promotion_id | INT | FK → dim_promotion | Applied promotion |
| loyalty_points_used | INT | DEFAULT 0 | Points redeemed |
| loyalty_points_earned | INT | DEFAULT 0 | Points earned from purchase |
| is_void | BIT | DEFAULT 0 | Whether transaction was voided |
| void_reason | VARCHAR(200) | | Reason for void |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 20. FACT_SALES_LINE_ITEM
**Purpose**: Individual items within transactions

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| line_item_id | BIGINT | PK, IDENTITY | Unique line item identifier |
| transaction_id | BIGINT | FK → fact_sales_transaction, NOT NULL | Parent transaction |
| product_id | INT | FK → dim_product, NOT NULL | Product sold |
| line_number | INT | | Line sequence number |
| quantity | INT | NOT NULL | Quantity sold |
| unit_price | DECIMAL(12,2) | | Price per unit |
| unit_cost | DECIMAL(12,2) | | Cost per unit |
| discount_amount | DECIMAL(12,2) | DEFAULT 0 | Line item discount |
| tax_amount | DECIMAL(12,2) | | Line item tax |
| line_total | DECIMAL(12,2) | | Final line total |
| promotion_id | INT | FK → dim_promotion | Line-level promotion |
| is_return | BIT | DEFAULT 0 | Whether this is a return item |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 21. FACT_INVENTORY
**Purpose**: Current inventory snapshot by location

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| inventory_id | BIGINT | PK, IDENTITY | Unique inventory record identifier |
| product_id | INT | FK → dim_product, NOT NULL | Product reference |
| store_id | INT | FK → dim_store | Store location (if store inventory) |
| warehouse_id | INT | FK → dim_warehouse | Warehouse location (if warehouse inventory) |
| quantity_on_hand | INT | | Physical quantity in stock |
| quantity_reserved | INT | DEFAULT 0 | Quantity allocated to orders |
| quantity_available | INT | | Quantity available for sale (computed) |
| quantity_on_order | INT | DEFAULT 0 | Quantity in pending POs |
| last_restock_date | DATE | | Last inventory receipt date |
| last_sold_date | DATE | | Last sale date |
| last_count_date | DATE | | Last physical count date |
| snapshot_date | DATE | NOT NULL | Date of this inventory record |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 22. FACT_PURCHASE_ORDER
**Purpose**: Supplier purchase order headers

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| po_id | BIGINT | PK, IDENTITY | Unique purchase order identifier |
| po_number | VARCHAR(50) | UNIQUE, NOT NULL | Purchase order number |
| supplier_id | INT | FK → dim_supplier, NOT NULL | Supplier reference |
| warehouse_id | INT | FK → dim_warehouse | Receiving warehouse |
| order_date | DATE | NOT NULL | Order placement date |
| expected_delivery_date | DATE | | Anticipated delivery date |
| actual_delivery_date | DATE | | Actual delivery date |
| status | VARCHAR(30) | | Draft, Submitted, Approved, Shipped, Received, Closed, Cancelled |
| subtotal | DECIMAL(14,2) | | Total before tax/shipping |
| tax_amount | DECIMAL(12,2) | | Tax amount |
| shipping_cost | DECIMAL(10,2) | | Shipping charges |
| total_amount | DECIMAL(14,2) | | Final PO total |
| created_by | INT | FK → dim_employee | Employee who created |
| approved_by | INT | FK → dim_employee | Approving manager |
| approved_date | DATE | | Approval date |
| notes | NVARCHAR(MAX) | | Order notes |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 23. FACT_PURCHASE_ORDER_LINE
**Purpose**: Individual items within purchase orders

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| po_line_id | BIGINT | PK, IDENTITY | Unique PO line identifier |
| po_id | BIGINT | FK → fact_purchase_order, NOT NULL | Parent purchase order |
| product_id | INT | FK → dim_product, NOT NULL | Product ordered |
| line_number | INT | | Line sequence number |
| quantity_ordered | INT | NOT NULL | Quantity ordered |
| quantity_received | INT | DEFAULT 0 | Quantity received |
| quantity_rejected | INT | DEFAULT 0 | Quantity rejected/damaged |
| unit_cost | DECIMAL(12,2) | | Cost per unit |
| line_total | DECIMAL(14,2) | | Total line cost |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 24. FACT_ORDER
**Purpose**: Customer order headers (e-commerce and phone)

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| order_id | BIGINT | PK, IDENTITY | Unique order identifier |
| order_number | VARCHAR(50) | UNIQUE, NOT NULL | Customer-facing order number |
| customer_id | BIGINT | FK → dim_customer, NOT NULL | Customer placing order |
| order_date | DATETIME | NOT NULL | Order placement timestamp |
| order_source | VARCHAR(30) | | Web, Mobile, Phone, InStore |
| order_status | VARCHAR(30) | | Pending, Confirmed, Processing, Shipped, Delivered, Cancelled |
| shipping_address_line1 | VARCHAR(255) | | Shipping street address |
| shipping_address_line2 | VARCHAR(255) | | Shipping address line 2 |
| shipping_city | VARCHAR(100) | | Shipping city |
| shipping_state | VARCHAR(100) | | Shipping state |
| shipping_postal_code | VARCHAR(20) | | Shipping ZIP |
| shipping_country | VARCHAR(100) | | Shipping country |
| billing_address_line1 | VARCHAR(255) | | Billing street address |
| billing_city | VARCHAR(100) | | Billing city |
| billing_state | VARCHAR(100) | | Billing state |
| billing_postal_code | VARCHAR(20) | | Billing ZIP |
| subtotal | DECIMAL(12,2) | | Order subtotal |
| shipping_cost | DECIMAL(10,2) | | Shipping charges |
| discount_amount | DECIMAL(12,2) | DEFAULT 0 | Total discounts |
| tax_amount | DECIMAL(12,2) | | Tax amount |
| total_amount | DECIMAL(12,2) | | Final order total |
| shipping_method_id | INT | FK → dim_shipping_method | Selected shipping method |
| promotion_id | INT | FK → dim_promotion | Applied promotion |
| estimated_delivery_date | DATE | | Expected delivery date |
| actual_delivery_date | DATE | | Actual delivery date |
| fulfillment_store_id | INT | FK → dim_store | Fulfilling store (if ship from store) |
| fulfillment_warehouse_id | INT | FK → dim_warehouse | Fulfilling warehouse |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |
| updated_at | DATETIME | | Last modification timestamp |

---

### 25. FACT_ORDER_LINE
**Purpose**: Individual items within customer orders

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| order_line_id | BIGINT | PK, IDENTITY | Unique order line identifier |
| order_id | BIGINT | FK → fact_order, NOT NULL | Parent order |
| product_id | INT | FK → dim_product, NOT NULL | Product ordered |
| line_number | INT | | Line sequence number |
| quantity_ordered | INT | NOT NULL | Quantity ordered |
| quantity_shipped | INT | DEFAULT 0 | Quantity shipped |
| quantity_cancelled | INT | DEFAULT 0 | Quantity cancelled |
| unit_price | DECIMAL(12,2) | | Price per unit |
| discount_amount | DECIMAL(12,2) | DEFAULT 0 | Line discount |
| tax_amount | DECIMAL(12,2) | | Line tax |
| line_total | DECIMAL(12,2) | | Final line total |
| line_status | VARCHAR(30) | | Pending, Shipped, Delivered, Cancelled |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 26. FACT_RETURN
**Purpose**: Customer return transactions

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| return_id | BIGINT | PK, IDENTITY | Unique return identifier |
| return_number | VARCHAR(50) | UNIQUE, NOT NULL | Return reference number |
| original_transaction_id | BIGINT | FK → fact_sales_transaction | Original POS transaction |
| original_order_id | BIGINT | FK → fact_order | Original online order |
| customer_id | BIGINT | FK → dim_customer | Returning customer |
| store_id | INT | FK → dim_store | Return processing store |
| employee_id | INT | FK → dim_employee | Processing employee |
| return_date | DATETIME | NOT NULL | Return timestamp |
| return_reason_id | INT | FK → dim_return_reason | Reason for return |
| return_type | VARCHAR(30) | | Refund, Exchange, StoreCredit |
| product_id | INT | FK → dim_product | Returned product |
| quantity | INT | | Quantity returned |
| refund_amount | DECIMAL(12,2) | | Refund amount |
| restocking_fee | DECIMAL(10,2) | DEFAULT 0 | Restocking fee charged |
| product_condition | VARCHAR(30) | | New, OpenBox, Damaged, Defective |
| disposition | VARCHAR(30) | | Restock, Damage, Dispose, ReturnToVendor |
| status | VARCHAR(30) | | Pending, Approved, Processed, Denied |
| notes | NVARCHAR(MAX) | | Return notes |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 27. FACT_EMPLOYEE_SCHEDULE
**Purpose**: Employee work schedules

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| schedule_id | BIGINT | PK, IDENTITY | Unique schedule record identifier |
| employee_id | INT | FK → dim_employee, NOT NULL | Employee reference |
| store_id | INT | FK → dim_store | Scheduled store |
| warehouse_id | INT | FK → dim_warehouse | Scheduled warehouse |
| schedule_date | DATE | NOT NULL | Scheduled work date |
| shift_start | TIME | | Shift start time |
| shift_end | TIME | | Shift end time |
| scheduled_hours | DECIMAL(5,2) | | Total scheduled hours |
| break_minutes | INT | | Scheduled break time |
| position | VARCHAR(50) | | Role for this shift |
| is_overtime | BIT | DEFAULT 0 | Whether shift is overtime |
| status | VARCHAR(20) | | Scheduled, Confirmed, Completed, Absent |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

### 28. FACT_DAILY_SALES_SUMMARY
**Purpose**: Aggregated daily sales metrics by store

| Column Name | Data Type | Constraints | Definition |
|-------------|-----------|-------------|------------|
| summary_id | BIGINT | PK, IDENTITY | Unique summary record identifier |
| store_id | INT | FK → dim_store, NOT NULL | Store reference |
| business_date | DATE | NOT NULL | Business date |
| total_transactions | INT | | Number of transactions |
| total_customers | INT | | Unique customers served |
| total_units_sold | INT | | Total units sold |
| gross_sales | DECIMAL(14,2) | | Gross sales amount |
| total_discounts | DECIMAL(12,2) | | Total discounts given |
| total_returns | DECIMAL(12,2) | | Total returns amount |
| net_sales | DECIMAL(14,2) | | Net sales (gross - discounts - returns) |
| total_tax | DECIMAL(12,2) | | Total tax collected |
| average_basket_size | DECIMAL(10,2) | | Average transaction value |
| average_items_per_transaction | DECIMAL(6,2) | | Average items per transaction |
| labor_hours | DECIMAL(8,2) | | Total labor hours |
| labor_cost | DECIMAL(12,2) | | Total labor cost |
| created_at | DATETIME | DEFAULT GETDATE() | Record creation timestamp |

---

## BLOB STORAGE TABLES

### 29. RAW_CUSTOMER_FEEDBACK (Azure Blob - JSON/CSV)
**Purpose**: Unstructured customer feedback data

| Column Name | Data Type | Definition |
|-------------|-----------|------------|
| feedback_id | STRING | Unique feedback identifier |
| customer_id | STRING | Customer reference (may not exist in dim_customer) |
| store_id | STRING | Store reference |
| order_id | STRING | Related order (if applicable) |
| feedback_date | STRING | Feedback submission date (various formats) |
| channel | STRING | Survey, Review, Social, Email, Phone |
| rating | STRING | Rating value (1-5 or 1-10 or text) |
| nps_score | STRING | Net Promoter Score |
| feedback_text | STRING | Raw feedback text |
| sentiment | STRING | Positive, Negative, Neutral, Mixed |
| topics | STRING | Detected topics (comma-separated) |
| source_file | STRING | Original source file name |
| ingestion_timestamp | STRING | When data was loaded |

---

### 30. RAW_PRODUCT_IMAGES (Azure Blob - JSON)
**Purpose**: Product image metadata and blob paths

| Column Name | Data Type | Definition |
|-------------|-----------|------------|
| image_id | STRING | Unique image identifier |
| product_id | STRING | Product reference |
| sku | STRING | Product SKU |
| image_type | STRING | Primary, Alternate, Lifestyle, Detail |
| image_url | STRING | Full blob storage URL |
| blob_path | STRING | Internal blob path |
| file_name | STRING | Original file name |
| file_size_bytes | STRING | File size |
| width_pixels | STRING | Image width |
| height_pixels | STRING | Image height |
| format | STRING | jpg, png, webp |
| alt_text | STRING | Accessibility text |
| display_order | STRING | Sort order for display |
| uploaded_date | STRING | Upload timestamp |
| uploaded_by | STRING | Uploading user/system |
| is_active | STRING | Whether image is active |

---

## RELATIONSHIP DIAGRAM

```
                                    ┌─────────────────┐
                                    │   dim_region    │
                                    └────────┬────────┘
                          ┌─────────────────┼─────────────────┐
                          ▼                 ▼                 ▼
                   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
                   │  dim_store  │   │dim_warehouse│   │             │
                   └──────┬──────┘   └──────┬──────┘   │             │
                          │                 │          │             │
         ┌────────────────┼─────────────────┼──────────┤             │
         ▼                ▼                 ▼          │             │
  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │             │
  │dim_register │  │dim_employee │  │fact_inventory│   │             │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │             │
         │                │                 │          │             │
         │                │                 │          │             │
         ▼                ▼                 ▼          │             │
  ┌─────────────────────────────────────────────┐      │             │
  │          fact_sales_transaction             │◄─────┘             │
  └─────────────────────┬───────────────────────┘                    │
                        │                                            │
                        ▼                                            │
              ┌─────────────────────┐                                │
              │ fact_sales_line_item│                                │
              └─────────┬───────────┘                                │
                        │                                            │
                        ▼                                            │
              ┌─────────────────────┐    ┌─────────────┐             │
              │    dim_product      │◄───│dim_category │             │
              └─────────┬───────────┘    └─────────────┘             │
                        │                                            │
                        │                ┌─────────────┐             │
                        └───────────────►│  dim_brand  │             │
                                         └─────────────┘             │
                                                                     │
  ┌─────────────────┐    ┌─────────────────┐                         │
  │  dim_customer   │◄───│dim_customer_seg │                         │
  └────────┬────────┘    └─────────────────┘                         │
           │             ┌─────────────────┐                         │
           └────────────►│dim_loyalty_tier │                         │
           │             └─────────────────┘                         │
           ▼                                                         │
    ┌─────────────┐                                                  │
    │ fact_order  │──────────────────────────────────────────────────┘
    └──────┬──────┘
           │
           ▼
   ┌───────────────┐        ┌─────────────────┐
   │fact_order_line│        │  dim_supplier   │
   └───────────────┘        └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────────┐
                            │ fact_purchase_order │
                            └─────────┬───────────┘
                                      │
                                      ▼
                           ┌────────────────────────┐
                           │fact_purchase_order_line│
                           └────────────────────────┘
```

---

## DATA QUALITY ISSUES (Non AI-Ready)

This dataset intentionally contains the following data quality issues to simulate real enterprise data:

### 1. Missing Values
- Customer emails and phone numbers with NULL values
- Products missing category assignments
- Employees without manager assignments

### 2. Inconsistent Formats
- Date formats: 'YYYY-MM-DD', 'MM/DD/YYYY', 'DD-Mon-YYYY'
- Phone formats: '(555) 123-4567', '555-123-4567', '5551234567', '+1-555-123-4567'
- Names: Mixed case, ALL CAPS, all lowercase

### 3. Duplicate Records
- Customers with slightly different names but same email
- Products with duplicate SKUs in different formats

### 4. Invalid Values
- Negative quantities in some inventory records
- Future dates in historical transactions
- Invalid email formats

### 5. Referential Integrity Issues
- Orders referencing non-existent customers
- Transactions with invalid store IDs

### 6. Data Type Inconsistencies
- Numeric values stored as strings
- Boolean values as 'Y/N', '1/0', 'true/false', 'Yes/No'

### 7. Outliers
- Extremely high transaction amounts
- Zero prices on some products

### 8. Encoding Issues
- Special characters in names and addresses
- Mixed encodings in text fields

---

## VERSION HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-19 | Data Engineering Team | Initial schema design |

