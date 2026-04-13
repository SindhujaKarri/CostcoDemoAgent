-- =====================================================
-- RETAIL ENTERPRISE DATA - AZURE SQL DDL SCRIPT
-- Database: RetailEnterpriseDB
-- Version: 1.0
-- Generated: January 2026
-- =====================================================

-- Create Database (run separately with appropriate permissions)
-- CREATE DATABASE RetailEnterpriseDB;
-- GO

USE RetailEnterpriseDB;
GO

-- =====================================================
-- SCHEMA: Create schemas for organization
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
    EXEC('CREATE SCHEMA dbo');
GO

-- =====================================================
-- DROP EXISTING TABLES (if recreating)
-- =====================================================
-- Drop fact tables first (due to FK dependencies)
IF OBJECT_ID('dbo.fact_daily_sales_summary', 'U') IS NOT NULL DROP TABLE dbo.fact_daily_sales_summary;
IF OBJECT_ID('dbo.fact_employee_schedule', 'U') IS NOT NULL DROP TABLE dbo.fact_employee_schedule;
IF OBJECT_ID('dbo.fact_return', 'U') IS NOT NULL DROP TABLE dbo.fact_return;
IF OBJECT_ID('dbo.fact_order_line', 'U') IS NOT NULL DROP TABLE dbo.fact_order_line;
IF OBJECT_ID('dbo.fact_order', 'U') IS NOT NULL DROP TABLE dbo.fact_order;
IF OBJECT_ID('dbo.fact_purchase_order_line', 'U') IS NOT NULL DROP TABLE dbo.fact_purchase_order_line;
IF OBJECT_ID('dbo.fact_purchase_order', 'U') IS NOT NULL DROP TABLE dbo.fact_purchase_order;
IF OBJECT_ID('dbo.fact_inventory', 'U') IS NOT NULL DROP TABLE dbo.fact_inventory;
IF OBJECT_ID('dbo.fact_sales_line_item', 'U') IS NOT NULL DROP TABLE dbo.fact_sales_line_item;
IF OBJECT_ID('dbo.fact_sales_transaction', 'U') IS NOT NULL DROP TABLE dbo.fact_sales_transaction;

-- Drop dimension tables
IF OBJECT_ID('dbo.dim_return_reason', 'U') IS NOT NULL DROP TABLE dbo.dim_return_reason;
IF OBJECT_ID('dbo.dim_shipping_method', 'U') IS NOT NULL DROP TABLE dbo.dim_shipping_method;
IF OBJECT_ID('dbo.dim_register', 'U') IS NOT NULL DROP TABLE dbo.dim_register;
IF OBJECT_ID('dbo.dim_promotion', 'U') IS NOT NULL DROP TABLE dbo.dim_promotion;
IF OBJECT_ID('dbo.dim_payment_method', 'U') IS NOT NULL DROP TABLE dbo.dim_payment_method;
IF OBJECT_ID('dbo.dim_warehouse', 'U') IS NOT NULL DROP TABLE dbo.dim_warehouse;
IF OBJECT_ID('dbo.dim_supplier', 'U') IS NOT NULL DROP TABLE dbo.dim_supplier;
IF OBJECT_ID('dbo.dim_employee', 'U') IS NOT NULL DROP TABLE dbo.dim_employee;
IF OBJECT_ID('dbo.dim_job_title', 'U') IS NOT NULL DROP TABLE dbo.dim_job_title;
IF OBJECT_ID('dbo.dim_department', 'U') IS NOT NULL DROP TABLE dbo.dim_department;
IF OBJECT_ID('dbo.dim_customer', 'U') IS NOT NULL DROP TABLE dbo.dim_customer;
IF OBJECT_ID('dbo.dim_loyalty_tier', 'U') IS NOT NULL DROP TABLE dbo.dim_loyalty_tier;
IF OBJECT_ID('dbo.dim_customer_segment', 'U') IS NOT NULL DROP TABLE dbo.dim_customer_segment;
IF OBJECT_ID('dbo.dim_product', 'U') IS NOT NULL DROP TABLE dbo.dim_product;
IF OBJECT_ID('dbo.dim_brand', 'U') IS NOT NULL DROP TABLE dbo.dim_brand;
IF OBJECT_ID('dbo.dim_category', 'U') IS NOT NULL DROP TABLE dbo.dim_category;
IF OBJECT_ID('dbo.dim_store', 'U') IS NOT NULL DROP TABLE dbo.dim_store;
IF OBJECT_ID('dbo.dim_region', 'U') IS NOT NULL DROP TABLE dbo.dim_region;
GO

-- =====================================================
-- DIMENSION TABLES
-- =====================================================

-- 1. DIM_REGION
CREATE TABLE dbo.dim_region (
    region_id INT IDENTITY(1,1) PRIMARY KEY,
    region_code VARCHAR(10) NOT NULL,
    region_name VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    timezone VARCHAR(50),
    currency_code VARCHAR(3),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_region_code UNIQUE (region_code)
);
GO

-- 2. DIM_STORE
CREATE TABLE dbo.dim_store (
    store_id INT IDENTITY(1,1) PRIMARY KEY,
    store_code VARCHAR(20) NOT NULL,
    store_name VARCHAR(200) NOT NULL,
    region_id INT,
    store_type VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(100),
    square_footage DECIMAL(10,2),
    opening_date DATE,
    status VARCHAR(20) DEFAULT 'Active',
    manager_employee_id INT,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_store_code UNIQUE (store_code),
    CONSTRAINT fk_store_region FOREIGN KEY (region_id) REFERENCES dbo.dim_region(region_id)
);
GO

-- 3. DIM_CATEGORY
CREATE TABLE dbo.dim_category (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    category_code VARCHAR(20) NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    parent_category_id INT,
    category_level INT,
    category_path VARCHAR(500),
    is_active BIT DEFAULT 1,
    display_order INT,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_category_code UNIQUE (category_code),
    CONSTRAINT fk_category_parent FOREIGN KEY (parent_category_id) REFERENCES dbo.dim_category(category_id)
);
GO

-- 4. DIM_BRAND
CREATE TABLE dbo.dim_brand (
    brand_id INT IDENTITY(1,1) PRIMARY KEY,
    brand_code VARCHAR(20) NOT NULL,
    brand_name VARCHAR(100) NOT NULL,
    brand_logo_url VARCHAR(500),
    manufacturer VARCHAR(200),
    country_of_origin VARCHAR(100),
    is_private_label BIT DEFAULT 0,
    website VARCHAR(255),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_brand_code UNIQUE (brand_code)
);
GO

-- 5. DIM_PRODUCT
CREATE TABLE dbo.dim_product (
    product_id INT IDENTITY(1,1) PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    upc VARCHAR(20),
    product_name VARCHAR(300) NOT NULL,
    product_description NVARCHAR(MAX),
    category_id INT,
    brand_id INT,
    unit_cost DECIMAL(12,2),
    unit_price DECIMAL(12,2),
    msrp DECIMAL(12,2),
    weight DECIMAL(10,3),
    weight_unit VARCHAR(10),
    dimensions VARCHAR(50),
    color VARCHAR(50),
    size VARCHAR(30),
    is_perishable BIT DEFAULT 0,
    shelf_life_days INT,
    reorder_level INT,
    reorder_quantity INT,
    is_active BIT DEFAULT 1,
    tax_category VARCHAR(50),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_product_sku UNIQUE (sku),
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES dbo.dim_category(category_id),
    CONSTRAINT fk_product_brand FOREIGN KEY (brand_id) REFERENCES dbo.dim_brand(brand_id)
);
GO

-- 6. DIM_CUSTOMER_SEGMENT
CREATE TABLE dbo.dim_customer_segment (
    segment_id INT IDENTITY(1,1) PRIMARY KEY,
    segment_code VARCHAR(20) NOT NULL,
    segment_name VARCHAR(100) NOT NULL,
    segment_description VARCHAR(500),
    min_annual_spend DECIMAL(12,2),
    max_annual_spend DECIMAL(12,2),
    min_purchase_frequency INT,
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_segment_code UNIQUE (segment_code)
);
GO

-- 7. DIM_LOYALTY_TIER
CREATE TABLE dbo.dim_loyalty_tier (
    tier_id INT IDENTITY(1,1) PRIMARY KEY,
    tier_code VARCHAR(20) NOT NULL,
    tier_name VARCHAR(50) NOT NULL,
    min_points INT NOT NULL,
    max_points INT,
    discount_percentage DECIMAL(5,2),
    points_multiplier DECIMAL(3,2) DEFAULT 1.0,
    benefits_description NVARCHAR(MAX),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_tier_code UNIQUE (tier_code)
);
GO

-- 8. DIM_CUSTOMER
CREATE TABLE dbo.dim_customer (
    customer_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    customer_code VARCHAR(30),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(20),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    customer_segment_id INT,
    loyalty_tier_id INT,
    loyalty_points_balance INT DEFAULT 0,
    acquisition_source VARCHAR(50),
    acquisition_date DATE,
    preferred_store_id INT,
    preferred_contact_method VARCHAR(30),
    opt_in_email BIT DEFAULT 0,
    opt_in_sms BIT DEFAULT 0,
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_customer_code UNIQUE (customer_code),
    CONSTRAINT fk_customer_segment FOREIGN KEY (customer_segment_id) REFERENCES dbo.dim_customer_segment(segment_id),
    CONSTRAINT fk_customer_tier FOREIGN KEY (loyalty_tier_id) REFERENCES dbo.dim_loyalty_tier(tier_id),
    CONSTRAINT fk_customer_store FOREIGN KEY (preferred_store_id) REFERENCES dbo.dim_store(store_id)
);
GO

-- 9. DIM_DEPARTMENT
CREATE TABLE dbo.dim_department (
    department_id INT IDENTITY(1,1) PRIMARY KEY,
    department_code VARCHAR(20) NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    parent_department_id INT,
    cost_center_code VARCHAR(20),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_department_code UNIQUE (department_code),
    CONSTRAINT fk_department_parent FOREIGN KEY (parent_department_id) REFERENCES dbo.dim_department(department_id)
);
GO

-- 10. DIM_JOB_TITLE
CREATE TABLE dbo.dim_job_title (
    job_title_id INT IDENTITY(1,1) PRIMARY KEY,
    title_code VARCHAR(20) NOT NULL,
    title_name VARCHAR(100) NOT NULL,
    department_id INT,
    job_level INT,
    min_salary DECIMAL(12,2),
    max_salary DECIMAL(12,2),
    is_management BIT DEFAULT 0,
    requires_commission BIT DEFAULT 0,
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_title_code UNIQUE (title_code),
    CONSTRAINT fk_title_department FOREIGN KEY (department_id) REFERENCES dbo.dim_department(department_id)
);
GO

-- 11. DIM_EMPLOYEE
CREATE TABLE dbo.dim_employee (
    employee_id INT IDENTITY(1,1) PRIMARY KEY,
    employee_code VARCHAR(20) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(200),
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(20),
    hire_date DATE NOT NULL,
    termination_date DATE,
    job_title_id INT,
    department_id INT,
    store_id INT,
    warehouse_id INT,
    manager_id INT,
    employment_type VARCHAR(30),
    status VARCHAR(20) DEFAULT 'Active',
    hourly_rate DECIMAL(10,2),
    salary DECIMAL(12,2),
    commission_rate DECIMAL(5,2),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_employee_code UNIQUE (employee_code),
    CONSTRAINT fk_employee_title FOREIGN KEY (job_title_id) REFERENCES dbo.dim_job_title(job_title_id),
    CONSTRAINT fk_employee_department FOREIGN KEY (department_id) REFERENCES dbo.dim_department(department_id),
    CONSTRAINT fk_employee_store FOREIGN KEY (store_id) REFERENCES dbo.dim_store(store_id),
    CONSTRAINT fk_employee_manager FOREIGN KEY (manager_id) REFERENCES dbo.dim_employee(employee_id)
);
GO

-- Add manager FK to store (after employee table exists)
ALTER TABLE dbo.dim_store ADD CONSTRAINT fk_store_manager 
    FOREIGN KEY (manager_employee_id) REFERENCES dbo.dim_employee(employee_id);
GO

-- 12. DIM_SUPPLIER
CREATE TABLE dbo.dim_supplier (
    supplier_id INT IDENTITY(1,1) PRIMARY KEY,
    supplier_code VARCHAR(30) NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(100),
    contact_email VARCHAR(200),
    contact_phone VARCHAR(20),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    payment_terms VARCHAR(50),
    lead_time_days INT,
    minimum_order_value DECIMAL(12,2),
    rating DECIMAL(3,2),
    tax_id VARCHAR(50),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_supplier_code UNIQUE (supplier_code)
);
GO

-- 13. DIM_WAREHOUSE
CREATE TABLE dbo.dim_warehouse (
    warehouse_id INT IDENTITY(1,1) PRIMARY KEY,
    warehouse_code VARCHAR(20) NOT NULL,
    warehouse_name VARCHAR(200) NOT NULL,
    region_id INT,
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    capacity_sqft DECIMAL(12,2),
    warehouse_type VARCHAR(50),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_warehouse_code UNIQUE (warehouse_code),
    CONSTRAINT fk_warehouse_region FOREIGN KEY (region_id) REFERENCES dbo.dim_region(region_id)
);
GO

-- Add warehouse FK to employee
ALTER TABLE dbo.dim_employee ADD CONSTRAINT fk_employee_warehouse 
    FOREIGN KEY (warehouse_id) REFERENCES dbo.dim_warehouse(warehouse_id);
GO

-- 14. DIM_PAYMENT_METHOD
CREATE TABLE dbo.dim_payment_method (
    payment_method_id INT IDENTITY(1,1) PRIMARY KEY,
    method_code VARCHAR(20) NOT NULL,
    method_name VARCHAR(50) NOT NULL,
    method_type VARCHAR(30),
    processing_fee_pct DECIMAL(5,3),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_payment_method_code UNIQUE (method_code)
);
GO

-- 15. DIM_PROMOTION
CREATE TABLE dbo.dim_promotion (
    promotion_id INT IDENTITY(1,1) PRIMARY KEY,
    promotion_code VARCHAR(30) NOT NULL,
    promotion_name VARCHAR(200) NOT NULL,
    promotion_type VARCHAR(50),
    discount_value DECIMAL(10,2),
    min_purchase_amount DECIMAL(10,2),
    max_discount_amount DECIMAL(10,2),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_stackable BIT DEFAULT 0,
    usage_limit INT,
    usage_per_customer INT,
    usage_count INT DEFAULT 0,
    applicable_channel VARCHAR(50),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_promotion_code UNIQUE (promotion_code)
);
GO

-- 16. DIM_REGISTER
CREATE TABLE dbo.dim_register (
    register_id INT IDENTITY(1,1) PRIMARY KEY,
    register_code VARCHAR(20) NOT NULL,
    store_id INT NOT NULL,
    register_type VARCHAR(30),
    hardware_model VARCHAR(100),
    ip_address VARCHAR(50),
    status VARCHAR(20) DEFAULT 'Active',
    install_date DATE,
    last_maintenance_date DATE,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_register_code UNIQUE (register_code),
    CONSTRAINT fk_register_store FOREIGN KEY (store_id) REFERENCES dbo.dim_store(store_id)
);
GO

-- 17. DIM_SHIPPING_METHOD
CREATE TABLE dbo.dim_shipping_method (
    shipping_method_id INT IDENTITY(1,1) PRIMARY KEY,
    method_code VARCHAR(20) NOT NULL,
    method_name VARCHAR(100) NOT NULL,
    carrier VARCHAR(100),
    estimated_days_min INT,
    estimated_days_max INT,
    base_cost DECIMAL(10,2),
    cost_per_pound DECIMAL(8,4),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_shipping_method_code UNIQUE (method_code)
);
GO

-- 18. DIM_RETURN_REASON
CREATE TABLE dbo.dim_return_reason (
    reason_id INT IDENTITY(1,1) PRIMARY KEY,
    reason_code VARCHAR(20) NOT NULL,
    reason_description VARCHAR(200) NOT NULL,
    reason_category VARCHAR(50),
    is_defect BIT DEFAULT 0,
    restocking_fee_pct DECIMAL(5,2),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_return_reason_code UNIQUE (reason_code)
);
GO

-- =====================================================
-- FACT TABLES
-- =====================================================

-- 19. FACT_SALES_TRANSACTION
CREATE TABLE dbo.fact_sales_transaction (
    transaction_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    transaction_number VARCHAR(50) NOT NULL,
    store_id INT NOT NULL,
    register_id INT,
    customer_id BIGINT,
    employee_id INT,
    transaction_date DATETIME NOT NULL,
    transaction_type VARCHAR(20),
    subtotal DECIMAL(12,2),
    discount_amount DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    payment_method_id INT,
    promotion_id INT,
    loyalty_points_used INT DEFAULT 0,
    loyalty_points_earned INT DEFAULT 0,
    is_void BIT DEFAULT 0,
    void_reason VARCHAR(200),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_transaction_number UNIQUE (transaction_number),
    CONSTRAINT fk_transaction_store FOREIGN KEY (store_id) REFERENCES dbo.dim_store(store_id),
    CONSTRAINT fk_transaction_register FOREIGN KEY (register_id) REFERENCES dbo.dim_register(register_id),
    CONSTRAINT fk_transaction_customer FOREIGN KEY (customer_id) REFERENCES dbo.dim_customer(customer_id),
    CONSTRAINT fk_transaction_employee FOREIGN KEY (employee_id) REFERENCES dbo.dim_employee(employee_id),
    CONSTRAINT fk_transaction_payment FOREIGN KEY (payment_method_id) REFERENCES dbo.dim_payment_method(payment_method_id),
    CONSTRAINT fk_transaction_promotion FOREIGN KEY (promotion_id) REFERENCES dbo.dim_promotion(promotion_id)
);
GO

-- 20. FACT_SALES_LINE_ITEM
CREATE TABLE dbo.fact_sales_line_item (
    line_item_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    product_id INT NOT NULL,
    line_number INT,
    quantity INT NOT NULL,
    unit_price DECIMAL(12,2),
    unit_cost DECIMAL(12,2),
    discount_amount DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(12,2),
    line_total DECIMAL(12,2),
    promotion_id INT,
    is_return BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_lineitem_transaction FOREIGN KEY (transaction_id) REFERENCES dbo.fact_sales_transaction(transaction_id),
    CONSTRAINT fk_lineitem_product FOREIGN KEY (product_id) REFERENCES dbo.dim_product(product_id),
    CONSTRAINT fk_lineitem_promotion FOREIGN KEY (promotion_id) REFERENCES dbo.dim_promotion(promotion_id)
);
GO

-- 21. FACT_INVENTORY
CREATE TABLE dbo.fact_inventory (
    inventory_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    product_id INT NOT NULL,
    store_id INT,
    warehouse_id INT,
    quantity_on_hand INT,
    quantity_reserved INT DEFAULT 0,
    quantity_available AS (quantity_on_hand - quantity_reserved),
    quantity_on_order INT DEFAULT 0,
    last_restock_date DATE,
    last_sold_date DATE,
    last_count_date DATE,
    snapshot_date DATE NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_inventory_product FOREIGN KEY (product_id) REFERENCES dbo.dim_product(product_id),
    CONSTRAINT fk_inventory_store FOREIGN KEY (store_id) REFERENCES dbo.dim_store(store_id),
    CONSTRAINT fk_inventory_warehouse FOREIGN KEY (warehouse_id) REFERENCES dbo.dim_warehouse(warehouse_id)
);
GO

-- 22. FACT_PURCHASE_ORDER
CREATE TABLE dbo.fact_purchase_order (
    po_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    po_number VARCHAR(50) NOT NULL,
    supplier_id INT NOT NULL,
    warehouse_id INT,
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    status VARCHAR(30),
    subtotal DECIMAL(14,2),
    tax_amount DECIMAL(12,2),
    shipping_cost DECIMAL(10,2),
    total_amount DECIMAL(14,2),
    created_by INT,
    approved_by INT,
    approved_date DATE,
    notes NVARCHAR(MAX),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_po_number UNIQUE (po_number),
    CONSTRAINT fk_po_supplier FOREIGN KEY (supplier_id) REFERENCES dbo.dim_supplier(supplier_id),
    CONSTRAINT fk_po_warehouse FOREIGN KEY (warehouse_id) REFERENCES dbo.dim_warehouse(warehouse_id),
    CONSTRAINT fk_po_created_by FOREIGN KEY (created_by) REFERENCES dbo.dim_employee(employee_id),
    CONSTRAINT fk_po_approved_by FOREIGN KEY (approved_by) REFERENCES dbo.dim_employee(employee_id)
);
GO

-- 23. FACT_PURCHASE_ORDER_LINE
CREATE TABLE dbo.fact_purchase_order_line (
    po_line_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    po_id BIGINT NOT NULL,
    product_id INT NOT NULL,
    line_number INT,
    quantity_ordered INT NOT NULL,
    quantity_received INT DEFAULT 0,
    quantity_rejected INT DEFAULT 0,
    unit_cost DECIMAL(12,2),
    line_total DECIMAL(14,2),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_poline_po FOREIGN KEY (po_id) REFERENCES dbo.fact_purchase_order(po_id),
    CONSTRAINT fk_poline_product FOREIGN KEY (product_id) REFERENCES dbo.dim_product(product_id)
);
GO

-- 24. FACT_ORDER
CREATE TABLE dbo.fact_order (
    order_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL,
    customer_id BIGINT NOT NULL,
    order_date DATETIME NOT NULL,
    order_source VARCHAR(30),
    order_status VARCHAR(30),
    shipping_address_line1 VARCHAR(255),
    shipping_address_line2 VARCHAR(255),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(100),
    shipping_postal_code VARCHAR(20),
    shipping_country VARCHAR(100),
    billing_address_line1 VARCHAR(255),
    billing_city VARCHAR(100),
    billing_state VARCHAR(100),
    billing_postal_code VARCHAR(20),
    subtotal DECIMAL(12,2),
    shipping_cost DECIMAL(10,2),
    discount_amount DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    shipping_method_id INT,
    promotion_id INT,
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    fulfillment_store_id INT,
    fulfillment_warehouse_id INT,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME,
    CONSTRAINT uq_order_number UNIQUE (order_number),
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES dbo.dim_customer(customer_id),
    CONSTRAINT fk_order_shipping FOREIGN KEY (shipping_method_id) REFERENCES dbo.dim_shipping_method(shipping_method_id),
    CONSTRAINT fk_order_promotion FOREIGN KEY (promotion_id) REFERENCES dbo.dim_promotion(promotion_id),
    CONSTRAINT fk_order_store FOREIGN KEY (fulfillment_store_id) REFERENCES dbo.dim_store(store_id),
    CONSTRAINT fk_order_warehouse FOREIGN KEY (fulfillment_warehouse_id) REFERENCES dbo.dim_warehouse(warehouse_id)
);
GO

-- 25. FACT_ORDER_LINE
CREATE TABLE dbo.fact_order_line (
    order_line_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id INT NOT NULL,
    line_number INT,
    quantity_ordered INT NOT NULL,
    quantity_shipped INT DEFAULT 0,
    quantity_cancelled INT DEFAULT 0,
    unit_price DECIMAL(12,2),
    discount_amount DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(12,2),
    line_total DECIMAL(12,2),
    line_status VARCHAR(30),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_orderline_order FOREIGN KEY (order_id) REFERENCES dbo.fact_order(order_id),
    CONSTRAINT fk_orderline_product FOREIGN KEY (product_id) REFERENCES dbo.dim_product(product_id)
);
GO

-- 26. FACT_RETURN
CREATE TABLE dbo.fact_return (
    return_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    return_number VARCHAR(50) NOT NULL,
    original_transaction_id BIGINT,
    original_order_id BIGINT,
    customer_id BIGINT,
    store_id INT,
    employee_id INT,
    return_date DATETIME NOT NULL,
    return_reason_id INT,
    return_type VARCHAR(30),
    product_id INT,
    quantity INT,
    refund_amount DECIMAL(12,2),
    restocking_fee DECIMAL(10,2) DEFAULT 0,
    product_condition VARCHAR(30),
    disposition VARCHAR(30),
    status VARCHAR(30),
    notes NVARCHAR(MAX),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT uq_return_number UNIQUE (return_number),
    CONSTRAINT fk_return_transaction FOREIGN KEY (original_transaction_id) REFERENCES dbo.fact_sales_transaction(transaction_id),
    CONSTRAINT fk_return_order FOREIGN KEY (original_order_id) REFERENCES dbo.fact_order(order_id),
    CONSTRAINT fk_return_customer FOREIGN KEY (customer_id) REFERENCES dbo.dim_customer(customer_id),
    CONSTRAINT fk_return_store FOREIGN KEY (store_id) REFERENCES dbo.dim_store(store_id),
    CONSTRAINT fk_return_employee FOREIGN KEY (employee_id) REFERENCES dbo.dim_employee(employee_id),
    CONSTRAINT fk_return_reason FOREIGN KEY (return_reason_id) REFERENCES dbo.dim_return_reason(reason_id),
    CONSTRAINT fk_return_product FOREIGN KEY (product_id) REFERENCES dbo.dim_product(product_id)
);
GO

-- 27. FACT_EMPLOYEE_SCHEDULE
CREATE TABLE dbo.fact_employee_schedule (
    schedule_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    employee_id INT NOT NULL,
    store_id INT,
    warehouse_id INT,
    schedule_date DATE NOT NULL,
    shift_start TIME,
    shift_end TIME,
    scheduled_hours DECIMAL(5,2),
    break_minutes INT,
    position VARCHAR(50),
    is_overtime BIT DEFAULT 0,
    status VARCHAR(20),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_schedule_employee FOREIGN KEY (employee_id) REFERENCES dbo.dim_employee(employee_id),
    CONSTRAINT fk_schedule_store FOREIGN KEY (store_id) REFERENCES dbo.dim_store(store_id),
    CONSTRAINT fk_schedule_warehouse FOREIGN KEY (warehouse_id) REFERENCES dbo.dim_warehouse(warehouse_id)
);
GO

-- 28. FACT_DAILY_SALES_SUMMARY
CREATE TABLE dbo.fact_daily_sales_summary (
    summary_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    store_id INT NOT NULL,
    business_date DATE NOT NULL,
    total_transactions INT,
    total_customers INT,
    total_units_sold INT,
    gross_sales DECIMAL(14,2),
    total_discounts DECIMAL(12,2),
    total_returns DECIMAL(12,2),
    net_sales DECIMAL(14,2),
    total_tax DECIMAL(12,2),
    average_basket_size DECIMAL(10,2),
    average_items_per_transaction DECIMAL(6,2),
    labor_hours DECIMAL(8,2),
    labor_cost DECIMAL(12,2),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_summary_store FOREIGN KEY (store_id) REFERENCES dbo.dim_store(store_id)
);
GO

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Fact table indexes
CREATE INDEX ix_transaction_date ON dbo.fact_sales_transaction(transaction_date);
CREATE INDEX ix_transaction_store ON dbo.fact_sales_transaction(store_id);
CREATE INDEX ix_transaction_customer ON dbo.fact_sales_transaction(customer_id);
CREATE INDEX ix_lineitem_transaction ON dbo.fact_sales_line_item(transaction_id);
CREATE INDEX ix_lineitem_product ON dbo.fact_sales_line_item(product_id);
CREATE INDEX ix_inventory_product ON dbo.fact_inventory(product_id);
CREATE INDEX ix_inventory_store ON dbo.fact_inventory(store_id);
CREATE INDEX ix_order_customer ON dbo.fact_order(customer_id);
CREATE INDEX ix_order_date ON dbo.fact_order(order_date);
CREATE INDEX ix_po_supplier ON dbo.fact_purchase_order(supplier_id);
CREATE INDEX ix_return_customer ON dbo.fact_return(customer_id);
CREATE INDEX ix_summary_date ON dbo.fact_daily_sales_summary(business_date);
GO

-- =====================================================
-- EXTENDED PROPERTIES FOR COLUMN DEFINITIONS
-- =====================================================

-- Example: Adding descriptions to key tables
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Unique customer identifier', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'dim_customer',
    @level2type = N'COLUMN', @level2name = 'customer_id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Customer first name', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'dim_customer',
    @level2type = N'COLUMN', @level2name = 'first_name';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Stock Keeping Unit - internal product code', 
    @level0type = N'SCHEMA', @level0name = 'dbo',
    @level1type = N'TABLE',  @level1name = 'dim_product',
    @level2type = N'COLUMN', @level2name = 'sku';
GO

PRINT 'Retail Enterprise Database schema created successfully!';
GO
