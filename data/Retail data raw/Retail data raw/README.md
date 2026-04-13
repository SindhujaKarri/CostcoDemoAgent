# Retail Enterprise Dataset - For Enterprise IQ
## Non AI-Ready Test Dataset with Data Quality Issues

---

## Quick Summary

| Metric | Value |
|--------|-------|
| **Total Tables** | 30 |
| **Azure SQL Tables** | 28 |
| **Azure Blob Tables** | 2 |
| **Business Domains** | 12 |
| **Total Records** | ~92,000+ |
| **Foreign Key Relationships** | 42 |

---

## Domains Covered

1. **Store Operations** - Regions, stores, registers, daily summaries
2. **Product Management** - Categories, brands, products
3. **Inventory Management** - Warehouses, stock levels
4. **Customer Management** - Segments, loyalty tiers, profiles
5. **Sales & Transactions** - POS transactions, line items, payments
6. **Order Management** - E-commerce orders, fulfillment
7. **Supply Chain** - Suppliers, purchase orders
8. **Human Resources** - Departments, employees, schedules
9. **Finance & Accounting** - Payment methods
10. **Marketing & Promotions** - Campaigns, discounts
11. **Customer Service** - Returns, complaints, feedback
12. **Analytics & Reporting** - Daily summaries, image metadata

---

## Data Quality Issues (Non AI-Ready)

This dataset intentionally contains the following data quality problems:

### 1. Missing Values (~5-15% per table)
- NULL emails, phones in dim_customer
- Missing manager assignments in dim_employee
- Empty category references

### 2. Inconsistent Formats
- **Dates**: 'YYYY-MM-DD', 'MM/DD/YYYY', 'DD-Mon-YYYY', Unix timestamps
- **Phones**: '(555) 123-4567', '555-123-4567', '5551234567', '+1-555-123-4567'
- **Names**: Mixed case, ALL CAPS, lowercase
- **Booleans**: '1', 'true', 'True', 'Y', 'Yes' vs '0', 'false', 'N', 'No'

### 3. Inconsistent Casing
- Store types: 'Flagship', 'FLAGSHIP', 'standard', 'Standard'
- Order sources: 'Web', 'WEB', 'Mobile', 'MOBILE'

### 4. Invalid/Orphan Records
- Orders referencing non-existent customers (customer_id = 999999)
- Stores with invalid region_id = 999
- Future dates in historical transactions

### 5. Data Anomalies
- Negative inventory quantities
- Zero or negative prices
- Cost higher than price
- Extreme outlier transaction amounts

### 6. Encoding Issues
- Special characters: José, François, Müller, Nguyễn, 田中

---

## Record Counts

### Dimension Tables (Azure SQL)
| Table | Records |
|-------|---------|
| dim_region | 8 |
| dim_store | 50 |
| dim_category | 24 |
| dim_brand | 15 |
| dim_product | 500 |
| dim_customer_segment | 6 |
| dim_loyalty_tier | 4 |
| dim_customer | 2,000 |
| dim_department | 10 |
| dim_job_title | 12 |
| dim_employee | 300 |
| dim_supplier | 50 |
| dim_warehouse | 7 |
| dim_payment_method | 11 |
| dim_promotion | 8 |
| dim_register | 277 |
| dim_shipping_method | 6 |
| dim_return_reason | 9 |

### Fact Tables (Azure SQL)
| Table | Records |
|-------|---------|
| fact_sales_transaction | 10,000 |
| fact_sales_line_item | 44,719 |
| fact_inventory | 6,100 |
| fact_order | 3,000 |
| fact_order_line | 10,576 |
| fact_purchase_order | 500 |
| fact_purchase_order_line | 2,725 |
| fact_return | 500 |
| fact_employee_schedule | 5,000 |
| fact_daily_sales_summary | 5,000 |

### Blob Storage Tables
| Table | Records |
|-------|---------|
| raw_customer_feedback | 1,000 |
| raw_product_images | 800 |

---

## File Structure

```
retail_enterprise_dataset/
├── README.md                    # This file
├── ontology/
│   └── retail_enterprise_ontology.md   #  Complete schema ontology
├── schema/
│   └── schema_reference.md      # Schema documentation with column definitions
├── ddl/
│   └── azure_sql_ddl.sql        # Azure SQL CREATE TABLE statements
├── data/
│   ├── dim_*.csv                # Dimension table data (18 files)
│   └── fact_*.csv               # Fact table data (10 files)
├── blob_data/
│   ├── raw_customer_feedback.csv/json
│   └── raw_product_images.csv/json
└── data_generator.py            # Python script to regenerate data
```

---

## For Kotesh

The **retail_enterprise_ontology.md** in the `/ontology` folder contains:
- Complete ER diagrams
- All 42 relationships mapped
- Column definitions
- Storage distribution (SQL vs Blob)
- Use cases for Enterprise IQ integration

---

**Generated:** January 19, 2026
**Version:** 1.0
