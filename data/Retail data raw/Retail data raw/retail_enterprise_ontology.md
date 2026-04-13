# Retail Enterprise Data Ontology
## Final Schema Documentation for Enterprise IQ Integration


---

## 1. EXECUTIVE SUMMARY

This document presents the complete ontology schema for the Retail Enterprise Dataset, designed to support data quality assessment workflows in Enterprise IQ. The dataset contains **30 tables** across **12 business domains**, stored in **Azure SQL Database** (28 tables) and **Azure Blob Storage** (2 tables).

**Key Statistics:**
- Total Tables: 30
- Azure SQL Tables: 28
- Azure Blob Tables: 2
- Business Domains: 12
- Total Relationships: 42 foreign key relationships
- Self-Referencing Hierarchies: 3 (Category, Department, Employee)

---

## 2. DOMAIN COVERAGE

| # | Domain | Tables | Description |
|---|--------|--------|-------------|
| 1 | **Store Operations** | dim_region, dim_store, dim_register, fact_daily_sales_summary | Physical retail locations, POS systems, daily metrics |
| 2 | **Product Management** | dim_category, dim_brand, dim_product | Product catalog, hierarchies, pricing |
| 3 | **Inventory Management** | dim_warehouse, fact_inventory | Stock levels, warehouse operations |
| 4 | **Customer Management** | dim_customer, dim_customer_segment, dim_loyalty_tier | Customer profiles, segmentation, loyalty programs |
| 5 | **Sales & Transactions** | fact_sales_transaction, fact_sales_line_item | POS transactions, payment processing |
| 6 | **Order Management** | fact_order, fact_order_line, dim_shipping_method | E-commerce orders, fulfillment, delivery |
| 7 | **Supply Chain** | dim_supplier, fact_purchase_order, fact_purchase_order_line | Vendor management, procurement |
| 8 | **Human Resources** | dim_department, dim_job_title, dim_employee, fact_employee_schedule | Workforce management, scheduling |
| 9 | **Finance & Accounting** | dim_payment_method | Payment processing, reconciliation |
| 10 | **Marketing & Promotions** | dim_promotion | Campaign management, discounts |
| 11 | **Customer Service** | dim_return_reason, fact_return, raw_customer_feedback | Returns, complaints, feedback |
| 12 | **Analytics & Reporting** | fact_daily_sales_summary, raw_product_images | Aggregated metrics, media assets |

---

## 3. ENTITY RELATIONSHIP DIAGRAM

```
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                           RETAIL ENTERPRISE DATA MODEL                                  ║
╠════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                         ║
║    ┌──────────────────────────────────────────────────────────────────────────────┐    ║
║    │                         STORE OPERATIONS DOMAIN                               │    ║
║    │                                                                               │    ║
║    │     ┌─────────────┐         ┌─────────────┐         ┌─────────────────────┐  │    ║
║    │     │ DIM_REGION  │◄────────│  DIM_STORE  │◄────────│ FACT_DAILY_SALES    │  │    ║
║    │     │             │    FK   │             │    FK   │ _SUMMARY            │  │    ║
║    │     │ region_id   │─────────│ region_id   │         │                     │  │    ║
║    │     │ region_code │         │ store_id    │─────────│ store_id            │  │    ║
║    │     │ region_name │         │ store_code  │         │ summary_date        │  │    ║
║    │     │ country     │         │ manager_id  │──┐      │ total_revenue       │  │    ║
║    │     │ timezone    │         └─────────────┘  │      └─────────────────────┘  │    ║
║    │     └─────────────┘                │         │                               │    ║
║    │                                    │         │      ┌─────────────────────┐  │    ║
║    │                                    ▼         │      │   DIM_REGISTER      │  │    ║
║    │                           ┌─────────────┐   │      │                     │  │    ║
║    │                           │DIM_WAREHOUSE│   │      │ register_id         │  │    ║
║    │                           │             │   │      │ store_id ───────────┤  │    ║
║    │                           │warehouse_id │   │      │ register_number     │  │    ║
║    │                           │ region_id   │───│      │ status              │  │    ║
║    │                           └─────────────┘   │      └─────────────────────┘  │    ║
║    └───────────────────────────────────│─────────│────────────────────────────────┘    ║
║                                        │         │                                      ║
║    ┌───────────────────────────────────│─────────│────────────────────────────────┐    ║
║    │                         HUMAN RESOURCES DOMAIN                                │    ║
║    │                                   │         │                                 │    ║
║    │  ┌──────────────┐  ┌──────────────┴─┐      │      ┌─────────────────────┐   │    ║
║    │  │DIM_DEPARTMENT│  │  DIM_EMPLOYEE  │◄─────┘      │FACT_EMPLOYEE_SCHEDULE│  │    ║
║    │  │              │  │                │             │                     │   │    ║
║    │  │department_id │──│ department_id  │◄────────────│ employee_id         │   │    ║
║    │  │parent_dept_id│  │ employee_id    │             │ schedule_date       │   │    ║
║    │  │ (self-ref)   │  │ manager_id ────┤(self-ref)   │ shift_start         │   │    ║
║    │  └──────────────┘  │ job_title_id ──┤             │ shift_end           │   │    ║
║    │                    │ store_id ──────┤             └─────────────────────┘   │    ║
║    │  ┌──────────────┐  │ warehouse_id ──┤                                       │    ║
║    │  │DIM_JOB_TITLE │──┘                │                                       │    ║
║    │  │              │                   │                                       │    ║
║    │  │ job_title_id │                   │                                       │    ║
║    │  │ title_name   │                   │                                       │    ║
║    │  └──────────────┘                   │                                       │    ║
║    └─────────────────────────────────────│───────────────────────────────────────┘    ║
║                                          │                                             ║
║    ┌─────────────────────────────────────│───────────────────────────────────────┐    ║
║    │                         PRODUCT MANAGEMENT DOMAIN                            │    ║
║    │                                     │                                        │    ║
║    │  ┌──────────────┐  ┌──────────────┐│     ┌───────────────────────────────┐  │    ║
║    │  │ DIM_CATEGORY │  │  DIM_BRAND   ││     │         DIM_PRODUCT           │  │    ║
║    │  │              │  │              ││     │                               │  │    ║
║    │  │ category_id  │──│              ││     │ product_id                    │  │    ║
║    │  │parent_cat_id │  │ brand_id ────┼┼─────│ category_id                   │  │    ║
║    │  │ (self-ref)   │──┼──────────────┼┼─────│ brand_id                      │  │    ║
║    │  │category_level│  │ brand_name   ││     │ sku (unique)                  │  │    ║
║    │  │category_path │  │ manufacturer ││     │ unit_cost / unit_price        │  │    ║
║    │  └──────────────┘  └──────────────┘│     │ is_perishable / shelf_life    │  │    ║
║    │                                    │     └───────────────────────────────┘  │    ║
║    └────────────────────────────────────│────────────────────────────────────────┘    ║
║                                         │                                             ║
║    ┌────────────────────────────────────│────────────────────────────────────────┐    ║
║    │                         CUSTOMER MANAGEMENT DOMAIN                           │    ║
║    │                                    │                                         │    ║
║    │  ┌───────────────────┐  ┌─────────┴────────┐  ┌────────────────────┐        │    ║
║    │  │DIM_CUSTOMER_SEGMENT│  │   DIM_CUSTOMER   │  │ DIM_LOYALTY_TIER   │        │    ║
║    │  │                   │  │                  │  │                    │        │    ║
║    │  │ segment_id ───────┼──│ segment_id       │  │ tier_id ───────────┤        │    ║
║    │  │ segment_name      │  │ customer_id      │──│                    │        │    ║
║    │  │ min_annual_spend  │  │ loyalty_tier_id ─┼──│ tier_name          │        │    ║
║    │  └───────────────────┘  │ preferred_store──┼──│ min_points         │        │    ║
║    │                         │ loyalty_points   │  │ discount_pct       │        │    ║
║    │                         └──────────────────┘  └────────────────────┘        │    ║
║    └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                        ║
║    ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║    │                         SALES & TRANSACTIONS DOMAIN                          │    ║
║    │                                                                              │    ║
║    │  ┌─────────────────────────────────┐    ┌───────────────────────────────┐   │    ║
║    │  │     FACT_SALES_TRANSACTION      │    │    FACT_SALES_LINE_ITEM       │   │    ║
║    │  │                                 │    │                               │   │    ║
║    │  │ transaction_id ─────────────────┼────│ transaction_id                │   │    ║
║    │  │ store_id ◄──────────────────────┤    │ line_item_id                  │   │    ║
║    │  │ register_id ◄───────────────────┤    │ product_id ◄──────────────────┤   │    ║
║    │  │ customer_id ◄───────────────────┤    │ quantity                      │   │    ║
║    │  │ employee_id ◄───────────────────┤    │ unit_price / line_total       │   │    ║
║    │  │ payment_method_id ◄─────────────┤    │ discount_amount               │   │    ║
║    │  │ promotion_id ◄──────────────────┤    │ promotion_id ◄────────────────┤   │    ║
║    │  │ transaction_total               │    │ tax_amount                    │   │    ║
║    │  └─────────────────────────────────┘    └───────────────────────────────┘   │    ║
║    │                                                                              │    ║
║    │  ┌─────────────────────┐  ┌─────────────────────┐                           │    ║
║    │  │ DIM_PAYMENT_METHOD  │  │   DIM_PROMOTION     │                           │    ║
║    │  │                     │  │                     │                           │    ║
║    │  │ payment_method_id   │  │ promotion_id        │                           │    ║
║    │  │ method_name         │  │ promotion_code      │                           │    ║
║    │  │ method_type         │  │ discount_type       │                           │    ║
║    │  └─────────────────────┘  │ discount_value      │                           │    ║
║    │                           │ start_date/end_date │                           │    ║
║    │                           └─────────────────────┘                           │    ║
║    └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                        ║
║    ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║    │                         ORDER MANAGEMENT DOMAIN                              │    ║
║    │                                                                              │    ║
║    │  ┌─────────────────────────────────┐    ┌───────────────────────────────┐   │    ║
║    │  │          FACT_ORDER             │    │      FACT_ORDER_LINE          │   │    ║
║    │  │                                 │    │                               │   │    ║
║    │  │ order_id ───────────────────────┼────│ order_id                      │   │    ║
║    │  │ customer_id ◄───────────────────┤    │ order_line_id                 │   │    ║
║    │  │ shipping_method_id ◄────────────┤    │ product_id ◄──────────────────┤   │    ║
║    │  │ promotion_id ◄──────────────────┤    │ quantity / unit_price         │   │    ║
║    │  │ fulfillment_store_id ◄──────────┤    │ line_total                    │   │    ║
║    │  │ fulfillment_warehouse_id ◄──────┤    │ fulfillment_status            │   │    ║
║    │  │ order_status / order_source     │    └───────────────────────────────┘   │    ║
║    │  │ order_date / shipped_date       │                                        │    ║
║    │  └─────────────────────────────────┘    ┌───────────────────────────────┐   │    ║
║    │                                         │   DIM_SHIPPING_METHOD         │   │    ║
║    │                                         │                               │   │    ║
║    │                                         │ shipping_method_id            │   │    ║
║    │                                         │ method_name / carrier         │   │    ║
║    │                                         │ estimated_days / base_cost    │   │    ║
║    │                                         └───────────────────────────────┘   │    ║
║    └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                        ║
║    ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║    │                         SUPPLY CHAIN DOMAIN                                  │    ║
║    │                                                                              │    ║
║    │  ┌─────────────────────┐  ┌─────────────────────────┐  ┌───────────────────┐│    ║
║    │  │    DIM_SUPPLIER     │  │  FACT_PURCHASE_ORDER    │  │FACT_PO_LINE       ││    ║
║    │  │                     │  │                         │  │                   ││    ║
║    │  │ supplier_id ────────┼──│ supplier_id             │  │ po_id ◄───────────┤│    ║
║    │  │ supplier_code       │  │ po_id ──────────────────┼──│ po_line_id        ││    ║
║    │  │ company_name        │  │ warehouse_id ◄──────────┤  │ product_id ◄──────┤│    ║
║    │  │ payment_terms       │  │ created_by_employee_id ◄┤  │ quantity_ordered  ││    ║
║    │  │ lead_time_days      │  │ approved_by_employee_id◄┤  │ unit_cost         ││    ║
║    │  └─────────────────────┘  │ po_status / total_amount│  │ quantity_received ││    ║
║    │                           └─────────────────────────┘  └───────────────────┘│    ║
║    └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                        ║
║    ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║    │                         INVENTORY DOMAIN                                     │    ║
║    │                                                                              │    ║
║    │  ┌─────────────────────────────────────────────────────────────────────┐    │    ║
║    │  │                        FACT_INVENTORY                                │    │    ║
║    │  │                                                                      │    │    ║
║    │  │  inventory_id | product_id ◄── | store_id ◄── | warehouse_id ◄──    │    │    ║
║    │  │  quantity_on_hand | quantity_reserved | quantity_available (computed)│    │    ║
║    │  │  reorder_point | last_count_date | last_receipt_date                 │    │    ║
║    │  └─────────────────────────────────────────────────────────────────────┘    │    ║
║    └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                        ║
║    ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║    │                         CUSTOMER SERVICE DOMAIN                              │    ║
║    │                                                                              │    ║
║    │  ┌─────────────────────┐  ┌─────────────────────────────────────────────┐   │    ║
║    │  │  DIM_RETURN_REASON  │  │              FACT_RETURN                     │   │    ║
║    │  │                     │  │                                             │   │    ║
║    │  │ return_reason_id ───┼──│ return_reason_id                            │   │    ║
║    │  │ reason_code         │  │ return_id                                   │   │    ║
║    │  │ reason_description  │  │ original_transaction_id ◄── (sales)         │   │    ║
║    │  │ requires_inspection │  │ original_order_id ◄── (orders)              │   │    ║
║    │  │ restocking_fee_pct  │  │ customer_id ◄── | store_id ◄──              │   │    ║
║    │  └─────────────────────┘  │ processed_by_employee_id ◄──                │   │    ║
║    │                           │ product_id ◄── | return_status              │   │    ║
║    │                           │ refund_amount / refund_method               │   │    ║
║    │                           └─────────────────────────────────────────────┘   │    ║
║    └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                        ║
║    ┌─────────────────────────────────────────────────────────────────────────────┐    ║
║    │                         AZURE BLOB STORAGE (Unstructured)                    │    ║
║    │                                                                              │    ║
║    │  ┌─────────────────────────────┐    ┌─────────────────────────────────┐     │    ║
║    │  │   RAW_CUSTOMER_FEEDBACK     │    │     RAW_PRODUCT_IMAGES          │     │    ║
║    │  │                             │    │                                 │     │    ║
║    │  │ feedback_id                 │    │ image_id                        │     │    ║
║    │  │ customer_id ◄── (dim)       │    │ product_id ◄── (dim)            │     │    ║
║    │  │ store_id ◄── (dim)          │    │ image_type                      │     │    ║
║    │  │ order_id ◄── (fact)         │    │ blob_path / image_url           │     │    ║
║    │  │ feedback_text (unstructured)│    │ file_size / dimensions          │     │    ║
║    │  │ rating / sentiment_score    │    │ alt_text / uploaded_date        │     │    ║
║    │  │ feedback_channel            │    │                                 │     │    ║
║    │  └─────────────────────────────┘    └─────────────────────────────────┘     │    ║
║    └─────────────────────────────────────────────────────────────────────────────┘    ║
║                                                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. COMPLETE TABLE INVENTORY

### 4.1 Azure SQL Tables (28)

| # | Table Name | Type | Domain | Primary Key | Row Count |
|---|------------|------|--------|-------------|-----------|
| 1 | dim_region | Dimension | Store Operations | region_id | 8 |
| 2 | dim_store | Dimension | Store Operations | store_id | 50 |
| 3 | dim_register | Dimension | Store Operations | register_id | ~250 |
| 4 | dim_category | Dimension | Product Management | category_id | 24 |
| 5 | dim_brand | Dimension | Product Management | brand_id | 15 |
| 6 | dim_product | Dimension | Product Management | product_id | 500 |
| 7 | dim_customer_segment | Dimension | Customer Management | segment_id | 6 |
| 8 | dim_loyalty_tier | Dimension | Customer Management | tier_id | 4 |
| 9 | dim_customer | Dimension | Customer Management | customer_id | 2,000 |
| 10 | dim_department | Dimension | Human Resources | department_id | 10 |
| 11 | dim_job_title | Dimension | Human Resources | job_title_id | 12 |
| 12 | dim_employee | Dimension | Human Resources | employee_id | 300 |
| 13 | dim_supplier | Dimension | Supply Chain | supplier_id | 50 |
| 14 | dim_warehouse | Dimension | Inventory | warehouse_id | 7 |
| 15 | dim_payment_method | Dimension | Finance | payment_method_id | 11 |
| 16 | dim_promotion | Dimension | Marketing | promotion_id | 8 |
| 17 | dim_shipping_method | Dimension | Order Management | shipping_method_id | 6 |
| 18 | dim_return_reason | Dimension | Customer Service | return_reason_id | 9 |
| 19 | fact_sales_transaction | Fact | Sales | transaction_id | 10,000 |
| 20 | fact_sales_line_item | Fact | Sales | line_item_id | ~40,000 |
| 21 | fact_inventory | Fact | Inventory | inventory_id | ~3,000 |
| 22 | fact_order | Fact | Order Management | order_id | 3,000 |
| 23 | fact_order_line | Fact | Order Management | order_line_id | ~12,000 |
| 24 | fact_purchase_order | Fact | Supply Chain | po_id | 500 |
| 25 | fact_purchase_order_line | Fact | Supply Chain | po_line_id | ~3,000 |
| 26 | fact_return | Fact | Customer Service | return_id | 500 |
| 27 | fact_employee_schedule | Fact | Human Resources | schedule_id | 5,000 |
| 28 | fact_daily_sales_summary | Fact | Analytics | summary_id | ~5,000 |

### 4.2 Azure Blob Storage Tables (2)

| # | Table Name | Type | Domain | Format | Row Count |
|---|------------|------|--------|--------|-----------|
| 29 | raw_customer_feedback | Unstructured | Customer Service | JSON/CSV | 1,000 |
| 30 | raw_product_images | Unstructured | Analytics | JSON/CSV | 800 |

---

## 5. RELATIONSHIP MATRIX

### 5.1 Foreign Key Relationships

| Source Table | Source Column | Target Table | Target Column | Relationship |
|--------------|---------------|--------------|---------------|--------------|
| dim_store | region_id | dim_region | region_id | Many-to-One |
| dim_store | manager_employee_id | dim_employee | employee_id | Many-to-One |
| dim_register | store_id | dim_store | store_id | Many-to-One |
| dim_category | parent_category_id | dim_category | category_id | Self-Reference |
| dim_product | category_id | dim_category | category_id | Many-to-One |
| dim_product | brand_id | dim_brand | brand_id | Many-to-One |
| dim_customer | customer_segment_id | dim_customer_segment | segment_id | Many-to-One |
| dim_customer | loyalty_tier_id | dim_loyalty_tier | tier_id | Many-to-One |
| dim_customer | preferred_store_id | dim_store | store_id | Many-to-One |
| dim_department | parent_department_id | dim_department | department_id | Self-Reference |
| dim_employee | department_id | dim_department | department_id | Many-to-One |
| dim_employee | job_title_id | dim_job_title | job_title_id | Many-to-One |
| dim_employee | store_id | dim_store | store_id | Many-to-One |
| dim_employee | warehouse_id | dim_warehouse | warehouse_id | Many-to-One |
| dim_employee | manager_id | dim_employee | employee_id | Self-Reference |
| dim_warehouse | region_id | dim_region | region_id | Many-to-One |
| fact_sales_transaction | store_id | dim_store | store_id | Many-to-One |
| fact_sales_transaction | register_id | dim_register | register_id | Many-to-One |
| fact_sales_transaction | customer_id | dim_customer | customer_id | Many-to-One |
| fact_sales_transaction | employee_id | dim_employee | employee_id | Many-to-One |
| fact_sales_transaction | payment_method_id | dim_payment_method | payment_method_id | Many-to-One |
| fact_sales_transaction | promotion_id | dim_promotion | promotion_id | Many-to-One |
| fact_sales_line_item | transaction_id | fact_sales_transaction | transaction_id | Many-to-One |
| fact_sales_line_item | product_id | dim_product | product_id | Many-to-One |
| fact_sales_line_item | promotion_id | dim_promotion | promotion_id | Many-to-One |
| fact_inventory | product_id | dim_product | product_id | Many-to-One |
| fact_inventory | store_id | dim_store | store_id | Many-to-One |
| fact_inventory | warehouse_id | dim_warehouse | warehouse_id | Many-to-One |
| fact_order | customer_id | dim_customer | customer_id | Many-to-One |
| fact_order | shipping_method_id | dim_shipping_method | shipping_method_id | Many-to-One |
| fact_order | promotion_id | dim_promotion | promotion_id | Many-to-One |
| fact_order | fulfillment_store_id | dim_store | store_id | Many-to-One |
| fact_order | fulfillment_warehouse_id | dim_warehouse | warehouse_id | Many-to-One |
| fact_order_line | order_id | fact_order | order_id | Many-to-One |
| fact_order_line | product_id | dim_product | product_id | Many-to-One |
| fact_purchase_order | supplier_id | dim_supplier | supplier_id | Many-to-One |
| fact_purchase_order | warehouse_id | dim_warehouse | warehouse_id | Many-to-One |
| fact_purchase_order | created_by_employee_id | dim_employee | employee_id | Many-to-One |
| fact_purchase_order | approved_by_employee_id | dim_employee | employee_id | Many-to-One |
| fact_purchase_order_line | po_id | fact_purchase_order | po_id | Many-to-One |
| fact_purchase_order_line | product_id | dim_product | product_id | Many-to-One |
| fact_return | original_transaction_id | fact_sales_transaction | transaction_id | Many-to-One |
| fact_return | original_order_id | fact_order | order_id | Many-to-One |
| fact_return | customer_id | dim_customer | customer_id | Many-to-One |
| fact_return | store_id | dim_store | store_id | Many-to-One |
| fact_return | processed_by_employee_id | dim_employee | employee_id | Many-to-One |
| fact_return | product_id | dim_product | product_id | Many-to-One |
| fact_return | return_reason_id | dim_return_reason | return_reason_id | Many-to-One |
| fact_employee_schedule | employee_id | dim_employee | employee_id | Many-to-One |
| fact_employee_schedule | store_id | dim_store | store_id | Many-to-One |
| fact_daily_sales_summary | store_id | dim_store | store_id | Many-to-One |
| raw_customer_feedback | customer_id | dim_customer | customer_id | Many-to-One |
| raw_customer_feedback | store_id | dim_store | store_id | Many-to-One |
| raw_customer_feedback | order_id | fact_order | order_id | Many-to-One |
| raw_product_images | product_id | dim_product | product_id | Many-to-One |

---

## 6. DATA QUALITY ISSUES (Non AI-Ready)

This dataset intentionally includes data quality issues to support Enterprise IQ's data quality assessment capabilities:

### 6.1 Issue Categories

| Category | Description | Affected Tables | % of Records |
|----------|-------------|-----------------|--------------|
| **Missing Values** | NULL in required fields | dim_customer, dim_employee, dim_product | 5-15% |
| **Format Inconsistency** | Dates, phones, names in multiple formats | All tables | 10-20% |
| **Duplicate Records** | Same entity, different representations | dim_customer, dim_product | 2-5% |
| **Invalid Values** | Negative quantities, future dates, invalid emails | fact_inventory, fact_sales_transaction | 1-5% |
| **Referential Integrity** | Orphan foreign keys | fact_order, fact_return | 2-5% |
| **Type Inconsistency** | Numbers as strings, boolean variations | blob tables | 15-25% |
| **Outliers** | Extreme values outside normal range | fact_sales_transaction | 0.5-1% |
| **Encoding Issues** | Special characters, mixed encodings | dim_customer, raw_customer_feedback | 3-5% |

### 6.2 Specific Examples

**Date Format Variations:**
- `2024-05-15` (ISO)
- `05/15/2024` (US)
- `15-May-2024` (Abbreviated)
- `15.05.2024` (European)
- `1715731200` (Unix timestamp)

**Boolean Representations:**
- `1`, `0`
- `true`, `false`, `True`, `False`, `TRUE`, `FALSE`
- `Y`, `N`, `Yes`, `No`, `YES`, `NO`

**Phone Format Variations:**
- `(555) 123-4567`
- `555-123-4567`
- `5551234567`
- `+1-555-123-4567`
- `555.123.4567`

---

## 7. STORAGE ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AZURE ENVIRONMENT                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    AZURE SQL DATABASE                           │     │
│  │                                                                 │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │     │
│  │  │  DIMENSIONS  │  │    FACTS     │  │   INDEXES    │          │     │
│  │  │  (18 tables) │  │  (10 tables) │  │              │          │     │
│  │  │              │  │              │  │  • FK Indexes│          │     │
│  │  │  • Regions   │  │  • Sales     │  │  • Date Keys │          │     │
│  │  │  • Stores    │  │  • Orders    │  │  • Lookups   │          │     │
│  │  │  • Products  │  │  • Inventory │  │              │          │     │
│  │  │  • Customers │  │  • POs       │  │              │          │     │
│  │  │  • Employees │  │  • Returns   │  │              │          │     │
│  │  │  • ...       │  │  • ...       │  │              │          │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    AZURE BLOB STORAGE                           │     │
│  │                                                                 │     │
│  │  Container: retail-enterprise-raw/                              │     │
│  │  ├── customer_feedback/                                         │     │
│  │  │   ├── raw_customer_feedback.csv                             │     │
│  │  │   └── raw_customer_feedback.json                            │     │
│  │  └── product_images/                                            │     │
│  │      ├── raw_product_images.csv                                │     │
│  │      └── raw_product_images.json                               │     │
│  │                                                                 │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. COLUMN DEFINITIONS SUMMARY

### 8.1 Key Business Columns

| Column | Table(s) | Definition |
|--------|----------|------------|
| `sku` | dim_product | Stock Keeping Unit - unique internal product identifier |
| `upc` | dim_product | Universal Product Code - standard barcode |
| `quantity_available` | fact_inventory | Computed: quantity_on_hand - quantity_reserved |
| `loyalty_points_balance` | dim_customer | Current accumulated loyalty points |
| `transaction_type` | fact_sales_transaction | Sale, Return, Exchange, Void |
| `order_status` | fact_order | Pending, Confirmed, Processing, Shipped, Delivered, Cancelled |
| `po_status` | fact_purchase_order | Draft, Submitted, Approved, Shipped, Received, Cancelled |
| `return_status` | fact_return | Initiated, Received, Inspected, Approved, Rejected, Refunded |
| `is_perishable` | dim_product | Boolean - product requires expiration tracking |
| `shelf_life_days` | dim_product | Number of days until product expiration |
| `lead_time_days` | dim_supplier | Average days from order to delivery |
| `restocking_fee_pct` | dim_return_reason | Percentage fee for restocking returned items |

### 8.2 Audit Columns (Present in all tables)

| Column | Definition |
|--------|------------|
| `created_at` | Timestamp when record was created |
| `updated_at` | Timestamp of last modification |

---

## 9. USE CASES FOR ENTERPRISE IQ

This dataset supports the following data quality assessment scenarios:

1. **Missing Value Detection** - Identify NULLs in critical business fields
2. **Format Standardization** - Detect and remediate inconsistent date/phone/name formats
3. **Duplicate Detection** - Find and merge duplicate customer/product records
4. **Referential Integrity** - Identify orphan foreign keys and broken relationships
5. **Outlier Detection** - Flag abnormal transaction amounts and quantities
6. **Type Consistency** - Standardize boolean and numeric representations
7. **Completeness Scoring** - Calculate data completeness percentages per table
8. **Relationship Mapping** - Auto-discover FK relationships from data patterns

---

## 10. APPENDIX: FILE LOCATIONS

### Generated Files
```
/home/claude/retail_enterprise_data/
├── schema/
│   └── schema_reference.md          # Complete schema documentation
├── ddl/
│   └── azure_sql_ddl.sql            # Azure SQL CREATE statements
├── data/
│   ├── dim_*.csv                    # Dimension tables (18 files)
│   └── fact_*.csv                   # Fact tables (10 files)
├── blob_data/
│   ├── raw_customer_feedback.csv    # Feedback data (CSV)
│   ├── raw_customer_feedback.json   # Feedback data (JSON)
│   ├── raw_product_images.csv       # Image metadata (CSV)
│   └── raw_product_images.json      # Image metadata (JSON)
├── ontology/
│   └── retail_enterprise_ontology.md # This document
└── data_generator.py                 # Python script for data generation
```

---

